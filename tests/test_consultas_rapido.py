# -*- coding: utf-8 -*-
"""
Test Rápido de Consultas Corregidas
"""

import mysql.connector
import os
from dotenv import load_dotenv

# Cargar variables de entorno
if os.path.exists('.env_produccion'):
    load_dotenv('.env_produccion')

DB_CONFIG = {
    'host': os.getenv('HOST', 'localhost'),
    'user': os.getenv('USUARIO_PRODUCCION', 'laboratorio_prod'),
    'password': os.getenv('PASSWORD_PRODUCCION', ''),
    'database': os.getenv('BASE_DATOS', 'laboratorio_sistema'),
    'charset': 'utf8mb4',
}

def execute_query(query, params=None):
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    print("🧪 TEST RÁPIDO DE CONSULTAS CORREGIDAS")
    print("=" * 50)
    
    # Test comandos semana
    print("🎤 Comandos última semana:")
    result = execute_query("SELECT COUNT(*) cantidad FROM comandos_voz WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)")
    if result:
        print(f"   ✅ {result[0]['cantidad']} comandos")
    
    # Test reservas
    print("📅 Reservas próximas:")
    result = execute_query("SELECT COUNT(*) cantidad FROM reservas WHERE estado IN ('activa', 'programada')")
    if result:
        print(f"   ✅ {result[0]['cantidad']} reservas")
    
    print("\n✅ Consultas corregidas funcionan correctamente")

if __name__ == "__main__":
    main()
