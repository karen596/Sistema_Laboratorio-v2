# SOLUCIÓN: Registros creados no aparecen en el sistema

## Problema Identificado

Los equipos e items de inventario creados desde el perfil admin NO aparecían en las listas porque:

### 1. **Equipos sin laboratorio_id**
- La función `crear_equipo_web()` NO estaba insertando el campo `laboratorio_id`
- Las consultas que muestran equipos usan `INNER JOIN` con la tabla `laboratorios`
- Los equipos sin `laboratorio_id` quedan excluidos del resultado

### 2. **Faltaba ruta para crear items de inventario**
- Solo existía la ruta GET `/inventario` para ver items
- No había ruta POST `/inventario/crear` para crear items desde la web

## Solución Implementada

### Cambio 1: Función `crear_equipo_web()` (línea 1063)

**ANTES:**
```python
query = """
    INSERT INTO equipos (id, nombre, tipo, estado, ubicacion, especificaciones)
    VALUES (%s, %s, %s, 'disponible', %s, %s)
"""
db_manager.execute_query(query, (equipo_id, nombre, tipo, ubicacion, especificaciones_json))
```

**DESPUÉS:**
```python
laboratorio_id = data.get('laboratorio_id', 1)  # Por defecto laboratorio 1

query = """
    INSERT INTO equipos (id, nombre, tipo, estado, ubicacion, laboratorio_id, especificaciones)
    VALUES (%s, %s, %s, 'disponible', %s, %s, %s)
"""
db_manager.execute_query(query, (equipo_id, nombre, tipo, ubicacion, laboratorio_id, especificaciones_json))
```

### Cambio 2: Nueva función `crear_item_inventario_web()` (línea 1143)

Se agregó una nueva ruta POST para crear items de inventario desde la interfaz web:

```python
@app.route('/inventario/crear', methods=['POST'])
@require_login
def crear_item_inventario_web():
    """Crear item de inventario desde interfaz web (sin JWT)"""
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        categoria = data.get('categoria')
        cantidad_actual = data.get('cantidad_actual', 0)
        cantidad_minima = data.get('cantidad_minima', 0)
        unidad = data.get('unidad', 'unidad')
        ubicacion = data.get('ubicacion')
        laboratorio_id = data.get('laboratorio_id', 1)  # Por defecto laboratorio 1
        proveedor = data.get('proveedor')
        costo_unitario = data.get('costo_unitario', 0)
        
        if not nombre:
            return jsonify({'success': False, 'message': 'Nombre es requerido'}), 400
        
        # Generar ID único
        import uuid
        item_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        
        query = """
            INSERT INTO inventario (id, nombre, categoria, cantidad_actual, cantidad_minima, 
                                  unidad, ubicacion, laboratorio_id, proveedor, costo_unitario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        db_manager.execute_query(query, (item_id, nombre, categoria, cantidad_actual, 
                                        cantidad_minima, unidad, ubicacion, laboratorio_id,
                                        proveedor, costo_unitario))
        
        return jsonify({'success': True, 'message': 'Item de inventario creado exitosamente', 'id': item_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
```

## Resultado

✓ **Ahora los equipos creados incluyen el `laboratorio_id`** y aparecerán en las listas
✓ **Se puede crear items de inventario desde la web** con la nueva ruta `/inventario/crear`
✓ **Todos los registros se asocian a un laboratorio** (por defecto laboratorio ID 1)

## Notas Importantes

1. **Laboratorio por defecto**: Si no se especifica `laboratorio_id`, se usa el laboratorio con ID 1
2. **IDs únicos**: Se generan IDs únicos automáticamente:
   - Equipos: `EQ-XXXXXXXX`
   - Inventario: `INV-XXXXXXXX`
3. **Validación**: Ambas funciones validan que los campos requeridos estén presentes

## Próximos Pasos

Si el frontend (JavaScript) envía el `laboratorio_id` en el formulario, los registros se asociarán al laboratorio correcto. De lo contrario, se usará el laboratorio por defecto (ID 1).

Para permitir seleccionar el laboratorio desde el formulario, el frontend debe incluir:
```javascript
{
    "nombre": "Nombre del equipo",
    "tipo": "Tipo",
    "ubicacion": "Ubicación",
    "laboratorio_id": 1,  // ID del laboratorio seleccionado
    "especificaciones": "Descripción..."
}
```
