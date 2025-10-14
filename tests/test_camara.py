# -*- coding: utf-8 -*-
import cv2

cap = cv2.VideoCapture(0)
if cap.isOpened():
    ok, frame = cap.read()
    if ok:
        print("✅ Cámara funcionando")
        print(f"   Resolución: {frame.shape[1]}x{frame.shape[0]}")
        cv2.imshow('Test Camara - ESC para cerrar', frame)
        while True:
            if cv2.waitKey(1) & 0xFF == 27:
                break
        cv2.destroyAllWindows()
    else:
        print("⚠️ Cámara detectada pero no captura")
else:
    print("❌ No se puede acceder a la cámara")
cap.release()
