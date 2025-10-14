import os
import re
import shutil
import argparse
import mysql.connector
from dotenv import load_dotenv

# Uso: py -3.11 scripts/migrar_imagenes_por_nombre.py --dry-run
#      py -3.11 scripts/migrar_imagenes_por_nombre.py --apply
# Migra estructura:
#   imagenes/objetos/<ID>/*  -> imagenes/objetos/<Nombre_sanitizado>/*
#   imagenes/equipos/<ID>/*  -> imagenes/equipos/<Nombre_sanitizado>/*
# y actualiza rutas en BD (objetos_imagenes.path)

def san(s: str) -> str:
    s = (s or '').strip()
    s = s.replace('..','').replace('/','').replace('\\','')
    s = re.sub(r"[^A-Za-z0-9_\- ]+", '', s)
    s = re.sub(r"\s+", '_', s)
    return s[:80]


def get_db():
    load_dotenv('.env_produccion')
    cfg = {
        'host': os.getenv('HOST', 'localhost'),
        'user': os.getenv('USUARIO_PRODUCCION', 'laboratorio_prod'),
        'password': os.getenv('PASSWORD_PRODUCCION', ''),
        'database': os.getenv('BASE_DATOS', 'laboratorio_sistema'),
        'charset': 'utf8mb4',
    }
    return mysql.connector.connect(**cfg)


def collect_migrations(base_dir: str, table: str, id_col: str, name_col: str):
    # Retorna lista de (src_dir, dst_dir, mappings_files) donde mappings_files es lista de (old_abs, new_abs)
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(f"SELECT {id_col} as id, {name_col} as nombre FROM {table}")
    rows = cur.fetchall()
    cur.close(); conn.close()
    migrations = []
    for row in rows:
        src = os.path.join('imagenes', base_dir, str(row['id']))
        if not os.path.isdir(src):
            continue
        dst = os.path.join('imagenes', base_dir, san(row['nombre']))
        file_mappings = []
        for root, _, files in os.walk(src):
            rel_root = os.path.relpath(root, src)
            for fn in files:
                old_abs = os.path.join(root, fn)
                new_abs = os.path.join(dst if rel_root == '.' else os.path.join(dst, rel_root), fn)
                file_mappings.append((old_abs, new_abs))
        migrations.append((src, dst, file_mappings))
    return migrations


def update_db_paths(file_mappings):
    # Actualiza objetos_imagenes.path para todas las rutas movidas
    conn = get_db()
    cur = conn.cursor()
    for old_abs, new_abs in file_mappings:
        old_db = old_abs.replace('\\','/')
        new_db = new_abs.replace('\\','/')
        cur.execute("UPDATE objetos_imagenes SET path=%s WHERE path=%s", (new_db, old_db))
    conn.commit()
    cur.close(); conn.close()


def main():
    parser = argparse.ArgumentParser(description='Migrar estructura de imagenes por nombre')
    parser.add_argument('--apply', action='store_true', help='Ejecuta migración (por defecto dry-run)')
    parser.add_argument('--dry-run', action='store_true', help='Simula sin mover archivos')
    args = parser.parse_args()
    dry = args.dry_run or not args.apply

    plan = []
    plan += collect_migrations('objetos', 'objetos', 'id', 'nombre')
    plan += collect_migrations('equipos', 'equipos', 'id', 'nombre')

    if not plan:
        print('No hay carpetas por ID para migrar. Nada que hacer.')
        return

    print('Resumen de migración:')
    total_files = 0
    for src, dst, files in plan:
        print(f" - {src} -> {dst} ({len(files)} archivos)")
        total_files += len(files)
    print(f'Total archivos: {total_files}')

    if dry:
        print('\nModo DRY-RUN: no se moverán archivos. Use --apply para ejecutar.')
        return

    # Ejecutar migración
    for src, dst, files in plan:
        for old_abs, new_abs in files:
            os.makedirs(os.path.dirname(new_abs), exist_ok=True)
            shutil.move(old_abs, new_abs)
        # Intentar eliminar carpeta vieja si queda vacía
        try:
            os.removedirs(src)
        except Exception:
            pass
        # Actualizar BD para este grupo
        update_db_paths(files)
        print(f'Migrado {src} -> {dst} ({len(files)} archivos)')

    print('Migración completada.')

if __name__ == '__main__':
    main()
