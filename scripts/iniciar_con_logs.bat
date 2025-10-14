@echo off
echo Iniciando servidor con logs...
python web_app.py 2>&1 | tee server_output.log
pause
