# -*- coding: utf-8 -*-
"""
Migración para Sistema de Laboratorios Jerárquico
Centro Minero SENA - Organización por Laboratorios/Aulas
"""

import mysql.connector
import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
if os.path.exists('.env_produccion'):
    load_dotenv('.env_produccion')

# Configuración de base de datos
DB_CONFIG = {
    'host': os.getenv('HOST', 'localhost'),
    'user': os.getenv('USUARIO_PRODUCCION', 'laboratorio_prod'),
    'password': os.getenv('PASSWORD_PRODUCCION', ''),
    'database': os.getenv('BASE_DATOS', 'laboratorio_sistema'),
    'charset': 'utf8mb4',
}

def ejecutar_migracion():
    """Ejecutar migración completa del sistema de laboratorios"""
    
    print("🏗️ MIGRACIÓN SISTEMA DE LABORATORIOS - CENTRO MINERO SENA")
    print("=" * 60)
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. Crear tabla de laboratorios
        print("📋 1. Creando tabla 'laboratorios'...")
        crear_tabla_laboratorios(cursor)
        
        # 2. Insertar laboratorios por defecto
        print("🏫 2. Insertando laboratorios por defecto...")
        insertar_laboratorios_defecto(cursor)
        
        # 3. Modificar tabla inventario
        print("📦 3. Modificando tabla 'inventario'...")
        modificar_tabla_inventario(cursor)
        
        # 4. Modificar tabla equipos
        print("🔧 4. Modificando tabla 'equipos'...")
        modificar_tabla_equipos(cursor)
        
        # 5. Migrar datos existentes
        print("🔄 5. Migrando datos existentes...")
        migrar_datos_existentes(cursor)
        
        # 6. Crear índices y restricciones
        print("🔗 6. Creando índices y restricciones...")
        crear_indices_restricciones(cursor)
        
        # 7. Crear vistas útiles
        print("👁️ 7. Creando vistas de consulta...")
        crear_vistas_consulta(cursor)
        
        conn.commit()
        print("✅ Migración completada exitosamente!")
        
        # Mostrar resumen
        mostrar_resumen_migracion(cursor)
        
    except mysql.connector.Error as e:
        print(f"❌ Error en migración: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def crear_tabla_laboratorios(cursor):
    """Crear tabla principal de laboratorios"""
    
    sql_laboratorios = """
    CREATE TABLE IF NOT EXISTS laboratorios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        codigo VARCHAR(20) NOT NULL UNIQUE,
        nombre VARCHAR(100) NOT NULL,
        tipo ENUM('laboratorio', 'aula', 'taller', 'almacen') NOT NULL DEFAULT 'laboratorio',
        ubicacion VARCHAR(200),
        capacidad_estudiantes INT DEFAULT 0,
        area_m2 DECIMAL(8,2),
        responsable VARCHAR(100),
        telefono_contacto VARCHAR(20),
        email_contacto VARCHAR(100),
        horario_disponible JSON,
        equipamiento_especializado TEXT,
        normas_seguridad TEXT,
        estado ENUM('activo', 'mantenimiento', 'inactivo') NOT NULL DEFAULT 'activo',
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        notas TEXT,
        
        INDEX idx_codigo (codigo),
        INDEX idx_tipo (tipo),
        INDEX idx_estado (estado),
        INDEX idx_responsable (responsable)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    cursor.execute(sql_laboratorios)
    print("  ✅ Tabla 'laboratorios' creada")

def insertar_laboratorios_defecto(cursor):
    """Insertar laboratorios típicos del Centro Minero SENA"""
    
    laboratorios_defecto = [
        {
            'codigo': 'LAB-QUI-001',
            'nombre': 'Laboratorio de Química General',
            'tipo': 'laboratorio',
            'ubicacion': 'Edificio A - Piso 2',
            'capacidad_estudiantes': 25,
            'area_m2': 80.0,
            'responsable': 'Instructor de Química',
            'equipamiento_especializado': 'Campanas extractoras, balanzas analíticas, espectrofotómetros',
            'normas_seguridad': 'Uso obligatorio de bata, gafas y guantes. Prohibido comer o beber.'
        },
        {
            'codigo': 'LAB-QUI-002',
            'nombre': 'Laboratorio de Química Analítica',
            'tipo': 'laboratorio',
            'ubicacion': 'Edificio A - Piso 2',
            'capacidad_estudiantes': 20,
            'area_m2': 75.0,
            'responsable': 'Instructor de Química Analítica',
            'equipamiento_especializado': 'Cromatógrafos, espectrometría de masas, HPLC',
            'normas_seguridad': 'Área de alta precisión. Acceso restringido a personal autorizado.'
        },
        {
            'codigo': 'LAB-MIN-001',
            'nombre': 'Laboratorio de Mineralogía',
            'tipo': 'laboratorio',
            'ubicacion': 'Edificio B - Piso 1',
            'capacidad_estudiantes': 30,
            'area_m2': 90.0,
            'responsable': 'Instructor de Mineralogía',
            'equipamiento_especializado': 'Microscopios petrográficos, difractómetros de rayos X',
            'normas_seguridad': 'Manejo cuidadoso de muestras minerales. Uso de mascarillas.'
        },
        {
            'codigo': 'LAB-MET-001',
            'nombre': 'Laboratorio de Metalurgia',
            'tipo': 'laboratorio',
            'ubicacion': 'Edificio C - Piso 1',
            'capacidad_estudiantes': 15,
            'area_m2': 120.0,
            'responsable': 'Instructor de Metalurgia',
            'equipamiento_especializado': 'Hornos de fusión, equipos de fundición, análisis térmico',
            'normas_seguridad': 'Área de alta temperatura. Equipo de protección completo obligatorio.'
        },
        {
            'codigo': 'AULA-001',
            'nombre': 'Aula de Química Teórica',
            'tipo': 'aula',
            'ubicacion': 'Edificio A - Piso 1',
            'capacidad_estudiantes': 40,
            'area_m2': 60.0,
            'responsable': 'Coordinador Académico',
            'equipamiento_especializado': 'Proyector, sistema audiovisual, modelos moleculares',
            'normas_seguridad': 'Aula estándar. Mantener orden y limpieza.'
        },
        {
            'codigo': 'TALL-001',
            'nombre': 'Taller de Preparación de Muestras',
            'tipo': 'taller',
            'ubicacion': 'Edificio B - Sótano',
            'capacidad_estudiantes': 12,
            'area_m2': 50.0,
            'responsable': 'Técnico de Laboratorio',
            'equipamiento_especializado': 'Molinos, tamices, prensas, equipos de trituración',
            'normas_seguridad': 'Área de ruido. Uso obligatorio de protección auditiva.'
        },
        {
            'codigo': 'ALM-001',
            'nombre': 'Almacén de Reactivos',
            'tipo': 'almacen',
            'ubicacion': 'Edificio A - Sótano',
            'capacidad_estudiantes': 0,
            'area_m2': 40.0,
            'responsable': 'Almacenista',
            'equipamiento_especializado': 'Estanterías especializadas, sistema de ventilación, alarmas',
            'normas_seguridad': 'Acceso restringido. Control de temperatura y humedad.'
        }
    ]
    
    sql_insert = """
    INSERT INTO laboratorios 
    (codigo, nombre, tipo, ubicacion, capacidad_estudiantes, area_m2, responsable, 
     equipamiento_especializado, normas_seguridad)
    VALUES (%(codigo)s, %(nombre)s, %(tipo)s, %(ubicacion)s, %(capacidad_estudiantes)s, 
            %(area_m2)s, %(responsable)s, %(equipamiento_especializado)s, %(normas_seguridad)s)
    """
    
    for lab in laboratorios_defecto:
        try:
            cursor.execute(sql_insert, lab)
            print(f"  ✅ Laboratorio '{lab['nombre']}' insertado")
        except mysql.connector.IntegrityError:
            print(f"  ⚠️ Laboratorio '{lab['nombre']}' ya existe")

def modificar_tabla_inventario(cursor):
    """Modificar tabla inventario para incluir laboratorio_id"""
    
    # Verificar si la columna ya existe
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'inventario' 
        AND COLUMN_NAME = 'laboratorio_id'
    """)
    
    if cursor.fetchone()[0] == 0:
        # Agregar columna laboratorio_id
        cursor.execute("""
            ALTER TABLE inventario 
            ADD COLUMN laboratorio_id INT NOT NULL DEFAULT 1 AFTER id
        """)
        print("  ✅ Columna 'laboratorio_id' agregada a 'inventario'")
        
        # Crear índice
        cursor.execute("""
            ALTER TABLE inventario 
            ADD INDEX idx_laboratorio_id (laboratorio_id)
        """)
        print("  ✅ Índice creado para 'laboratorio_id' en 'inventario'")
    else:
        print("  ⚠️ Columna 'laboratorio_id' ya existe en 'inventario'")

def modificar_tabla_equipos(cursor):
    """Modificar tabla equipos para incluir laboratorio_id"""
    
    # Verificar si la columna ya existe
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'equipos' 
        AND COLUMN_NAME = 'laboratorio_id'
    """)
    
    if cursor.fetchone()[0] == 0:
        # Agregar columna laboratorio_id
        cursor.execute("""
            ALTER TABLE equipos 
            ADD COLUMN laboratorio_id INT NOT NULL DEFAULT 1 AFTER id
        """)
        print("  ✅ Columna 'laboratorio_id' agregada a 'equipos'")
        
        # Crear índice
        cursor.execute("""
            ALTER TABLE equipos 
            ADD INDEX idx_laboratorio_id (laboratorio_id)
        """)
        print("  ✅ Índice creado para 'laboratorio_id' en 'equipos'")
    else:
        print("  ⚠️ Columna 'laboratorio_id' ya existe en 'equipos'")

def migrar_datos_existentes(cursor):
    """Migrar datos existentes asignándolos a laboratorios según ubicación"""
    
    # Mapeo de ubicaciones a laboratorios
    mapeo_ubicaciones = {
        'Laboratorio A': 1,  # LAB-QUI-001
        'Laboratorio B': 2,  # LAB-QUI-002
        'Lab Química': 1,
        'Lab Analítica': 2,
        'Mineralogía': 3,    # LAB-MIN-001
        'Metalurgia': 4,     # LAB-MET-001
        'Aula': 5,           # AULA-001
        'Taller': 6,         # TALL-001
        'Almacén': 7,        # ALM-001
    }
    
    # Migrar inventario
    cursor.execute("SELECT id, ubicacion FROM inventario WHERE laboratorio_id = 1")
    items_inventario = cursor.fetchall()
    
    for item_id, ubicacion in items_inventario:
        laboratorio_id = 1  # Por defecto: Laboratorio de Química General
        
        if ubicacion:
            for key, lab_id in mapeo_ubicaciones.items():
                if key.lower() in ubicacion.lower():
                    laboratorio_id = lab_id
                    break
        
        cursor.execute("""
            UPDATE inventario 
            SET laboratorio_id = %s 
            WHERE id = %s
        """, (laboratorio_id, item_id))
    
    print(f"  ��� {len(items_inventario)} items de inventario migrados")
    
    # Migrar equipos
    cursor.execute("SELECT id, ubicacion FROM equipos WHERE laboratorio_id = 1")
    equipos = cursor.fetchall()
    
    for equipo_id, ubicacion in equipos:
        laboratorio_id = 1  # Por defecto: Laboratorio de Química General
        
        if ubicacion:
            for key, lab_id in mapeo_ubicaciones.items():
                if key.lower() in ubicacion.lower():
                    laboratorio_id = lab_id
                    break
        
        cursor.execute("""
            UPDATE equipos 
            SET laboratorio_id = %s 
            WHERE id = %s
        """, (laboratorio_id, equipo_id))
    
    print(f"  ✅ {len(equipos)} equipos migrados")

def crear_indices_restricciones(cursor):
    """Crear restricciones de clave foránea"""
    
    try:
        # FK para inventario
        cursor.execute("""
            ALTER TABLE inventario 
            ADD CONSTRAINT fk_inventario_laboratorio 
            FOREIGN KEY (laboratorio_id) REFERENCES laboratorios(id) 
            ON DELETE RESTRICT ON UPDATE CASCADE
        """)
        print("  ✅ FK creada: inventario → laboratorios")
    except mysql.connector.Error:
        print("  ⚠️ FK inventario → laboratorios ya existe")
    
    try:
        # FK para equipos
        cursor.execute("""
            ALTER TABLE equipos 
            ADD CONSTRAINT fk_equipos_laboratorio 
            FOREIGN KEY (laboratorio_id) REFERENCES laboratorios(id) 
            ON DELETE RESTRICT ON UPDATE CASCADE
        """)
        print("  ✅ FK creada: equipos → laboratorios")
    except mysql.connector.Error:
        print("  ⚠️ FK equipos → laboratorios ya existe")

def crear_vistas_consulta(cursor):
    """Crear vistas útiles para consultas"""
    
    # Vista resumen por laboratorio
    vista_resumen = """
    CREATE OR REPLACE VIEW vista_resumen_laboratorios AS
    SELECT 
        l.id,
        l.codigo,
        l.nombre,
        l.tipo,
        l.ubicacion,
        l.estado,
        COUNT(DISTINCT e.id) as total_equipos,
        COUNT(DISTINCT i.id) as total_items_inventario,
        COUNT(DISTINCT CASE WHEN e.estado = 'disponible' THEN e.id END) as equipos_disponibles,
        COUNT(DISTINCT CASE WHEN i.cantidad_actual <= i.cantidad_minima THEN i.id END) as items_stock_bajo,
        SUM(DISTINCT i.cantidad_actual * IFNULL(i.costo_unitario, 0)) as valor_total_inventario
    FROM laboratorios l
    LEFT JOIN equipos e ON l.id = e.laboratorio_id
    LEFT JOIN inventario i ON l.id = i.laboratorio_id
    GROUP BY l.id, l.codigo, l.nombre, l.tipo, l.ubicacion, l.estado
    """
    
    cursor.execute(vista_resumen)
    print("  ✅ Vista 'vista_resumen_laboratorios' creada")
    
    # Vista inventario detallado
    vista_inventario = """
    CREATE OR REPLACE VIEW vista_inventario_detallado AS
    SELECT 
        l.codigo as laboratorio_codigo,
        l.nombre as laboratorio_nombre,
        l.tipo as laboratorio_tipo,
        i.id as item_id,
        i.nombre as item_nombre,
        i.categoria,
        i.cantidad_actual,
        i.cantidad_minima,
        i.unidad,
        i.ubicacion as ubicacion_especifica,
        i.proveedor,
        i.costo_unitario,
        (i.cantidad_actual * IFNULL(i.costo_unitario, 0)) as valor_total,
        CASE 
            WHEN i.cantidad_actual <= i.cantidad_minima THEN 'CRÍTICO'
            WHEN i.cantidad_actual <= i.cantidad_minima * 1.5 THEN 'BAJO'
            ELSE 'NORMAL'
        END as nivel_stock,
        DATE_FORMAT(i.fecha_vencimiento, '%Y-%m-%d') as fecha_vencimiento
    FROM laboratorios l
    INNER JOIN inventario i ON l.id = i.laboratorio_id
    WHERE l.estado = 'activo'
    ORDER BY l.codigo, i.categoria, i.nombre
    """
    
    cursor.execute(vista_inventario)
    print("  ✅ Vista 'vista_inventario_detallado' creada")
    
    # Vista equipos por laboratorio
    vista_equipos = """
    CREATE OR REPLACE VIEW vista_equipos_laboratorio AS
    SELECT 
        l.codigo as laboratorio_codigo,
        l.nombre as laboratorio_nombre,
        l.tipo as laboratorio_tipo,
        e.id as equipo_id,
        e.nombre as equipo_nombre,
        e.tipo as equipo_tipo,
        e.estado as equipo_estado,
        e.ubicacion as ubicacion_especifica,
        DATE_FORMAT(e.ultima_calibracion, '%Y-%m-%d') as ultima_calibracion,
        DATE_FORMAT(e.proximo_mantenimiento, '%Y-%m-%d') as proximo_mantenimiento,
        CASE 
            WHEN e.proximo_mantenimiento <= CURDATE() THEN 'VENCIDO'
            WHEN e.proximo_mantenimiento <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 'PRÓXIMO'
            ELSE 'VIGENTE'
        END as estado_mantenimiento
    FROM laboratorios l
    INNER JOIN equipos e ON l.id = e.laboratorio_id
    WHERE l.estado = 'activo'
    ORDER BY l.codigo, e.tipo, e.nombre
    """
    
    cursor.execute(vista_equipos)
    print("  ✅ Vista 'vista_equipos_laboratorio' creada")

def mostrar_resumen_migracion(cursor):
    """Mostrar resumen de la migración"""
    
    print("\n📊 RESUMEN DE MIGRACIÓN")
    print("=" * 40)
    
    # Contar laboratorios
    cursor.execute("SELECT COUNT(*) FROM laboratorios")
    total_labs = cursor.fetchone()[0]
    print(f"🏫 Laboratorios creados: {total_labs}")
    
    # Contar por tipo
    cursor.execute("""
        SELECT tipo, COUNT(*) 
        FROM laboratorios 
        GROUP BY tipo 
        ORDER BY tipo
    """)
    
    for tipo, count in cursor.fetchall():
        print(f"  - {tipo.title()}: {count}")
    
    # Inventario por laboratorio
    cursor.execute("""
        SELECT l.nombre, COUNT(i.id) as items
        FROM laboratorios l
        LEFT JOIN inventario i ON l.id = i.laboratorio_id
        GROUP BY l.id, l.nombre
        ORDER BY items DESC
    """)
    
    print(f"\n📦 Distribución de Inventario:")
    for lab_nombre, items in cursor.fetchall():
        print(f"  - {lab_nombre}: {items} items")
    
    # Equipos por laboratorio
    cursor.execute("""
        SELECT l.nombre, COUNT(e.id) as equipos
        FROM laboratorios l
        LEFT JOIN equipos e ON l.id = e.laboratorio_id
        GROUP BY l.id, l.nombre
        ORDER BY equipos DESC
    """)
    
    print(f"\n🔧 Distribución de Equipos:")
    for lab_nombre, equipos in cursor.fetchall():
        print(f"  - {lab_nombre}: {equipos} equipos")
    
    print(f"\n✅ Migración completada exitosamente!")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    ejecutar_migracion()
