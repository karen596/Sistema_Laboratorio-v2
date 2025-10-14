# -*- coding: utf-8 -*-
import pyttsx3

try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    if voices:
        print(f"✅ Voces disponibles: {len(voices)}")
        for i, v in enumerate(voices[:5]):
            print(f"  {i}: {v.name}")
        for v in voices:
            if 'spanish' in v.name.lower() or 'es' in getattr(v, 'id', '').lower():
                engine.setProperty('voice', v.id)
                break
    engine.say("Sistema de laboratorio funcionando correctamente")
    engine.runAndWait()
    print("✅ Síntesis de voz OK")
except Exception as e:
    print(f"❌ Error en síntesis de voz: {e}")
