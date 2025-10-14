# -*- coding: utf-8 -*-
import speech_recognition as sr

print("🔎 Listando micrófonos disponibles (índice: nombre):")
try:
    nombres = sr.Microphone.list_microphone_names()
    if not nombres:
        print("❌ No se detectan dispositivos de entrada de audio")
    else:
        for i, name in enumerate(nombres):
            print(f"[{i}] {name}")
        print("\nUsa el índice en otros scripts con sr.Microphone(device_index=IDX)")
except Exception as e:
    print(f"❌ Error listando micrófonos: {e}")
