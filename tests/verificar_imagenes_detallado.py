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

print("=" * 80)
print("ANALISIS DETALLADO DE IMAGENES")
print("=" * 80)

conn = mysql.connector.connect(**config)
cursor = conn.cursor(dictionary=True)

# Ver todas las imágenes con detalles
print("\n[TODAS LAS IMAGENES EN LA BASE DE DATOS]:")
cursor.execute("""
    SELECT oi.id, oi.objeto_id, o.nombre as objeto_nombre, oi.vista, oi.path 
    FROM objetos_imagenes oi
    JOIN objetos o ON oi.objeto_id = o.id
    ORDER BY oi.id
""")
imagenes = cursor.fetchall()

for img in imagenes:
    # Extraer nombre de carpeta del path
    partes = img['path'].split('/')
    carpeta_tipo = partes[1] if len(partes) > 1 else '?'  # objetos o equipos
    carpeta_nombre = partes[2] if len(partes) > 2 else '?'  # nombre del objeto
    
    print(f"\nImagen ID: {img['id']}")
    print(f"  Asociada a: {img['objeto_nombre']} (ID: {img['objeto_id']})")
    print(f"  Vista: {img['vista']}")
    print(f"  Path: {img['path']}")
    print(f"  Carpeta tipo: {carpeta_tipo}")
    print(f"  Carpeta nombre: {carpeta_nombre}")
    
    # Verificar si el archivo existe
    if os.path.exists(img['path']):
        print(f"  ✓ Archivo existe")
    else:
        print(f"  ✗ Archivo NO existe")

# Resumen por objeto
print("\n" + "=" * 80)
print("[RESUMEN POR OBJETO]:")
cursor.execute("""
    SELECT o.id, o.nombre, o.categoria, COUNT(oi.id) as total_imagenes
    FROM objetos o
    LEFT JOIN objetos_imagenes oi ON o.id = oi.objeto_id
    GROUP BY o.id, o.nombre, o.categoria
    ORDER BY o.id
""")
resumen = cursor.fetchall()
for r in resumen:
    print(f"  {r['nombre']} (ID: {r['id']}, Categoría: {r['categoria']}): {r['total_imagenes']} imágenes")

# Agrupar por carpeta
print("\n" + "=" * 80)
print("[IMAGENES AGRUPADAS POR CARPETA]:")
cursor.execute("SELECT path FROM objetos_imagenes ORDER BY path")
paths = [row['path'] for row in cursor.fetchall()]

carpetas = {}
for path in paths:
    partes = path.split('/')
    if len(partes) >= 3:
        carpeta_key = f"{partes[1]}/{partes[2]}"  # ej: "objetos/Betun"
        if carpeta_key not in carpetas:
            carpetas[carpeta_key] = []
        carpetas[carpeta_key].append(path)

for carpeta, imgs in sorted(carpetas.items()):
    print(f"\n{carpeta}: {len(imgs)} imágenes")
    for img in imgs:
        print(f"  - {img}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
