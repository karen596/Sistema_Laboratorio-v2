#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test simple para verificar conexión a BD
"""

import os
import sys
from dotenv import load_dotenv

# Cargar configuración
load_dotenv('.env_produccion')

print("=" * 70)
print("🧪 TEST SIMPLE DE BASE DE DATOS")
print("=" * 70)

try:
    import mysql.connector
    
    config = {
        'host': os.getenv('HOST', 'localhost'),
        'user': os.getenv('USUARIO_PRODUCCION', 'root'),
        'password': os.getenv('PASSWORD_PRODUCCION', ''),
        'database': os.getenv('BASE_DATOS', 'laboratorio_sistema')
    }
    
    print(f"\n📡 Conectando a MySQL...")
    print(f"   Host: {config['host']}")
    print(f"   Usuario: {config['user']}")
    print(f"   Base de datos: {config['database']}")
    
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)
    
    print("✅ Conexión establecida\n")
    
    # Probar INSERT
    print("📝 Probando INSERT en tabla objetos...")
    try:
        cursor.execute(
            "INSERT INTO objetos (nombre, categoria, descripcion) VALUES (%s, %s, %s)",
            ("Test Simple", "Categoria Test", "Descripción de prueba")
        )
        conn.commit()
        print(f"✅ INSERT exitoso, ID: {cursor.lastrowid}")
        
        # Verificar
        cursor.execute("SELECT * FROM objetos WHERE id = %s", (cursor.lastrowid,))
        result = cursor.fetchone()
        print(f"✅ Verificación: {result}")
        
        # Limpiar
        cursor.execute("DELETE FROM objetos WHERE id = %s", (cursor.lastrowid,))
        conn.commit()
        print("✅ Limpieza completada")
        
    except Exception as e:
        print(f"❌ Error en INSERT: {e}")
        import traceback
        traceback.print_exc()
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETADO")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
