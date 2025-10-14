#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verificar estructura de tabla equipos"""

import mysql.connector
import os

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'laboratorio_sistema',
    'charset': 'utf8mb4',
}

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    print("="*70)
    print("ESTRUCTURA DE TABLA: equipos")
    print("="*70)
    
    cursor.execute("DESCRIBE equipos")
    columns = cursor.fetchall()
    
    print(f"\n{'Campo':<25} {'Tipo':<20} {'Null':<8} {'Key':<8} {'Default':<15}")
    print("-"*70)
    
    for col in columns:
        print(f"{col['Field']:<25} {col['Type']:<20} {col['Null']:<8} {col['Key']:<8} {str(col['Default']):<15}")
    
    print("\n" + "="*70)
    print("FOREIGN KEYS en equipos")
    print("="*70)
    
    cursor.execute("""
        SELECT 
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = 'laboratorio_sistema'
        AND TABLE_NAME = 'equipos'
        AND REFERENCED_TABLE_NAME IS NOT NULL
    """)
    
    fks = cursor.fetchall()
    if fks:
        for fk in fks:
            print(f"{fk['COLUMN_NAME']} → {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}")
    else:
        print("No hay foreign keys")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
