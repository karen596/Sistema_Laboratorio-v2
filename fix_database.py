"""
Script para agregar columnas faltantes a la base de datos
"""
import mysql.connector
import os
from dotenv import load_dotenv

# Cargar variables de entorno
if os.path.exists('.env_produccion'):
    load_dotenv('.env_produccion')

# Configuración de BD
config = {
    'host': os.getenv('HOST', 'localhost'),
    'user': os.getenv('USUARIO_PRODUCCION', 'laboratorio_prod'),
    'password': os.getenv('PASSWORD_PRODUCCION', ''),
    'database': os.getenv('BASE_DATOS', 'laboratorio_sistema'),
}

print("="*60)
print("REPARACIÓN DE BASE DE DATOS")
print("="*60)

try:
    # Conectar a la BD
    print("\n[1] Conectando a la base de datos...")
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    print("  ✓ Conexión exitosa")
    
    # Verificar si la columna equipo_id existe
    print("\n[2] Verificando columna 'equipo_id' en tabla 'equipos'...")
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
          AND TABLE_NAME = 'equipos' 
          AND COLUMN_NAME = 'equipo_id'
    """, (config['database'],))
    
    result = cursor.fetchone()
    
    if result:
        print("  ✓ La columna 'equipo_id' ya existe")
    else:
        print("  ⚠ La columna 'equipo_id' NO existe. Agregando...")
        
        # Agregar columna
        cursor.execute("""
            ALTER TABLE equipos 
            ADD COLUMN equipo_id VARCHAR(50) UNIQUE AFTER id
        """)
        print("  ✓ Columna 'equipo_id' agregada")
        
        # Actualizar registros existentes
        print("\n[3] Actualizando registros existentes...")
        cursor.execute("""
            UPDATE equipos 
            SET equipo_id = CONCAT('EQ_', UPPER(SUBSTRING(MD5(CONCAT(id, nombre)), 1, 8)))
            WHERE equipo_id IS NULL OR equipo_id = ''
        """)
        affected = cursor.rowcount
        print(f"  ✓ {affected} registros actualizados")
        
        conn.commit()
    
    # Verificar y agregar columnas faltantes
    columnas_requeridas = [
        ('descripcion', 'TEXT', 'especificaciones'),
        ('fecha_registro', 'DATETIME DEFAULT CURRENT_TIMESTAMP', 'estado'),
        ('objeto_id', 'INT', 'equipo_id'),
        ('entrenado_ia', 'BOOLEAN DEFAULT FALSE', 'objeto_id'),
    ]
    
    for columna, tipo, after in columnas_requeridas:
        print(f"\n[4.{columnas_requeridas.index((columna, tipo, after)) + 1}] Verificando columna '{columna}'...")
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
              AND TABLE_NAME = 'equipos' 
              AND COLUMN_NAME = %s
        """, (config['database'], columna))
        
        result = cursor.fetchone()
        
        if result:
            print(f"  ✓ La columna '{columna}' ya existe")
        else:
            print(f"  ⚠ La columna '{columna}' NO existe. Agregando...")
            try:
                cursor.execute(f"""
                    ALTER TABLE equipos 
                    ADD COLUMN {columna} {tipo} AFTER {after}
                """)
                print(f"  ✓ Columna '{columna}' agregada")
                conn.commit()
            except mysql.connector.Error as e:
                print(f"  ⚠ Error agregando '{columna}': {e}")
    
    # Hacer lo mismo para la tabla inventario
    print("\n[5] Verificando columnas en tabla 'inventario'...")
    columnas_inventario = [
        ('descripcion', 'TEXT', 'categoria'),
        ('fecha_registro', 'DATETIME DEFAULT CURRENT_TIMESTAMP', 'cantidad_minima'),
        ('cantidad_minima', 'INT DEFAULT 0', 'unidad'),
    ]
    
    for columna, tipo, after in columnas_inventario:
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
              AND TABLE_NAME = 'inventario' 
              AND COLUMN_NAME = %s
        """, (config['database'], columna))
        
        result = cursor.fetchone()
        
        if not result:
            try:
                print(f"  ⚠ Agregando '{columna}' a inventario...")
                cursor.execute(f"""
                    ALTER TABLE inventario 
                    ADD COLUMN {columna} {tipo} AFTER {after}
                """)
                conn.commit()
                print(f"  ✓ Columna '{columna}' agregada a inventario")
            except mysql.connector.Error as e:
                # Puede que la columna ya exista o el AFTER no sea válido
                print(f"  → '{columna}' ya existe o no se pudo agregar")
    
    # Verificar columnas en tabla usuarios para reconocimiento facial
    print("\n[6] Verificando columnas de reconocimiento facial en 'usuarios'...")
    columnas_usuarios = [
        ('rostro_encoding', 'TEXT', 'password_hash'),
        ('rostro_data', 'LONGBLOB', 'rostro_encoding'),
    ]
    
    for columna, tipo, after in columnas_usuarios:
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
              AND TABLE_NAME = 'usuarios' 
              AND COLUMN_NAME = %s
        """, (config['database'], columna))
        
        result = cursor.fetchone()
        
        if not result:
            try:
                print(f"  ⚠ Agregando '{columna}' a usuarios...")
                cursor.execute(f"""
                    ALTER TABLE usuarios 
                    ADD COLUMN {columna} {tipo} AFTER {after}
                """)
                conn.commit()
                print(f"  ✓ Columna '{columna}' agregada a usuarios")
            except mysql.connector.Error as e:
                print(f"  → '{columna}' ya existe o no se pudo agregar: {e}")
        else:
            print(f"  ✓ Columna '{columna}' ya existe en usuarios")
    
    # Mostrar algunos registros
    print("\n[7] Verificando datos...")
    cursor.execute("SELECT id, equipo_id, nombre FROM equipos LIMIT 5")
    equipos = cursor.fetchall()
    
    if equipos:
        print("  Equipos en la BD:")
        for eq in equipos:
            print(f"    • ID: {eq[0]}, Código: {eq[1]}, Nombre: {eq[2]}")
    else:
        print("  ⚠ No hay equipos en la BD")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✓ REPARACIÓN COMPLETADA EXITOSAMENTE")
    print("="*60)
    print("\nAhora puedes iniciar el servidor: python web_app.py\n")
    
except mysql.connector.Error as e:
    print(f"\n✗ Error de MySQL: {e}")
    print("\nVerifica:")
    print("  1. Que MySQL esté corriendo")
    print("  2. Las credenciales en .env_produccion")
    print("  3. Que la base de datos exista\n")
except Exception as e:
    print(f"\n✗ Error inesperado: {e}\n")
