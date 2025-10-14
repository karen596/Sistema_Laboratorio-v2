# -*- coding: utf-8 -*-
"""
Test Rápido de Reconocimiento Facial Optimizado
"""

import time
import cv2
import numpy as np
from facial_recognition_module import FacialRecognitionManager

def test_facial_speed():
    """Probar velocidad del reconocimiento facial"""
    print("🧪 TEST DE VELOCIDAD - RECONOCIMIENTO FACIAL")
    print("=" * 50)
    
    # Inicializar manager
    manager = FacialRecognitionManager()
    
    # Crear imagen de prueba (simulando captura de cámara)
    # Imagen de 640x480 (tamaño optimizado)
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    print("📸 Probando detección de rostros...")
    start_time = time.time()
    
    try:
        faces = manager.detect_faces(test_image)
        detection_time = time.time() - start_time
        
        print(f"✅ Detección completada en {detection_time:.2f} segundos")
        print(f"📊 Rostros detectados: {len(faces)}")
        
        if detection_time < 2.0:
            print("🚀 Velocidad: EXCELENTE (< 2s)")
        elif detection_time < 5.0:
            print("⚡ Velocidad: BUENA (< 5s)")
        else:
            print("🐌 Velocidad: LENTA (> 5s) - Necesita más optimización")
            
    except Exception as e:
        print(f"❌ Error en detección: {e}")
    
    print("\n💡 RECOMENDACIONES:")
    print("- Si es lento, verifica que tienes las dependencias optimizadas")
    print("- El modelo 'hog' es más rápido que 'cnn'")
    print("- Imágenes más pequeñas procesan más rápido")

if __name__ == "__main__":
    test_facial_speed()
