"""
Script para listar todas las rutas registradas en Flask
"""
import sys
sys.path.insert(0, '.')

from web_app import app

print("\n" + "="*60)
print("RUTAS REGISTRADAS EN FLASK")
print("="*60 + "\n")

routes = []
for rule in app.url_map.iter_rules():
    routes.append({
        'endpoint': rule.endpoint,
        'methods': ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
        'path': str(rule)
    })

# Ordenar por path
routes.sort(key=lambda x: x['path'])

# Filtrar solo rutas de API visual
visual_routes = [r for r in routes if '/visual' in r['path']]

if visual_routes:
    print("RUTAS DE API VISUAL:")
    print("-" * 60)
    for route in visual_routes:
        print(f"{route['methods']:10} {route['path']}")
    print()
else:
    print("⚠ No se encontraron rutas de API visual\n")

# Buscar específicamente la ruta de update_metadata
update_route = [r for r in routes if 'update_metadata' in r['path'].lower()]
if update_route:
    print("✓ Ruta update_metadata encontrada:")
    for route in update_route:
        print(f"  {route['methods']:10} {route['path']}")
else:
    print("✗ Ruta update_metadata NO encontrada")

print()
