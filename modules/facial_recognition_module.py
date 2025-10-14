# -*- coding: utf-8 -*-
"""
Módulo de Reconocimiento Facial
Centro Minero SENA - Sistema de Laboratorio
"""

import os
import cv2
import face_recognition
import numpy as np
import json
import base64
from PIL import Image
from io import BytesIO
import logging
from typing import List, Dict, Optional, Tuple

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FacialRecognitionManager:
    """Gestor principal del sistema de reconocimiento facial"""
    
    def __init__(self):
        self.min_face_size = (100, 100)  # Tamaño mínimo de rostro
        self.max_face_size = (800, 800)  # Tamaño máximo de rostro
        self.quality_threshold = 50.0    # Umbral mínimo de calidad
        self.encoding_tolerance = 0.6    # Tolerancia para comparación
        
    def capture_from_camera(self, camera_index: int = 0, num_frames: int = 5) -> List[np.ndarray]:
        """
        Capturar múltiples frames desde la cámara
        
        Args:
            camera_index: Índice de la cámara (0 por defecto)
            num_frames: Número de frames a capturar
            
        Returns:
            Lista de imágenes capturadas
        """
        try:
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                raise Exception(f"No se pudo abrir la cámara {camera_index}")
            
            # Configurar resolución
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            frames = []
            frame_count = 0
            
            logger.info(f"Capturando {num_frames} frames desde cámara {camera_index}")
            
            while frame_count < num_frames:
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"No se pudo capturar frame {frame_count + 1}")
                    continue
                
                # Convertir BGR a RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(rgb_frame)
                frame_count += 1
                
                logger.info(f"Frame {frame_count}/{num_frames} capturado")
            
            cap.release()
            return frames
            
        except Exception as e:
            logger.error(f"Error capturando desde cámara: {e}")
            if 'cap' in locals():
                cap.release()
            raise
    
    def process_image_from_base64(self, image_base64: str) -> np.ndarray:
        """
        Procesar imagen desde base64
        
        Args:
            image_base64: Imagen en formato base64
            
        Returns:
            Array numpy de la imagen
        """
        try:
            # Remover prefijo si existe
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            
            # Decodificar base64
            image_data = base64.b64decode(image_base64)
            
            # Convertir a PIL Image
            pil_image = Image.open(BytesIO(image_data))
            
            # Convertir a RGB si es necesario
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convertir a numpy array
            image_array = np.array(pil_image)
            
            return image_array
            
        except Exception as e:
            logger.error(f"Error procesando imagen base64: {e}")
            raise
    
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Detectar rostros en una imagen
        
        Args:
            image: Imagen como array numpy
            
        Returns:
            Lista de rostros detectados con información
        """
        try:
            # Redimensionar imagen para acelerar detección
            height, width = image.shape[:2]
            if width > 640:
                scale = 640 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))
                logger.info(f"Imagen redimensionada para detección: {width}x{height} -> {new_width}x{new_height}")
            
            # Detectar ubicaciones de rostros con modelo rápido
            face_locations = face_recognition.face_locations(image, model='hog')
            
            if not face_locations:
                return []
            
            faces_info = []
            
            for i, (top, right, bottom, left) in enumerate(face_locations):
                # Extraer región del rostro
                face_image = image[top:bottom, left:right]
                
                # Calcular dimensiones
                face_width = right - left
                face_height = bottom - top
                
                # Calcular calidad básica (basada en tamaño y nitidez)
                quality = self._calculate_image_quality(face_image)
                
                face_info = {
                    'index': i,
                    'location': (top, right, bottom, left),
                    'width': face_width,
                    'height': face_height,
                    'size': (face_width, face_height),
                    'quality': quality,
                    'face_image': face_image,
                    'valid': self._is_valid_face(face_width, face_height, quality)
                }
                
                faces_info.append(face_info)
            
            logger.info(f"Detectados {len(faces_info)} rostros en la imagen")
            return faces_info
            
        except Exception as e:
            logger.error(f"Error detectando rostros: {e}")
            raise
    
    def generate_face_encoding(self, image: np.ndarray, face_location: Optional[Tuple] = None) -> Optional[np.ndarray]:
        """
        Generar encoding facial de una imagen
        
        Args:
            image: Imagen como array numpy
            face_location: Ubicación específica del rostro (opcional)
            
        Returns:
            Encoding facial como array numpy
        """
        try:
            # Redimensionar imagen para acelerar procesamiento
            height, width = image.shape[:2]
            if width > 640:
                scale = 640 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))
                logger.info(f"Imagen redimensionada de {width}x{height} a {new_width}x{new_height}")
            
            if face_location:
                # Ajustar ubicación si se redimensionó
                if width > 640:
                    scale = 640 / width
                    top, right, bottom, left = face_location
                    face_location = (
                        int(top * scale),
                        int(right * scale), 
                        int(bottom * scale),
                        int(left * scale)
                    )
                # Usar ubicación específica
                encodings = face_recognition.face_encodings(image, [face_location], model='small')
            else:
                # Detectar automáticamente con modelo rápido
                encodings = face_recognition.face_encodings(image, model='small')
            
            if not encodings:
                logger.warning("No se pudo generar encoding facial")
                return None
            
            # Retornar el primer encoding
            encoding = encodings[0]
            logger.info(f"Encoding facial generado: {len(encoding)} dimensiones")
            
            return encoding
            
        except Exception as e:
            logger.error(f"Error generando encoding facial: {e}")
            return None
    
    def register_user_face(self, user_id: str, image: np.ndarray) -> Dict:
        """
        Registrar rostro de usuario
        
        Args:
            user_id: ID del usuario
            image: Imagen con el rostro
            
        Returns:
            Resultado del registro
        """
        try:
            logger.info(f"Iniciando registro facial para usuario: {user_id}")
            
            # Detectar rostros
            faces = self.detect_faces(image)
            
            if not faces:
                return {
                    'success': False,
                    'error': 'No se detectaron rostros en la imagen',
                    'code': 'NO_FACE_DETECTED'
                }
            
            if len(faces) > 1:
                return {
                    'success': False,
                    'error': f'Se detectaron {len(faces)} rostros. Solo debe haber uno.',
                    'code': 'MULTIPLE_FACES'
                }
            
            face = faces[0]
            
            # Validar calidad del rostro
            if not face['valid']:
                return {
                    'success': False,
                    'error': f'Calidad del rostro insuficiente: {face["quality"]:.1f}%',
                    'code': 'LOW_QUALITY',
                    'quality': face['quality']
                }
            
            # Generar encoding
            encoding = self.generate_face_encoding(image, face['location'])
            
            if encoding is None:
                return {
                    'success': False,
                    'error': 'No se pudo generar el encoding facial',
                    'code': 'ENCODING_FAILED'
                }
            
            # Convertir encoding a formato serializable
            encoding_json = json.dumps(encoding.tolist())
            
            # Convertir imagen de referencia a base64
            reference_image = self._image_to_base64(face['face_image'])
            
            result = {
                'success': True,
                'user_id': user_id,
                'encoding': encoding_json,
                'reference_image': reference_image,
                'quality': face['quality'],
                'face_size': face['size'],
                'message': f'Rostro registrado exitosamente (calidad: {face["quality"]:.1f}%)'
            }
            
            logger.info(f"Registro facial exitoso para usuario {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error en registro facial: {e}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'code': 'INTERNAL_ERROR'
            }
    
    def _calculate_image_quality(self, image: np.ndarray) -> float:
        """
        Calcular calidad de imagen basada en nitidez y contraste
        
        Args:
            image: Imagen como array numpy
            
        Returns:
            Calidad como porcentaje (0-100)
        """
        try:
            # Convertir a escala de grises
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Calcular varianza del Laplaciano (nitidez)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calcular contraste (desviación estándar)
            contrast = np.std(gray)
            
            # Normalizar y combinar métricas
            sharpness_score = min(laplacian_var / 100.0, 1.0) * 50
            contrast_score = min(contrast / 50.0, 1.0) * 50
            
            quality = sharpness_score + contrast_score
            
            return min(quality, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculando calidad: {e}")
            return 0.0
    
    def _is_valid_face(self, width: int, height: int, quality: float) -> bool:
        """
        Validar si un rostro cumple los criterios mínimos
        
        Args:
            width: Ancho del rostro
            height: Alto del rostro
            quality: Calidad de la imagen
            
        Returns:
            True si es válido
        """
        # Verificar tamaño mínimo
        if width < self.min_face_size[0] or height < self.min_face_size[1]:
            return False
        
        # Verificar tamaño máximo
        if width > self.max_face_size[0] or height > self.max_face_size[1]:
            return False
        
        # Verificar calidad mínima
        if quality < self.quality_threshold:
            return False
        
        return True
    
    def _image_to_base64(self, image: np.ndarray) -> str:
        """
        Convertir imagen numpy a base64
        
        Args:
            image: Imagen como array numpy
            
        Returns:
            Imagen en formato base64
        """
        try:
            # Convertir a PIL Image
            pil_image = Image.fromarray(image)
            
            # Guardar en buffer
            buffer = BytesIO()
            pil_image.save(buffer, format='JPEG', quality=85)
            
            # Convertir a base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return f"data:image/jpeg;base64,{image_base64}"
            
        except Exception as e:
            logger.error(f"Error convirtiendo imagen a base64: {e}")
            return ""

# Instancia global del gestor
facial_manager = FacialRecognitionManager()

def test_camera():
    """Función de prueba para verificar la cámara"""
    try:
        print("🔍 Probando cámara...")
        frames = facial_manager.capture_from_camera(num_frames=1)
        
        if frames:
            print(f"✅ Cámara funcionando. Capturado frame de {frames[0].shape}")
            
            # Detectar rostros en el frame
            faces = facial_manager.detect_faces(frames[0])
            print(f"👤 Rostros detectados: {len(faces)}")
            
            for i, face in enumerate(faces):
                print(f"  Rostro {i+1}: {face['size']}, calidad: {face['quality']:.1f}%")
        else:
            print("❌ No se pudieron capturar frames")
            
    except Exception as e:
        print(f"❌ Error probando cámara: {e}")

if __name__ == "__main__":
    test_camera()
