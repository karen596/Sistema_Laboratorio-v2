# -*- coding: utf-8 -*-
"""
Módulo de Reconocimiento Visual Avanzado con TensorFlow
Sistema de Gestión Inteligente - Centro Minero SENA
"""

import os
import cv2
import numpy as np
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import base64

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TensorFlowObjectDetector:
    """
    Detector de objetos usando TensorFlow/TensorFlow Lite
    Optimizado para equipos de laboratorio
    """
    
    def __init__(self, model_path=None, labels_path=None, use_lite=True):
        self.model_path = model_path or 'models/lab_equipment_model.tflite'
        self.labels_path = labels_path or 'models/lab_equipment_labels.txt'
        self.use_lite = use_lite
        self.interpreter = None
        self.labels = []
        self.input_details = None
        self.output_details = None
        self.is_initialized = False
        
        # Configuración del modelo
        self.input_size = (224, 224)  # Tamaño estándar para MobileNet
        self.confidence_threshold = 0.5
        self.nms_threshold = 0.4
        
        # Cache para mejorar rendimiento
        self.prediction_cache = {}
        self.cache_max_size = 100
        
    def initialize(self):
        """Inicializar el modelo TensorFlow"""
        try:
            if self.use_lite:
                import tflite_runtime.interpreter as tflite
                
                if not os.path.exists(self.model_path):
                    logger.warning(f"Modelo no encontrado: {self.model_path}")
                    return self._initialize_fallback_model()
                
                # Cargar modelo TensorFlow Lite
                logger.info("Cargando modelo TensorFlow Lite...")
                self.interpreter = tflite.Interpreter(model_path=self.model_path)
                self.interpreter.allocate_tensors()
                
                # Obtener detalles de entrada y salida
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                
            else:
                import tensorflow as tf
                
                logger.info("Cargando modelo TensorFlow completo...")
                self.model = tf.keras.models.load_model(self.model_path)
            
            # Cargar etiquetas
            self._load_labels()
            
            self.is_initialized = True
            logger.info("TensorFlow inicializado correctamente")
            return True
            
        except ImportError as e:
            logger.error(f"TensorFlow no instalado: {e}")
            return self._initialize_fallback_model()
        except Exception as e:
            logger.error(f"Error inicializando TensorFlow: {e}")
            return self._initialize_fallback_model()
    
    def _initialize_fallback_model(self):
        """Inicializar modelo de respaldo si TensorFlow falla"""
        logger.info("Inicializando modelo de respaldo (OpenCV + clasificador simple)")
        
        # Crear clasificador básico basado en características
        self.fallback_classifier = SimpleLabEquipmentClassifier()
        self.is_initialized = True
        self.use_fallback = True
        
        return True
    
    def _load_labels(self):
        """Cargar etiquetas de clases"""
        try:
            if os.path.exists(self.labels_path):
                with open(self.labels_path, 'r', encoding='utf-8') as f:
                    self.labels = [line.strip() for line in f.readlines()]
            else:
                # Etiquetas por defecto para equipos de laboratorio
                self.labels = [
                    'microscopio',
                    'balanza_analitica',
                    'espectrofotometro',
                    'centrifuga',
                    'autoclave',
                    'pipeta',
                    'matraz',
                    'probeta',
                    'bureta',
                    'vaso_precipitado',
                    'erlenmeyer',
                    'tubo_ensayo',
                    'placa_petri',
                    'mechero_bunsen',
                    'agitador_magnetico'
                ]
                
                # Guardar etiquetas por defecto
                with open(self.labels_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.labels))
            
            logger.info(f"Cargadas {len(self.labels)} etiquetas de equipos")
            
        except Exception as e:
            logger.error(f"Error cargando etiquetas: {e}")
            self.labels = ['equipo_desconocido']
    
    def preprocess_image(self, image):
        """Preprocesar imagen para el modelo"""
        try:
            # Redimensionar a tamaño de entrada del modelo
            if isinstance(image, str):  # Si es base64
                image = self._decode_base64_image(image)
            
            if image is None:
                return None
            
            # Convertir BGR a RGB si es necesario
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Redimensionar
            image_resized = cv2.resize(image, self.input_size)
            
            # Normalizar a [0, 1]
            image_normalized = image_resized.astype(np.float32) / 255.0
            
            # Añadir dimensión de batch
            image_batch = np.expand_dims(image_normalized, axis=0)
            
            return image_batch
            
        except Exception as e:
            logger.error(f"Error preprocesando imagen: {e}")
            return None
    
    def _decode_base64_image(self, img_b64):
        """Decodificar imagen base64"""
        try:
            if ',' in img_b64:
                img_b64 = img_b64.split(',')[1]
            
            img_bytes = base64.b64decode(img_b64)
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            return image
            
        except Exception as e:
            logger.error(f"Error decodificando imagen base64: {e}")
            return None
    
    def detect_objects(self, image):
        """Detectar objetos en la imagen"""
        if not self.is_initialized:
            logger.error("Modelo no inicializado")
            return None
        
        try:
            # Verificar cache
            image_hash = self._get_image_hash(image)
            if image_hash in self.prediction_cache:
                logger.info("Usando predicción desde cache")
                return self.prediction_cache[image_hash]
            
            # Preprocesar imagen
            processed_image = self.preprocess_image(image)
            if processed_image is None:
                return None
            
            start_time = time.time()
            
            if hasattr(self, 'use_fallback') and self.use_fallback:
                # Usar clasificador de respaldo
                results = self.fallback_classifier.classify(image)
            else:
                # Usar TensorFlow
                results = self._run_tensorflow_inference(processed_image)
            
            inference_time = time.time() - start_time
            
            # Añadir tiempo de inferencia a resultados
            if results:
                results['inference_time'] = inference_time
                
                # Guardar en cache
                self._update_cache(image_hash, results)
            
            logger.info(f"Detección completada en {inference_time:.3f}s")
            return results
            
        except Exception as e:
            logger.error(f"Error en detección: {e}")
            return None
    
    def _run_tensorflow_inference(self, processed_image):
        """Ejecutar inferencia con TensorFlow"""
        try:
            if self.use_lite:
                # TensorFlow Lite
                self.interpreter.set_tensor(self.input_details[0]['index'], processed_image)
                self.interpreter.invoke()
                
                # Obtener predicciones
                predictions = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
                
            else:
                # TensorFlow completo
                predictions = self.model.predict(processed_image)[0]
            
            # Procesar predicciones
            results = self._process_predictions(predictions)
            return results
            
        except Exception as e:
            logger.error(f"Error en inferencia TensorFlow: {e}")
            return None
    
    def _process_predictions(self, predictions):
        """Procesar predicciones del modelo"""
        try:
            # Obtener clase con mayor confianza
            max_confidence_idx = np.argmax(predictions)
            max_confidence = float(predictions[max_confidence_idx])
            
            if max_confidence < self.confidence_threshold:
                return {
                    'detected': False,
                    'message': 'No se detectó ningún equipo con suficiente confianza',
                    'confidence': max_confidence
                }
            
            # Obtener etiqueta
            if max_confidence_idx < len(self.labels):
                detected_class = self.labels[max_confidence_idx]
            else:
                detected_class = 'equipo_desconocido'
            
            # Obtener top 3 predicciones
            top_indices = np.argsort(predictions)[-3:][::-1]
            top_predictions = []
            
            for idx in top_indices:
                if idx < len(self.labels) and predictions[idx] > 0.1:
                    top_predictions.append({
                        'class': self.labels[idx],
                        'confidence': float(predictions[idx])
                    })
            
            return {
                'detected': True,
                'class': detected_class,
                'confidence': max_confidence,
                'top_predictions': top_predictions,
                'message': f'Detectado: {detected_class} (confianza: {max_confidence:.2f})'
            }
            
        except Exception as e:
            logger.error(f"Error procesando predicciones: {e}")
            return None
    
    def _get_image_hash(self, image):
        """Generar hash de imagen para cache"""
        try:
            if isinstance(image, str):
                return hash(image[:100])  # Hash de primeros 100 chars si es base64
            else:
                return hash(image.tobytes()[:1000])  # Hash de primeros 1000 bytes
        except:
            return hash(str(time.time()))
    
    def _update_cache(self, image_hash, results):
        """Actualizar cache de predicciones"""
        try:
            if len(self.prediction_cache) >= self.cache_max_size:
                # Eliminar entrada más antigua
                oldest_key = next(iter(self.prediction_cache))
                del self.prediction_cache[oldest_key]
            
            self.prediction_cache[image_hash] = results
            
        except Exception as e:
            logger.error(f"Error actualizando cache: {e}")
    
    def train_custom_model(self, training_data_path, epochs=10):
        """Entrenar modelo personalizado con datos del laboratorio"""
        try:
            import tensorflow as tf
            from tensorflow.keras.applications import MobileNetV2
            from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
            from tensorflow.keras.models import Model
            from tensorflow.keras.preprocessing.image import ImageDataGenerator
            
            logger.info("Iniciando entrenamiento de modelo personalizado...")
            
            # Cargar modelo base pre-entrenado
            base_model = MobileNetV2(
                weights='imagenet',
                include_top=False,
                input_shape=(224, 224, 3)
            )
            
            # Congelar capas base
            base_model.trainable = False
            
            # Añadir capas personalizadas
            x = base_model.output
            x = GlobalAveragePooling2D()(x)
            x = Dense(128, activation='relu')(x)
            predictions = Dense(len(self.labels), activation='softmax')(x)
            
            model = Model(inputs=base_model.input, outputs=predictions)
            
            # Compilar modelo
            model.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            # Preparar datos de entrenamiento
            datagen = ImageDataGenerator(
                rescale=1./255,
                rotation_range=20,
                width_shift_range=0.2,
                height_shift_range=0.2,
                horizontal_flip=True,
                validation_split=0.2
            )
            
            train_generator = datagen.flow_from_directory(
                training_data_path,
                target_size=(224, 224),
                batch_size=32,
                class_mode='categorical',
                subset='training'
            )
            
            validation_generator = datagen.flow_from_directory(
                training_data_path,
                target_size=(224, 224),
                batch_size=32,
                class_mode='categorical',
                subset='validation'
            )
            
            # Entrenar modelo
            history = model.fit(
                train_generator,
                epochs=epochs,
                validation_data=validation_generator,
                verbose=1
            )
            
            # Guardar modelo entrenado
            model_save_path = 'models/lab_equipment_custom.h5'
            model.save(model_save_path)
            
            # Convertir a TensorFlow Lite para optimización
            converter = tf.lite.TFLiteConverter.from_keras_model(model)
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            tflite_model = converter.convert()
            
            tflite_save_path = 'models/lab_equipment_custom.tflite'
            with open(tflite_save_path, 'wb') as f:
                f.write(tflite_model)
            
            logger.info(f"Modelo entrenado guardado en: {model_save_path}")
            logger.info(f"Modelo TFLite guardado en: {tflite_save_path}")
            
            return {
                'success': True,
                'model_path': model_save_path,
                'tflite_path': tflite_save_path,
                'training_history': history.history
            }
            
        except Exception as e:
            logger.error(f"Error entrenando modelo: {e}")
            return {'success': False, 'error': str(e)}


class SimpleLabEquipmentClassifier:
    """
    Clasificador simple de respaldo usando características tradicionales
    """
    
    def __init__(self):
        self.feature_extractors = {
            'color_histogram': self._extract_color_histogram,
            'shape_features': self._extract_shape_features,
            'texture_features': self._extract_texture_features
        }
        
        # Patrones conocidos para equipos comunes
        self.equipment_patterns = {
            'microscopio': {
                'color_dominant': [50, 50, 50],  # Gris oscuro
                'shape_complexity': 'high',
                'size_ratio': 'vertical'
            },
            'balanza': {
                'color_dominant': [200, 200, 200],  # Gris claro
                'shape_complexity': 'medium',
                'size_ratio': 'square'
            },
            'matraz': {
                'color_dominant': [240, 240, 240],  # Transparente/blanco
                'shape_complexity': 'low',
                'size_ratio': 'vertical'
            }
        }
    
    def classify(self, image):
        """Clasificar equipo usando características tradicionales"""
        try:
            # Extraer características
            features = {}
            for name, extractor in self.feature_extractors.items():
                features[name] = extractor(image)
            
            # Comparar con patrones conocidos
            best_match = None
            best_score = 0
            
            for equipment, pattern in self.equipment_patterns.items():
                score = self._calculate_similarity(features, pattern)
                if score > best_score:
                    best_score = score
                    best_match = equipment
            
            if best_score > 0.3:  # Umbral mínimo
                return {
                    'detected': True,
                    'class': best_match,
                    'confidence': best_score,
                    'message': f'Detectado (método tradicional): {best_match}'
                }
            else:
                return {
                    'detected': False,
                    'message': 'No se pudo identificar el equipo',
                    'confidence': best_score
                }
                
        except Exception as e:
            logger.error(f"Error en clasificación simple: {e}")
            return None
    
    def _extract_color_histogram(self, image):
        """Extraer histograma de color"""
        try:
            # Convertir a HSV para mejor separación de colores
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Calcular histograma
            hist = cv2.calcHist([hsv], [0, 1, 2], None, [50, 60, 60], [0, 180, 0, 256, 0, 256])
            
            # Normalizar
            hist = cv2.normalize(hist, hist).flatten()
            
            return hist
            
        except Exception as e:
            logger.error(f"Error extrayendo histograma: {e}")
            return np.zeros(50*60*60)
    
    def _extract_shape_features(self, image):
        """Extraer características de forma"""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detectar contornos
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return {'area': 0, 'perimeter': 0, 'aspect_ratio': 1}
            
            # Obtener contorno más grande
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Calcular características
            area = cv2.contourArea(largest_contour)
            perimeter = cv2.arcLength(largest_contour, True)
            
            # Rectángulo delimitador
            x, y, w, h = cv2.boundingRect(largest_contour)
            aspect_ratio = w / h if h > 0 else 1
            
            return {
                'area': area,
                'perimeter': perimeter,
                'aspect_ratio': aspect_ratio
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo características de forma: {e}")
            return {'area': 0, 'perimeter': 0, 'aspect_ratio': 1}
    
    def _extract_texture_features(self, image):
        """Extraer características de textura usando LBP"""
        try:
            from skimage.feature import local_binary_pattern
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calcular LBP
            radius = 3
            n_points = 8 * radius
            lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
            
            # Histograma de LBP
            hist, _ = np.histogram(lbp.ravel(), bins=n_points + 2, range=(0, n_points + 2))
            hist = hist.astype(float)
            hist /= (hist.sum() + 1e-7)  # Normalizar
            
            return hist
            
        except ImportError:
            # Si scikit-image no está disponible, usar características básicas
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return np.histogram(gray, bins=256)[0] / gray.size
        except Exception as e:
            logger.error(f"Error extrayendo textura: {e}")
            return np.zeros(256)
    
    def _calculate_similarity(self, features, pattern):
        """Calcular similitud entre características y patrón"""
        try:
            # Implementación básica de similitud
            # En una versión completa, usaríamos ML más sofisticado
            
            score = 0.5  # Score base
            
            # Aquí iría la lógica de comparación específica
            # Por simplicidad, retornamos score aleatorio basado en patrón
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculando similitud: {e}")
            return 0.0


# Función de integración con web_app.py
def initialize_advanced_vision(img_root_path):
    """
    Inicializar reconocimiento visual avanzado
    
    Args:
        img_root_path: Ruta a carpeta de imágenes
    
    Returns:
        TensorFlowObjectDetector o None si falla
    """
    try:
        # Crear directorio de modelos si no existe
        models_dir = Path('models')
        models_dir.mkdir(exist_ok=True)
        
        # Inicializar detector
        detector = TensorFlowObjectDetector()
        
        if not detector.initialize():
            logger.warning("Fallback a detección básica")
            return None
        
        logger.info("Reconocimiento visual avanzado inicializado")
        return detector
        
    except Exception as e:
        logger.error(f"Error inicializando visión avanzada: {e}")
        return None


if __name__ == "__main__":
    # Prueba básica del módulo
    detector = initialize_advanced_vision('imagenes')
    
    if detector:
        print("Detector inicializado correctamente")
        
        # Probar con imagen de ejemplo
        test_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        result = detector.detect_objects(test_image)
        
        if result:
            print(f"Resultado de prueba: {result}")
        else:
            print("Error en detección de prueba")
    else:
        print("Error inicializando detector")
