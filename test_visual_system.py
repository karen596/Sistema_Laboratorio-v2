"""
Script de Testing para Sistema de Reconocimiento Visual
Verifica que todos los componentes funcionen correctamente
"""

import requests
import json
import os
from pathlib import Path

# Configuración
BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api"

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(name, status, message=""):
    """Imprime resultado de test con formato"""
    symbol = "✓" if status else "✗"
    color = Colors.GREEN if status else Colors.RED
    print(f"{color}{symbol}{Colors.RESET} {name}")
    if message:
        print(f"  → {message}")

def print_section(title):
    """Imprime título de sección"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def test_server_running():
    """Test 1: Verificar que el servidor está corriendo"""
    try:
        response = requests.get(BASE_URL, timeout=5)
        return True, f"Servidor respondiendo (Status: {response.status_code})"
    except Exception as e:
        return False, f"Servidor no responde: {str(e)}"

def test_update_metadata_endpoint():
    """Test 2: Verificar endpoint de actualización de metadatos"""
    try:
        response = requests.post(
            f"{API_URL}/visual/update_metadata",
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return True, f"Actualizados: {data.get('updated_count', 0)} archivos, Errores: {len(data.get('errors', []))}"
            else:
                return False, f"Error en respuesta: {data.get('message', 'Unknown')}"
        else:
            return False, f"Status code: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_metadata_files():
    """Test 3: Verificar archivos metadata.json actualizados"""
    base_paths = [
        'imagenes/entrenamiento/equipo',
        'imagenes/entrenamiento/item',
        'imagenes/equipo',
        'imagenes/item'
    ]
    
    found_files = []
    files_with_lab = []
    files_without_lab = []
    
    for base_path in base_paths:
        if not os.path.exists(base_path):
            continue
        
        for item_folder in os.listdir(base_path):
            item_dir = os.path.join(base_path, item_folder)
            if not os.path.isdir(item_dir):
                continue
            
            metadata_file = os.path.join(item_dir, 'metadata.json')
            if os.path.exists(metadata_file):
                found_files.append(metadata_file)
                
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    if isinstance(metadata, dict):
                        if metadata.get('laboratorio_nombre'):
                            files_with_lab.append({
                                'path': metadata_file,
                                'nombre': metadata.get('nombre'),
                                'lab': metadata.get('laboratorio_nombre')
                            })
                        else:
                            files_without_lab.append(metadata_file)
                except Exception as e:
                    print(f"  {Colors.YELLOW}⚠{Colors.RESET} Error leyendo {metadata_file}: {str(e)}")
    
    if not found_files:
        return False, "No se encontraron archivos metadata.json"
    
    success = len(files_with_lab) > 0
    msg = f"Total: {len(found_files)}, Con laboratorio: {len(files_with_lab)}, Sin laboratorio: {len(files_without_lab)}"
    
    if files_with_lab:
        print(f"\n  {Colors.GREEN}Archivos con información de laboratorio:{Colors.RESET}")
        for file_info in files_with_lab[:5]:  # Mostrar solo los primeros 5
            print(f"    • {file_info['nombre']} → {file_info['lab']}")
        if len(files_with_lab) > 5:
            print(f"    ... y {len(files_with_lab) - 5} más")
    
    return success, msg

def test_visual_stats():
    """Test 4: Verificar endpoint de estadísticas"""
    try:
        response = requests.get(f"{API_URL}/visual/stats", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            
            # Extraer números según el formato
            if isinstance(stats.get('equipos'), dict):
                equipos = stats['equipos'].get('count', 0)
                items = stats['items'].get('count', 0)
                imagenes = stats['equipos'].get('images', 0) + stats['items'].get('images', 0)
            else:
                equipos = stats.get('equipos_entrenados', 0)
                items = stats.get('items_entrenados', 0)
                imagenes = stats.get('total_imagenes', 0)
            
            return True, f"Equipos: {equipos}, Items: {items}, Imágenes: {imagenes}"
        else:
            return False, f"Status code: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_metadata_content():
    """Test 5: Verificar contenido detallado de un metadata"""
    # Buscar el primer metadata disponible
    test_file = None
    base_paths = ['imagenes/entrenamiento/equipo', 'imagenes/equipo']
    
    for base_path in base_paths:
        if not os.path.exists(base_path):
            continue
        
        for item_folder in os.listdir(base_path):
            item_dir = os.path.join(base_path, item_folder)
            metadata_file = os.path.join(item_dir, 'metadata.json')
            if os.path.exists(metadata_file):
                test_file = metadata_file
                break
        if test_file:
            break
    
    if not test_file:
        return False, "No se encontró ningún archivo metadata.json para probar"
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        required_fields = ['nombre', 'tipo', 'categoria', 'laboratorio_id']
        optional_fields = ['laboratorio_nombre', 'laboratorio_ubicacion', 'ubicacion']
        
        missing = [field for field in required_fields if field not in metadata]
        present_optional = [field for field in optional_fields if field in metadata and metadata[field]]
        
        if missing:
            return False, f"Faltan campos requeridos: {', '.join(missing)}"
        
        print(f"\n  {Colors.GREEN}Ejemplo de metadata ({Path(test_file).parent.name}):{Colors.RESET}")
        print(f"    • Nombre: {metadata.get('nombre')}")
        print(f"    • Tipo: {metadata.get('tipo')}")
        print(f"    • Categoría: {metadata.get('categoria')}")
        print(f"    • Laboratorio ID: {metadata.get('laboratorio_id')}")
        if 'laboratorio_nombre' in metadata:
            print(f"    • Laboratorio: {metadata.get('laboratorio_nombre')}")
        if 'laboratorio_ubicacion' in metadata:
            print(f"    • Ubicación Lab: {metadata.get('laboratorio_ubicacion')}")
        if 'ubicacion' in metadata:
            print(f"    • Ubicación Específica: {metadata.get('ubicacion')}")
        
        return True, f"Campos opcionales presentes: {len(present_optional)}/{len(optional_fields)}"
    
    except Exception as e:
        return False, f"Error leyendo metadata: {str(e)}"

def test_training_structure():
    """Test 6: Verificar estructura de carpetas de entrenamiento"""
    expected_structure = {
        'imagenes/entrenamiento': ['equipo', 'item'],
        'imagenes': ['equipo', 'item']
    }
    
    found = []
    missing = []
    
    for base, subdirs in expected_structure.items():
        if os.path.exists(base):
            found.append(base)
            for subdir in subdirs:
                full_path = os.path.join(base, subdir)
                if os.path.exists(full_path):
                    # Contar items en esta carpeta
                    items = [d for d in os.listdir(full_path) if os.path.isdir(os.path.join(full_path, d))]
                    found.append(f"{full_path} ({len(items)} items)")
                else:
                    missing.append(full_path)
        else:
            missing.append(base)
    
    if found:
        print(f"\n  {Colors.GREEN}Estructura encontrada:{Colors.RESET}")
        for item in found:
            print(f"    • {item}")
    
    if missing:
        print(f"\n  {Colors.YELLOW}No encontrado:{Colors.RESET}")
        for item in missing:
            print(f"    • {item}")
    
    return len(found) > 0, f"Encontradas: {len(found)} rutas, Faltantes: {len(missing)}"

def run_all_tests():
    """Ejecutar todos los tests"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"  TESTING - SISTEMA DE RECONOCIMIENTO VISUAL")
    print(f"{'='*60}{Colors.RESET}\n")
    
    tests = [
        ("Servidor corriendo", test_server_running),
        ("Estructura de carpetas", test_training_structure),
        ("Archivos metadata.json", test_metadata_files),
        ("Contenido de metadata", test_metadata_content),
        ("Estadísticas visuales", test_visual_stats),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print_section(test_name)
        try:
            success, message = test_func()
            print_test(test_name, success, message)
            results.append(success)
        except Exception as e:
            print_test(test_name, False, f"Error inesperado: {str(e)}")
            results.append(False)
    
    # Resumen final
    print_section("RESUMEN")
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    color = Colors.GREEN if percentage == 100 else Colors.YELLOW if percentage >= 50 else Colors.RED
    print(f"{color}Tests pasados: {passed}/{total} ({percentage:.1f}%){Colors.RESET}\n")
    
    if percentage == 100:
        print(f"{Colors.GREEN}✓ ¡Todos los tests pasaron exitosamente!{Colors.RESET}\n")
    elif percentage >= 50:
        print(f"{Colors.YELLOW}⚠ Algunos tests fallaron. Revisa los detalles arriba.{Colors.RESET}\n")
    else:
        print(f"{Colors.RED}✗ Múltiples tests fallaron. Verifica la configuración del sistema.{Colors.RESET}\n")
    
    return percentage == 100

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Testing interrumpido por el usuario{Colors.RESET}\n")
        exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Error fatal: {str(e)}{Colors.RESET}\n")
        exit(1)
