# -*- coding: utf-8 -*-
"""
Módulo de Reconocimiento de Voz Avanzado con Mozilla DeepSpeech
Sistema de Gestión Inteligente - Centro Minero SENA
"""

import os
import wave
import numpy as np
import webrtcvad
from collections import deque
import threading
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepSpeechVoiceRecognizer:
    """
    Reconocedor de voz offline usando Mozilla DeepSpeech
    Optimizado para comandos de laboratorio en español
    """
    
    def __init__(self, model_path=None, scorer_path=None):
        self.model_path = model_path or 'models/deepspeech-es.pbmm'
        self.scorer_path = scorer_path or 'models/deepspeech-es.scorer'
        self.model = None
        self.is_initialized = False
        self.vad = webrtcvad.Vad(2)  # Agresividad media
        self.sample_rate = 16000
        self.frame_duration_ms = 30
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        
        # Buffer para audio continuo
        self.audio_buffer = deque(maxlen=int(self.sample_rate * 10))  # 10 segundos
        self.is_listening = False
        
        # Vocabulario específico del laboratorio
        self.lab_vocabulary = {
            'equipos': ['microscopio', 'balanza', 'espectrómetro', 'centrífuga', 'autoclave'],
            'acciones': ['reservar', 'consultar', 'estado', 'disponible', 'crear', 'cancelar'],
            'navegacion': ['ir', 'abrir', 'página', 'dashboard', 'inventario', 'reportes'],
            'inventario': ['stock', 'cantidad', 'mínimo', 'crítico', 'reactivos', 'materiales']
        }
        
    def initialize(self):
        """Inicializar el modelo DeepSpeech"""
        try:
            import deepspeech
            
            if not os.path.exists(self.model_path):
                logger.warning(f"Modelo no encontrado: {self.model_path}")
                return False
                
            logger.info("Cargando modelo DeepSpeech...")
            self.model = deepspeech.Model(self.model_path)
            
            if os.path.exists(self.scorer_path):
                logger.info("Cargando scorer de idioma...")
                self.model.enableExternalScorer(self.scorer_path)
                
            # Configurar beam search para mejor precisión
            self.model.setBeamWidth(500)
            
            # Añadir vocabulario específico del laboratorio
            self._add_custom_vocabulary()
            
            self.is_initialized = True
            logger.info("DeepSpeech inicializado correctamente")
            return True
            
        except ImportError:
            logger.error("DeepSpeech no instalado. Usar: pip install deepspeech")
            return False
        except Exception as e:
            logger.error(f"Error inicializando DeepSpeech: {e}")
            return False
    
    def _add_custom_vocabulary(self):
        """Añadir vocabulario específico del laboratorio al modelo"""
        try:
            # Crear lista de palabras técnicas con mayor peso
            custom_words = []
            for category, words in self.lab_vocabulary.items():
                for word in words:
                    custom_words.append(f"{word} 10.0")  # Mayor probabilidad
            
            # Nota: En versiones futuras de DeepSpeech se puede usar addHotWords
            logger.info(f"Vocabulario personalizado: {len(custom_words)} términos")
            
        except Exception as e:
            logger.warning(f"No se pudo añadir vocabulario personalizado: {e}")
    
    def preprocess_audio(self, audio_data):
        """Preprocesar audio para DeepSpeech"""
        try:
            # Convertir a 16kHz mono si es necesario
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Normalizar a int16
            if audio_data.dtype != np.int16:
                audio_data = (audio_data * 32767).astype(np.int16)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error preprocesando audio: {e}")
            return None
    
    def detect_voice_activity(self, audio_chunk):
        """Detectar actividad de voz usando WebRTC VAD"""
        try:
            # Convertir a bytes si es necesario
            if isinstance(audio_chunk, np.ndarray):
                audio_bytes = audio_chunk.tobytes()
            else:
                audio_bytes = audio_chunk
                
            return self.vad.is_speech(audio_bytes, self.sample_rate)
            
        except Exception as e:
            logger.error(f"Error en detección de voz: {e}")
            return False
    
    def recognize_speech(self, audio_data):
        """Reconocer voz usando DeepSpeech"""
        if not self.is_initialized:
            logger.error("DeepSpeech no inicializado")
            return None
            
        try:
            # Preprocesar audio
            processed_audio = self.preprocess_audio(audio_data)
            if processed_audio is None:
                return None
            
            # Reconocimiento con DeepSpeech
            start_time = time.time()
            text = self.model.stt(processed_audio)
            inference_time = time.time() - start_time
            
            logger.info(f"Reconocimiento completado en {inference_time:.2f}s: '{text}'")
            
            # Post-procesamiento específico del laboratorio
            processed_text = self._postprocess_lab_command(text)
            
            return {
                'text': processed_text,
                'confidence': self._estimate_confidence(text),
                'inference_time': inference_time,
                'raw_text': text
            }
            
        except Exception as e:
            logger.error(f"Error en reconocimiento: {e}")
            return None
    
    def _postprocess_lab_command(self, text):
        """Post-procesar texto para comandos de laboratorio"""
        if not text:
            return text
            
        # Convertir a minúsculas
        text = text.lower().strip()
        
        # Correcciones comunes para términos técnicos
        corrections = {
            'microscopio': ['micro scopio', 'microscopio'],
            'espectrómetro': ['espectro metro', 'espectrometro'],
            'centrífuga': ['centrifuga', 'centrífuga'],
            'inventario': ['inventario', 'inventario'],
            'reservar': ['reservar', 'reserva'],
            'disponible': ['disponible', 'disponibles'],
            'estado': ['estado', 'estados']
        }
        
        for correct, variants in corrections.items():
            for variant in variants:
                text = text.replace(variant, correct)
        
        return text
    
    def _estimate_confidence(self, text):
        """Estimar confianza basada en vocabulario conocido"""
        if not text:
            return 0.0
            
        words = text.lower().split()
        known_words = 0
        
        # Contar palabras conocidas del vocabulario del laboratorio
        all_lab_words = []
        for category_words in self.lab_vocabulary.values():
            all_lab_words.extend(category_words)
        
        for word in words:
            if word in all_lab_words or len(word) > 2:  # Palabras largas probablemente correctas
                known_words += 1
        
        confidence = known_words / len(words) if words else 0.0
        return min(confidence, 1.0)
    
    def start_continuous_listening(self, callback=None):
        """Iniciar escucha continua con detección de actividad de voz"""
        if not self.is_initialized:
            logger.error("DeepSpeech no inicializado")
            return False
            
        self.is_listening = True
        
        def listen_thread():
            try:
                import pyaudio
                
                # Configurar PyAudio
                audio = pyaudio.PyAudio()
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=self.frame_size
                )
                
                logger.info("Iniciando escucha continua...")
                voice_frames = []
                silence_count = 0
                
                while self.is_listening:
                    # Leer frame de audio
                    frame = stream.read(self.frame_size)
                    audio_data = np.frombuffer(frame, dtype=np.int16)
                    
                    # Detectar actividad de voz
                    if self.detect_voice_activity(frame):
                        voice_frames.append(audio_data)
                        silence_count = 0
                    else:
                        silence_count += 1
                        
                        # Si hay silencio después de voz, procesar
                        if voice_frames and silence_count > 10:  # ~300ms de silencio
                            # Concatenar frames de voz
                            voice_audio = np.concatenate(voice_frames)
                            
                            # Reconocer si hay suficiente audio
                            if len(voice_audio) > self.sample_rate * 0.5:  # Mínimo 0.5s
                                result = self.recognize_speech(voice_audio)
                                
                                if result and callback:
                                    callback(result)
                            
                            voice_frames = []
                            silence_count = 0
                
                # Limpiar recursos
                stream.stop_stream()
                stream.close()
                audio.terminate()
                
            except ImportError:
                logger.error("PyAudio no instalado. Usar: pip install pyaudio")
            except Exception as e:
                logger.error(f"Error en escucha continua: {e}")
        
        # Iniciar hilo de escucha
        listen_thread = threading.Thread(target=listen_thread, daemon=True)
        listen_thread.start()
        
        return True
    
    def stop_listening(self):
        """Detener escucha continua"""
        self.is_listening = False
        logger.info("Escucha continua detenida")


class VoiceCommandProcessor:
    """
    Procesador de comandos de voz específico para el laboratorio
    Integra DeepSpeech con la lógica de comandos existente
    """
    
    def __init__(self, voice_recognizer, command_processor_func):
        self.voice_recognizer = voice_recognizer
        self.process_command = command_processor_func
        self.command_history = deque(maxlen=100)
        
    def start_voice_control(self):
        """Iniciar control por voz"""
        def on_speech_recognized(result):
            try:
                text = result['text']
                confidence = result['confidence']
                
                logger.info(f"Comando reconocido: '{text}' (confianza: {confidence:.2f})")
                
                # Procesar solo si la confianza es suficiente
                if confidence > 0.3:  # Umbral ajustable
                    # Usar la función existente de procesamiento de comandos
                    response = self.process_command(text)
                    
                    # Registrar en historial
                    self.command_history.append({
                        'timestamp': time.time(),
                        'text': text,
                        'confidence': confidence,
                        'response': response,
                        'inference_time': result.get('inference_time', 0)
                    })
                    
                    logger.info(f"Respuesta: {response.get('mensaje', 'Sin respuesta')}")
                    
                else:
                    logger.warning(f"Confianza baja, ignorando comando: {text}")
                    
            except Exception as e:
                logger.error(f"Error procesando comando de voz: {e}")
        
        return self.voice_recognizer.start_continuous_listening(on_speech_recognized)
    
    def get_command_stats(self):
        """Obtener estadísticas de comandos de voz"""
        if not self.command_history:
            return {}
            
        recent_commands = list(self.command_history)[-50:]  # Últimos 50
        
        avg_confidence = np.mean([cmd['confidence'] for cmd in recent_commands])
        avg_inference_time = np.mean([cmd['inference_time'] for cmd in recent_commands])
        success_rate = len([cmd for cmd in recent_commands if cmd['response'].get('exito', False)]) / len(recent_commands)
        
        return {
            'total_commands': len(self.command_history),
            'recent_commands': len(recent_commands),
            'avg_confidence': avg_confidence,
            'avg_inference_time': avg_inference_time,
            'success_rate': success_rate,
            'last_command': recent_commands[-1] if recent_commands else None
        }


# Función de inicialización para integrar con web_app.py
def initialize_advanced_voice_recognition(command_processor_func):
    """
    Inicializar reconocimiento de voz avanzado
    
    Args:
        command_processor_func: Función procesar_comando_voz de web_app.py
    
    Returns:
        VoiceCommandProcessor o None si falla
    """
    try:
        # Inicializar DeepSpeech
        recognizer = DeepSpeechVoiceRecognizer()
        
        if not recognizer.initialize():
            logger.warning("Fallback a reconocimiento básico")
            return None
        
        # Crear procesador de comandos
        processor = VoiceCommandProcessor(recognizer, command_processor_func)
        
        logger.info("Reconocimiento de voz avanzado inicializado")
        return processor
        
    except Exception as e:
        logger.error(f"Error inicializando reconocimiento avanzado: {e}")
        return None


if __name__ == "__main__":
    # Prueba básica del módulo
    def dummy_processor(text):
        return {'mensaje': f'Comando procesado: {text}', 'exito': True}
    
    processor = initialize_advanced_voice_recognition(dummy_processor)
    
    if processor:
        print("Iniciando reconocimiento de voz... (Ctrl+C para salir)")
        processor.start_voice_control()
        
        try:
            while True:
                time.sleep(1)
                stats = processor.get_command_stats()
                if stats.get('total_commands', 0) > 0:
                    print(f"Comandos procesados: {stats['total_commands']}")
        except KeyboardInterrupt:
            print("Deteniendo reconocimiento...")
            processor.voice_recognizer.stop_listening()
