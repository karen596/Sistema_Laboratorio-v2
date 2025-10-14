# -*- coding: utf-8 -*-
# Sistema de Gestión Inteligente de Laboratorios (CLI Prototipo)
# Centro Minero - Regional Boyacá - SENA

import os
import sys
import datetime
import logging
from datetime import datetime as dt
from typing import List, Optional, Dict

import cv2
import numpy as np
import mysql.connector
from mysql.connector import Error
import speech_recognition as sr
import pyttsx3


# ============================== CONFIGURACIÓN ==============================
class Configuracion:
    # Base de datos (credenciales provistas por el usuario)
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = '1234'
    DB_NAME = 'laboratorio_sistema'

    # Voz
    VOZ_IDIOMA = 'es-ES'
    VOZ_VELOCIDAD = 150
    VOZ_VOLUMEN = 0.8
    VOZ_TIMEOUT = 8
    # Índice del micrófono (PyAudio/SpeechRecognition). Usar None para predeterminado.
    MIC_DEVICE_INDEX = 1

    # Cámara
    CAMERA_INDEX = 0
    ROSTRO_CASCADE = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

    # Rutas
    DIR_LOGS = 'logs'


# ================================ UTILIDADES ================================
class Utilidades:
    @staticmethod
    def validar_fecha(fecha_str: str) -> bool:
        try:
            datetime.datetime.strptime(fecha_str, '%Y-%m-%d %H:%M')
            return True
        except ValueError:
            return False

    @staticmethod
    def validar_email(email: str) -> bool:
        import re
        patron = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        return re.fullmatch(patron, email) is not None

    @staticmethod
    def crear_directorio_si_no_existe(ruta: str):
        if not os.path.exists(ruta):
            os.makedirs(ruta)


# ================================= LOGGING =================================
class Logger:
    def __init__(self):
        Utilidades.crear_directorio_si_no_existe(Configuracion.DIR_LOGS)
        log_filename = os.path.join(Configuracion.DIR_LOGS, f"sistema_{dt.now().strftime('%Y%m%d')}.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('sistema')

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)


log = Logger()


# ================================ BASE DATOS ================================
class DatabaseManager:
    def __init__(self,
                 host=Configuracion.DB_HOST,
                 user=Configuracion.DB_USER,
                 password=Configuracion.DB_PASSWORD,
                 database=Configuracion.DB_NAME):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def conectar(self) -> bool:
        try:
            self.connection = mysql.connector.connect(host=self.host, user=self.user, password=self.password)
            if self.connection.is_connected():
                self._bootstrap()
                return True
        except Error as e:
            log.error(f"Error MySQL: {e}")
        return False

    def _bootstrap(self):
        c = self.connection.cursor()
        c.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        c.execute(f"USE {self.database}")
        # Tablas mínimas para arrancar
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id VARCHAR(50) PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                tipo ENUM('instructor','aprendiz','administrador') NOT NULL,
                programa VARCHAR(100),
                nivel_acceso INT DEFAULT 1,
                activo BOOLEAN DEFAULT TRUE,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                rostro_data LONGBLOB,
                email VARCHAR(100),
                telefono VARCHAR(20)
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS equipos (
                id VARCHAR(50) PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                tipo VARCHAR(50) NOT NULL,
                estado ENUM('disponible','en_uso','mantenimiento','fuera_servicio') DEFAULT 'disponible',
                ubicacion VARCHAR(100)
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS inventario (
                id VARCHAR(50) PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                categoria VARCHAR(50),
                cantidad_actual INT DEFAULT 0,
                cantidad_minima INT DEFAULT 0,
                unidad VARCHAR(20)
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS reservas (
                id VARCHAR(50) PRIMARY KEY,
                usuario_id VARCHAR(50),
                equipo_id VARCHAR(50),
                fecha_inicio DATETIME NOT NULL,
                fecha_fin DATETIME NOT NULL,
                estado ENUM('programada','activa','completada','cancelada') DEFAULT 'programada',
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                FOREIGN KEY (equipo_id) REFERENCES equipos(id)
            )
            """
        )
        self.connection.commit()
        c.close()
        # Reabrir ya con DB
        self.connection.close()
        self.connection = mysql.connector.connect(
            host=self.host, user=self.user, password=self.password, database=self.database
        )
        log.info("Base de datos lista")

    def ejecutar_consulta(self, q: str, params: tuple = None) -> List[tuple]:
        try:
            cur = self.connection.cursor()
            cur.execute(q, params or ())
            rows = cur.fetchall()
            cur.close()
            return rows
        except Error as e:
            log.error(f"Consulta falló: {e}")
            return []

    def ejecutar_comando(self, q: str, params: tuple = None) -> bool:
        try:
            cur = self.connection.cursor()
            cur.execute(q, params or ())
            self.connection.commit()
            cur.close()
            return True
        except Error as e:
            log.error(f"Comando falló: {e}")
            return False

    def cerrar(self):
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                log.info("Conexión MySQL cerrada")
        except Exception:
            pass


# ================================ RECONOCIMIENTO DE VOZ ================================
class ReconocimientoVoz:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.recognizer = sr.Recognizer()
        # Parámetros recomendados para mejorar estabilidad
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.6  # fin de frase más ágil
        self.recognizer.non_speaking_duration = 0.3
        try:
            # Intentar con el índice configurado
            if Configuracion.MIC_DEVICE_INDEX is not None:
                try:
                    self.microphone = sr.Microphone(device_index=Configuracion.MIC_DEVICE_INDEX)
                except Exception:
                    # Fallback al dispositivo predeterminado
                    self.microphone = sr.Microphone()
            else:
                self.microphone = sr.Microphone()
        except Exception:
            self.microphone = None
        self.engine = pyttsx3.init()
        self._configurar_voz()
        self.usuario_actual: Optional[str] = None

    def _configurar_voz(self):
        try:
            self.engine.setProperty('rate', Configuracion.VOZ_VELOCIDAD)
            self.engine.setProperty('volume', Configuracion.VOZ_VOLUMEN)
            for v in self.engine.getProperty('voices'):
                if 'spanish' in v.name.lower() or 'es' in getattr(v, 'id', '').lower():
                    self.engine.setProperty('voice', v.id)
                    break
        except Exception:
            pass

    def hablar(self, msg: str):
        print(f"🔊 {msg}")
        try:
            self.engine.say(msg)
            self.engine.runAndWait()
        except Exception:
            pass

    def escuchar(self) -> Optional[str]:
        # Intentar recrear micrófono si no está disponible
        if not self.microphone:
            try:
                self.microphone = sr.Microphone(device_index=Configuracion.MIC_DEVICE_INDEX) if Configuracion.MIC_DEVICE_INDEX is not None else sr.Microphone()
            except Exception as e:
                log.error(f"Micrófono no disponible: {e}")
                return None

        try:
            with self.microphone as source:
                # Calibración a ruido ambiente
                self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
                # Asegurar un umbral mínimo razonable
                if self.recognizer.energy_threshold < 150:
                    self.recognizer.energy_threshold = 150
                audio = self.recognizer.listen(
                    source,
                    timeout=Configuracion.VOZ_TIMEOUT,
                    phrase_time_limit=8
                )
            text = self.recognizer.recognize_google(audio, language=Configuracion.VOZ_IDIOMA)
            return text.lower()
        except sr.WaitTimeoutError:
            log.error("Reconocimiento falló: tiempo de espera sin detectar voz")
            return None
        except sr.UnknownValueError:
            log.error("Reconocimiento falló: no se entendió el audio")
            return None
        except sr.RequestError as e:
            log.error(f"Reconocimiento falló (servicio): {e}")
            return None
        except Exception as e:
            log.error(f"Reconocimiento falló: {e}")
            return None

    def procesar(self, comando: str) -> Dict:
        c = comando.lower()
        if any(k in c for k in ['disponible', 'equipo', 'estado']):
            q = "SELECT nombre, tipo, estado, ubicacion FROM equipos ORDER BY nombre LIMIT 5"
            rs = self.db.ejecutar_consulta(q)
            if rs:
                lista = ", ".join([f"{n} ({t}) {e} en {u}" for n, t, e, u in rs])
                return {"accion": "equipos", "mensaje": f"Equipos: {lista}."}
            return {"accion": "equipos", "mensaje": "No hay equipos registrados."}
        if any(k in c for k in ['inventario', 'stock']):
            q = "SELECT nombre, cantidad_actual, unidad FROM inventario WHERE cantidad_actual>0 LIMIT 5"
            rs = self.db.ejecutar_consulta(q)
            if rs:
                lista = ", ".join([f"{n}: {cant} {un}" for n, cant, un in rs])
                return {"accion": "inventario", "mensaje": f"Inventario: {lista}."}
            return {"accion": "inventario", "mensaje": "Inventario vacío."}
        if 'ayuda' in c:
            return {"accion": "ayuda", "mensaje": "Diga: 'equipos disponibles', 'inventario', 'reservar equipo'."}
        return {"accion": "desconocido", "mensaje": "No entendí. Diga 'ayuda'."}


# ================================== VISIÓN ==================================
class ProcesadorImagenes:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.cascade_cara = cv2.CascadeClassifier(Configuracion.ROSTRO_CASCADE)

    def capturar_imagen(self) -> Optional[np.ndarray]:
        cap = cv2.VideoCapture(Configuracion.CAMERA_INDEX)
        if not cap.isOpened():
            print("❌ No se puede acceder a la cámara")
            return None
        print("📸 Presione ESPACIO para capturar, ESC para cancelar")
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            cv2.imshow('Captura', frame)
            k = cv2.waitKey(1) & 0xFF
            if k == 32:
                cap.release(); cv2.destroyAllWindows()
                return frame
            if k == 27:
                break
        cap.release(); cv2.destroyAllWindows()
        return None

    def identificar_usuario_placeholder(self, imagen: np.ndarray) -> Optional[str]:
        # Placeholder: devuelve el primer usuario con rostro_data
        q = "SELECT id FROM usuarios WHERE rostro_data IS NOT NULL LIMIT 1"
        rs = self.db.ejecutar_consulta(q)
        return rs[0][0] if rs else None


# ================================ CONTROLADOR ================================
class SistemaLaboratorio:
    def __init__(self):
        self.db = DatabaseManager()
        if not self.db.conectar():
            raise RuntimeError('No se pudo conectar a MySQL')
        self.voz = ReconocimientoVoz(self.db)
        self.vision = ProcesadorImagenes(self.db)
        self.usuario_actual: Optional[str] = None
        print("🚀 Sistema iniciado")

    def menu(self):
        while True:
            print("\n=== SISTEMA GIL - MENÚ ===")
            print("1) Identificación por rostro (placeholder)")
            print("2) Activar control por voz")
            print("3) Consultar equipos")
            print("4) Consultar inventario")
            print("9) Salir")
            op = input("Opción: ").strip()
            if op == '1':
                self.identificacion_rostro()
            elif op == '2':
                self.control_voz()
            elif op == '3':
                self.consultar_equipos()
            elif op == '4':
                self.consultar_inventario()
            elif op == '9':
                break
            else:
                print('Opción no válida')
        self.db.cerrar()
        print('👋 Fin')

    def identificacion_rostro(self):
        img = self.vision.capturar_imagen()
        if img is None:
            print('No se capturó imagen')
            return
        uid = self.vision.identificar_usuario_placeholder(img)
        if uid:
            self.usuario_actual = uid
            print(f"Usuario identificado: {uid}")
        else:
            print('No se pudo identificar usuario (placeholder)')

    def control_voz(self):
        print("🎤 Diga 'salir' para terminar")
        self.voz.hablar("Control por voz activado. Diga ayuda para opciones.")
        while True:
            cmd = self.voz.escuchar()
            if not cmd:
                print('Esperando...')
                continue
            if 'salir' in cmd:
                self.voz.hablar('Control por voz desactivado')
                break
            resp = self.voz.procesar(cmd)
            self.voz.hablar(resp.get('mensaje', ''))

    def consultar_equipos(self):
        q = "SELECT nombre, tipo, estado, ubicacion FROM equipos ORDER BY nombre LIMIT 10"
        rs = self.db.ejecutar_consulta(q)
        if not rs:
            print('No hay equipos para mostrar')
            return
        print("\nEQUIPO | TIPO | ESTADO | UBICACIÓN")
        for n, t, e, u in rs:
            print(f"- {n} | {t} | {e} | {u}")

    def consultar_inventario(self):
        q = "SELECT nombre, categoria, cantidad_actual, cantidad_minima, unidad FROM inventario ORDER BY nombre LIMIT 20"
        rs = self.db.ejecutar_consulta(q)
        if not rs:
            print('Inventario vacío')
            return
        print("\nITEM | CATEGORÍA | ACTUAL | MÍNIMO | UNIDAD")
        for n, c, a, m, u in rs:
            indicador = '🔴' if a <= m else ('🟡' if a <= int(m*1.5) else '🟢')
            print(f"{indicador} {n} | {c} | {a} | {m} | {u}")


def main():
    try:
        sistema = SistemaLaboratorio()
        sistema.menu()
    except KeyboardInterrupt:
        print('\nInterrumpido por el usuario')
    except Exception as e:
        print(f"Error fatal: {e}")


if __name__ == '__main__':
    main()
