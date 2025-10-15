#!/usr/bin/env python3
"""
Script para corregir incompatibilidades de tipos de datos
y recrear las foreign keys correctamente
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

def verificar_tipos_datos(connection):
    """Verifica los tipos de datos de las columnas relacionadas"""
    print_header("VERIFICACIÓN DE TIPOS DE DATOS")
    
    cursor = connection.cursor(dictionary=True)
    
    tablas_columnas = [
        ('equipos', 'id'),
        ('historial_uso', 'equipo_id'),
        ('mantenimientos', 'equipo_id'),
        ('reservas', 'equipo_id'),
        ('inventario', 'id'),
    ]
    
    print("\n  Tipos de datos actuales:\n")
    
    for tabla, columna in tablas_columnas:
        try:
            query = """
            SELECT COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = %s
            AND COLUMN_NAME = %s
            """
            
            cursor.execute(query, (DB_CONFIG['database'], tabla, columna))
            result = cursor.fetchone()
            
            if result:
                print(f"  {tabla}.{columna}:")
                print(f"    Tipo: {result['COLUMN_TYPE']}")
                print(f"    Nullable: {result['IS_NULLABLE']}")
                print(f"    Default: {result['COLUMN_DEFAULT']}\n")
            else:
                print(f"  ⚠ {tabla}.{columna}: NO ENCONTRADA\n")
                
        except Error as e:
            print(f"  ✗ Error verificando {tabla}.{columna}: {e}\n")
    
    cursor.close()

def corregir_tipos_datos(connection):
    """Corrige los tipos de datos para que sean compatibles"""
    print_header("CORRECCIÓN DE TIPOS DE DATOS")
    
    cursor = connection.cursor()
    correcciones = 0
    
    # Las columnas equipo_id deben ser VARCHAR(50) para coincidir con equipos.id
    alteraciones = [
        ("historial_uso", "equipo_id", "ALTER TABLE historial_uso MODIFY COLUMN equipo_id VARCHAR(50)"),
        ("mantenimientos", "equipo_id", "ALTER TABLE mantenimientos MODIFY COLUMN equipo_id VARCHAR(50)"),
        ("reservas", "equipo_id", "ALTER TABLE reservas MODIFY COLUMN equipo_id VARCHAR(50)"),
    ]
    
    for tabla, columna, query in alteraciones:
        try:
            cursor.execute(query)
            connection.commit()
            print(f"  ✓ {tabla}.{columna} → VARCHAR(50)")
            correcciones += 1
        except Error as e:
            print(f"  ⚠ Error al modificar {tabla}.{columna}: {e}")
    
    cursor.close()
    print(f"\n✓ {correcciones} tipo(s) de dato corregido(s)")
    return correcciones > 0

def recrear_foreign_keys(connection):
    """Recrea las foreign keys con los tipos correctos"""
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
            else:
                print(f"  ✗ Error al crear FK {fk['constraint']}: {e}")
    
    cursor.close()
    print(f"\n✓ {recreadas} Foreign Key(s) creada(s)")

def crear_tabla_movimientos_inventario(connection):
    """Crea la tabla movimientos_inventario con tipos correctos"""
    print_header("CREACIÓN DE TABLA movimientos_inventario")
    
    try:
        cursor = connection.cursor()
        
        # Primero verificar el tipo de inventario.id
        cursor.execute("""
            SELECT COLUMN_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'inventario'
            AND COLUMN_NAME = 'id'
        """, (DB_CONFIG['database'],))
        
        result = cursor.fetchone()
        tipo_inventario_id = result[0] if result else 'varchar(50)'
        print(f"  Tipo de inventario.id: {tipo_inventario_id}")
        
        # Crear tabla con el tipo correcto
        create_query = f"""
        CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id INT AUTO_INCREMENT PRIMARY KEY,
            inventario_id {tipo_inventario_id} NOT NULL,
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

def limpiar_datos_huerfanos(connection):
    """Limpia datos que no tienen referencias válidas"""
    print_header("LIMPIEZA DE DATOS HUÉRFANOS")
    
    cursor = connection.cursor()
    
    # Limpiar registros en historial_uso con equipo_id inválido
    try:
        cursor.execute("""
            DELETE FROM historial_uso 
            WHERE equipo_id NOT IN (SELECT id FROM equipos)
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
    
    # Limpiar registros en mantenimientos con equipo_id inválido
    try:
        cursor.execute("""
            DELETE FROM mantenimientos 
            WHERE equipo_id NOT IN (SELECT id FROM equipos)
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
    
    # Limpiar registros en reservas con equipo_id inválido
    try:
        cursor.execute("""
            DELETE FROM reservas 
            WHERE equipo_id NOT IN (SELECT id FROM equipos)
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

def verificacion_final(connection):
    """Verificación final del estado de la base de datos"""
    print_header("VERIFICACIÓN FINAL")
    
    cursor = connection.cursor()
    
    # Contar equipos
    cursor.execute("SELECT COUNT(*) FROM equipos")
    print(f"✓ Equipos: {cursor.fetchone()[0]} registros")
    
    # Verificar FK a equipos
    cursor.execute("""
        SELECT TABLE_NAME, CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s
        AND REFERENCED_TABLE_NAME = 'equipos'
    """, (DB_CONFIG['database'],))
    
    fks = cursor.fetchall()
    print(f"✓ Foreign Keys a 'equipos': {len(fks)}")
    for tabla, constraint in fks:
        print(f"  - {tabla} → equipos")
    
    # Verificar tabla movimientos_inventario
    try:
        cursor.execute("SELECT COUNT(*) FROM movimientos_inventario")
        print(f"✓ Movimientos inventario: {cursor.fetchone()[0]} registros")
    except:
        print("⚠ Tabla movimientos_inventario no disponible")
    
    cursor.close()

def main():
    print("\n" + "=" * 80)
    print("  CORRECCIÓN DE TIPOS DE DATOS Y FOREIGN KEYS")
    print("  Sistema de Laboratorio - Centro Minero SENA")
    print("=" * 80)
    
    connection = None
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        
        if connection.is_connected():
            print(f"\n✓ Conectado a la base de datos: {DB_CONFIG['database']}")
            
            # 1. Verificar tipos de datos actuales
            verificar_tipos_datos(connection)
            
            # 2. Limpiar datos huérfanos antes de crear FK
            limpiar_datos_huerfanos(connection)
            
            # 3. Corregir tipos de datos
            corregir_tipos_datos(connection)
            
            # 4. Recrear foreign keys
            recrear_foreign_keys(connection)
            
            # 5. Crear tabla movimientos_inventario
            crear_tabla_movimientos_inventario(connection)
            
            # 6. Verificación final
            verificacion_final(connection)
            
            print("\n" + "=" * 80)
            print("  ✓✓✓ CORRECCIÓN COMPLETADA EXITOSAMENTE")
            print("=" * 80)
            print("\n  La base de datos está lista para usar.")
            print("  Puedes ejecutar tu aplicación:")
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
