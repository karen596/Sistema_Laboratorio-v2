#!/usr/bin/env python3
"""
Script para recrear la tabla equipos en la base de datos
"""

import mysql.connector
from mysql.connector import Error

def recrear_tabla_equipos():
    """Crea la tabla equipos si no existe"""
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1234',
            database='laboratorio_sistema'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            print("Conectado a la base de datos laboratorio_sistema")
            
            # SQL para crear la tabla equipos
            create_table_query = """
            CREATE TABLE IF NOT EXISTS equipos (
                id VARCHAR(50) PRIMARY KEY,
                equipo_id VARCHAR(50) UNIQUE,
                nombre VARCHAR(100) NOT NULL,
                tipo VARCHAR(50) NOT NULL,
                estado ENUM('disponible','en_uso','mantenimiento','fuera_servicio') DEFAULT 'disponible',
                ubicacion VARCHAR(100),
                laboratorio_id INT DEFAULT 1,
                marca VARCHAR(100),
                modelo VARCHAR(100),
                numero_serie VARCHAR(100),
                fecha_adquisicion DATE,
                ultima_calibracion DATE,
                proximo_mantenimiento DATE,
                observaciones TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_estado (estado),
                INDEX idx_tipo (tipo),
                INDEX idx_laboratorio_id (laboratorio_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_table_query)
            print("✓ Tabla 'equipos' creada o verificada exitosamente")
            
            # Verificar la estructura de la tabla
            cursor.execute("DESCRIBE equipos")
            columns = cursor.fetchall()
            
            print("\n=== Estructura de la tabla equipos ===")
            for column in columns:
                print(f"  - {column[0]}: {column[1]}")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM equipos")
            count = cursor.fetchone()[0]
            print(f"\n✓ Total de registros en equipos: {count}")
            
            connection.commit()
            print("\n✓ Operación completada exitosamente")
            
    except Error as e:
        print(f"✗ Error al conectar a MySQL: {e}")
        print("\nSi el error es de autenticación, edita el script y configura:")
        print("  - user: tu usuario de MySQL")
        print("  - password: tu contraseña de MySQL")
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n✓ Conexión cerrada")

if __name__ == "__main__":
    print("=== RECREAR TABLA EQUIPOS ===\n")
    recrear_tabla_equipos()
