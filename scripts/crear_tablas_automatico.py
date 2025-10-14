#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear automáticamente las tablas de objetos y visión
"""

import os
import sys
from dotenv import load_dotenv
import mysql.connector

# Cargar configuración
load_dotenv('.env_produccion')

def crear_tablas():
    """Crear tablas de objetos y objetos_imagenes"""
    
    print("=" * 70)
    print("🔧 CREANDO TABLAS DE SISTEMA DE VISIÓN")
    print("=" * 70)
    
    try:
        # Conectar a MySQL
        config = {
            'host': os.getenv('HOST', 'localhost'),
            'user': os.getenv('USUARIO_PRODUCCION', 'root'),
            'password': os.getenv('PASSWORD_PRODUCCION', ''),
            'database': os.getenv('BASE_DATOS', 'laboratorio_sistema')
        }
        
        print(f"\n📡 Conectando a MySQL...")
        print(f"   Host: {config['host']}")
        print(f"   Usuario: {config['user']}")
        print(f"   Base de datos: {config['database']}")
        
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        print("✅ Conexión establecida\n")
        
        # Crear tabla objetos
        print("📋 Creando tabla 'objetos'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS objetos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(200) NOT NULL,
                categoria VARCHAR(100) DEFAULT NULL,
                descripcion TEXT,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_objeto (nombre, categoria)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Tabla 'objetos' creada")
        
        # Crear tabla objetos_imagenes
        print("\n📋 Creando tabla 'objetos_imagenes'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS objetos_imagenes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                objeto_id INT NOT NULL,
                path VARCHAR(500) NOT NULL,
                thumbnail MEDIUMBLOB,
                notas TEXT,
                fuente VARCHAR(50) DEFAULT 'upload',
                vista VARCHAR(50) DEFAULT NULL COMMENT 'frontal, posterior, superior, inferior, lateral_derecha, lateral_izquierda',
                fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (objeto_id) REFERENCES objetos(id) ON DELETE CASCADE,
                INDEX idx_objeto (objeto_id),
                INDEX idx_vista (vista)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Tabla 'objetos_imagenes' creada")
        
        conn.commit()
        
        # Verificar tablas
        print("\n🔍 Verificando tablas creadas...")
        cursor.execute("SHOW TABLES LIKE 'objetos%'")
        tablas = cursor.fetchall()
        
        for tabla in tablas:
            print(f"   ✅ {tabla[0]}")
        
        # Mostrar estructura de objetos
        print("\n📊 Estructura de tabla 'objetos':")
        cursor.execute("DESCRIBE objetos")
        for row in cursor.fetchall():
            print(f"   - {row[0]}: {row[1]}")
        
        # Mostrar estructura de objetos_imagenes
        print("\n📊 Estructura de tabla 'objetos_imagenes':")
        cursor.execute("DESCRIBE objetos_imagenes")
        for row in cursor.fetchall():
            print(f"   - {row[0]}: {row[1]}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print("🎉 ¡TABLAS CREADAS EXITOSAMENTE!")
        print("=" * 70)
        print("\n✅ Ahora puedes usar el sistema de registro de objetos")
        print("✅ Accede a: http://localhost:5000/objetos/registrar")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"\n❌ Error de MySQL: {e}")
        print("\n💡 Verifica:")
        print("   - MySQL está corriendo")
        print("   - Credenciales en .env_produccion son correctas")
        print("   - La base de datos existe")
        return False
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        if crear_tablas():
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario")
        sys.exit(1)
