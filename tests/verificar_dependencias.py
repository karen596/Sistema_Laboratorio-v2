#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificación Simple de Dependencias
"""

print("🧪 VERIFICANDO DEPENDENCIAS DEL SISTEMA VISUAL")
print("=" * 50)

# Test OpenCV
try:
    import cv2
    print(f"✅ OpenCV: {cv2.__version__}")
    opencv_ok = True
except ImportError as e:
    print(f"❌ OpenCV: {e}")
    opencv_ok = False

# Test NumPy
try:
    import numpy as np
    print(f"✅ NumPy: {np.__version__}")
    numpy_ok = True
except ImportError as e:
    print(f"❌ NumPy: {e}")
    numpy_ok = False

# Test Módulo Visual
try:
    from visual_recognition_module import visual_manager
    print("✅ Módulo de reconocimiento visual: OK")
    visual_ok = True
except ImportError as e:
    print(f"❌ Módulo visual: {e}")
    visual_ok = False

print("\n🔍 PROBANDO FUNCIONALIDADES BÁSICAS")
print("=" * 50)

if opencv_ok and numpy_ok and visual_ok:
    try:
        # Crear imagen de prueba
        import numpy as np
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Probar extracción de características
        keypoints, descriptors = visual_manager.extract_features(test_image)
        
        if descriptors is not None:
            print(f"✅ Extracción de características: {len(descriptors)} puntos")
        else:
            print("⚠️ Extracción: Sin características (normal con imagen aleatoria)")
        
        # Probar estadísticas
        stats = visual_manager.get_training_stats()
        print(f"✅ Estadísticas: {stats}")
        
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("✅ El sistema de reconocimiento visual está listo")
        
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
else:
    print("\n❌ Faltan dependencias críticas")

print("\n📋 PRÓXIMOS PASOS:")
print("1. Ejecuta: python web_app.py")
print("2. Ve a: http://localhost:5000/entrenamiento-visual")
print("3. ¡Comienza a entrenar la IA!")
