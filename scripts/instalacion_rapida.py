#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Instalación Rápida - Sistema de Laboratorios SENA
Configura todo automáticamente para despliegue inmediato
"""

import os
import sys
import secrets
import subprocess

def crear_env_produccion():
    """Crear archivo .env_produccion con valores por defecto"""
    print("🔐 Generando archivo de configuración...")
    
    # Generar claves seguras
    flask_key = secrets.token_hex(32)
    jwt_key = secrets.token_hex(32)
    
    contenido = f"""# ========================================
# CONFIGURACIÓN DE PRODUCCIÓN
# Sistema de Laboratorios - Centro Minero SENA
# Generado automáticamente
# ========================================

# Base de Datos MySQL
HOST=localhost
USUARIO_PRODUCCION=root
PASSWORD_PRODUCCION=
BASE_DATOS=laboratorio_sistema

# Claves de Seguridad (Generadas automáticamente)
FLASK_SECRET_KEY={flask_key}
JWT_SECRET_KEY={jwt_key}

# Configuración de Flask
FLASK_ENV=production
DEBUG=False

# Configuración de Sesión
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Configuración de JWT
JWT_TOKEN_LOCATION=headers
JWT_ACCESS_TOKEN_EXPIRES=28800
"""
    
    with open('.env_produccion', 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print("✅ Archivo .env_produccion creado")
    print("\n⚠️ IMPORTANTE: Edita .env_produccion y configura:")
    print("   - PASSWORD_PRODUCCION (contraseña de MySQL)")
    print("   - USUARIO_PRODUCCION (si no es 'root')")

def crear_directorios():
    """Crear directorios necesarios"""
    print("\n📁 Creando directorios...")
    
    directorios = [
        'models',
        'static/css',
        'static/js',
        'static/img',
        'logs',
        'backups'
    ]
    
    for directorio in directorios:
        os.makedirs(directorio, exist_ok=True)
        print(f"  ✅ {directorio}")

def verificar_mysql():
    """Verificar que MySQL esté instalado"""
    print("\n🗄️ Verificando MySQL...")
    
    try:
        import mysql.connector
        print("  ✅ MySQL Connector instalado")
        return True
    except ImportError:
        print("  ❌ MySQL Connector NO instalado")
        print("  💡 Se instalará con requirements.txt")
        return False

def instalar_dependencias():
    """Instalar dependencias de Python"""
    print("\n📦 Instalando dependencias...")
    print("⏳ Esto puede tomar varios minutos...")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        print("\n💡 Intenta manualmente:")
        print("   pip install -r requirements.txt")
        return False

def verificar_base_datos():
    """Verificar conexión a base de datos"""
    print("\n🗄️ Verificando base de datos...")
    
    try:
        from dotenv import load_dotenv
        import mysql.connector
        
        load_dotenv('.env_produccion')
        
        config = {
            'host': os.getenv('HOST', 'localhost'),
            'user': os.getenv('USUARIO_PRODUCCION', 'root'),
            'password': os.getenv('PASSWORD_PRODUCCION', ''),
        }
        
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Verificar si existe la base de datos
        cursor.execute("SHOW DATABASES LIKE 'laboratorio_sistema'")
        existe = cursor.fetchone()
        
        if existe:
            print("  ✅ Base de datos 'laboratorio_sistema' encontrada")
        else:
            print("  ⚠️ Base de datos 'laboratorio_sistema' NO encontrada")
            print("\n  💡 Debes crear la base de datos:")
            print("     1. Abre MySQL Workbench")
            print("     2. Ejecuta: CREATE DATABASE laboratorio_sistema;")
            print("     3. Importa: datos_iniciales.sql")
        
        cursor.close()
        conn.close()
        return existe is not None
        
    except Exception as e:
        print(f"  ❌ Error de conexión: {e}")
        print("\n  💡 Verifica:")
        print("     - MySQL está corriendo")
        print("     - Credenciales en .env_produccion son correctas")
        return False

def main():
    """Ejecutar instalación completa"""
    print("=" * 70)
    print("🚀 INSTALACIÓN RÁPIDA - SISTEMA DE LABORATORIOS SENA")
    print("=" * 70)
    
    # 1. Crear archivo de configuración
    if not os.path.exists('.env_produccion'):
        crear_env_produccion()
    else:
        print("✅ Archivo .env_produccion ya existe")
    
    # 2. Crear directorios
    crear_directorios()
    
    # 3. Verificar MySQL
    verificar_mysql()
    
    # 4. Preguntar si instalar dependencias
    print("\n" + "=" * 70)
    respuesta = input("¿Deseas instalar las dependencias ahora? (s/n): ")
    
    if respuesta.lower() == 's':
        if instalar_dependencias():
            print("\n✅ Instalación de dependencias completada")
        else:
            print("\n⚠️ Instala las dependencias manualmente antes de continuar")
    else:
        print("\n⚠️ Recuerda instalar las dependencias:")
        print("   pip install -r requirements.txt")
    
    # 5. Verificar base de datos
    print("\n" + "=" * 70)
    verificar_base_datos()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE INSTALACIÓN")
    print("=" * 70)
    print("\n✅ Configuración creada")
    print("✅ Directorios creados")
    
    print("\n📋 PRÓXIMOS PASOS:")
    print("=" * 70)
    print("\n1. Editar .env_produccion:")
    print("   - Configurar PASSWORD_PRODUCCION")
    print("   - Verificar USUARIO_PRODUCCION")
    
    print("\n2. Configurar MySQL:")
    print("   - Crear base de datos: CREATE DATABASE laboratorio_sistema;")
    print("   - Importar datos: SOURCE datos_iniciales.sql;")
    
    print("\n3. Verificar instalación:")
    print("   python verificar_proyecto.py")
    
    print("\n4. Iniciar servidor:")
    print("   python web_app.py")
    print("   O ejecutar: iniciar_servidor.bat")
    
    print("\n" + "=" * 70)
    print("🎯 ¡Instalación completada!")
    print("=" * 70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Instalación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante la instalación: {e}")
        import traceback
        traceback.print_exc()
