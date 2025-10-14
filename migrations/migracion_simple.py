# -*- coding: utf-8 -*-
"""
Migración Simplificada para Permisos Limitados
Centro Minero SENA - Solo modificaciones permitidas
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

def verificar_permisos():
    """Verificar qué operaciones podemos realizar"""
    print("🔍 VERIFICANDO PERMISOS DEL USUARIO...")
    print("=" * 50)
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Verificar permisos
        cursor.execute("SHOW GRANTS FOR CURRENT_USER()")
        grants = cursor.fetchall()
        
        print("📋 Permisos actuales:")
        for grant in grants:
            print(f"  {grant[0]}")
        
        # Verificar si existe tabla laboratorios
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'laboratorios'
        """)
        
        tabla_existe = cursor.fetchone()[0] > 0
        print(f"\n📊 Tabla 'laboratorios' existe: {'✅ Sí' if tabla_existe else '❌ No'}")
        
        if tabla_existe:
            cursor.execute("SELECT COUNT(*) FROM laboratorios")
            count = cursor.fetchone()[0]
            print(f"📊 Laboratorios registrados: {count}")
        
        # Verificar columnas en inventario
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'inventario' 
            AND COLUMN_NAME = 'laboratorio_id'
        """)
        
        col_inventario = cursor.fetchone()[0] > 0
        print(f"📊 Columna 'laboratorio_id' en inventario: {'✅ Sí' if col_inventario else '❌ No'}")
        
        # Verificar columnas en equipos
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'equipos' 
            AND COLUMN_NAME = 'laboratorio_id'
        """)
        
        col_equipos = cursor.fetchone()[0] > 0
        print(f"📊 Columna 'laboratorio_id' en equipos: {'✅ Sí' if col_equipos else '❌ No'}")
        
        return {
            'tabla_laboratorios': tabla_existe,
            'col_inventario': col_inventario,
            'col_equipos': col_equipos
        }
        
    except mysql.connector.Error as e:
        print(f"❌ Error verificando permisos: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def crear_laboratorios_temporales():
    """Crear datos de laboratorios usando INSERT si no existen"""
    print("\n🏗️ INTENTANDO CREAR DATOS DE LABORATORIOS...")
    print("=" * 50)
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Intentar crear tabla con CREATE TEMPORARY
        try:
            print("📋 Intentando crear tabla temporal...")
            cursor.execute("""
                CREATE TEMPORARY TABLE temp_laboratorios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    codigo VARCHAR(20) NOT NULL UNIQUE,
                    nombre VARCHAR(100) NOT NULL,
                    tipo ENUM('laboratorio', 'aula', 'taller', 'almacen') NOT NULL DEFAULT 'laboratorio',
                    ubicacion VARCHAR(200),
                    capacidad_estudiantes INT DEFAULT 0,
                    responsable VARCHAR(100),
                    estado ENUM('activo', 'mantenimiento', 'inactivo') NOT NULL DEFAULT 'activo'
                )
            """)
            print("✅ Tabla temporal creada")
            
            # Insertar datos
            laboratorios = [
                ('LAB-QUI-001', 'Laboratorio de Química General', 'laboratorio', 'Edificio A - Piso 2', 25, 'Instructor de Química'),
                ('LAB-QUI-002', 'Laboratorio de Química Analítica', 'laboratorio', 'Edificio A - Piso 2', 20, 'Instructor de Química Analítica'),
                ('LAB-MIN-001', 'Laboratorio de Mineralogía', 'laboratorio', 'Edificio B - Piso 1', 30, 'Instructor de Mineralogía'),
                ('LAB-MET-001', 'Laboratorio de Metalurgia', 'laboratorio', 'Edificio C - Piso 1', 15, 'Instructor de Metalurgia'),
                ('AULA-001', 'Aula de Química Teórica', 'aula', 'Edificio A - Piso 1', 40, 'Coordinador Académico'),
                ('TALL-001', 'Taller de Preparación de Muestras', 'taller', 'Edificio B - Sótano', 12, 'Técnico de Laboratorio'),
                ('ALM-001', 'Almacén de Reactivos', 'almacen', 'Edificio A - Sótano', 0, 'Almacenista')
            ]
            
            cursor.executemany("""
                INSERT INTO temp_laboratorios 
                (codigo, nombre, tipo, ubicacion, capacidad_estudiantes, responsable)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, laboratorios)
            
            print(f"✅ {len(laboratorios)} laboratorios insertados en tabla temporal")
            
            # Mostrar datos
            cursor.execute("SELECT * FROM temp_laboratorios ORDER BY codigo")
            labs = cursor.fetchall()
            
            print("\n📋 Laboratorios disponibles:")
            for lab in labs:
                print(f"  {lab[1]} - {lab[2]} ({lab[3]})")
            
            return True
            
        except mysql.connector.Error as e:
            print(f"❌ No se pudo crear tabla temporal: {e}")
            return False
        
    except mysql.connector.Error as e:
        print(f"❌ Error general: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def simular_asignacion_laboratorios():
    """Simular cómo se asignarían los laboratorios a equipos e inventario"""
    print("\n🎯 SIMULACIÓN DE ASIGNACIÓN DE LABORATORIOS")
    print("=" * 50)
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Mapeo de ubicaciones a laboratorios
        mapeo = {
            'Laboratorio A': 'LAB-QUI-001 (Química General)',
            'Lab Química': 'LAB-QUI-001 (Química General)',
            'Laboratorio B': 'LAB-QUI-002 (Química Analítica)',
            'Analítica': 'LAB-QUI-002 (Química Analítica)',
            'Mineralogía': 'LAB-MIN-001 (Mineralogía)',
            'Metalurgia': 'LAB-MET-001 (Metalurgia)',
            'Aula': 'AULA-001 (Aula Teórica)',
            'Taller': 'TALL-001 (Taller Muestras)',
            'Almacén': 'ALM-001 (Almacén Reactivos)'
        }
        
        # Analizar inventario
        cursor.execute("SELECT ubicacion, COUNT(*) as cantidad FROM inventario GROUP BY ubicacion ORDER BY cantidad DESC")
        inventario_ubicaciones = cursor.fetchall()
        
        print("📦 DISTRIBUCIÓN DE INVENTARIO:")
        for ubicacion, cantidad in inventario_ubicaciones:
            laboratorio_asignado = 'LAB-QUI-001 (Química General)'  # Por defecto
            
            if ubicacion:
                for key, lab in mapeo.items():
                    if key.lower() in ubicacion.lower():
                        laboratorio_asignado = lab
                        break
            
            print(f"  📍 {ubicacion or 'Sin ubicación'}: {cantidad} items → {laboratorio_asignado}")
        
        # Analizar equipos
        cursor.execute("SELECT ubicacion, COUNT(*) as cantidad FROM equipos GROUP BY ubicacion ORDER BY cantidad DESC")
        equipos_ubicaciones = cursor.fetchall()
        
        print("\n🔧 DISTRIBUCIÓN DE EQUIPOS:")
        for ubicacion, cantidad in equipos_ubicaciones:
            laboratorio_asignado = 'LAB-QUI-001 (Química General)'  # Por defecto
            
            if ubicacion:
                for key, lab in mapeo.items():
                    if key.lower() in ubicacion.lower():
                        laboratorio_asignado = lab
                        break
            
            print(f"  📍 {ubicacion or 'Sin ubicación'}: {cantidad} equipos → {laboratorio_asignado}")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error en simulación: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def generar_instrucciones():
    """Generar instrucciones para el administrador"""
    print("\n📋 INSTRUCCIONES PARA EL ADMINISTRADOR")
    print("=" * 60)
    print("""
🔑 OPCIÓN 1: Ejecutar como administrador de MySQL
   1. Conectarse como root o administrador:
      mysql -u root -p laboratorio_sistema
   
   2. Ejecutar el archivo SQL:
      SOURCE migracion_laboratorios.sql;

🔑 OPCIÓN 2: Otorgar permisos al usuario actual
   1. Como administrador, ejecutar:
      GRANT CREATE, ALTER, INDEX, REFERENCES ON laboratorio_sistema.* TO 'laboratorio_prod'@'localhost';
      FLUSH PRIVILEGES;
   
   2. Luego ejecutar:
      py -3.11 migracion_laboratorios.py

🔑 OPCIÓN 3: Modificación manual paso a paso
   1. Crear tabla laboratorios (como admin)
   2. Agregar columnas laboratorio_id a inventario y equipos
   3. Ejecutar script de migración de datos

📧 CONTACTAR AL ADMINISTRADOR DE BASE DE DATOS
   - Solicitar permisos CREATE, ALTER, INDEX, REFERENCES
   - O solicitar ejecución del archivo migracion_laboratorios.sql
   - Explicar que es para reorganizar inventarios por laboratorios
""")

def main():
    """Función principal"""
    print("🏗️ MIGRACIÓN SISTEMA DE LABORATORIOS - CENTRO MINERO SENA")
    print("=" * 60)
    print("⚠️  MODO PERMISOS LIMITADOS")
    print()
    
    # Verificar permisos
    estado = verificar_permisos()
    
    if not estado:
        print("\n❌ No se pudo verificar el estado de la base de datos")
        return
    
    # Intentar crear datos temporales
    if not estado['tabla_laboratorios']:
        print("\n⚠️ Tabla 'laboratorios' no existe")
        crear_laboratorios_temporales()
    else:
        print("\n✅ Tabla 'laboratorios' ya existe")
    
    # Simular asignaciones
    simular_asignacion_laboratorios()
    
    # Generar instrucciones
    generar_instrucciones()
    
    print(f"\n✅ Análisis completado - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🎯 PRÓXIMOS PASOS:")
    print("   1. Contactar al administrador de BD")
    print("   2. Ejecutar migracion_laboratorios.sql como admin")
    print("   3. Reiniciar el servidor web")
    print("   4. Probar la nueva funcionalidad de laboratorios")

if __name__ == "__main__":
    main()
