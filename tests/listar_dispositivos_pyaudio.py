# -*- coding: utf-8 -*-
"""
Lista dispositivos según PyAudio (los índices que usa SpeechRecognition internamente).
Ejecuta:
    py -3.11 listar_dispositivos_pyaudio.py
"""
import pyaudio

pa = pyaudio.PyAudio()
print("🔎 Dispositivos (PyAudio):")

try:
    default_host_api = pa.get_default_host_api_info()
    default_input_index = default_host_api.get('defaultInputDevice', -1)
except Exception:
    default_input_index = -1

for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    name = info.get('name', 'Unknown')
    max_in = info.get('maxInputChannels', 0)
    rate = int(info.get('defaultSampleRate', 0))
    mark = ' (DEFAULT INPUT)' if i == default_input_index else ''
    print(f"[{i}] IN={max_in} SR={rate} - {name}{mark}")

pa.terminate()
print("\nSugerencia: elige un índice con IN>0. Prueba ese índice en test_microfono_device.py <idx>.")
