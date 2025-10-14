@echo off
echo 🚀 ACTIVANDO ENTORNO VIRTUAL - CENTRO MINERO SENA
echo ================================================

REM Activar entorno virtual
call .venv\Scripts\activate.bat

echo ✅ Entorno virtual activado
echo 💡 Para ejecutar el servidor: python web_app.py
echo 💡 Para salir del entorno: deactivate
echo.

REM Mantener la ventana abierta
cmd /k
