# -*- coding: utf-8 -*-
"""
Prueba el micrófono usando un índice específico.
Uso:
    py -3.11 test_microfono_device.py 0
(reemplaza 0 por el índice listado en listar_microfonos.py)
"""
import sys
import time
import speech_recognition as sr

if len(sys.argv) < 2:
    print("Uso: py -3.11 test_microfono_device.py <device_index>")
    sys.exit(1)

try:
    device_index = int(sys.argv[1])
except ValueError:
    print("El índice debe ser numérico")
    sys.exit(1)

print(f"🎤 Probando micrófono índice {device_index} ...")

r = sr.Recognizer()
try:
    with sr.Microphone(device_index=device_index) as source:
        print("Ajustando ruido ambiente (1s)...")
        r.adjust_for_ambient_noise(source, duration=1)
        print("Hable algo (5s de espera)...")
        audio = r.listen(source, timeout=5)
    print("Intentando reconocer (Google)...")
    texto = r.recognize_google(audio, language='es-ES')
    print(f"✅ Reconocido: {texto}")
except sr.WaitTimeoutError:
    print("⏰ No se detectó audio en el tiempo esperado.")
except Exception as e:
    print(f"❌ Error usando el micrófono: {e}")
