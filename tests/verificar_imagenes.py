#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
print("VERIFICANDO IMAGENES DE OBJETOS")
print("=" * 70)

conn = mysql.connector.connect(**config)
cursor = conn.cursor(dictionary=True)

# Ver todos los objetos
print("\n[OBJETOS REGISTRADOS]:")
cursor.execute("SELECT id, nombre, categoria FROM objetos ORDER BY id")
objetos = cursor.fetchall()
for obj in objetos:
    print(f"  ID: {obj['id']} - {obj['nombre']} ({obj['categoria'] or 'Sin categoría'})")

# Ver todas las imágenes
print("\n[IMAGENES REGISTRADAS]:")
cursor.execute("SELECT id, objeto_id, vista, path FROM objetos_imagenes ORDER BY objeto_id, id")
imagenes = cursor.fetchall()
if imagenes:
    for img in imagenes:
        print(f"  Imagen ID: {img['id']} - Objeto ID: {img['objeto_id']} - Vista: {img['vista']} - Path: {img['path']}")
else:
    print("  No hay imágenes registradas en la base de datos")

# Contar imágenes por objeto
print("\n[RESUMEN POR OBJETO]:")
cursor.execute("""
    SELECT o.id, o.nombre, COUNT(oi.id) as total_imagenes
    FROM objetos o
    LEFT JOIN objetos_imagenes oi ON o.id = oi.objeto_id
    GROUP BY o.id, o.nombre
    ORDER BY o.id
""")
resumen = cursor.fetchall()
for r in resumen:
    print(f"  {r['nombre']} (ID: {r['id']}): {r['total_imagenes']} imágenes")

cursor.close()
conn.close()

print("\n" + "=" * 70)
