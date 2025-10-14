#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de verificación del proyecto antes del despliegue
Verifica que todos los componentes estén correctamente configurados
"""

import os
import sys

def verificar_archivos():
    """Verificar que existan todos los archivos necesarios"""
    archivos_criticos = [
        'web_app.py',
        'requirements.txt',
        '.env_produccion',
        'templates/base.html',
        'templates/login.html',
        'templates/dashboard.html',
        'templates/laboratorios.html',
        'templates/equipos.html',
        'templates/inventario.html',
        'templates/reservas.html',
        'templates/usuarios.html',
        'templates/registro_facial.html',
        'templates/entrenamiento_visual.html',
    ]
    
    print("📁 Verificando archivos críticos...")
    faltantes = []
    for archivo in archivos_criticos:
        if os.path.exists(archivo):
            print(f"  ✅ {archivo}")
        else:
            print(f"  ❌ {archivo} - FALTANTE")
            faltantes.append(archivo)
    
    return len(faltantes) == 0, faltantes

def verificar_imports():
    """Verificar que se puedan importar los módulos necesarios"""
    print("\n📦 Verificando dependencias Python...")
    modulos = [
        ('flask', 'Flask'),
        ('flask_restful', 'Flask-RESTful'),
        ('flask_jwt_extended', 'Flask-JWT-Extended'),
        ('flask_cors', 'Flask-CORS'),
        ('mysql.connector', 'MySQL Connector'),
        ('cv2', 'OpenCV'),
        ('numpy', 'NumPy'),
        ('PIL', 'Pillow'),
    ]
    
    faltantes = []
    for modulo, nombre in modulos:
        try:
            __import__(modulo)
            print(f"  ✅ {nombre}")
        except ImportError:
            print(f"  ❌ {nombre} - NO INSTALADO")
            faltantes.append(nombre)
    
    return len(faltantes) == 0, faltantes

def verificar_env():
    """Verificar variables de entorno"""
    print("\n⚙️ Verificando configuración...")
    
    if not os.path.exists('.env_produccion'):
        print("  ❌ Archivo .env_produccion no encontrado")
        return False
    
    from dotenv import load_dotenv
    load_dotenv('.env_produccion')
    
    variables_necesarias = [
        'HOST',
        'USUARIO_PRODUCCION',
        'PASSWORD_PRODUCCION',
        'BASE_DATOS',
        'FLASK_SECRET_KEY',
        'JWT_SECRET_KEY'
    ]
    
    faltantes = []
    for var in variables_necesarias:
        valor = os.getenv(var)
        if valor:
            print(f"  ✅ {var} = {'*' * len(valor)}")
        else:
            print(f"  ❌ {var} - NO DEFINIDA")
            faltantes.append(var)
    
    return len(faltantes) == 0, faltantes

def verificar_base_datos():
    """Verificar conexión a base de datos"""
    print("\n🗄️ Verificando conexión a base de datos...")
    
    try:
        from dotenv import load_dotenv
        import mysql.connector
        
        load_dotenv('.env_produccion')
        
        config = {
            'host': os.getenv('HOST', 'localhost'),
            'user': os.getenv('USUARIO_PRODUCCION', 'root'),
            'password': os.getenv('PASSWORD_PRODUCCION', ''),
            'database': os.getenv('BASE_DATOS', 'laboratorio_sistema'),
        }
        
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SHOW TABLES")
        tablas = [t[0] for t in cursor.fetchall()]
        
        tablas_necesarias = [
            'usuarios',
            'laboratorios',
            'equipos',
            'inventario',
            'reservas'
        ]
        
        print(f"  ✅ Conexión exitosa a {config['database']}")
        print(f"  📊 Tablas encontradas: {len(tablas)}")
        
        faltantes = []
        for tabla in tablas_necesarias:
            if tabla in tablas:
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                count = cursor.fetchone()[0]
                print(f"    ✅ {tabla} ({count} registros)")
            else:
                print(f"    ❌ {tabla} - NO EXISTE")
                faltantes.append(tabla)
        
        cursor.close()
        conn.close()
        
        return len(faltantes) == 0, faltantes
        
    except Exception as e:
        print(f"  ❌ Error de conexión: {e}")
        return False, [str(e)]

def main():
    """Ejecutar todas las verificaciones"""
    print("=" * 70)
    print("🔍 VERIFICACIÓN DEL PROYECTO - CENTRO MINERO SENA")
    print("=" * 70)
    
    resultados = []
    
    # 1. Archivos
    ok, faltantes = verificar_archivos()
    resultados.append(('Archivos', ok, faltantes))
    
    # 2. Dependencias
    ok, faltantes = verificar_imports()
    resultados.append(('Dependencias', ok, faltantes))
    
    # 3. Configuración
    ok, faltantes = verificar_env()
    resultados.append(('Configuración', ok, faltantes))
    
    # 4. Base de datos
    ok, faltantes = verificar_base_datos()
    resultados.append(('Base de Datos', ok, faltantes))
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 70)
    
    todo_ok = True
    for nombre, ok, faltantes in resultados:
        if ok:
            print(f"✅ {nombre}: OK")
        else:
            print(f"❌ {nombre}: FALTAN {len(faltantes)} elementos")
            for item in faltantes:
                print(f"   - {item}")
            todo_ok = False
    
    print("=" * 70)
    
    if todo_ok:
        print("✅ ¡PROYECTO LISTO PARA DESPLEGAR!")
        print("\nPara iniciar el servidor:")
        print("  python web_app.py")
        return 0
    else:
        print("❌ HAY PROBLEMAS QUE CORREGIR ANTES DE DESPLEGAR")
        print("\nRevisa los elementos marcados con ❌ arriba")
        return 1

if __name__ == '__main__':
    sys.exit(main())
