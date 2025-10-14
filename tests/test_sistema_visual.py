# -*- coding: utf-8 -*-
"""
Test del Sistema de Reconocimiento Visual
Verificar que todo funciona correctamente
"""

def test_imports():
    """Probar que todas las dependencias están disponibles"""
    print("🧪 PROBANDO DEPENDENCIAS DEL SISTEMA VISUAL")
    print("=" * 50)
    
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
    except ImportError as e:
        print(f"❌ NumPy: {e}")
        return False
    
    try:
        from visual_recognition_module import visual_manager
        print("✅ Módulo de reconocimiento visual importado")
    except ImportError as e:
        print(f"❌ Módulo visual: {e}")
        return False
    
    return True

def test_visual_manager():
    """Probar funcionalidades básicas del gestor visual"""
    print("\n🔍 PROBANDO GESTOR DE RECONOCIMIENTO VISUAL")
    print("=" * 50)
    
    try:
        from visual_recognition_module import visual_manager
        
        # Probar estadísticas
        stats = visual_manager.get_training_stats()
        print(f"✅ Estadísticas obtenidas: {stats}")
        
        # Probar detección de características (imagen de prueba)
        import numpy as np
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        keypoints, descriptors = visual_manager.extract_features(test_image)
        if descriptors is not None:
            print(f"✅ Extracción de características: {len(descriptors)} características")
        else:
            print("⚠️ No se pudieron extraer características (normal con imagen aleatoria)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en gestor visual: {e}")
        return False

def test_api_availability():
    """Verificar que las APIs están disponibles"""
    print("\n🌐 VERIFICANDO DISPONIBILIDAD DE APIs")
    print("=" * 50)
    
    try:
        import requests
        
        # Probar que el servidor está corriendo
        base_url = "http://localhost:5000"
        
        endpoints = [
            "/api/visual/stats",
            "/entrenamiento-visual"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=2)
                if response.status_code < 500:
                    print(f"✅ {endpoint}: Disponible")
                else:
                    print(f"⚠️ {endpoint}: Error {response.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"❌ {endpoint}: Servidor no disponible")
            except Exception as e:
                print(f"⚠️ {endpoint}: {e}")
        
        return True
        
    except ImportError:
        print("⚠️ requests no disponible - instala con: pip install requests")
        return True  # No es crítico

def main():
    """Función principal de pruebas"""
    print("🚀 TEST COMPLETO DEL SISTEMA DE RECONOCIMIENTO VISUAL")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Dependencias
    if not test_imports():
        all_passed = False
    
    # Test 2: Gestor visual
    if not test_visual_manager():
        all_passed = False
    
    # Test 3: APIs (opcional)
    test_api_availability()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ El sistema de reconocimiento visual está listo")
        print("🌐 Puedes acceder a: http://localhost:5000/entrenamiento-visual")
    else:
        print("❌ Algunos tests fallaron")
        print("💡 Revisa los errores arriba y corrige las dependencias")
    
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Ejecuta: python web_app.py")
    print("2. Ve a: http://localhost:5000/entrenamiento-visual")
    print("3. Entrena la IA con imágenes de equipos")
    print("4. Prueba el reconocimiento en tiempo real")

if __name__ == "__main__":
    main()
