#!/usr/bin/env python3
"""
Script para corregir problemas de collation y recrear foreign keys
"""

import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'laboratorio_sistema'
}

def print_header(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def corregir_collation_columnas(connection):
    """Corrige el collation de las columnas para que sean compatibles"""
    print_header("CORRECCIÓN DE COLLATION")
    
    cursor = connection.cursor()
    correcciones = 0
    
    # Usar utf8mb4_unicode_ci para todas las columnas VARCHAR relacionadas
    alteraciones = [
        ("equipos", "id", "ALTER TABLE equipos MODIFY COLUMN id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"),
        ("historial_uso", "equipo_id", "ALTER TABLE historial_uso MODIFY COLUMN equipo_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"),
        ("mantenimientos", "equipo_id", "ALTER TABLE mantenimientos MODIFY COLUMN equipo_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"),
        ("reservas", "equipo_id", "ALTER TABLE reservas MODIFY COLUMN equipo_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"),
        ("inventario", "id", "ALTER TABLE inventario MODIFY COLUMN id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"),
        ("usuarios", "id", "ALTER TABLE usuarios MODIFY COLUMN id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL"),
    ]
    
    for tabla, columna, query in alteraciones:
        try:
            cursor.execute(query)
            connection.commit()
            print(f"  ✓ {tabla}.{columna} → utf8mb4_unicode_ci")
            correcciones += 1
        except Error as e:
            print(f"  ⚠ Error al modificar {tabla}.{columna}: {e}")
    
    cursor.close()
    print(f"\n✓ {correcciones} collation(s) corregido(s)")
    return correcciones > 0

def limpiar_datos_huerfanos(connection):
    """Limpia datos que no tienen referencias válidas"""
    print_header("LIMPIEZA DE DATOS HUÉRFANOS")
    
    cursor = connection.cursor()
    
    # Limpiar con COLLATE explícito
    try:
        cursor.execute("""
            DELETE FROM historial_uso 
            WHERE equipo_id NOT IN (
                SELECT id COLLATE utf8mb4_unicode_ci FROM equipos
            )
            AND equipo_id IS NOT NULL
        """)
        deleted = cursor.rowcount
        connection.commit()
        if deleted > 0:
            print(f"  ✓ {deleted} registro(s) huérfano(s) eliminado(s) de historial_uso")
        else:
            print(f"  - No hay registros huérfanos en historial_uso")
    except Error as e:
        print(f"  ⚠ Error limpiando historial_uso: {e}")
    
    try:
        cursor.execute("""
            DELETE FROM mantenimientos 
            WHERE equipo_id NOT IN (
                SELECT id COLLATE utf8mb4_unicode_ci FROM equipos
            )
            AND equipo_id IS NOT NULL
        """)
        deleted = cursor.rowcount
        connection.commit()
        if deleted > 0:
            print(f"  ✓ {deleted} registro(s) huérfano(s) eliminado(s) de mantenimientos")
        else:
            print(f"  - No hay registros huérfanos en mantenimientos")
    except Error as e:
        print(f"  ⚠ Error limpiando mantenimientos: {e}")
    
    try:
        cursor.execute("""
            DELETE FROM reservas 
            WHERE equipo_id NOT IN (
                SELECT id COLLATE utf8mb4_unicode_ci FROM equipos
            )
            AND equipo_id IS NOT NULL
        """)
        deleted = cursor.rowcount
        connection.commit()
        if deleted > 0:
            print(f"  ✓ {deleted} registro(s) huérfano(s) eliminado(s) de reservas")
        else:
            print(f"  - No hay registros huérfanos en reservas")
    except Error as e:
        print(f"  ⚠ Error limpiando reservas: {e}")
    
    cursor.close()

def recrear_foreign_keys(connection):
    """Recrea las foreign keys después de corregir collations"""
    print_header("RECREACIÓN DE FOREIGN KEYS")
    
    cursor = connection.cursor()
    recreadas = 0
    
    foreign_keys = [
        {
            'tabla': 'historial_uso',
            'constraint': 'historial_uso_ibfk_1',
            'columna': 'equipo_id',
            'referencia': 'equipos(id)'
        },
        {
            'tabla': 'mantenimientos',
            'constraint': 'mantenimientos_ibfk_1',
            'columna': 'equipo_id',
            'referencia': 'equipos(id)'
        },
        {
            'tabla': 'reservas',
            'constraint': 'reservas_ibfk_2',
            'columna': 'equipo_id',
            'referencia': 'equipos(id)'
        }
    ]
    
    for fk in foreign_keys:
        try:
            query = f"""
            ALTER TABLE `{fk['tabla']}` 
            ADD CONSTRAINT `{fk['constraint']}` 
            FOREIGN KEY (`{fk['columna']}`) 
            REFERENCES {fk['referencia']} 
            ON DELETE CASCADE
            """
            
            cursor.execute(query)
            connection.commit()
            print(f"  ✓ FK creada: {fk['tabla']}.{fk['constraint']}")
            recreadas += 1
            
        except Error as e:
            if "Duplicate" in str(e) or "already exists" in str(e):
                print(f"  - FK ya existe: {fk['tabla']}.{fk['constraint']}")
                recreadas += 1
            else:
                print(f"  ✗ Error al crear FK {fk['constraint']}: {e}")
    
    cursor.close()
    print(f"\n✓ {recreadas} Foreign Key(s) creada(s)/verificada(s)")
    return recreadas

def crear_tabla_movimientos_inventario(connection):
    """Crea la tabla movimientos_inventario"""
    print_header("CREACIÓN DE TABLA movimientos_inventario")
    
    try:
        cursor = connection.cursor()
        
        create_query = """
        CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id INT AUTO_INCREMENT PRIMARY KEY,
            inventario_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
            tipo_movimiento ENUM('entrada','salida','ajuste','transferencia') NOT NULL,
            cantidad INT NOT NULL,
            fecha_movimiento DATETIME DEFAULT CURRENT_TIMESTAMP,
            usuario_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
            observaciones TEXT,
            destino VARCHAR(100),
            documento_referencia VARCHAR(100),
            
            INDEX idx_inventario_id (inventario_id),
            INDEX idx_tipo_movimiento (tipo_movimiento),
            INDEX idx_fecha (fecha_movimiento),
            INDEX idx_usuario_id (usuario_id),
            
            FOREIGN KEY (inventario_id) REFERENCES inventario(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(create_query)
        connection.commit()
        print("✓ Tabla 'movimientos_inventario' creada exitosamente")
        
        cursor.close()
        return True
        
    except Error as e:
        if "already exists" in str(e):
            print("✓ Tabla 'movimientos_inventario' ya existe")
            return True
        else:
            print(f"✗ Error al crear tabla: {e}")
            return False

def verificacion_final(connection):
    """Verificación final completa"""
    print_header("VERIFICACIÓN FINAL")
    
    cursor = connection.cursor(dictionary=True)
    
    # Contar equipos
    cursor.execute("SELECT COUNT(*) as count FROM equipos")
    print(f"✓ Equipos: {cursor.fetchone()['count']} registros")
    
    # Contar equipos por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad 
        FROM equipos 
        GROUP BY estado
    """)
    print("\n  Equipos por estado:")
    for row in cursor.fetchall():
        print(f"    - {row['estado']}: {row['cantidad']}")
    
    # Verificar FK a equipos
    cursor.execute("""
        SELECT TABLE_NAME, CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s
        AND REFERENCED_TABLE_NAME = 'equipos'
    """, (DB_CONFIG['database'],))
    
    fks = cursor.fetchall()
    print(f"\n✓ Foreign Keys a 'equipos': {len(fks)}")
    for fk in fks:
        print(f"  - {fk['TABLE_NAME']} → equipos ({fk['CONSTRAINT_NAME']})")
    
    # Verificar tabla movimientos_inventario
    try:
        cursor.execute("SELECT COUNT(*) as count FROM movimientos_inventario")
        print(f"\n✓ Movimientos inventario: {cursor.fetchone()['count']} registros")
    except:
        print("\n⚠ Tabla movimientos_inventario no disponible")
    
    # Verificar collations
    print("\n  Verificación de collations:")
    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, COLLATION_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s
        AND TABLE_NAME IN ('equipos', 'historial_uso', 'mantenimientos', 'reservas', 'inventario')
        AND COLUMN_NAME IN ('id', 'equipo_id', 'inventario_id')
        ORDER BY TABLE_NAME, COLUMN_NAME
    """, (DB_CONFIG['database'],))
    
    for row in cursor.fetchall():
        print(f"    {row['TABLE_NAME']}.{row['COLUMN_NAME']}: {row['COLLATION_NAME']}")
    
    cursor.close()

def main():
    print("\n" + "=" * 80)
    print("  SOLUCIÓN DEFINITIVA: Collation y Foreign Keys")
    print("  Sistema de Laboratorio - Centro Minero SENA")
    print("=" * 80)
    
    connection = None
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        
        if connection.is_connected():
            print(f"\n✓ Conectado a la base de datos: {DB_CONFIG['database']}")
            
            # 1. Corregir collations
            corregir_collation_columnas(connection)
            
            # 2. Limpiar datos huérfanos
            limpiar_datos_huerfanos(connection)
            
            # 3. Recrear foreign keys
            fks_creadas = recrear_foreign_keys(connection)
            
            # 4. Crear tabla movimientos_inventario
            crear_tabla_movimientos_inventario(connection)
            
            # 5. Verificación final
            verificacion_final(connection)
            
            print("\n" + "=" * 80)
            if fks_creadas >= 3:
                print("  ✓✓✓ BASE DE DATOS COMPLETAMENTE REPARADA")
                print("=" * 80)
                print("\n  ¡Todo está listo! Puedes ejecutar tu aplicación:")
                print("\n  python web_app.py")
            else:
                print("  ⚠ REPARACIÓN PARCIAL")
                print("=" * 80)
                print("\n  Algunas FK no se pudieron crear.")
                print("  Sin embargo, la tabla 'equipos' existe y tiene datos.")
                print("  Puedes intentar ejecutar la aplicación:")
                print("\n  python web_app.py")
            
            print("\n" + "=" * 80 + "\n")
            
    except Error as e:
        print(f"\n✗ Error de conexión: {e}")
        
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("✓ Conexión cerrada\n")

if __name__ == "__main__":
    main()
