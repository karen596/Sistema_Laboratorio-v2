@echo off
echo 🚀 INSTALANDO DEPENDENCIAS DE RECONOCIMIENTO VISUAL
echo ===================================================

REM Activar entorno virtual
call .venv\Scripts\activate.bat

echo ✅ Entorno virtual activado
echo 📦 Instalando OpenCV y dependencias para reconocimiento visual...

REM Instalar dependencias específicas para reconocimiento visual
pip install opencv-python==4.8.1.78
pip install numpy==1.24.3

echo ✅ Instalación de OpenCV completada
echo 💡 El sistema de reconocimiento visual está listo
echo 🌐 Accede a: http://localhost:5000/entrenamiento-visual
echo.

pause
