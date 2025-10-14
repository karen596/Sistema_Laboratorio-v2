# -*- coding: utf-8 -*-
"""
Módulo de Reconocimiento Visual de Equipos e Items
Centro Minero SENA - Sistema de Laboratorios
"""

import os
import cv2
import numpy as np
import json
import base64
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisualRecognitionManager:
    """
    Gestor de reconocimiento visual para equipos e items de laboratorio
    """
    
    def __init__(self, storage_path: str = "visual_data"):
        """
        Inicializar el gestor de reconocimiento visual
        
        Args:
            storage_path: Ruta donde se almacenan las imágenes y datos
        """
        self.storage_path = Path(storage_path)
        self.equipos_path = self.storage_path / "equipos"
        self.items_path = self.storage_path / "items"
        self.models_path = self.storage_path / "models"
        
        # Crear directorios si no existen
        for path in [self.equipos_path, self.items_path, self.models_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar detector de características
        self.detector = cv2.ORB_create(nfeatures=1000)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        logger.info("VisualRecognitionManager inicializado")
    
    def base64_to_image(self, base64_string: str) -> np.ndarray:
        """
        Convertir imagen base64 a array numpy
        
        Args:
            base64_string: Imagen en formato base64
            
        Returns:
            Imagen como array numpy
        """
        try:
            # Remover prefijo si existe
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decodificar
            image_data = base64.b64decode(base64_string)
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return image
        except Exception as e:
            logger.error(f"Error convirtiendo base64 a imagen: {e}")
            return None
    
    def extract_features(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extraer características de una imagen
        
        Args:
            image: Imagen como array numpy
            
        Returns:
            Tupla con keypoints y descriptores
        """
        try:
            # Convertir a escala de grises si es necesario
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Detectar keypoints y descriptores
            keypoints, descriptors = self.detector.detectAndCompute(gray, None)
            
            if descriptors is None:
                logger.warning("No se pudieron extraer características de la imagen")
                return None, None
            
            logger.info(f"Extraídas {len(keypoints)} características")
            return keypoints, descriptors
            
        except Exception as e:
            logger.error(f"Error extrayendo características: {e}")
            return None, None
    
    def save_training_image(self, item_type: str, item_id: str, image: np.ndarray, 
                          metadata: Dict) -> Dict:
        """
        Guardar imagen de entrenamiento para un equipo o item
        
        Args:
            item_type: 'equipo' o 'item'
            item_id: ID del equipo o item
            image: Imagen como array numpy
            metadata: Metadatos adicionales
            
        Returns:
            Resultado de la operación
        """
        try:
            # Determinar ruta base
            base_path = self.equipos_path if item_type == 'equipo' else self.items_path
            item_path = base_path / str(item_id)
            item_path.mkdir(exist_ok=True)
            
            # Generar nombre único para la imagen
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_hash = hashlib.md5(image.tobytes()).hexdigest()[:8]
            image_filename = f"{timestamp}_{image_hash}.jpg"
            image_path = item_path / image_filename
            
            # Guardar imagen
            cv2.imwrite(str(image_path), image)
            
            # Extraer características
            keypoints, descriptors = self.extract_features(image)
            
            if descriptors is None:
                return {
                    'success': False,
                    'message': 'No se pudieron extraer características de la imagen'
                }
            
            # Guardar descriptores
            features_filename = f"{timestamp}_{image_hash}_features.npz"
            features_path = item_path / features_filename
            
            np.savez_compressed(
                str(features_path),
                descriptors=descriptors,
                keypoints=np.array([[kp.pt[0], kp.pt[1], kp.angle, kp.size] for kp in keypoints])
            )
            
            # Guardar metadatos
            metadata_info = {
                'item_type': item_type,
                'item_id': item_id,
                'image_file': image_filename,
                'features_file': features_filename,
                'timestamp': timestamp,
                'num_features': len(descriptors),
                'image_size': image.shape[:2],
                **metadata
            }
            
            metadata_path = item_path / f"{timestamp}_{image_hash}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_info, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Imagen de entrenamiento guardada: {item_type} {item_id}")
            
            return {
                'success': True,
                'message': 'Imagen de entrenamiento guardada exitosamente',
                'files': {
                    'image': str(image_path),
                    'features': str(features_path),
                    'metadata': str(metadata_path)
                },
                'num_features': len(descriptors)
            }
            
        except Exception as e:
            logger.error(f"Error guardando imagen de entrenamiento: {e}")
            return {
                'success': False,
                'message': f'Error guardando imagen: {str(e)}'
            }
    
    def recognize_item(self, image: np.ndarray, confidence_threshold: float = 0.3) -> Dict:
        """
        Reconocer un equipo o item en una imagen
        
        Args:
            image: Imagen a analizar
            confidence_threshold: Umbral de confianza mínimo
            
        Returns:
            Resultado del reconocimiento
        """
        try:
            # Extraer características de la imagen de consulta
            query_keypoints, query_descriptors = self.extract_features(image)
            
            if query_descriptors is None:
                return {
                    'success': False,
                    'message': 'No se pudieron extraer características de la imagen'
                }
            
            best_match = None
            best_score = 0
            all_matches = []
            
            # Buscar en equipos y items
            for item_type in ['equipo', 'item']:
                base_path = self.equipos_path if item_type == 'equipo' else self.items_path
                
                if not base_path.exists():
                    continue
                
                for item_dir in base_path.iterdir():
                    if not item_dir.is_dir():
                        continue
                    
                    item_id = item_dir.name
                    
                    # Buscar archivos de características
                    for features_file in item_dir.glob("*_features.npz"):
                        try:
                            # Cargar características guardadas
                            features_data = np.load(str(features_file))
                            stored_descriptors = features_data['descriptors']
                            
                            # Comparar características
                            matches = self.matcher.match(query_descriptors, stored_descriptors)
                            
                            if len(matches) < 10:  # Muy pocas coincidencias
                                continue
                            
                            # Calcular score basado en distancia promedio
                            distances = [m.distance for m in matches]
                            avg_distance = np.mean(distances)
                            score = max(0, 1 - (avg_distance / 256))  # Normalizar a 0-1
                            
                            # Cargar metadatos
                            metadata_file = features_file.with_suffix('.json').name.replace('_features', '_metadata')
                            metadata_path = item_dir / metadata_file
                            
                            metadata = {}
                            if metadata_path.exists():
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                            
                            match_info = {
                                'item_type': item_type,
                                'item_id': item_id,
                                'score': score,
                                'num_matches': len(matches),
                                'avg_distance': avg_distance,
                                'metadata': metadata
                            }
                            
                            all_matches.append(match_info)
                            
                            if score > best_score:
                                best_score = score
                                best_match = match_info
                        
                        except Exception as e:
                            logger.warning(f"Error procesando {features_file}: {e}")
                            continue
            
            # Ordenar matches por score
            all_matches.sort(key=lambda x: x['score'], reverse=True)
            
            if best_match and best_score >= confidence_threshold:
                return {
                    'success': True,
                    'recognized': True,
                    'item_type': best_match['item_type'],
                    'item_id': best_match['item_id'],
                    'confidence': best_score,
                    'num_matches': best_match['num_matches'],
                    'metadata': best_match['metadata'],
                    'all_candidates': all_matches[:5]  # Top 5 candidatos
                }
            else:
                return {
                    'success': True,
                    'recognized': False,
                    'message': 'No se encontraron coincidencias suficientes',
                    'best_score': best_score,
                    'threshold': confidence_threshold,
                    'all_candidates': all_matches[:3]  # Top 3 candidatos
                }
        
        except Exception as e:
            logger.error(f"Error en reconocimiento: {e}")
            return {
                'success': False,
                'message': f'Error en reconocimiento: {str(e)}'
            }
    
    def get_training_stats(self) -> Dict:
        """
        Obtener estadísticas del entrenamiento
        
        Returns:
            Estadísticas del sistema
        """
        try:
            stats = {
                'equipos': {'count': 0, 'images': 0},
                'items': {'count': 0, 'images': 0},
                'total_features': 0
            }
            
            for item_type in ['equipo', 'item']:
                base_path = self.equipos_path if item_type == 'equipo' else self.items_path
                key = 'equipos' if item_type == 'equipo' else 'items'
                
                if base_path.exists():
                    item_dirs = [d for d in base_path.iterdir() if d.is_dir()]
                    stats[key]['count'] = len(item_dirs)
                    
                    for item_dir in item_dirs:
                        features_files = list(item_dir.glob("*_features.npz"))
                        stats[key]['images'] += len(features_files)
                        
                        for features_file in features_files:
                            try:
                                features_data = np.load(str(features_file))
                                stats['total_features'] += len(features_data['descriptors'])
                            except:
                                pass
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {'error': str(e)}
    
    def delete_training_data(self, item_type: str, item_id: str) -> Dict:
        """
        Eliminar datos de entrenamiento de un item
        
        Args:
            item_type: 'equipo' o 'item'
            item_id: ID del item
            
        Returns:
            Resultado de la operación
        """
        try:
            base_path = self.equipos_path if item_type == 'equipo' else self.items_path
            item_path = base_path / str(item_id)
            
            if not item_path.exists():
                return {
                    'success': False,
                    'message': 'No se encontraron datos de entrenamiento para este item'
                }
            
            # Contar archivos antes de eliminar
            files_count = len(list(item_path.iterdir()))
            
            # Eliminar directorio y contenido
            import shutil
            shutil.rmtree(str(item_path))
            
            return {
                'success': True,
                'message': f'Datos de entrenamiento eliminados ({files_count} archivos)',
                'deleted_files': files_count
            }
            
        except Exception as e:
            logger.error(f"Error eliminando datos de entrenamiento: {e}")
            return {
                'success': False,
                'message': f'Error eliminando datos: {str(e)}'
            }

# Instancia global del gestor
visual_manager = VisualRecognitionManager()
