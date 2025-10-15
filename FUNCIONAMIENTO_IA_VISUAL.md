# 🤖 FUNCIONAMIENTO DEL SISTEMA DE IA VISUAL

## ✅ ESTADO ACTUAL DEL SISTEMA

Según el diagnóstico realizado, el sistema de IA visual está **funcionando correctamente**:

### 📊 Estadísticas Actuales

**Base de Datos:**
- ✅ 12 Equipos registrados
- ✅ 25 Items de inventario registrados
- ✅ 6 Objetos con reconocimiento visual
- ✅ 36 Imágenes de entrenamiento guardadas

**Sistema de Entrenamiento:**
- ✅ 2 Equipos con entrenamiento visual (celular_poco_x3, mano_valdelamar_v2)
- ✅ 32 Registros en metadata
- ⚠️ 0 Items de inventario con entrenamiento (aún no se han entrenado)

---

## 🔄 FLUJO DE REGISTRO DE EQUIPOS/ITEMS CON IMÁGENES

### Opción 1: Sistema de Entrenamiento Visual (Equipos/Items de BD)

**Endpoint:** `POST /api/visual/training`

**Flujo:**
1. **Usuario registra equipo/item** en la base de datos (usando `/equipos/crear` o `/inventario/crear`)
2. **Sistema genera ID único** (ej: `EQ-ABC12345` o `INV-XYZ67890`)
3. **Usuario entrena el reconocimiento visual:**
   - Envía imágenes desde diferentes ángulos
   - Especifica el `item_type` ('equipo' o 'item')
   - Especifica el `item_id` (el ID del equipo/item en BD)
   - Especifica el `view_angle` (frontal, posterior, lateral_derecha, etc.)

4. **Sistema guarda las imágenes:**
   ```
   📁 imagenes/entrenamiento/equipo/[ID_EQUIPO]/
      ├── frontal_20251014_120000.jpg
      ├── posterior_20251014_120030.jpg
      ├── lateral_derecha_20251014_120100.jpg
      └── metadata.json
   
   📁 imagenes/entrenamiento/item/[ID_ITEM]/
      ├── frontal_20251014_120000.jpg
      ├── superior_20251014_120030.jpg
      └── metadata.json
   ```

5. **Metadata guardada:**
   ```json
   [
     {
       "description": "Vista frontal del equipo",
       "view_angle": "frontal",
       "filepath": "imagenes/entrenamiento/equipo/EQ-ABC12345/frontal_20251014_120000.jpg",
       "training_date": "2025-10-14T12:00:00",
       "num_features": 496,
       "item_details": {
         "id": "EQ-ABC12345",
         "nombre": "Microscopio Óptico",
         "tipo": "Microscopio",
         "estado": "disponible",
         "ubicacion": "Lab Química"
       }
     }
   ]
   ```

**✅ Ventajas:**
- Vinculado directamente a la BD
- Metadata completa con detalles del item
- Reconocimiento por ID único
- Ideal para equipos e items del inventario oficial

---

### Opción 2: Sistema de Objetos (Registro Unificado)

**Endpoint:** `POST /api/objetos/crear_con_imagen`

**Flujo:**
1. **Usuario crea objeto con imagen** en un solo paso
2. **Sistema crea registro en tabla `objetos`**
3. **Sistema guarda imagen:**
   ```
   📁 imagenes/objetos/[nombre_objeto]/[vista]/
      ├── img_20251014_120000.jpg
      ├── img_20251014_120030.jpg
      └── ...
   ```

4. **Registro en BD:**
   - Tabla `objetos`: nombre, categoría, descripción
   - Tabla `objetos_imagenes`: path, thumbnail, vista, fuente

**✅ Ventajas:**
- Registro rápido en un solo paso
- Ideal para objetos generales (EPP, herramientas, etc.)
- Thumbnails automáticos
- Organización por vistas

---

## 📍 ESTRUCTURA DE DIRECTORIOS ACTUAL

```
imagenes/
├── entrenamiento/
│   ├── equipo/
│   │   ├── celular_poco_x3/          ← 5 imágenes + metadata.json
│   │   └── mano_valdelamar_v2/       ← 6 imágenes + metadata.json
│   └── item/                          ← Vacío (sin entrenamientos aún)
│
└── objetos/
    ├── Betun/
    │   ├── frontal/
    │   ├── posterior/
    │   ├── inferior/
    │   └── superior/
    ├── Cargador/
    ├── Celular/
    ├── Lata Mentas/
    └── Samnsung/
```

---

## 🔍 PROBLEMA IDENTIFICADO

### ⚠️ Inconsistencia en Nombres de Carpetas

**Observación del diagnóstico:**
- Las carpetas en `imagenes/entrenamiento/equipo/` usan **nombres** en lugar de **IDs**:
  - `celular_poco_x3` ❌ (debería ser el ID del equipo, ej: `EQ-ABC12345`)
  - `mano_valdelamar_v2` ❌ (debería ser el ID del equipo)

**Problema:**
- El código actual en `VisualTrainingAPI` guarda con el ID:
  ```python
  base_dir = os.path.join('imagenes', 'entrenamiento', item_type, str(item_id))
  ```
- Pero las carpetas existentes usan nombres

**Solución:**
Hay dos opciones:

1. **Opción A (Recomendada):** Usar IDs como está en el código
   - Renombrar carpetas existentes a sus IDs correspondientes
   - Mantener el código actual

2. **Opción B:** Modificar el código para usar nombres sanitizados
   - Cambiar el código para usar nombres en lugar de IDs
   - Mantener las carpetas actuales

---

## 🛠️ CORRECCIÓN RECOMENDADA

Voy a verificar si las carpetas actuales corresponden a equipos en la BD y proponer una solución.

### Verificación Necesaria:

1. ¿Existe un equipo con nombre "celular_poco_x3" en la BD?
2. ¿Existe un equipo con nombre "mano_valdelamar_v2" en la BD?
3. ¿Cuáles son sus IDs reales?

### Propuesta de Corrección:

**Si queremos usar IDs (RECOMENDADO):**
```python
# El código actual ya está correcto:
base_dir = os.path.join('imagenes', 'entrenamiento', item_type, str(item_id))
# Ejemplo: imagenes/entrenamiento/equipo/EQ-ABC12345/
```

**Si queremos usar nombres:**
```python
# Modificar el código para sanitizar nombres:
import re

def sanitize_name(name):
    name = name.lower().replace(' ', '_')
    name = re.sub(r'[^a-z0-9_-]', '', name)
    return name

base_dir = os.path.join('imagenes', 'entrenamiento', item_type, sanitize_name(item_details['nombre']))
# Ejemplo: imagenes/entrenamiento/equipo/microscopio_optico/
```

---

## 📋 ENDPOINTS DISPONIBLES

### 1. Entrenar Reconocimiento Visual
**POST** `/api/visual/training`

**Body:**
```json
{
  "item_type": "equipo",           // o "item"
  "item_id": "EQ-ABC12345",        // ID del equipo/item en BD
  "image_base64": "data:image/jpeg;base64,...",
  "view_angle": "frontal",         // frontal, posterior, lateral_derecha, etc.
  "description": "Vista frontal del microscopio"
}
```

**Respuesta:**
```json
{
  "message": "Imagen de entrenamiento guardada exitosamente",
  "filepath": "imagenes/entrenamiento/equipo/EQ-ABC12345/frontal_20251014_120000.jpg",
  "num_features": 496,
  "total_images": 5,
  "item_details": { ... }
}
```

---

### 2. Reconocer Equipo/Item por Imagen
**POST** `/api/visual/recognize`

**Body:**
```json
{
  "image_base64": "data:image/jpeg;base64,...",
  "confidence_threshold": 0.3
}
```

**Respuesta (si reconoce):**
```json
{
  "recognized": true,
  "item_type": "equipo",
  "item_id": "EQ-ABC12345",
  "confidence": 0.85,
  "item_details": {
    "id": "EQ-ABC12345",
    "nombre": "Microscopio Óptico",
    "tipo": "Microscopio",
    "estado": "disponible"
  }
}
```

---

### 3. Crear Objeto con Imagen
**POST** `/api/objetos/crear_con_imagen`

**Body:**
```json
{
  "nombre": "Casco de Seguridad",
  "categoria": "EPP",
  "descripcion": "Casco amarillo",
  "image_base64": "data:image/jpeg;base64,...",
  "vista": "frontal",
  "notas": "Primera imagen"
}
```

**Respuesta:**
```json
{
  "message": "Objeto e imagen guardados",
  "id": 7
}
```

---

### 4. Estadísticas del Sistema Visual
**GET** `/api/visual/stats`

**Respuesta:**
```json
{
  "equipos_registrados": 2,
  "items_registrados": 0,
  "total_imagenes": 11,
  "imagenes_entrenamiento": 11,
  "imagenes_registro": 0
}
```

---

## ✅ CONCLUSIÓN

### Estado Actual:
- ✅ **Sistema funcionando correctamente**
- ✅ **Endpoints configurados**
- ✅ **Base de datos con registros**
- ✅ **Imágenes guardándose correctamente**
- ⚠️ **Inconsistencia menor en nombres de carpetas** (usar IDs vs nombres)

### Recomendaciones:
1. **Usar IDs para carpetas de entrenamiento** (como está en el código actual)
2. **Renombrar carpetas existentes** a sus IDs correspondientes
3. **Documentar el proceso** para usuarios futuros
4. **Entrenar items de inventario** para completar el sistema

### Próximos Pasos:
1. Identificar los IDs reales de "celular_poco_x3" y "mano_valdelamar_v2"
2. Renombrar las carpetas a sus IDs
3. Actualizar metadata.json con los IDs correctos
4. Entrenar algunos items de inventario como prueba
