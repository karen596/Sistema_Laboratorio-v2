import re, pathlib

p = pathlib.Path('web_app.py')
src = p.read_text(encoding='utf-8')

def ensure_block(src, marker, block, before_marker=None):
    if marker in src:
        return src
    if before_marker and before_marker in src:
        pos = src.find(before_marker)
        return src[:pos] + block + "\n" + src[pos:]
    return src + "\n" + block

# A) Helper de preprocesamiento ORB (resize + CLAHE)
if '_preprocess_for_orb' not in src:
    block = r'''
def _preprocess_for_orb(img: np.ndarray) -> np.ndarray:
    try:
        if img is None:
            return img
        h, w = img.shape[:2]
        maxw = 640
        if w > maxw:
            scale = maxw/float(w)
            img = cv2.resize(img, (int(w*scale), int(h*scale)))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape)==3 else img
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        eq = clahe.apply(gray)
        return eq
    except Exception:
        return img
'''
    # Insertar antes de sección de errores para mantener orden
    before = '\n# =====================================================================\n# MANEJO DE ERRORES'
    src = ensure_block(src, '_preprocess_for_orb', block, before_marker=before)

# B) Loader slim (solo objetos reconocibles, límite por objeto)
if '_load_template_images_slim' not in src:
    block = r'''
def _load_template_images_slim(max_per_key: int = 12):
    """
    Carga plantillas SOLO de objetos registrados por admin (si existe reconocer=1),
    primero desde BD (objetos_imagenes.imagen) y luego desde FS imagenes/objetos/<slug>/...
    Limita el número de imágenes por objeto para evitar sobrecarga.
    Devuelve lista de tuplas (key, img_preprocesada_grayscale).
    """
    import re, os, cv2, numpy as np
    templates = []
    allow = set()
    # construir allow desde BD si es posible
    try:
        rows = db_manager.execute_query("SELECT nombre FROM objetos WHERE reconocer=1") or []
        allow = { re.sub(r"\s+", '_', re.sub(r"[^a-z0-9_\- ]+", '', (r['nombre'] or '').lower())).strip() for r in rows }
    except Exception:
        try:
            rows = db_manager.execute_query("SELECT nombre FROM objetos") or []
            allow = { re.sub(r"\s+", '_', re.sub(r"[^a-z0-9_\- ]+", '', (r['nombre'] or '').lower())).strip() for r in rows }
        except Exception:
            allow = set()

    counts = {}

    # 1) Desde BD
    try:
        rows = db_manager.execute_query("""
            SELECT o.nombre, oi.imagen
            FROM objetos_imagenes oi
            JOIN objetos o ON o.id = oi.objeto_id
        """) or []
        for r in rows:
            nm = (r.get('nombre') or '').lower()
            key = re.sub(r"\s+", '_', re.sub(r"[^a-z0-9_\- ]+", '', nm)).strip()
            if allow and key not in allow:
                continue
            if counts.get(key, 0) >= max_per_key:
                continue
            blob = r.get('imagen')
            if not blob:
                continue
            arr = np.frombuffer(blob, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                continue
            img = _preprocess_for_orb(img)
            templates.append((key, img))
            counts[key] = counts.get(key, 0) + 1
    except Exception:
        pass

    # 2) Desde FS: imagenes/objetos/<carpeta>/**
    try:
        base = os.path.join(IMG_ROOT, 'objetos')
        if os.path.isdir(base):
            for entry in os.listdir(base):
                folder_path = os.path.join(base, entry)
                if not os.path.isdir(folder_path):
                    continue
                key = re.sub(r"\s+", '_', re.sub(r"[^a-z0-9_\- ]+", '', (entry or '').lower())).strip()
                if allow and key not in allow:
                    continue
                for root, _, files in os.walk(folder_path):
                    for fn in files:
                        if not fn.lower().endswith(('.jpg', '.jpeg', '.png')):
                            continue
                        if counts.get(key, 0) >= max_per_key:
                            break
                        path = os.path.join(root, fn)
                        img = cv2.imread(path, cv2.IMREAD_COLOR)
                        if img is None:
                            continue
                        img = _preprocess_for_orb(img)
                        templates.append((key, img))
                        counts[key] = counts.get(key, 0) + 1
    except Exception:
        pass

    return templates
'''
    before = '\n# =====================================================================\n# MANEJO DE ERRORES'
    src = ensure_block(src, '_load_template_images_slim', block, before_marker=before)

# C) Endpoint rápido: /api/vision/debug_counts_fast
if "def vision_debug_counts_fast():" not in src:
    block = r'''
@app.get('/api/vision/debug_counts_fast')
def vision_debug_counts_fast():
    """
    Recorre imagenes/ y cuenta archivos sin decodificarlos. Responde rápido.
    """
    import os
    report = {'root': IMG_ROOT, 'objetos': {}, 'equipos': {}, 'otros': {}}
    base = IMG_ROOT
    if not os.path.isdir(base):
        return jsonify({'root': IMG_ROOT, 'message': 'IMG_ROOT no existe'}), 200

    def count_dir(d):
        c = 0
        for _, _, files in os.walk(d):
            for fn in files:
                if fn.lower().endswith(('.jpg', '.jpeg', '.png')):
                    c += 1
        return c

    # objetos
    obj_dir = os.path.join(base, 'objetos')
    if os.path.isdir(obj_dir):
        for entry in os.listdir(obj_dir):
            f = os.path.join(obj_dir, entry)
            if os.path.isdir(f):
                report['objetos'][entry] = count_dir(f)

    # equipos
    eq_dir = os.path.join(base, 'equipos')
    if os.path.isdir(eq_dir):
        for entry in os.listdir(eq_dir):
            f = os.path.join(eq_dir, entry)
            if os.path.isdir(f):
                report['equipos'][entry] = count_dir(f)

    # otros
    for entry in os.listdir(base):
        if entry in ('objetos','equipos'):
            continue
        f = os.path.join(base, entry)
        if os.path.isdir(f):
            report['otros'][entry] = count_dir(f)

    # desde BD
    try:
        db_rows = db_manager.execute_query("SELECT o.nombre, COUNT(oi.id) c FROM objetos o LEFT JOIN objetos_imagenes oi ON oi.objeto_id=o.id GROUP BY o.id, o.nombre") or []
        report['objetos_db'] = { r['nombre']: r['c'] for r in db_rows }
    except Exception:
        report['objetos_db'] = {}

    return jsonify(report), 200
'''
    # Insertarlo antes de la sección de manejo de errores
    before = '\n# =====================================================================\n# MANEJO DE ERRORES'
    src = ensure_block(src, "def vision_debug_counts_fast():", block, before_marker=before)

# D) Usar loader SLIM en vision_match y preprocesar frame
src = re.sub(
    r"templates\s*=\s*_load_template_images\(\)",
    "templates = _load_template_images_slim(max_per_key=12)",
    src,
    count=1
)
src = re.sub(
    r"(frame\s*=\s*_decode_image_base64\(img_b64\)\s*\n\s*if frame is None:\s*return jsonify\(\{'message': 'Imagen inválida'\}\), 400)",
    r"frame = _decode_image_base64(img_b64)\n    frame = _preprocess_for_orb(frame)\n    if frame is None:\n        return jsonify({'message': 'Imagen inválida'}), 400",
    src,
    count=1
)

p.write_text(src, encoding='utf-8')
print('OK')
