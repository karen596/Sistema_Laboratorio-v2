# -*- coding: utf-8 -*-
"""
Lista dispositivos de audio usando sounddevice (no requiere PyAudio).
Uso:
    py -3.11 listar_microfonos_sd.py
"""
import sounddevice as sd

try:
    devices = sd.query_devices()
    if not devices:
        print("❌ No se detectan dispositivos de audio")
    else:
        print("🔎 Dispositivos de audio (índice: tipo - nombre):")
        for i, dev in enumerate(devices):
            io = []
            if dev.get('max_input_channels', 0) > 0:
                io.append('IN')
            if dev.get('max_output_channels', 0) > 0:
                io.append('OUT')
            print(f"[{i}] {'/'.join(io) or 'N/A'} - {dev.get('name', 'Unknown')}")
        print("\nUsa un índice que tenga 'IN' para micrófono.")
except Exception as e:
    print(f"❌ Error listando con sounddevice: {e}")
