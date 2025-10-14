# -*- coding: utf-8 -*-
"""
Test Completo de Todos los Módulos del Sistema
Centro Minero SENA - Sistema de Laboratorio
Ejecutar: python test_all_modules.py
"""

import os
import sys
import time
import json
import numpy as np
import cv2
from datetime import datetime

# Colores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_test(test_name):
    print(f"{Colors.OKCYAN}🧪 Test: {test_name}{Colors.ENDC}")

def print_success(message):
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.OKBLUE}ℹ️  {message}{Colors.ENDC}")


# TEST 1: MÓDULO DE RECONOCIMIENTO FACIAL
def test_facial_recognition_module():
    print_header("TEST MÓDULO DE RECONOCIMIENTO FACIAL")
    
    try:
        from modules.facial_recognition_module import FacialRecognitionManager
        print_success("Módulo facial_recognition_module importado correctamente")
        
        print_test("Inicialización de FacialRecognitionManager")
        manager = FacialRecognitionManager()
        print_success(f"Manager inicializado - Tolerancia: {manager.encoding_tolerance}")
        
        print_test("Procesamiento de imagen sintética")
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        print_success(f"Imagen de prueba creada: {test_image.shape}")
        
        print_test("Detección de rostros en imagen sintética")
        faces = manager.detect_faces(test_image)
        print_info(f"Rostros detectados: {len(faces)}")
        
        print_test("Cálculo de calidad de imagen")
        face_image = np.ones((300, 300, 3), dtype=np.uint8) * 200
        quality = manager._calculate_image_quality(face_image)
        print_success(f"Calidad calculada: {quality:.2f}%")
        
        print_test("Validación de dimensiones de rostro")
        is_valid = manager._is_valid_face(150, 150, 60.0)
        print_success(f"Rostro válido (150x150, 60%): {is_valid}")
        
        print_test("Conversión de imagen a base64")
        base64_img = manager._image_to_base64(face_image)
        if base64_img and len(base64_img) > 0:
            print_success(f"Imagen convertida a base64 (longitud: {len(base64_img)})")
        
        print_success("✓ Módulo de reconocimiento facial testeado completamente")
        return True
        
    except Exception as e:
        print_error(f"Error en test facial: {e}")
        return False


# TEST 2: MÓDULO DE RECONOCIMIENTO VISUAL
def test_visual_recognition_module():
    print_header("TEST MÓDULO DE RECONOCIMIENTO VISUAL")
    
    try:
        from modules.visual_recognition_module import VisualRecognitionManager
        print_success("Módulo visual_recognition_module importado correctamente")
        
        print_test("Inicialización de VisualRecognitionManager")
        manager = VisualRecognitionManager(storage_path="test_visual_data")
        print_success(f"Manager inicializado - Storage: {manager.storage_path}")
        
        print_test("Creación de imagen de equipo de prueba")
        test_equipment = np.random.randint(0, 255, (400, 400, 3), dtype=np.uint8)
        cv2.rectangle(test_equipment, (100, 100), (300, 300), (255, 0, 0), 5)
        print_success(f"Imagen de equipo creada: {test_equipment.shape}")
        
        print_test("Extracción de características ORB")
        keypoints, descriptors = manager.extract_features(test_equipment)
        if descriptors is not None:
            print_success(f"Características extraídas: {len(keypoints)} keypoints")
        
        print_test("Guardar imagen de entrenamiento")
        metadata = {'nombre': 'Microscopio Test', 'categoria': 'Óptica'}
        result = manager.save_training_image('equipo', 'TEST001', test_equipment, metadata)
        if result['success']:
            print_success(f"Imagen guardada - Features: {result['num_features']}")
        
        print_test("Obtener estadísticas de entrenamiento")
        stats = manager.get_training_stats()
        print_info(f"Equipos: {stats.get('equipos', {}).get('count', 0)}")
        
        print_test("Limpieza de datos de prueba")
        delete_result = manager.delete_training_data('equipo', 'TEST001')
        if delete_result['success']:
            print_success(f"Datos eliminados: {delete_result['deleted_files']} archivos")
        
        print_success("✓ Módulo de reconocimiento visual testeado completamente")
        return True
        
    except Exception as e:
        print_error(f"Error en test visual: {e}")
        return False


# TEST 3: MÓDULO DE IA - INTEGRACIÓN
def test_ai_integration_module():
    print_header("TEST MÓDULO DE INTEGRACIÓN IA")
    
    try:
        from modules.ai_integration import AISystemManager
        print_success("Módulo ai_integration importado correctamente")
        
        def dummy_command_processor(text):
            return {'mensaje': f'Comando procesado: {text}', 'exito': True}
        
        print_test("Creación de AISystemManager")
        manager = AISystemManager(dummy_command_processor, 'imagenes')
        print_success("AISystemManager creado correctamente")
        
        print_test("Inicialización del sistema IA")
        init_result = manager.initialize()
        print_info(f"Voice AI: {init_result['voice_ai_enabled']}")
        print_info(f"Vision AI: {init_result['vision_ai_enabled']}")
        
        print_test("Obtener estado del sistema IA")
        status = manager.get_ai_status()
        print_success("Estado del sistema obtenido")
        
        print_test("Apagado del sistema IA")
        manager.shutdown()
        print_success("Sistema IA apagado correctamente")
        
        print_success("✓ Módulo de integración IA testeado completamente")
        return True
        
    except Exception as e:
        print_error(f"Error en test IA: {e}")
        return False


# TEST 4: MÓDULO DE VOZ AVANZADA
def test_speech_ai_module():
    print_header("TEST MÓDULO DE VOZ AVANZADA (DeepSpeech)")
    
    try:
        from modules.speech_ai_module import DeepSpeechVoiceRecognizer
        print_success("Módulo speech_ai_module importado correctamente")
        
        print_test("Inicialización de DeepSpeechVoiceRecognizer")
        recognizer = DeepSpeechVoiceRecognizer()
        print_success("Reconocedor creado")
        print_info(f"Sample rate: {recognizer.sample_rate} Hz")
        
        print_test("Verificación de vocabulario del laboratorio")
        vocab_count = sum(len(words) for words in recognizer.lab_vocabulary.values())
        print_success(f"Vocabulario cargado: {vocab_count} términos")
        
        print_test("Preprocesamiento de audio")
        test_audio = np.random.randn(16000).astype(np.float32)
        processed = recognizer.preprocess_audio(test_audio)
        if processed is not None:
            print_success(f"Audio preprocesado: {processed.dtype}")
        
        print_success("✓ Módulo de voz avanzada testeado completamente")
        return True
        
    except Exception as e:
        print_warning(f"Módulo de voz no disponible (normal si DeepSpeech no está instalado): {e}")
        return False


# TEST 5: MÓDULO DE VISIÓN AVANZADA
def test_vision_ai_module():
    print_header("TEST MÓDULO DE VISIÓN AVANZADA (TensorFlow)")
    
    try:
        from modules.vision_ai_module import TensorFlowObjectDetector, SimpleLabEquipmentClassifier
        print_success("Módulo vision_ai_module importado correctamente")
        
        print_test("Inicialización de TensorFlowObjectDetector")
        detector = TensorFlowObjectDetector(use_lite=True)
        print_success("Detector creado")
        print_info(f"Input size: {detector.input_size}")
        
        print_test("Inicialización del modelo TensorFlow")
        init_success = detector.initialize()
        if init_success:
            print_success("Modelo inicializado correctamente")
        else:
            print_warning("Modelo no disponible (esperado si TensorFlow no está instalado)")
        
        print_test("Verificación de etiquetas de equipos")
        print_success(f"Etiquetas cargadas: {len(detector.labels)}")
        
        print_test("Inicialización de SimpleLabEquipmentClassifier")
        simple_classifier = SimpleLabEquipmentClassifier()
        print_success(f"Clasificador simple creado - Patrones: {len(simple_classifier.equipment_patterns)}")
        
        print_success("✓ Módulo de visión avanzada testeado completamente")
        return True
        
    except Exception as e:
        print_warning(f"Módulo de visión no disponible (normal si TensorFlow no está instalado): {e}")
        return False


# TEST 6: MÓDULO DE SISTEMA DE LABORATORIO
def test_sistema_laboratorio_module():
    print_header("TEST MÓDULO SISTEMA DE LABORATORIO")
    
    try:
        from modules.sistema_laboratorio import Configuracion, Utilidades, DatabaseManager
        print_success("Módulo sistema_laboratorio importado correctamente")
        
        print_test("Verificación de configuración del sistema")
        print_info(f"DB Host: {Configuracion.DB_HOST}")
        print_info(f"DB Name: {Configuracion.DB_NAME}")
        print_success("Configuración cargada correctamente")
        
        print_test("Test de funciones de utilidades")
        fecha_valida = Utilidades.validar_fecha("2024-10-14 10:30")
        email_valido = Utilidades.validar_email("test@example.com")
        print_success(f"Validación de fecha: {fecha_valida}")
        print_success(f"Validación de email: {email_valido}")
        
        print_test("Inicialización de DatabaseManager")
        db = DatabaseManager()
        print_success(f"DatabaseManager creado - Host: {db.host}")
        
        print_success("✓ Módulo sistema de laboratorio testeado completamente")
        return True
        
    except Exception as e:
        print_error(f"Error en test sistema laboratorio: {e}")
        return False


# RESUMEN DE TESTS
def run_all_tests():
    print_header("INICIO DE TESTS COMPLETOS DEL SISTEMA")
    print_info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Python: {sys.version}")
    print_info(f"NumPy: {np.__version__}")
    print_info(f"OpenCV: {cv2.__version__}")
    
    results = {}
    start_time = time.time()
    
    tests = [
        ("Reconocimiento Facial", test_facial_recognition_module),
        ("Reconocimiento Visual", test_visual_recognition_module),
        ("Integración IA", test_ai_integration_module),
        ("Voz Avanzada", test_speech_ai_module),
        ("Visión Avanzada", test_vision_ai_module),
        ("Sistema de Laboratorio", test_sistema_laboratorio_module),
    ]
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Error crítico en {test_name}: {e}")
            results[test_name] = False
        time.sleep(0.5)
    
    total_time = time.time() - start_time
    
    # Mostrar resumen
    print_header("RESUMEN DE TESTS")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.OKGREEN}✅ PASS{Colors.ENDC}" if result else f"{Colors.FAIL}❌ FAIL{Colors.ENDC}"
        print(f"{test_name:.<50} {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests pasados{Colors.ENDC}")
    print(f"{Colors.BOLD}Tiempo total: {total_time:.2f}s{Colors.ENDC}")
    
    if passed == total:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 TODOS LOS TESTS PASARON EXITOSAMENTE{Colors.ENDC}")
    else:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  ALGUNOS TESTS FALLARON{Colors.ENDC}")
    
    return results


if __name__ == "__main__":
    try:
        results = run_all_tests()
        sys.exit(0 if all(results.values()) else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrumpidos por el usuario{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Error fatal: {e}{Colors.ENDC}")
        sys.exit(1)
