# =====================================================================
# SCRIPT DE INICIO RÁPIDO - SISTEMA LABORATORIO SENA
# =====================================================================
# Script para iniciar el servidor de forma rápida en producción

param(
    [string]$Modo = "waitress",  # waitress, development, gunicorn
    [int]$Puerto = 5000,
    [string]$HostAddress = "0.0.0.0",
    [int]$Workers = 4
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "SISTEMA LABORATORIO SENA - INICIO" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$PROYECTO_DIR = $PSScriptRoot
$VENV_DIR = "$PROYECTO_DIR\.venv"

# Verificar entorno virtual
if (-not (Test-Path $VENV_DIR)) {
    Write-Host "ERROR: Entorno virtual no encontrado" -ForegroundColor Red
    Write-Host "Ejecute primero: .\desplegar_produccion.ps1" -ForegroundColor Yellow
    exit 1
}

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
& "$VENV_DIR\Scripts\Activate.ps1"

# Verificar archivo .env_produccion
if (-not (Test-Path "$PROYECTO_DIR\.env_produccion")) {
    Write-Host "ADVERTENCIA: .env_produccion no encontrado" -ForegroundColor Yellow
    Write-Host "Usando configuración por defecto" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Configuración:" -ForegroundColor Cyan
Write-Host "  Modo:     $Modo" -ForegroundColor White
Write-Host "  Host:     $HostAddress" -ForegroundColor White
Write-Host "  Puerto:   $Puerto" -ForegroundColor White
Write-Host "  Workers:  $Workers" -ForegroundColor White
Write-Host ""

# Iniciar según el modo
switch ($Modo.ToLower()) {
    "waitress" {
        Write-Host "Iniciando con Waitress (Producción)..." -ForegroundColor Green
        Write-Host ""
        
        # Verificar si waitress está instalado
        $waitressInstalled = pip list | Select-String "waitress"
        if (-not $waitressInstalled) {
            Write-Host "Instalando Waitress..." -ForegroundColor Yellow
            pip install waitress
        }
        
        Write-Host "Servidor iniciado en: http://${HostAddress}:${Puerto}" -ForegroundColor Green
        Write-Host "Presione Ctrl+C para detener" -ForegroundColor Gray
        Write-Host ""
        
        waitress-serve --host=$HostAddress --port=$Puerto --threads=$Workers wsgi:application
    }
    
    "gunicorn" {
        Write-Host "Iniciando con Gunicorn (Linux/Unix)..." -ForegroundColor Green
        Write-Host ""
        
        # Verificar si gunicorn está instalado
        $gunicornInstalled = pip list | Select-String "gunicorn"
        if (-not $gunicornInstalled) {
            Write-Host "Instalando Gunicorn..." -ForegroundColor Yellow
            pip install gunicorn
        }
        
        Write-Host "Servidor iniciado en: http://${HostAddress}:${Puerto}" -ForegroundColor Green
        Write-Host "Presione Ctrl+C para detener" -ForegroundColor Gray
        Write-Host ""
        
        gunicorn -w $Workers -b "${HostAddress}:${Puerto}" wsgi:application
    }
    
    "development" {
        Write-Host "Iniciando en modo DESARROLLO..." -ForegroundColor Yellow
        Write-Host "ADVERTENCIA: No usar en producción" -ForegroundColor Red
        Write-Host ""
        
        Write-Host "Servidor iniciado en: http://localhost:${Puerto}" -ForegroundColor Green
        Write-Host "Presione Ctrl+C para detener" -ForegroundColor Gray
        Write-Host ""
        
        $env:FLASK_ENV = "development"
        $env:FLASK_DEBUG = "1"
        python web_app.py
    }
    
    default {
        Write-Host "ERROR: Modo desconocido: $Modo" -ForegroundColor Red
        Write-Host "Modos disponibles: waitress, gunicorn, development" -ForegroundColor Yellow
        exit 1
    }
}
