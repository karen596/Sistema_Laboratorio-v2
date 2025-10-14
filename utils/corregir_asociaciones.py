#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para corregir las asociaciones de imágenes a objetos
basándose en el nombre de la carpeta donde están guardadas
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
print("CORRIGIENDO ASOCIACIONES DE IMAGENES")
print("=" * 70)

conn = mysql.connector.connect(**config)
cursor = conn.cursor(dictionary=True)

# Obtener todos los objetos
cursor.execute("SELECT id, nombre FROM objetos")
objetos = {obj['nombre'].lower(): obj['id'] for obj in cursor.fetchall()}

print(f"\n[OBJETOS ENCONTRADOS]: {len(objetos)}")
for nombre, obj_id in objetos.items():
    print(f"  {nombre} -> ID: {obj_id}")

# Obtener todas las imágenes
cursor.execute("SELECT id, objeto_id, path FROM objetos_imagenes")
imagenes = cursor.fetchall()

print(f"\n[PROCESANDO {len(imagenes)} IMAGENES]:")

correcciones = 0
for img in imagenes:
    path = img['path']
    objeto_id_actual = img['objeto_id']
    
    # Extraer el nombre del objeto del path
    # Formato: imagenes/objetos/NombreObjeto/vista/archivo.jpg
    # o: imagenes/equipos/NombreObjeto/vista/archivo.jpg
    partes = path.split('/')
    if len(partes) >= 3:
        nombre_carpeta = partes[2].lower()  # Obtener el nombre de la carpeta
        
        # Buscar el ID correcto basado en el nombre de la carpeta
        objeto_id_correcto = None
        for nombre_obj, obj_id in objetos.items():
            if nombre_obj in nombre_carpeta or nombre_carpeta in nombre_obj:
                objeto_id_correcto = obj_id
                break
        
        if objeto_id_correcto and objeto_id_correcto != objeto_id_actual:
            print(f"  ✓ Corrigiendo imagen {img['id']}: {path}")
            print(f"    Objeto actual: {objeto_id_actual} -> Objeto correcto: {objeto_id_correcto}")
            
            # Actualizar la asociación
            cursor.execute(
                "UPDATE objetos_imagenes SET objeto_id = %s WHERE id = %s",
                (objeto_id_correcto, img['id'])
            )
            correcciones += 1

conn.commit()

print(f"\n[RESULTADO]:")
print(f"  Total de correcciones: {correcciones}")

# Mostrar resumen actualizado
print("\n[RESUMEN ACTUALIZADO]:")
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
print("¡Corrección completada!")
print("=" * 70)
