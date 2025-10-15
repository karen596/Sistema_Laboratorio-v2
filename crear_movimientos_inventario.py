#!/usr/bin/env python3
"""
Script para crear la tabla movimientos_inventario sin FK problemáticas
"""

import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'laboratorio_sistema'
}

def main():
    print("\n" + "=" * 80)
    print("  CREACIÓN DE TABLA: movimientos_inventario")
    print("=" * 80)
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        
        if connection.is_connected():
            print(f"\n✓ Conectado a la base de datos: {DB_CONFIG['database']}")
            
            cursor = connection.cursor()
            
            # Crear tabla sin FK a usuarios (solo con FK a inventario)
            create_query = """
            CREATE TABLE IF NOT EXISTS movimientos_inventario (
                id INT AUTO_INCREMENT PRIMARY KEY,
                inventario_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                tipo_movimiento ENUM('entrada','salida','ajuste','transferencia') NOT NULL,
                cantidad INT NOT NULL,
                fecha_movimiento DATETIME DEFAULT CURRENT_TIMESTAMP,
                usuario_id VARCHAR(50),
                observaciones TEXT,
                destino VARCHAR(100),
                documento_referencia VARCHAR(100),
                
                INDEX idx_inventario_id (inventario_id),
                INDEX idx_tipo_movimiento (tipo_movimiento),
                INDEX idx_fecha (fecha_movimiento),
                INDEX idx_usuario_id (usuario_id),
                
                FOREIGN KEY (inventario_id) REFERENCES inventario(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_query)
            connection.commit()
            print("✓ Tabla 'movimientos_inventario' creada exitosamente")
            
            # Verificar
            cursor.execute("SELECT COUNT(*) FROM movimientos_inventario")
            count = cursor.fetchone()[0]
            print(f"✓ Registros en movimientos_inventario: {count}")
            
            cursor.close()
            
            print("\n" + "=" * 80)
            print("  ✓ COMPLETADO")
            print("=" * 80 + "\n")
            
    except Error as e:
        if "already exists" in str(e):
            print("\n✓ La tabla 'movimientos_inventario' ya existe")
        else:
            print(f"\n✗ Error: {e}")
        
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("✓ Conexión cerrada\n")

if __name__ == "__main__":
    main()
