# -*- coding: utf-8 -*-
"""
Script de Diagnóstico del Sistema de Backups
Verifica la configuración y disponibilidad de herramientas necesarias
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
if os.path.exists('.env_produccion'):
    load_dotenv('.env_produccion')

print("=" * 70)
print("DIAGNÓSTICO DEL SISTEMA DE BACKUPS")
print("=" * 70)

# 1. Verificar directorio de backups
print("\n[1] VERIFICANDO DIRECTORIO DE BACKUPS")
print("-" * 70)
backup_dir = Path('backups')
if backup_dir.exists():
    print(f"✓ Directorio existe: {backup_dir.absolute()}")
    backups = list(backup_dir.glob('*.sql'))
    print(f"✓ Backups encontrados: {len(backups)}")
    for backup in backups[:5]:  # Mostrar primeros 5
        size_mb = backup.stat().st_size / 1024 / 1024
        print(f"  - {backup.name} ({size_mb:.2f} MB)")
else:
    print(f"✗ Directorio no existe: {backup_dir.absolute()}")
    print("  Creando directorio...")
    backup_dir.mkdir(exist_ok=True)
    print(f"✓ Directorio creado: {backup_dir.absolute()}")

# 2. Verificar variables de entorno
print("\n[2] VERIFICANDO VARIABLES DE ENTORNO")
print("-" * 70)
env_vars = {
    'HOST': os.getenv('HOST', 'localhost'),
    'USUARIO_PRODUCCION': os.getenv('USUARIO_PRODUCCION', ''),
    'PASSWORD_PRODUCCION': os.getenv('PASSWORD_PRODUCCION', ''),
    'BASE_DATOS': os.getenv('BASE_DATOS', '')
}

for key, value in env_vars.items():
    if value:
        if 'PASSWORD' in key:
            print(f"✓ {key}: {'*' * len(value)}")
        else:
            print(f"✓ {key}: {value}")
    else:
        print(f"✗ {key}: NO CONFIGURADO")

# 3. Buscar MySQL en el sistema
print("\n[3] BUSCANDO INSTALACIÓN DE MySQL/MariaDB")
print("-" * 70)

# Rutas comunes de MySQL en Windows
common_paths = [
    r"C:\Program Files\MySQL\MySQL Server 8.0\bin",
    r"C:\Program Files\MySQL\MySQL Server 5.7\bin",
    r"C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin",
    r"C:\Program Files (x86)\MySQL\MySQL Server 5.7\bin",
    r"C:\xampp\mysql\bin",
    r"C:\wamp64\bin\mysql\mysql8.0.31\bin",
    r"C:\wamp\bin\mysql\mysql8.0.31\bin",
    r"C:\laragon\bin\mysql\mysql-8.0.30-winx64\bin",
]

mysql_path = None
mysqldump_path = None

# Buscar en PATH del sistema
print("Buscando en PATH del sistema...")
try:
    result = subprocess.run(['where', 'mysql'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        mysql_path = result.stdout.strip().split('\n')[0]
        print(f"✓ mysql encontrado en PATH: {mysql_path}")
except Exception as e:
    print(f"✗ mysql no encontrado en PATH: {e}")

try:
    result = subprocess.run(['where', 'mysqldump'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        mysqldump_path = result.stdout.strip().split('\n')[0]
        print(f"✓ mysqldump encontrado en PATH: {mysqldump_path}")
except Exception as e:
    print(f"✗ mysqldump no encontrado en PATH: {e}")

# Buscar en rutas comunes
if not mysql_path or not mysqldump_path:
    print("\nBuscando en rutas comunes de instalación...")
    for path in common_paths:
        mysql_exe = Path(path) / "mysql.exe"
        mysqldump_exe = Path(path) / "mysqldump.exe"
        
        if mysql_exe.exists() and not mysql_path:
            mysql_path = str(mysql_exe)
            print(f"✓ mysql encontrado: {mysql_path}")
        
        if mysqldump_exe.exists() and not mysqldump_path:
            mysqldump_path = str(mysqldump_exe)
            print(f"✓ mysqldump encontrado: {mysqldump_path}")
        
        if mysql_path and mysqldump_path:
            break

if not mysql_path:
    print("✗ mysql.exe NO ENCONTRADO en el sistema")
if not mysqldump_path:
    print("✗ mysqldump.exe NO ENCONTRADO en el sistema")

# 4. Probar conexión a la base de datos
print("\n[4] PROBANDO CONEXIÓN A LA BASE DE DATOS")
print("-" * 70)

if mysql_path and env_vars['USUARIO_PRODUCCION'] and env_vars['BASE_DATOS']:
    try:
        cmd = [
            mysql_path,
            '-h', env_vars['HOST'],
            '-u', env_vars['USUARIO_PRODUCCION'],
            f"-p{env_vars['PASSWORD_PRODUCCION']}",
            '-e', 'SELECT VERSION();',
            env_vars['BASE_DATOS']
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"✓ Conexión exitosa a la base de datos")
            print(f"  Versión MySQL: {result.stdout.strip()}")
        else:
            print(f"✗ Error de conexión:")
            print(f"  {result.stderr}")
    except Exception as e:
        print(f"✗ Error probando conexión: {e}")
else:
    print("✗ No se puede probar conexión (faltan datos de configuración o mysql.exe)")

# 5. Probar creación de backup de prueba
print("\n[5] PROBANDO CREACIÓN DE BACKUP DE PRUEBA")
print("-" * 70)

if mysqldump_path and env_vars['USUARIO_PRODUCCION'] and env_vars['BASE_DATOS']:
    try:
        test_backup = backup_dir / 'test_backup.sql'
        
        cmd = [
            mysqldump_path,
            '-h', env_vars['HOST'],
            '-u', env_vars['USUARIO_PRODUCCION'],
            f"-p{env_vars['PASSWORD_PRODUCCION']}",
            '--single-transaction',
            '--routines',
            '--triggers',
            env_vars['BASE_DATOS']
        ]
        
        print(f"Ejecutando comando: {' '.join([c if 'PASSWORD' not in c else '-p***' for c in cmd])}")
        
        with open(test_backup, 'w', encoding='utf-8') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )
        
        if result.returncode == 0:
            size_mb = test_backup.stat().st_size / 1024 / 1024
            print(f"✓ Backup de prueba creado exitosamente")
            print(f"  Archivo: {test_backup.name}")
            print(f"  Tamaño: {size_mb:.2f} MB")
            print(f"  Ubicación: {test_backup.absolute()}")
            
            # Eliminar backup de prueba
            test_backup.unlink()
            print(f"✓ Backup de prueba eliminado")
        else:
            print(f"✗ Error creando backup:")
            print(f"  {result.stderr}")
            if test_backup.exists():
                test_backup.unlink()
    except Exception as e:
        print(f"✗ Error en prueba de backup: {e}")
        import traceback
        traceback.print_exc()
else:
    print("✗ No se puede probar backup (faltan datos de configuración o mysqldump.exe)")

# 6. Resumen y recomendaciones
print("\n" + "=" * 70)
print("RESUMEN Y RECOMENDACIONES")
print("=" * 70)

issues = []
recommendations = []

if not mysql_path:
    issues.append("mysql.exe no encontrado")
    recommendations.append("Instalar MySQL o agregar la ruta de MySQL al PATH del sistema")

if not mysqldump_path:
    issues.append("mysqldump.exe no encontrado")
    recommendations.append("Verificar que mysqldump.exe esté en la carpeta bin de MySQL")

if not env_vars['USUARIO_PRODUCCION']:
    issues.append("USUARIO_PRODUCCION no configurado")
    recommendations.append("Configurar USUARIO_PRODUCCION en .env_produccion")

if not env_vars['PASSWORD_PRODUCCION']:
    issues.append("PASSWORD_PRODUCCION no configurado")
    recommendations.append("Configurar PASSWORD_PRODUCCION en .env_produccion")

if not env_vars['BASE_DATOS']:
    issues.append("BASE_DATOS no configurado")
    recommendations.append("Configurar BASE_DATOS en .env_produccion")

if issues:
    print("\n⚠️  PROBLEMAS DETECTADOS:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    
    print("\n💡 RECOMENDACIONES:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
else:
    print("\n✓ SISTEMA DE BACKUPS CONFIGURADO CORRECTAMENTE")
    print("  Todas las verificaciones pasaron exitosamente")

# Guardar rutas encontradas
if mysql_path or mysqldump_path:
    print("\n📝 RUTAS ENCONTRADAS (para configuración):")
    if mysql_path:
        print(f"  MYSQL_PATH={mysql_path}")
    if mysqldump_path:
        print(f"  MYSQLDUMP_PATH={mysqldump_path}")

print("\n" + "=" * 70)
print("FIN DEL DIAGNÓSTICO")
print("=" * 70)
