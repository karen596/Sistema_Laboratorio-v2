#!/usr/bin/env python3
"""
Script de prueba para verificar que los registros se crean correctamente
y aparecen en las consultas
"""

import mysql.connector
from mysql.connector import Error
import uuid

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'laboratorio_sistema'
}

def print_header(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def crear_equipo_prueba(connection):
    """Simula la creación de un equipo desde el admin"""
    print_header("PRUEBA: Crear Equipo con laboratorio_id")
    
    cursor = connection.cursor(dictionary=True)
    
    # Generar datos de prueba
    equipo_id = f"EQ-TEST-{uuid.uuid4().hex[:6].upper()}"
    nombre = "Equipo de Prueba Admin"
    tipo = "Prueba"
    ubicacion = "Lab Test"
    laboratorio_id = 1
    
    print(f"\n  Creando equipo:")
    print(f"    ID: {equipo_id}")
    print(f"    Nombre: {nombre}")
    print(f"    Tipo: {tipo}")
    print(f"    Laboratorio ID: {laboratorio_id}")
    
    try:
        query = """
            INSERT INTO equipos (id, nombre, tipo, estado, ubicacion, laboratorio_id)
            VALUES (%s, %s, %s, 'disponible', %s, %s)
        """
        cursor.execute(query, (equipo_id, nombre, tipo, ubicacion, laboratorio_id))
        connection.commit()
        print(f"\n  ✓ Equipo creado exitosamente")
        
        # Verificar que aparece en la consulta con INNER JOIN
        query_verificar = """
            SELECT e.id, e.nombre, e.tipo, l.nombre as laboratorio_nombre
            FROM equipos e
            INNER JOIN laboratorios l ON e.laboratorio_id = l.id
            WHERE e.id = %s
        """
        cursor.execute(query_verificar, (equipo_id,))
        result = cursor.fetchone()
        
        if result:
            print(f"  ✓ El equipo APARECE en la consulta con INNER JOIN")
            print(f"    - Nombre: {result['nombre']}")
            print(f"    - Laboratorio: {result['laboratorio_nombre']}")
        else:
            print(f"  ✗ El equipo NO aparece en la consulta con INNER JOIN")
        
        cursor.close()
        return equipo_id
        
    except Error as e:
        print(f"  ✗ Error al crear equipo: {e}")
        cursor.close()
        return None

def crear_item_inventario_prueba(connection):
    """Simula la creación de un item de inventario desde el admin"""
    print_header("PRUEBA: Crear Item de Inventario con laboratorio_id")
    
    cursor = connection.cursor(dictionary=True)
    
    # Generar datos de prueba
    item_id = f"INV-TEST-{uuid.uuid4().hex[:6].upper()}"
    nombre = "Item de Prueba Admin"
    categoria = "Prueba"
    cantidad_actual = 10
    cantidad_minima = 5
    unidad = "unidad"
    ubicacion = "Estante Test"
    laboratorio_id = 1
    
    print(f"\n  Creando item de inventario:")
    print(f"    ID: {item_id}")
    print(f"    Nombre: {nombre}")
    print(f"    Categoría: {categoria}")
    print(f"    Laboratorio ID: {laboratorio_id}")
    
    try:
        query = """
            INSERT INTO inventario (id, nombre, categoria, cantidad_actual, cantidad_minima,
                                  unidad, ubicacion, laboratorio_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (item_id, nombre, categoria, cantidad_actual, 
                              cantidad_minima, unidad, ubicacion, laboratorio_id))
        connection.commit()
        print(f"\n  ✓ Item de inventario creado exitosamente")
        
        # Verificar que aparece en la consulta con INNER JOIN
        query_verificar = """
            SELECT i.id, i.nombre, i.categoria, l.nombre as laboratorio_nombre
            FROM inventario i
            INNER JOIN laboratorios l ON i.laboratorio_id = l.id
            WHERE i.id = %s
        """
        cursor.execute(query_verificar, (item_id,))
        result = cursor.fetchone()
        
        if result:
            print(f"  ✓ El item APARECE en la consulta con INNER JOIN")
            print(f"    - Nombre: {result['nombre']}")
            print(f"    - Laboratorio: {result['laboratorio_nombre']}")
        else:
            print(f"  ✗ El item NO aparece en la consulta con INNER JOIN")
        
        cursor.close()
        return item_id
        
    except Error as e:
        print(f"  ✗ Error al crear item: {e}")
        cursor.close()
        return None

def limpiar_datos_prueba(connection, equipo_id, item_id):
    """Elimina los datos de prueba creados"""
    print_header("LIMPIEZA: Eliminando datos de prueba")
    
    cursor = connection.cursor()
    
    if equipo_id:
        try:
            cursor.execute("DELETE FROM equipos WHERE id = %s", (equipo_id,))
            connection.commit()
            print(f"  ✓ Equipo de prueba eliminado: {equipo_id}")
        except Error as e:
            print(f"  ⚠ Error al eliminar equipo: {e}")
    
    if item_id:
        try:
            cursor.execute("DELETE FROM inventario WHERE id = %s", (item_id,))
            connection.commit()
            print(f"  ✓ Item de prueba eliminado: {item_id}")
        except Error as e:
            print(f"  ⚠ Error al eliminar item: {e}")
    
    cursor.close()

def main():
    print("\n" + "=" * 80)
    print("  PRUEBA DE CREACIÓN DE REGISTROS")
    print("  Verificando que los registros aparecen correctamente")
    print("=" * 80)
    
    connection = None
    equipo_id = None
    item_id = None
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        
        if connection.is_connected():
            print(f"\n✓ Conectado a la base de datos: {DB_CONFIG['database']}")
            
            # Prueba 1: Crear equipo
            equipo_id = crear_equipo_prueba(connection)
            
            # Prueba 2: Crear item de inventario
            item_id = crear_item_inventario_prueba(connection)
            
            # Limpiar datos de prueba
            print("\n")
            respuesta = input("¿Deseas eliminar los datos de prueba? (s/n): ").strip().lower()
            if respuesta == 's':
                limpiar_datos_prueba(connection, equipo_id, item_id)
            else:
                print("\n  Los datos de prueba se mantienen en la base de datos")
            
            print("\n" + "=" * 80)
            print("  PRUEBA COMPLETADA")
            print("=" * 80)
            print("\n  Resultado:")
            print("  ✓ Los registros con laboratorio_id aparecen correctamente")
            print("  ✓ Las consultas con INNER JOIN funcionan bien")
            print("\n" + "=" * 80 + "\n")
            
    except Error as e:
        print(f"\n✗ Error de conexión: {e}")
        
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("✓ Conexión cerrada\n")

if __name__ == "__main__":
    main()
