# -*- coding: utf-8 -*-
"""
Ejecutar: py -3.11 test_dependencias.py
"""

def test_mysql():
    try:
        import mysql.connector
        print("✅ mysql-connector-python: INSTALADO")
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='1234',
                connect_timeout=5
            )
            conn.close()
            print("✅ MySQL: CONEXIÓN EXITOSA")
            return True
        except mysql.connector.Error as e:
            print(f"⚠️ MySQL: INSTALADO pero conexión falló: {e}")
            return True
    except ImportError:
        print("❌ mysql-connector-python: NO INSTALADO")
        return False

def test_opencv():
    try:
        import cv2
        print(f"✅ OpenCV: INSTALADO (versión {cv2.__version__})")
        import numpy as np
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _ = gray
        print("✅ OpenCV: FUNCIONALIDAD BÁSICA OK")
        return True
    except ImportError:
        print("❌ OpenCV: NO INSTALADO")
        return False
    except Exception as e:
        print(f"⚠️ OpenCV: INSTALADO pero error en funcionalidad: {e}")
        return False

def test_speech_recognition():
    try:
        import speech_recognition as sr
        print("✅ SpeechRecognition: INSTALADO")
        r = sr.Recognizer()
        _ = r
        print("✅ SpeechRecognition: INICIALIZACIÓN OK")
        return True
    except ImportError:
        print("❌ SpeechRecognition: NO INSTALADO")
        return False
    except Exception as e:
        print(f"⚠️ SpeechRecognition: INSTALADO pero error: {e}")
        return False

def test_pyttsx3():
    try:
        import pyttsx3
        print("✅ pyttsx3: INSTALADO")
        engine = pyttsx3.init()
        engine.stop()
        print("✅ pyttsx3: INICIALIZACIÓN OK")
        return True
    except ImportError:
        print("❌ pyttsx3: NO INSTALADO")
        return False
    except Exception as e:
        print(f"⚠️ pyttsx3: INSTALADO pero error: {e}")
        return True

def test_pillow():
    try:
        from PIL import Image
        import PIL
        print(f"✅ Pillow: INSTALADO (versión {PIL.__version__})")
        img = Image.new('RGB', (50, 50), color='red')
        _ = img
        print("✅ Pillow: FUNCIONALIDAD BÁSICA OK")
        return True
    except ImportError:
        print("❌ Pillow: NO INSTALADO")
        return False

def test_numpy():
    try:
        import numpy as np
        print(f"✅ NumPy: INSTALADO (versión {np.__version__})")
        arr = np.array([1,2,3])
        _ = arr.sum()
        print("✅ NumPy: FUNCIONALIDAD BÁSICA OK")
        return True
    except ImportError:
        print("❌ NumPy: NO INSTALADO")
        return False

def test_utilidades():
    try:
        from datetime import datetime
        import dateutil.parser
        import pytz
        _ = datetime.now(), pytz.UTC
        print("✅ Utilidades de fecha/hora: INSTALADAS")
        return True
    except ImportError as e:
        print(f"⚠️ Utilidades de fecha/hora: {e}")
        return False

def test_hardware():
    print("\n🔍 PROBANDO ACCESO A HARDWARE:")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✅ Cámara: ACCESIBLE")
            cap.release()
        else:
            print("⚠️ Cámara: NO ACCESIBLE (opcional)")
    except Exception as e:
        print(f"⚠️ Cámara: ERROR - {e}")
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
        print("✅ Micrófono: ACCESIBLE")
    except Exception as e:
        print(f"⚠️ Micrófono: ERROR - {e}")

def main():
    print("🧪 VERIFICACIÓN DE DEPENDENCIAS - SISTEMA LABORATORIO SENA")
    print("="*70)
    tests = [
        ("MySQL Connector", test_mysql),
        ("OpenCV", test_opencv),
        ("SpeechRecognition", test_speech_recognition),
        ("pyttsx3", test_pyttsx3),
        ("Pillow", test_pillow),
        ("NumPy", test_numpy),
        ("Utilidades", test_utilidades),
    ]
    resultados = []
    for nombre, fn in tests:
        print(f"\n🔍 Probando {nombre}:")
        resultados.append(fn())
    test_hardware()
    print("\n"+"="*70)
    ok = sum(resultados)
    total = len(resultados)
    if ok == total:
        print("🎉 ¡TODAS LAS DEPENDENCIAS INSTALADAS CORRECTAMENTE!")
    elif ok >= total - 1:
        print("✅ Dependencias principales OK (algunos opcionales fallaron)")
    else:
        print("❌ Faltan dependencias críticas")
    print(f"📈 Éxito: {ok}/{total}")
    print("="*70)

if __name__ == '__main__':
    main()
