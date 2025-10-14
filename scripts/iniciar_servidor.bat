@echo off
echo 🚀 INICIANDO SERVIDOR - CENTRO MINERO SENA
echo ==========================================

REM Verificar si existe el entorno virtual
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Entorno virtual no encontrado
    echo 💡 Ejecuta: python -m venv .venv
    echo 💡 Luego: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activar entorno virtual
call .venv\Scripts\activate.bat

echo ✅ Entorno virtual activado
echo 🔍 Verificando dependencias...

REM Verificar dependencias críticas
python -c "import flask, mysql.connector, cv2, numpy" 2>nul
if errorlevel 1 (
    echo ❌ Faltan dependencias
    echo 💡 Instalando dependencias...
    pip install -r requirements.txt
)

echo ✅ Dependencias verificadas
echo 🌐 Iniciando servidor web...
echo 💡 Accede a: http://localhost:5000
echo 💡 Para detener: Ctrl+C
echo.

REM Ejecutar servidor
python web_app.py

pause
