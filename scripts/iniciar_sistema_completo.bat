@echo off
echo 🚀 INICIANDO SISTEMA COMPLETO - CENTRO MINERO SENA
echo ===================================================

REM Activar entorno virtual
call .venv\Scripts\activate.bat

echo ✅ Entorno virtual activado
echo 🧪 Probando sistema de reconocimiento visual...

REM Probar dependencias
python test_sistema_visual.py

echo.
echo 🌐 Iniciando servidor web completo...
echo 💡 Funcionalidades disponibles:
echo    - Dashboard: http://localhost:5000/dashboard
echo    - Equipos: http://localhost:5000/equipos
echo    - Inventario: http://localhost:5000/inventario
echo    - Registro Facial: http://localhost:5000/registro-facial
echo    - IA Visual: http://localhost:5000/entrenamiento-visual
echo.
echo 🛑 Para detener: Ctrl+C
echo.

REM Ejecutar servidor
python web_app.py

pause
