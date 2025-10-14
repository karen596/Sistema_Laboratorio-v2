#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificar estructura de tablas
"""

import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv('.env_produccion')

config = {
    'host': os.getenv('HOST', 'localhost'),
    'user': os.getenv('USUARIO_PRODUCCION', 'root'),
    'password': os.getenv('PASSWORD_PRODUCCION', ''),
    'database': os.getenv('BASE_DATOS', 'laboratorio_sistema')
}

print("=" * 70)
print("VERIFICANDO ESTRUCTURA DE TABLAS")
print("=" * 70)

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

print("\n[TABLA: objetos]")
cursor.execute("DESCRIBE objetos")
for row in cursor.fetchall():
    print(f"  - {row[0]}: {row[1]}")

print("\n[TABLA: objetos_imagenes]")
cursor.execute("DESCRIBE objetos_imagenes")
for row in cursor.fetchall():
    print(f"  - {row[0]}: {row[1]}")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("VERIFICACION COMPLETADA")
print("=" * 70)
