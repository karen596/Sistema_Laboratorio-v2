#!/usr/bin/env python3
"""
Script para crear las tablas faltantes identificadas en el diagnóstico
- equipos (CRÍTICO)
- movimientos_inventario
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

def crear_tabla_equipos(connection):
    """Crea la tabla equipos"""
    print_header("CREANDO TABLA: equipos")
    
    try:
        cursor = connection.cursor()
        
        # Crear tabla equipos SIN foreign key a laboratorios para evitar problemas
        create_query = """
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
            ('EQ010', 'EQ_010', 'Campana Extractora', 'Campana', 'disponible', 'Lab Química General', 1)
        ON DUPLICATE KEY UPDATE nombre=VALUES(nombre)
        """
        
        cursor.execute(insert_query)
        connection.commit()
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM equipos")
        count = cursor.fetchone()[0]
        print(f"✓ {count} equipos insertados/actualizados")
        
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

def crear_tabla_movimientos_inventario(connection):
    """Crea la tabla movimientos_inventario"""
    print_header("CREANDO TABLA: movimientos_inventario")
    
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
        
        # Insertar datos de ejemplo
        print("\n  Insertando movimientos de ejemplo...")
        insert_query = """
        INSERT INTO movimientos_inventario 
        (inventario_id, tipo_movimiento, cantidad, usuario_id, observaciones)
        SELECT 
            i.id,
            'entrada',
            10,
            (SELECT id FROM usuarios LIMIT 1),
            'Inventario inicial'
        FROM inventario i
        LIMIT 5
        ON DUPLICATE KEY UPDATE id=id
        """
        
        cursor.execute(insert_query)
        connection.commit()
        
        cursor.execute("SELECT COUNT(*) FROM movimientos_inventario")
        count = cursor.fetchone()[0]
        print(f"✓ {count} movimiento(s) de ejemplo insertado(s)")
        
        cursor.close()
        return True
        
    except Error as e:
        print(f"✗ Error al crear tabla movimientos_inventario: {e}")
        return False

def agregar_columnas_faltantes(connection):
    """Agrega columnas faltantes a tablas existentes"""
    print_header("AGREGANDO COLUMNAS FALTANTES")
    
    cursor = connection.cursor()
    columnas_agregadas = 0
    
    # Columnas para agregar
    alteraciones = [
        # Tabla usuarios
        ("usuarios", "password", "ALTER TABLE usuarios ADD COLUMN password VARCHAR(255) AFTER email"),
        ("usuarios", "rol", "ALTER TABLE usuarios ADD COLUMN rol ENUM('admin','instructor','estudiante','tecnico') DEFAULT 'estudiante' AFTER password"),
        ("usuarios", "estado", "ALTER TABLE usuarios ADD COLUMN estado ENUM('activo','inactivo','suspendido') DEFAULT 'activo' AFTER rol"),
        ("usuarios", "fecha_creacion", "ALTER TABLE usuarios ADD COLUMN fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER estado"),
        ("usuarios", "ultimo_acceso", "ALTER TABLE usuarios ADD COLUMN ultimo_acceso DATETIME AFTER fecha_creacion"),
        
        # Tabla reservas
        ("reservas", "proposito", "ALTER TABLE reservas ADD COLUMN proposito TEXT AFTER estado"),
        
        # Tabla historial_uso
        ("historial_uso", "proposito", "ALTER TABLE historial_uso ADD COLUMN proposito TEXT AFTER duracion_minutos"),
        
        # Tabla mantenimientos
        ("mantenimientos", "tipo_mantenimiento", "ALTER TABLE mantenimientos ADD COLUMN tipo_mantenimiento ENUM('preventivo','correctivo','calibracion','limpieza') AFTER equipo_id"),
        ("mantenimientos", "fecha_mantenimiento", "ALTER TABLE mantenimientos ADD COLUMN fecha_mantenimiento DATE AFTER tipo_mantenimiento"),
        ("mantenimientos", "tecnico_responsable", "ALTER TABLE mantenimientos ADD COLUMN tecnico_responsable VARCHAR(100) AFTER fecha_mantenimiento"),
        ("mantenimientos", "estado", "ALTER TABLE mantenimientos ADD COLUMN estado ENUM('programado','en_proceso','completado','cancelado') DEFAULT 'programado' AFTER costo"),
    ]
    
    for tabla, columna, query in alteraciones:
        try:
            # Verificar si la columna ya existe
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{DB_CONFIG['database']}' 
                AND TABLE_NAME = '{tabla}' 
                AND COLUMN_NAME = '{columna}'
            """)
            
            existe = cursor.fetchone()[0] > 0
            
            if not existe:
                cursor.execute(query)
                connection.commit()
                print(f"  ✓ Columna '{columna}' agregada a tabla '{tabla}'")
                columnas_agregadas += 1
            else:
                print(f"  - Columna '{columna}' ya existe en '{tabla}'")
                
        except Error as e:
            print(f"  ✗ Error al agregar '{columna}' a '{tabla}': {e}")
    
    cursor.close()
    print(f"\n✓ Total de columnas agregadas: {columnas_agregadas}")
    return columnas_agregadas > 0

def verificar_resultado(connection):
    """Verifica que las tablas se crearon correctamente"""
    print_header("VERIFICACIÓN FINAL")
    
    cursor = connection.cursor()
    
    # Verificar tabla equipos
    cursor.execute("SELECT COUNT(*) FROM equipos")
    equipos_count = cursor.fetchone()[0]
    print(f"✓ Tabla 'equipos': {equipos_count} registros")
    
    # Verificar tabla movimientos_inventario
    cursor.execute("SELECT COUNT(*) FROM movimientos_inventario")
    movimientos_count = cursor.fetchone()[0]
    print(f"✓ Tabla 'movimientos_inventario': {movimientos_count} registros")
    
    # Verificar foreign keys que dependen de equipos
    cursor.execute("""
        SELECT TABLE_NAME, CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s
        AND REFERENCED_TABLE_NAME = 'equipos'
    """, (DB_CONFIG['database'],))
    
    fks = cursor.fetchall()
    print(f"\n✓ Relaciones de clave foránea a 'equipos': {len(fks)}")
    for tabla, constraint in fks:
        print(f"  - {tabla} ({constraint})")
    
    cursor.close()

def main():
    print("\n" + "=" * 80)
    print("  CREACIÓN DE TABLAS FALTANTES")
    print("  Sistema de Laboratorio - Centro Minero SENA")
    print("=" * 80)
    
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(**DB_CONFIG)
        
        if connection.is_connected():
            print(f"\n✓ Conectado a la base de datos: {DB_CONFIG['database']}")
            
            # 1. Crear tabla equipos (CRÍTICO)
            if not crear_tabla_equipos(connection):
                print("\n⚠ No se pudo crear la tabla equipos. Abortando...")
                return
            
            # 2. Crear tabla movimientos_inventario
            crear_tabla_movimientos_inventario(connection)
            
            # 3. Agregar columnas faltantes
            agregar_columnas_faltantes(connection)
            
            # 4. Verificar resultado
            verificar_resultado(connection)
            
            print("\n" + "=" * 80)
            print("  ✓✓✓ PROCESO COMPLETADO EXITOSAMENTE")
            print("=" * 80)
            print("\n  Ahora puedes ejecutar tu aplicación:")
            print("  python web_app.py")
            print("\n" + "=" * 80 + "\n")
            
    except Error as e:
        print(f"\n✗ Error de conexión: {e}")
        
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("✓ Conexión cerrada\n")

if __name__ == "__main__":
    main()
