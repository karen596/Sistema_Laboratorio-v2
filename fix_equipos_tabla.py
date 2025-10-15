#!/usr/bin/env python3
"""
Script para solucionar el problema de la tabla equipos
Elimina las FK que apuntan a equipos, crea la tabla, y las recrea
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

def obtener_foreign_keys_a_equipos(connection):
    """Obtiene todas las FK que apuntan a la tabla equipos"""
    cursor = connection.cursor(dictionary=True)
    
    query = """
    SELECT 
        TABLE_NAME,
        CONSTRAINT_NAME,
        COLUMN_NAME
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = %s
    AND REFERENCED_TABLE_NAME = 'equipos'
    """
    
    cursor.execute(query, (DB_CONFIG['database'],))
    fks = cursor.fetchall()
    cursor.close()
    
    return fks

def eliminar_foreign_keys(connection, fks):
    """Elimina las foreign keys temporalmente"""
    print_header("PASO 1: Eliminando Foreign Keys temporalmente")
    
    cursor = connection.cursor()
    
    for fk in fks:
        try:
            query = f"ALTER TABLE `{fk['TABLE_NAME']}` DROP FOREIGN KEY `{fk['CONSTRAINT_NAME']}`"
            cursor.execute(query)
            connection.commit()
            print(f"  ✓ FK eliminada: {fk['TABLE_NAME']}.{fk['CONSTRAINT_NAME']}")
        except Error as e:
            print(f"  ⚠ Error al eliminar FK {fk['CONSTRAINT_NAME']}: {e}")
    
    cursor.close()
    print(f"\n✓ {len(fks)} Foreign Key(s) eliminada(s) temporalmente")

def crear_tabla_equipos(connection):
    """Crea la tabla equipos SIN foreign keys"""
    print_header("PASO 2: Creando tabla equipos")
    
    try:
        cursor = connection.cursor()
        
        # Primero eliminar la tabla si existe (por si quedó corrupta)
        cursor.execute("DROP TABLE IF EXISTS equipos")
        print("  - Tabla equipos anterior eliminada (si existía)")
        
        # Crear tabla equipos sin FK
        create_query = """
        CREATE TABLE equipos (
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
        
        cursor.execute(create_query)
        connection.commit()
        print("✓ Tabla 'equipos' creada exitosamente")
        
        # Insertar datos de ejemplo
        print("\n  Insertando datos de ejemplo...")
        insert_query = """
        INSERT INTO equipos (id, equipo_id, nombre, tipo, estado, ubicacion, laboratorio_id)
        VALUES 
            ('EQ001', 'EQ_001', 'Microscopio Óptico Binocular', 'Microscopio', 'disponible', 'Lab Química General', 1),
            ('EQ002', 'EQ_002', 'Balanza Analítica Digital', 'Balanza', 'disponible', 'Lab Química General', 1),
            ('EQ003', 'EQ_003', 'Espectrofotómetro UV-Vis', 'Espectrofotómetro', 'disponible', 'Lab Química Analítica', 2),
            ('EQ004', 'EQ_004', 'pH-metro Digital', 'Medidor', 'disponible', 'Lab Química General', 1),
            ('EQ005', 'EQ_005', 'Centrífuga de Laboratorio', 'Centrífuga', 'mantenimiento', 'Lab Química Analítica', 2),
            ('EQ006', 'EQ_006', 'Agitador Magnético', 'Agitador', 'disponible', 'Lab Química General', 1),
            ('EQ007', 'EQ_007', 'Microscopio Petrográfico', 'Microscopio', 'disponible', 'Lab Mineralogía', 1),
            ('EQ008', 'EQ_008', 'Horno de Secado', 'Horno', 'disponible', 'Lab Química General', 1),
            ('EQ009', 'EQ_009', 'Destilador de Agua', 'Destilador', 'en_uso', 'Lab Química General', 1),
            ('EQ010', 'EQ_010', 'Campana Extractora', 'Campana', 'disponible', 'Lab Química General', 1),
            ('EQ011', 'EQ_011', 'Autoclave', 'Esterilizador', 'disponible', 'Lab Química General', 1),
            ('EQ012', 'EQ_012', 'Refractómetro', 'Medidor', 'disponible', 'Lab Química Analítica', 2)
        """
        
        cursor.execute(insert_query)
        connection.commit()
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM equipos")
        count = cursor.fetchone()[0]
        print(f"✓ {count} equipos insertados")
        
        # Mostrar resumen por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad 
            FROM equipos 
            GROUP BY estado
        """)
        print("\n  Resumen por estado:")
        for row in cursor.fetchall():
            print(f"    - {row[0]}: {row[1]} equipo(s)")
        
        cursor.close()
        return True
        
    except Error as e:
        print(f"✗ Error al crear tabla equipos: {e}")
        return False

def recrear_foreign_keys(connection, fks):
    """Recrea las foreign keys que fueron eliminadas"""
    print_header("PASO 3: Recreando Foreign Keys")
    
    cursor = connection.cursor()
    recreadas = 0
    
    for fk in fks:
        try:
            # Recrear la FK
            query = f"""
            ALTER TABLE `{fk['TABLE_NAME']}` 
            ADD CONSTRAINT `{fk['CONSTRAINT_NAME']}` 
            FOREIGN KEY (`{fk['COLUMN_NAME']}`) 
            REFERENCES equipos(id) 
            ON DELETE CASCADE
            """
            
            cursor.execute(query)
            connection.commit()
            print(f"  ✓ FK recreada: {fk['TABLE_NAME']}.{fk['CONSTRAINT_NAME']}")
            recreadas += 1
            
        except Error as e:
            # Si la FK ya existe, no es un error crítico
            if "Duplicate key" in str(e) or "already exists" in str(e):
                print(f"  - FK ya existe: {fk['TABLE_NAME']}.{fk['CONSTRAINT_NAME']}")
            else:
                print(f"  ⚠ Error al recrear FK {fk['CONSTRAINT_NAME']}: {e}")
    
    cursor.close()
    print(f"\n✓ {recreadas} Foreign Key(s) recreada(s)")

def crear_tabla_movimientos_inventario(connection):
    """Crea la tabla movimientos_inventario"""
    print_header("PASO 4: Creando tabla movimientos_inventario")
    
    try:
        cursor = connection.cursor()
        
        create_query = """
        CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id INT AUTO_INCREMENT PRIMARY KEY,
            inventario_id VARCHAR(50) NOT NULL,
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
            print(f"✗ Error al crear tabla movimientos_inventario: {e}")
            return False

def verificar_resultado(connection):
    """Verifica que todo se creó correctamente"""
    print_header("VERIFICACIÓN FINAL")
    
    cursor = connection.cursor()
    
    # Verificar tabla equipos
    cursor.execute("SELECT COUNT(*) FROM equipos")
    equipos_count = cursor.fetchone()[0]
    print(f"✓ Tabla 'equipos': {equipos_count} registros")
    
    # Verificar tabla movimientos_inventario
    try:
        cursor.execute("SELECT COUNT(*) FROM movimientos_inventario")
        movimientos_count = cursor.fetchone()[0]
        print(f"✓ Tabla 'movimientos_inventario': {movimientos_count} registros")
    except:
        print("⚠ Tabla 'movimientos_inventario': no verificada")
    
    # Verificar foreign keys a equipos
    cursor.execute("""
        SELECT TABLE_NAME, CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s
        AND REFERENCED_TABLE_NAME = 'equipos'
    """, (DB_CONFIG['database'],))
    
    fks = cursor.fetchall()
    print(f"\n✓ Relaciones de clave foránea a 'equipos': {len(fks)}")
    for tabla, constraint in fks:
        print(f"  - {tabla} → equipos ({constraint})")
    
    cursor.close()

def main():
    print("\n" + "=" * 80)
    print("  SOLUCIÓN: Crear tabla EQUIPOS")
    print("  Sistema de Laboratorio - Centro Minero SENA")
    print("=" * 80)
    
    connection = None
    
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(**DB_CONFIG)
        
        if connection.is_connected():
            print(f"\n✓ Conectado a la base de datos: {DB_CONFIG['database']}")
            
            # Paso 1: Obtener y eliminar FKs existentes
            fks = obtener_foreign_keys_a_equipos(connection)
            
            if fks:
                print(f"\n  Se encontraron {len(fks)} FK(s) que apuntan a 'equipos':")
                for fk in fks:
                    print(f"    - {fk['TABLE_NAME']}.{fk['CONSTRAINT_NAME']}")
                
                eliminar_foreign_keys(connection, fks)
            else:
                print("\n  No se encontraron FK que apunten a 'equipos'")
            
            # Paso 2: Crear tabla equipos
            if not crear_tabla_equipos(connection):
                print("\n⚠ No se pudo crear la tabla equipos. Abortando...")
                return
            
            # Paso 3: Recrear FKs
            if fks:
                recrear_foreign_keys(connection, fks)
            
            # Paso 4: Crear tabla movimientos_inventario
            crear_tabla_movimientos_inventario(connection)
            
            # Verificación final
            verificar_resultado(connection)
            
            print("\n" + "=" * 80)
            print("  ✓✓✓ PROCESO COMPLETADO EXITOSAMENTE")
            print("=" * 80)
            print("\n  La tabla 'equipos' ha sido creada correctamente.")
            print("  Ahora puedes ejecutar tu aplicación:")
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
