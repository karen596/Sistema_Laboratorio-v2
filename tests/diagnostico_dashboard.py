# -*- coding: utf-8 -*-
"""
Diagnóstico del Dashboard - Centro Minero SENA
Verificar por qué no se actualizan las estadísticas
"""

import mysql.connector
import os
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

def execute_query(query, params=None):
    """Ejecutar consulta y manejar errores"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if query.strip().upper().startswith('SELECT'):
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount
        
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"❌ Error en consulta: {e}")
        print(f"📋 Query: {query}")
        return None

def verificar_tablas():
    """Verificar que existan las tablas necesarias"""
    print("🔍 VERIFICANDO TABLAS NECESARIAS")
    print("=" * 50)
    
    tablas_necesarias = ['equipos', 'inventario', 'reservas', 'comandos_voz', 'usuarios']
    
    for tabla in tablas_necesarias:
        try:
            result = execute_query(f"SELECT COUNT(*) as total FROM {tabla}")
            if result:
                print(f"✅ {tabla}: {result[0]['total']} registros")
            else:
                print(f"❌ {tabla}: Error al consultar")
        except Exception as e:
            print(f"❌ {tabla}: No existe o error - {e}")

def verificar_estadisticas_dashboard():
    """Verificar las consultas específicas del dashboard"""
    print("\n📊 VERIFICANDO ESTADÍSTICAS DEL DASHBOARD")
    print("=" * 50)
    
    # 1. Equipos por estado
    print("\n1. 🔧 EQUIPOS POR ESTADO:")
    query = "SELECT estado, COUNT(*) cantidad FROM equipos GROUP BY estado"
    result = execute_query(query)
    if result:
        for row in result:
            print(f"   {row['estado']}: {row['cantidad']}")
    else:
        print("   ❌ No se pudieron obtener datos de equipos")
    
    # 2. Inventario crítico
    print("\n2. 📦 INVENTARIO CRÍTICO:")
    query = "SELECT COUNT(*) cantidad FROM inventario WHERE cantidad_actual <= cantidad_minima"
    result = execute_query(query)
    if result:
        print(f"   Items críticos: {result[0]['cantidad']}")
    else:
        print("   ❌ No se pudieron obtener datos de inventario")
    
    # 3. Reservas activas
    print("\n3. 📅 RESERVAS ACTIVAS:")
    query = "SELECT COUNT(*) cantidad FROM reservas WHERE estado = 'activa'"
    result = execute_query(query)
    if result:
        print(f"   Reservas activas: {result[0]['cantidad']}")
    else:
        print("   ❌ No se pudieron obtener datos de reservas")
    
    # 4. Comandos de voz hoy
    print("\n4. 🎤 COMANDOS DE VOZ HOY:")
    query = "SELECT COUNT(*) cantidad FROM comandos_voz WHERE DATE(fecha) = CURDATE()"
    result = execute_query(query)
    if result:
        print(f"   Comandos hoy: {result[0]['cantidad']}")
    else:
        print("   ❌ No se pudieron obtener datos de comandos de voz")
        
        # Verificar si existe la tabla comandos_voz
        print("   🔍 Verificando tabla comandos_voz...")
        check_query = "SHOW TABLES LIKE 'comandos_voz'"
        check_result = execute_query(check_query)
        if not check_result:
            print("   ⚠️ La tabla 'comandos_voz' no existe")

def verificar_estructura_tablas():
    """Verificar la estructura de las tablas"""
    print("\n🏗️ VERIFICANDO ESTRUCTURA DE TABLAS")
    print("=" * 50)
    
    tablas = ['equipos', 'inventario', 'reservas']
    
    for tabla in tablas:
        print(f"\n📋 Estructura de {tabla}:")
        query = f"DESCRIBE {tabla}"
        result = execute_query(query)
        if result:
            for field in result:
                print(f"   {field['Field']}: {field['Type']}")
        else:
            print(f"   ❌ No se pudo obtener estructura de {tabla}")

def crear_datos_prueba():
    """Crear algunos datos de prueba si las tablas están vacías"""
    print("\n🧪 CREANDO DATOS DE PRUEBA")
    print("=" * 50)
    
    # Verificar si hay datos en equipos
    equipos_count = execute_query("SELECT COUNT(*) as total FROM equipos")
    if equipos_count and equipos_count[0]['total'] == 0:
        print("📝 Creando equipos de prueba...")
        queries = [
            "INSERT INTO equipos (id, nombre, tipo, estado, laboratorio_id) VALUES ('EQ001', 'Microscopio 1', 'optico', 'disponible', 1)",
            "INSERT INTO equipos (id, nombre, tipo, estado, laboratorio_id) VALUES ('EQ002', 'Centrifuga 1', 'mecanico', 'mantenimiento', 1)",
            "INSERT INTO equipos (id, nombre, tipo, estado, laboratorio_id) VALUES ('EQ003', 'Balanza 1', 'precision', 'disponible', 2)"
        ]
        for query in queries:
            execute_query(query)
    
    # Verificar inventario
    inventario_count = execute_query("SELECT COUNT(*) as total FROM inventario")
    if inventario_count and inventario_count[0]['total'] == 0:
        print("📝 Creando items de inventario de prueba...")
        queries = [
            "INSERT INTO inventario (nombre, categoria, cantidad_actual, cantidad_minima, unidad, laboratorio_id) VALUES ('Reactivo A', 'quimico', 5, 10, 'ml', 1)",
            "INSERT INTO inventario (nombre, categoria, cantidad_actual, cantidad_minima, unidad, laboratorio_id) VALUES ('Reactivo B', 'quimico', 15, 20, 'ml', 1)"
        ]
        for query in queries:
            execute_query(query)

def main():
    """Función principal"""
    print("🚀 DIAGNÓSTICO DEL DASHBOARD - CENTRO MINERO SENA")
    print("=" * 60)
    
    verificar_tablas()
    verificar_estadisticas_dashboard()
    verificar_estructura_tablas()
    
    print("\n💡 RECOMENDACIONES:")
    print("=" * 50)
    print("1. Si alguna tabla no existe, ejecuta las migraciones correspondientes")
    print("2. Si las tablas están vacías, agrega datos de prueba")
    print("3. Verifica que los nombres de campos coincidan con las consultas")
    print("4. Si 'comandos_voz' no existe, es normal (funcionalidad opcional)")

if __name__ == "__main__":
    main()
