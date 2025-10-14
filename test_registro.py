"""
Script de prueba para validar el sistema de registro completo
"""
import sys
import os

print("=" * 60)
print("VALIDACIÓN DEL SISTEMA DE REGISTRO COMPLETO")
print("=" * 60)

# 1. Verificar imports necesarios
print("\n[1/6] Verificando imports necesarios...")
try:
    import json
    import uuid
    import re
    import base64
    import io
    from PIL import Image
    print("✅ Todos los imports disponibles")
except ImportError as e:
    print(f"❌ Error en imports: {e}")
    sys.exit(1)

# 2. Verificar estructura de carpetas
print("\n[2/6] Verificando estructura de carpetas...")
required_dirs = ['imagenes', 'templates', 'static']
for dir_name in required_dirs:
    if os.path.exists(dir_name):
        print(f"✅ Carpeta '{dir_name}' existe")
    else:
        print(f"⚠️  Carpeta '{dir_name}' no existe, se creará automáticamente")

# 3. Verificar archivos de templates
print("\n[3/6] Verificando templates...")
templates_required = [
    'templates/registro_completo.html',
    'templates/registros_gestion.html',
    'templates/base.html'
]
for template in templates_required:
    if os.path.exists(template):
        print(f"✅ Template '{template}' existe")
    else:
        print(f"❌ Template '{template}' NO existe")

# 4. Verificar web_app.py
print("\n[4/6] Verificando rutas en web_app.py...")
try:
    with open('web_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    routes_to_check = [
        ('/registro-completo', 'Formulario de registro'),
        ('/registros-gestion', 'Gestión de registros'),
        ('/api/registro-completo', 'API de registro'),
        ('/api/registros-completos', 'API listar registros'),
        ('/api/registro-detalle', 'API detalles'),
        ('/api/registro-eliminar', 'API eliminar')
    ]
    
    for route, desc in routes_to_check:
        if route in content:
            print(f"✅ Ruta '{route}' ({desc})")
        else:
            print(f"❌ Ruta '{route}' NO encontrada")
    
except Exception as e:
    print(f"❌ Error leyendo web_app.py: {e}")

# 5. Verificar función api_registro_completo
print("\n[5/6] Verificando función api_registro_completo...")
try:
    with open('web_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('import json', 'Import de json'),
        ('import uuid', 'Import de uuid'),
        ('import re', 'Import de re'),
        ('import base64', 'Import de base64'),
        ('from PIL import Image', 'Import de PIL'),
        ('def api_registro_completo():', 'Función principal'),
        ('tipo_registro = data.get', 'Obtención de tipo_registro'),
        ('if tipo_registro == \'equipo\':', 'Validación de equipo'),
        ('equipo_id = f"EQ_', 'Generación de ID equipo'),
        ('item_id = f"ITEM_', 'Generación de ID item'),
        ('objeto_dir = os.path.join(\'imagenes\', tipo_dir', 'Creación de carpetas'),
        ('metadata.json', 'Archivo de metadatos'),
        ('return jsonify({', 'Respuesta JSON')
    ]
    
    for check_str, desc in checks:
        if check_str in content:
            print(f"✅ {desc}")
        else:
            print(f"❌ {desc} NO encontrado")
            
except Exception as e:
    print(f"❌ Error verificando función: {e}")

# 6. Resumen
print("\n" + "=" * 60)
print("RESUMEN DE VALIDACIÓN")
print("=" * 60)

print("\n✅ PASOS PARA PROBAR EL SISTEMA:")
print("1. Reinicia el servidor: python web_app.py")
print("2. Accede a: http://localhost:5000/registro-completo")
print("3. Llena el formulario:")
print("   - Selecciona tipo (Equipo o Item)")
print("   - Ingresa nombre y categoría")
print("   - Selecciona laboratorio")
print("   - Activa la cámara y captura fotos")
print("4. Haz clic en 'Guardar Registro'")
print("5. Verifica que se cree la carpeta en:")
print("   - imagenes/equipo/[nombre]/ o")
print("   - imagenes/item/[nombre]/")
print("6. Verifica que contenga:")
print("   - frontal.jpg, posterior.jpg, etc.")
print("   - metadata.json")

print("\n✅ PARA VER LOS REGISTROS:")
print("1. Accede a: http://localhost:5000/registros-gestion")
print("2. Verás todos los equipos e items registrados")
print("3. Puedes ver detalles, editar o eliminar")

print("\n" + "=" * 60)
print("VALIDACIÓN COMPLETADA")
print("=" * 60)
