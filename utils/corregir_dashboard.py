# -*- coding: utf-8 -*-
"""
Corrección del Dashboard - Centro Minero SENA
Verificar y corregir las consultas de estadísticas
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
    """Ejecutar consulta con manejo correcto de conexiones"""
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if query.strip().upper().startswith('SELECT'):
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount
        
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def verificar_estados_reservas():
    """Verificar los estados de las reservas"""
    print("📅 VERIFICANDO ESTADOS DE RESERVAS:")
    print("-" * 40)
    
    # Ver todos los estados de reservas
    query = "SELECT estado, COUNT(*) as cantidad FROM reservas GROUP BY estado"
    result = execute_query(query)
    
    if result:
        for row in result:
            print(f"   Estado '{row['estado']}': {row['cantidad']} reservas")
    
    # Ver detalles de las reservas
    query = "SELECT id, usuario_id, equipo_id, estado, fecha_inicio, fecha_fin FROM reservas LIMIT 5"
    result = execute_query(query)
    
    if result:
        print("\n📋 Detalles de reservas:")
        for row in result:
            print(f"   ID: {row['id']}, Estado: {row['estado']}, Usuario: {row['usuario_id']}")

def verificar_inventario_critico():
    """Verificar por qué no aparece inventario crítico"""
    print("\n📦 VERIFICANDO INVENTARIO CRÍTICO:")
    print("-" * 40)
    
    # Ver todos los items con sus cantidades
    query = """
        SELECT nombre, cantidad_actual, cantidad_minima, 
               (cantidad_actual <= cantidad_minima) as es_critico
        FROM inventario 
        ORDER BY (cantidad_actual - cantidad_minima)
        LIMIT 10
    """
    result = execute_query(query)
    
    if result:
        print("📋 Items de inventario:")
        for row in result:
            status = "🔴 CRÍTICO" if row['es_critico'] else "✅ OK"
            print(f"   {row['nombre']}: {row['cantidad_actual']}/{row['cantidad_minima']} {status}")
    
    # Contar críticos
    query = "SELECT COUNT(*) as cantidad FROM inventario WHERE cantidad_actual <= cantidad_minima"
    result = execute_query(query)
    if result:
        print(f"\n📊 Total items críticos: {result[0]['cantidad']}")

def verificar_comandos_voz():
    """Verificar comandos de voz por fecha"""
    print("\n🎤 VERIFICANDO COMANDOS DE VOZ:")
    print("-" * 40)
    
    # Ver comandos por fecha
    query = """
        SELECT DATE(fecha) as fecha, COUNT(*) as cantidad 
        FROM comandos_voz 
        GROUP BY DATE(fecha) 
        ORDER BY fecha DESC 
        LIMIT 7
    """
    result = execute_query(query)
    
    if result:
        print("📋 Comandos por fecha:")
        for row in result:
            print(f"   {row['fecha']}: {row['cantidad']} comandos")
    
    # Ver comandos de hoy
    query = "SELECT COUNT(*) as cantidad FROM comandos_voz WHERE DATE(fecha) = CURDATE()"
    result = execute_query(query)
    if result:
        print(f"\n📊 Comandos hoy: {result[0]['cantidad']}")

def crear_datos_prueba():
    """Crear algunos datos de prueba para el dashboard"""
    print("\n🧪 CREANDO DATOS DE PRUEBA:")
    print("-" * 40)
    
    # Crear items críticos en inventario
    print("📦 Creando items críticos...")
    queries = [
        """
        UPDATE inventario 
        SET cantidad_actual = 2, cantidad_minima = 10 
        WHERE nombre LIKE '%Reactivo%' 
        LIMIT 2
        """,
        """
        INSERT IGNORE INTO inventario 
        (nombre, categoria, cantidad_actual, cantidad_minima, unidad, laboratorio_id) 
        VALUES 
        ('Alcohol Etílico', 'quimico', 50, 100, 'ml', 1),
        ('Papel Filtro', 'material', 5, 20, 'unidad', 1)
        """
    ]
    
    for query in queries:
        result = execute_query(query)
        if result is not None:
            print(f"   ✅ Query ejecutada")
    
    # Crear reserva activa
    print("📅 Creando reserva activa...")
    query = """
        INSERT IGNORE INTO reservas 
        (id, usuario_id, equipo_id, estado, fecha_inicio, fecha_fin, proposito) 
        VALUES 
        ('RES001', 'USR001', 'EQ001', 'activa', NOW(), DATE_ADD(NOW(), INTERVAL 2 HOUR), 'Prueba dashboard')
    """
    result = execute_query(query)
    if result is not None:
        print(f"   ✅ Reserva creada")
    
    # Crear comando de voz de hoy
    print("🎤 Creando comando de voz de hoy...")
    query = """
        INSERT IGNORE INTO comandos_voz 
        (usuario_id, comando, respuesta, exito, fecha) 
        VALUES 
        ('USR001', 'mostrar dashboard', 'Navegando al dashboard', TRUE, NOW())
    """
    result = execute_query(query)
    if result is not None:
        print(f"   ✅ Comando creado")

def verificar_estadisticas_finales():
    """Verificar las estadísticas después de los cambios"""
    print("\n📊 ESTADÍSTICAS FINALES DEL DASHBOARD:")
    print("=" * 50)
    
    # Equipos por estado
    query = "SELECT estado, COUNT(*) cantidad FROM equipos GROUP BY estado"
    result = execute_query(query)
    if result:
        print("🔧 Equipos por estado:")
        for row in result:
            print(f"   {row['estado']}: {row['cantidad']}")
    
    # Inventario crítico
    query = "SELECT COUNT(*) cantidad FROM inventario WHERE cantidad_actual <= cantidad_minima"
    result = execute_query(query)
    if result:
        print(f"📦 Inventario crítico: {result[0]['cantidad']}")
    
    # Reservas activas
    query = "SELECT COUNT(*) cantidad FROM reservas WHERE estado = 'activa'"
    result = execute_query(query)
    if result:
        print(f"📅 Reservas activas: {result[0]['cantidad']}")
    
    # Comandos de hoy
    query = "SELECT COUNT(*) cantidad FROM comandos_voz WHERE DATE(fecha) = CURDATE()"
    result = execute_query(query)
    if result:
        print(f"🎤 Comandos hoy: {result[0]['cantidad']}")

def main():
    """Función principal"""
    print("🔧 CORRECCIÓN DEL DASHBOARD - CENTRO MINERO SENA")
    print("=" * 60)
    
    verificar_estados_reservas()
    verificar_inventario_critico()
    verificar_comandos_voz()
    
    print("\n" + "="*60)
    respuesta = input("¿Quieres crear datos de prueba para el dashboard? (s/n): ")
    
    if respuesta.lower() in ['s', 'si', 'y', 'yes']:
        crear_datos_prueba()
        verificar_estadisticas_finales()
    
    print("\n✅ Diagnóstico completado")
    print("💡 Reinicia el servidor web para ver los cambios")

if __name__ == "__main__":
    main()
