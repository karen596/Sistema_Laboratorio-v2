# -*- coding: utf-8 -*-
"""
Integración de IA Avanzada con el Sistema Existente
Sistema de Gestión Inteligente - Centro Minero SENA
"""

import logging
from typing import Optional, Dict, Any
import time

# Importar módulos de IA
try:
    from speech_ai_module import initialize_advanced_voice_recognition
    SPEECH_AI_AVAILABLE = True
except ImportError:
    SPEECH_AI_AVAILABLE = False

try:
    from vision_ai_module import initialize_advanced_vision
    VISION_AI_AVAILABLE = True
except ImportError:
    VISION_AI_AVAILABLE = False

logger = logging.getLogger(__name__)

class AISystemManager:
    """
    Gestor principal del sistema de IA
    Coordina reconocimiento de voz y visión avanzados
    """
    
    def __init__(self, command_processor_func, img_root_path):
        self.command_processor = command_processor_func
        self.img_root_path = img_root_path
        
        # Componentes de IA
        self.voice_processor = None
        self.vision_detector = None
        
        # Estados
        self.voice_ai_enabled = False
        self.vision_ai_enabled = False
        
        # Estadísticas
        self.stats = {
            'voice_commands_processed': 0,
            'vision_detections_made': 0,
            'ai_initialization_time': 0,
            'fallback_usage': {
                'voice': 0,
                'vision': 0
            }
        }
    
    def initialize(self):
        """Inicializar todos los componentes de IA"""
        start_time = time.time()
        
        logger.info("Inicializando sistema de IA avanzada...")
        
        # Inicializar reconocimiento de voz
        if SPEECH_AI_AVAILABLE:
            try:
                self.voice_processor = initialize_advanced_voice_recognition(
                    self.command_processor
                )
                if self.voice_processor:
                    self.voice_ai_enabled = True
                    logger.info("✅ Reconocimiento de voz avanzado activado")
                else:
                    logger.warning("⚠️ Fallback a reconocimiento de voz básico")
                    self.stats['fallback_usage']['voice'] += 1
            except Exception as e:
                logger.error(f"❌ Error inicializando voz avanzada: {e}")
        else:
            logger.warning("⚠️ Módulo de voz avanzada no disponible")
        
        # Inicializar reconocimiento visual
        if VISION_AI_AVAILABLE:
            try:
                self.vision_detector = initialize_advanced_vision(self.img_root_path)
                if self.vision_detector:
                    self.vision_ai_enabled = True
                    logger.info("✅ Reconocimiento visual avanzado activado")
                else:
                    logger.warning("⚠️ Fallback a reconocimiento visual básico")
                    self.stats['fallback_usage']['vision'] += 1
            except Exception as e:
                logger.error(f"❌ Error inicializando visión avanzada: {e}")
        else:
            logger.warning("⚠️ Módulo de visión avanzada no disponible")
        
        initialization_time = time.time() - start_time
        self.stats['ai_initialization_time'] = initialization_time
        
        logger.info(f"Sistema de IA inicializado en {initialization_time:.2f}s")
        
        return {
            'voice_ai_enabled': self.voice_ai_enabled,
            'vision_ai_enabled': self.vision_ai_enabled,
            'initialization_time': initialization_time
        }
    
    def start_voice_control(self):
        """Iniciar control por voz avanzado"""
        if self.voice_ai_enabled and self.voice_processor:
            try:
                success = self.voice_processor.start_voice_control()
                if success:
                    logger.info("🎤 Control por voz avanzado iniciado")
                    return True
                else:
                    logger.error("❌ Error iniciando control por voz")
                    return False
            except Exception as e:
                logger.error(f"❌ Error en control por voz: {e}")
                return False
        else:
            logger.warning("⚠️ Control por voz avanzado no disponible")
            return False
    
    def process_voice_command(self, audio_data):
        """Procesar comando de voz con IA avanzada"""
        if self.voice_ai_enabled and self.voice_processor:
            try:
                result = self.voice_processor.voice_recognizer.recognize_speech(audio_data)
                if result and result.get('text'):
                    # Procesar comando
                    response = self.command_processor(result['text'])
                    
                    self.stats['voice_commands_processed'] += 1
                    
                    return {
                        'success': True,
                        'recognized_text': result['text'],
                        'confidence': result.get('confidence', 0),
                        'response': response,
                        'ai_enhanced': True
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No se pudo reconocer el comando',
                        'ai_enhanced': True
                    }
            except Exception as e:
                logger.error(f"Error procesando comando de voz: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'ai_enhanced': True
                }
        else:
            # Fallback a método básico
            self.stats['fallback_usage']['voice'] += 1
            return {
                'success': False,
                'error': 'IA de voz no disponible',
                'ai_enhanced': False
            }
    
    def detect_objects_advanced(self, image_data):
        """Detectar objetos con IA avanzada"""
        if self.vision_ai_enabled and self.vision_detector:
            try:
                result = self.vision_detector.detect_objects(image_data)
                
                if result:
                    self.stats['vision_detections_made'] += 1
                    
                    return {
                        'success': True,
                        'detection_result': result,
                        'ai_enhanced': True
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No se pudo procesar la imagen',
                        'ai_enhanced': True
                    }
            except Exception as e:
                logger.error(f"Error en detección avanzada: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'ai_enhanced': True
                }
        else:
            # Fallback a método básico
            self.stats['fallback_usage']['vision'] += 1
            return {
                'success': False,
                'error': 'IA de visión no disponible',
                'ai_enhanced': False
            }
    
    def get_ai_status(self):
        """Obtener estado del sistema de IA"""
        status = {
            'voice_ai': {
                'enabled': self.voice_ai_enabled,
                'available': SPEECH_AI_AVAILABLE,
                'stats': {}
            },
            'vision_ai': {
                'enabled': self.vision_ai_enabled,
                'available': VISION_AI_AVAILABLE,
                'stats': {}
            },
            'general_stats': self.stats
        }
        
        # Estadísticas de voz
        if self.voice_processor:
            try:
                voice_stats = self.voice_processor.get_command_stats()
                status['voice_ai']['stats'] = voice_stats
            except:
                pass
        
        # Estadísticas de visión
        if self.vision_detector:
            status['vision_ai']['stats'] = {
                'cache_size': len(getattr(self.vision_detector, 'prediction_cache', {})),
                'model_initialized': self.vision_detector.is_initialized
            }
        
        return status
    
    def train_custom_vision_model(self, training_data_path, epochs=10):
        """Entrenar modelo de visión personalizado"""
        if self.vision_ai_enabled and self.vision_detector:
            try:
                logger.info("Iniciando entrenamiento de modelo personalizado...")
                result = self.vision_detector.train_custom_model(training_data_path, epochs)
                
                if result.get('success'):
                    logger.info("✅ Modelo personalizado entrenado exitosamente")
                    
                    # Recargar detector con nuevo modelo
                    self.vision_detector.model_path = result['tflite_path']
                    self.vision_detector.initialize()
                    
                return result
                
            except Exception as e:
                logger.error(f"Error entrenando modelo: {e}")
                return {'success': False, 'error': str(e)}
        else:
            return {
                'success': False,
                'error': 'Sistema de visión avanzada no disponible'
            }
    
    def shutdown(self):
        """Cerrar sistema de IA"""
        logger.info("Cerrando sistema de IA...")
        
        # Detener reconocimiento de voz
        if self.voice_processor:
            try:
                self.voice_processor.voice_recognizer.stop_listening()
            except:
                pass
        
        # Limpiar cache de visión
        if self.vision_detector:
            try:
                self.vision_detector.prediction_cache.clear()
            except:
                pass
        
        logger.info("Sistema de IA cerrado")


# Funciones de integración para web_app.py
def create_ai_manager(command_processor_func, img_root_path):
    """
    Crear y configurar el gestor de IA
    
    Args:
        command_processor_func: Función procesar_comando_voz de web_app.py
        img_root_path: Ruta a carpeta de imágenes
    
    Returns:
        AISystemManager inicializado
    """
    try:
        manager = AISystemManager(command_processor_func, img_root_path)
        init_result = manager.initialize()
        
        logger.info(f"Gestor de IA creado: {init_result}")
        return manager
        
    except Exception as e:
        logger.error(f"Error creando gestor de IA: {e}")
        return None


def enhance_vision_match_endpoint(ai_manager, original_match_func):
    """
    Mejorar endpoint de vision/match con IA avanzada
    
    Args:
        ai_manager: Instancia de AISystemManager
        original_match_func: Función original _match_orb_flann
    
    Returns:
        Función mejorada de matching
    """
    def enhanced_match(frame, templates, min_good=10):
        try:
            # Intentar con IA avanzada primero
            if ai_manager and ai_manager.vision_ai_enabled:
                ai_result = ai_manager.detect_objects_advanced(frame)
                
                if ai_result.get('success'):
                    detection = ai_result['detection_result']
                    
                    if detection.get('detected'):
                        return {
                            'equipo_id': detection['class'],
                            'score': int(detection['confidence'] * 100),
                            'passed': detection['confidence'] > 0.5,
                            'ai_enhanced': True,
                            'method': 'tensorflow'
                        }
            
            # Fallback a método original
            logger.info("Usando método de matching original (ORB+FLANN)")
            original_result = original_match_func(frame, templates, min_good)
            
            if original_result:
                original_result['ai_enhanced'] = False
                original_result['method'] = 'orb_flann'
            
            return original_result
            
        except Exception as e:
            logger.error(f"Error en matching mejorado: {e}")
            # Fallback completo a método original
            return original_match_func(frame, templates, min_good)
    
    return enhanced_match


# Configuración de dependencias adicionales
def get_ai_requirements():
    """Obtener lista de dependencias adicionales para IA"""
    return [
        "# IA Avanzada - Reconocimiento de Voz",
        "deepspeech==0.9.3",
        "webrtcvad==2.0.10",
        "pyaudio==0.2.11",
        "",
        "# IA Avanzada - Visión por Computadora", 
        "tensorflow==2.13.0",
        "tflite-runtime==2.13.0",
        "scikit-image==0.21.0",
        "",
        "# Utilidades adicionales",
        "librosa==0.10.1",  # Para procesamiento de audio
        "matplotlib==3.7.2",  # Para visualización de entrenamientos
        "seaborn==0.12.2"  # Para gráficos de estadísticas
    ]


if __name__ == "__main__":
    # Prueba básica del sistema
    def dummy_processor(text):
        return {'mensaje': f'Procesado: {text}', 'exito': True}
    
    manager = create_ai_manager(dummy_processor, 'imagenes')
    
    if manager:
        print("✅ Gestor de IA inicializado")
        
        # Mostrar estado
        status = manager.get_ai_status()
        print(f"Estado del sistema: {status}")
        
        # Probar detección de objetos
        import numpy as np
        test_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        result = manager.detect_objects_advanced(test_image)
        print(f"Resultado de detección: {result}")
        
    else:
        print("❌ Error inicializando gestor de IA")
