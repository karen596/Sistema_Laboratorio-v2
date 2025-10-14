# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que el sistema de backups funcione correctamente
después de las correcciones aplicadas.
"""
import os
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('.env_produccion')

def test_backup_creation():
    """Prueba la creación de un backup usando la misma lógica que web_app.py"""
    print("=" * 70)
    print("PRUEBA DE CREACIÓN DE BACKUP (POST-FIX)")
    print("=" * 70)
    
    # Configuración
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f'backup_test_fix_{timestamp}.sql'
    
    # Obtener configuración
    mysqldump_path = os.getenv('MYSQLDUMP_PATH', 'mysqldump')
    host = os.getenv('HOST', 'localhost')
    user = os.getenv('USUARIO_PRODUCCION', 'laboratorio_prod')
    password = os.getenv('PASSWORD_PRODUCCION', '')
    database = os.getenv('BASE_DATOS', 'laboratorio_sistema')
    
    print(f"\n📋 CONFIGURACIÓN:")
    print(f"  - mysqldump: {mysqldump_path}")
    print(f"  - Host: {host}")
    print(f"  - Usuario: {user}")
    print(f"  - Base de datos: {database}")
    print(f"  - Archivo destino: {backup_file}")
    
    # Construir comando
    cmd = [
        mysqldump_path,
        '-h', host,
        '-u', user,
        f'-p{password}',
        '--single-transaction',
        '--routines',
        '--triggers',
        database
    ]
    
    print(f"\n🔧 COMANDO A EJECUTAR:")
    # Ocultar password en el output
    cmd_display = cmd.copy()
    cmd_display[4] = '-p' + '*' * 20
    print(f"  {' '.join(cmd_display)}")
    
    # Ejecutar backup
    print(f"\n⏳ Ejecutando backup...")
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True)
        
        # Verificar resultado
        file_size = backup_file.stat().st_size
        file_size_mb = file_size / 1024 / 1024
        
        print(f"\n✅ BACKUP CREADO EXITOSAMENTE")
        print(f"  - Archivo: {backup_file.name}")
        print(f"  - Tamaño: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        print(f"  - Ubicación: {backup_file.absolute()}")
        
        if file_size == 0:
            print(f"\n⚠️  ADVERTENCIA: El archivo está vacío (0 bytes)")
            return False
        elif file_size < 1024:
            print(f"\n⚠️  ADVERTENCIA: El archivo es muy pequeño ({file_size} bytes)")
            return False
        else:
            print(f"\n✅ El tamaño del archivo es correcto")
            
            # Leer primeras líneas para verificar contenido
            with open(backup_file, 'r', encoding='utf-8') as f:
                first_lines = [f.readline() for _ in range(5)]
            
            print(f"\n📄 PRIMERAS LÍNEAS DEL BACKUP:")
            for i, line in enumerate(first_lines, 1):
                print(f"  {i}: {line.strip()[:80]}")
            
            return True
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR AL CREAR BACKUP:")
        print(f"  Código de error: {e.returncode}")
        if e.stderr:
            print(f"  Mensaje: {e.stderr.decode('utf-8', errors='ignore')}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO:")
        print(f"  {type(e).__name__}: {str(e)}")
        return False

def list_existing_backups():
    """Lista todos los backups existentes"""
    print("\n" + "=" * 70)
    print("BACKUPS EXISTENTES")
    print("=" * 70)
    
    backup_dir = Path('backups')
    if not backup_dir.exists():
        print("❌ Directorio de backups no existe")
        return
    
    backups = sorted(backup_dir.glob('*.sql'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not backups:
        print("📭 No hay backups disponibles")
        return
    
    print(f"\n📦 Total de backups: {len(backups)}\n")
    
    for i, backup in enumerate(backups, 1):
        size = backup.stat().st_size
        size_mb = size / 1024 / 1024
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        
        status = "✅" if size > 0 else "⚠️ "
        print(f"{status} {i}. {backup.name}")
        print(f"     Tamaño: {size_mb:.2f} MB ({size:,} bytes)")
        print(f"     Fecha: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

if __name__ == "__main__":
    list_existing_backups()
    success = test_backup_creation()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
        print("\nEl sistema de backups está funcionando correctamente.")
        print("Ahora puedes crear backups desde la aplicación web sin problemas.")
    else:
        print("❌ PRUEBA FALLIDA")
        print("\nRevisar los errores anteriores para diagnosticar el problema.")
    print("=" * 70)
