# -*- coding: utf-8 -*-
"""
Probar Dashboard Mejorado - Centro Minero SENA
Verificar que las nuevas estadísticas funcionan correctamente
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

def probar_estadisticas_mejoradas():
    """Probar todas las nuevas estadísticas"""
    print("📊 PROBANDO ESTADÍSTICAS MEJORADAS DEL DASHBOARD")
    print("=" * 60)
    
    # Equipos por estado
    print("🔧 EQUIPOS POR ESTADO:")
    eq = execute_query("SELECT estado, COUNT(*) cantidad FROM equipos GROUP BY estado")
    if eq:
        for row in eq:
            print(f"   {row['estado']}: {row['cantidad']}")
    
    # Equipos disponibles
    print("\n⚡ EQUIPOS DISPONIBLES:")
    disp = execute_query("SELECT COUNT(*) cantidad FROM equipos WHERE estado = 'disponible'")
    if disp:
        print(f"   Disponibles: {disp[0]['cantidad']}")
    
    # Items con stock bajo
    print("\n📦 INVENTARIO CON STOCK BAJO (≤ 1.5x mínimo):")
    bajo = execute_query("SELECT COUNT(*) cantidad FROM inventario WHERE cantidad_actual <= (cantidad_minima * 1.5)")
    if bajo:
        print(f"   Stock bajo: {bajo[0]['cantidad']}")
    
    # Items bien abastecidos
    print("\n✅ ITEMS BIEN ABASTECIDOS:")
    bien = execute_query("SELECT COUNT(*) cantidad FROM inventario WHERE cantidad_actual > cantidad_minima")
    if bien:
        print(f"   Bien abastecidos: {bien[0]['cantidad']}")
    
    # Reservas próximas
    print("\n📅 RESERVAS PRÓXIMAS:")
    prox = execute_query("SELECT COUNT(*) cantidad FROM reservas WHERE estado IN ('activa', 'programada') AND fecha_inicio >= CURDATE()")
    if prox:
        print(f"   Próximas: {prox[0]['cantidad']}")
    
    # Comandos última semana
    print("\n🎤 COMANDOS ÚLTIMA SEMANA:")
    sem = execute_query("SELECT COUNT(*) cantidad FROM comandos_voz WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAYS)")
    if sem:
        print(f"   Comandos (7 días): {sem[0]['cantidad']}")
    
    # Usuarios activos semana
    print("\n👥 USUARIOS ACTIVOS (7 días):")
    ua_sem = execute_query("SELECT COUNT(DISTINCT usuario_id) cantidad FROM comandos_voz WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAYS)")
    if ua_sem:
        print(f"   Usuarios activos: {ua_sem[0]['cantidad']}")
    
    # Total laboratorios
    print("\n🏢 TOTAL LABORATORIOS ACTIVOS:")
    labs = execute_query("SELECT COUNT(*) cantidad FROM laboratorios WHERE estado = 'activo'")
    if labs:
        print(f"   Laboratorios: {labs[0]['cantidad']}")
    
    # Total inventario
    print("\n📋 TOTAL ITEMS EN INVENTARIO:")
    total_inv = execute_query("SELECT COUNT(*) cantidad FROM inventario")
    if total_inv:
        print(f"   Total items: {total_inv[0]['cantidad']}")

def main():
    """Función principal"""
    print("🚀 VERIFICACIÓN DEL DASHBOARD MEJORADO")
    print("=" * 60)
    
    probar_estadisticas_mejoradas()
    
    print("\n" + "="*60)
    print("✅ DASHBOARD MEJORADO LISTO")
    print("💡 Reinicia el servidor para ver los cambios:")
    print("   python web_app.py")
    print("🌐 Luego accede a: http://localhost:5000")

if __name__ == "__main__":
    main()
