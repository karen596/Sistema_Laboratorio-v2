#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generador de claves secretas para .env_produccion
"""

import secrets
import os

def generar_env_template():
    """Generar archivo .env_produccion con claves seguras"""
    
    print("🔐 GENERADOR DE CLAVES SECRETAS")
    print("=" * 60)
    
    # Generar claves
    flask_secret = secrets.token_hex(32)
    jwt_secret = secrets.token_hex(32)
    
    print("\n✅ Claves generadas exitosamente:\n")
    print(f"FLASK_SECRET_KEY={flask_secret}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    
    # Verificar si ya existe .env_produccion
    if os.path.exists('.env_produccion'):
        print("\n⚠️ El archivo .env_produccion ya existe.")
        respuesta = input("¿Deseas crear un nuevo archivo? (s/n): ")
        if respuesta.lower() != 's':
            print("❌ Operación cancelada")
            return
    
    # Solicitar datos de base de datos
    print("\n📊 Configuración de Base de Datos")
    print("-" * 60)
    
    host = input("Host de MySQL [localhost]: ").strip() or "localhost"
    usuario = input("Usuario de MySQL [laboratorio_prod]: ").strip() or "laboratorio_prod"
    password = input("Contraseña de MySQL: ").strip()
    database = input("Nombre de la base de datos [laboratorio_sistema]: ").strip() or "laboratorio_sistema"
    
    # Crear contenido del archivo
    contenido = f"""# ========================================
# CONFIGURACIÓN DE PRODUCCIÓN
# Sistema de Laboratorios - Centro Minero SENA
# ========================================

# Base de Datos MySQL
HOST={host}
USUARIO_PRODUCCION={usuario}
PASSWORD_PRODUCCION={password}
BASE_DATOS={database}

# Claves de Seguridad (Generadas automáticamente)
FLASK_SECRET_KEY={flask_secret}
JWT_SECRET_KEY={jwt_secret}

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

# ========================================
# IMPORTANTE:
# - NO subir este archivo a Git
# - Mantener las claves secretas seguras
# - Cambiar contraseñas por defecto
# ========================================
"""
    
    # Guardar archivo
    with open('.env_produccion', 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print("\n✅ Archivo .env_produccion creado exitosamente")
    print("\n⚠️ IMPORTANTE:")
    print("  1. Este archivo contiene información sensible")
    print("  2. NO lo subas a Git o repositorios públicos")
    print("  3. Mantén las claves secretas seguras")
    print("  4. Cambia las contraseñas por defecto en la base de datos")
    
    # Verificar .gitignore
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            contenido_gitignore = f.read()
        
        if '.env_produccion' not in contenido_gitignore:
            print("\n⚠️ Agregando .env_produccion a .gitignore...")
            with open('.gitignore', 'a') as f:
                f.write('\n# Archivos de configuración\n.env_produccion\n')
            print("✅ .gitignore actualizado")
    else:
        print("\n⚠️ Creando archivo .gitignore...")
        with open('.gitignore', 'w') as f:
            f.write('# Archivos de configuración\n.env_produccion\n')
        print("✅ .gitignore creado")
    
    print("\n" + "=" * 60)
    print("🚀 ¡Configuración completada!")
    print("\nPróximos pasos:")
    print("  1. Verificar que MySQL esté corriendo")
    print("  2. Crear la base de datos e importar datos_iniciales.sql")
    print("  3. Ejecutar: python verificar_proyecto.py")
    print("  4. Iniciar el servidor: python web_app.py")
    print("=" * 60)

if __name__ == '__main__':
    try:
        generar_env_template()
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
