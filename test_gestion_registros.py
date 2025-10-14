# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la funcionalidad de gestión de registros
Verifica estructura de tablas y operaciones CRUD
"""

import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime

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

def get_connection():
    """Obtener conexión a la base de datos"""
    return mysql.connector.connect(**DB_CONFIG)

def print_section(title):
    """Imprimir sección con formato"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_table_structure():
    """Verificar estructura de tablas equipos e inventario"""
    print_section("1. VERIFICACIÓN DE ESTRUCTURA DE TABLAS")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verificar tabla equipos
    print("\n📋 Tabla: EQUIPOS")
    cursor.execute("DESCRIBE equipos")
    equipos_columns = cursor.fetchall()
    
    print(f"{'Campo':<25} {'Tipo':<20} {'Null':<10} {'Key':<10}")
    print("-" * 70)
    for col in equipos_columns:
        print(f"{col['Field']:<25} {col['Type']:<20} {col['Null']:<10} {col['Key']:<10}")
    
    # Verificar tabla inventario
    print("\n📋 Tabla: INVENTARIO")
    cursor.execute("DESCRIBE inventario")
    inventario_columns = cursor.fetchall()
    
    print(f"{'Campo':<25} {'Tipo':<20} {'Null':<10} {'Key':<10}")
    print("-" * 70)
    for col in inventario_columns:
        print(f"{col['Field']:<25} {col['Type']:<20} {col['Null']:<10} {col['Key']:<10}")
    
    cursor.close()
    conn.close()
    
    return equipos_columns, inventario_columns

def test_list_registros():
    """Probar listado de registros"""
    print_section("2. PRUEBA: LISTAR REGISTROS")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Listar equipos
    print("\n🔧 EQUIPOS:")
    query_equipos = """
        SELECT e.id, e.nombre, e.tipo, e.estado, e.ubicacion, 
               l.nombre as laboratorio_nombre, e.laboratorio_id
        FROM equipos e
        LEFT JOIN laboratorios l ON e.laboratorio_id = l.id
        LIMIT 5
    """
    cursor.execute(query_equipos)
    equipos = cursor.fetchall()
    
    if equipos:
        print(f"✅ Se encontraron {len(equipos)} equipos (mostrando primeros 5)")
        for eq in equipos:
            print(f"   - ID: {eq['id']}, Nombre: {eq['nombre']}, Tipo: {eq['tipo']}, Estado: {eq['estado']}")
    else:
        print("⚠️  No hay equipos registrados")
    
    # Listar items
    print("\n📦 ITEMS DE INVENTARIO:")
    query_items = """
        SELECT i.id, i.nombre, i.categoria, i.cantidad_actual, i.ubicacion,
               l.nombre as laboratorio_nombre, i.laboratorio_id
        FROM inventario i
        LEFT JOIN laboratorios l ON i.laboratorio_id = l.id
        LIMIT 5
    """
    cursor.execute(query_items)
    items = cursor.fetchall()
    
    if items:
        print(f"✅ Se encontraron {len(items)} items (mostrando primeros 5)")
        for item in items:
            print(f"   - ID: {item['id']}, Nombre: {item['nombre']}, Categoría: {item['categoria']}, Stock: {item['cantidad_actual']}")
    else:
        print("⚠️  No hay items registrados")
    
    cursor.close()
    conn.close()
    
    return equipos, items

def test_get_detalle(tipo, id_registro):
    """Probar obtención de detalles de un registro"""
    print_section(f"3. PRUEBA: OBTENER DETALLE ({tipo.upper()})")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    if tipo == 'equipo':
        query = """
            SELECT e.*, l.nombre as laboratorio_nombre, o.id as objeto_id
            FROM equipos e
            LEFT JOIN laboratorios l ON e.laboratorio_id = l.id
            LEFT JOIN objetos o ON e.objeto_id = o.id
            WHERE e.id = %s
        """
    else:
        query = """
            SELECT i.*, l.nombre as laboratorio_nombre
            FROM inventario i
            LEFT JOIN laboratorios l ON i.laboratorio_id = l.id
            WHERE i.id = %s
        """
    
    try:
        cursor.execute(query, (id_registro,))
        registro = cursor.fetchone()
        
        if registro:
            print(f"✅ Registro encontrado: {id_registro}")
            print(f"\n📄 Detalles:")
            for key, value in registro.items():
                if value is not None:
                    print(f"   {key}: {value}")
            return True
        else:
            print(f"❌ Registro no encontrado: {id_registro}")
            return False
    except Exception as e:
        print(f"❌ Error al obtener detalle: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def test_update_registro(tipo, id_registro, datos_prueba):
    """Probar actualización de un registro"""
    print_section(f"4. PRUEBA: ACTUALIZAR REGISTRO ({tipo.upper()})")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if tipo == 'equipo':
            query = """
                UPDATE equipos 
                SET nombre = %s, tipo = %s, ubicacion = %s, estado = %s
                WHERE id = %s
            """
            params = (
                datos_prueba.get('nombre'),
                datos_prueba.get('tipo'),
                datos_prueba.get('ubicacion'),
                datos_prueba.get('estado'),
                id_registro
            )
        else:
            query = """
                UPDATE inventario 
                SET nombre = %s, categoria = %s, ubicacion = %s, cantidad_actual = %s
                WHERE id = %s
            """
            params = (
                datos_prueba.get('nombre'),
                datos_prueba.get('categoria'),
                datos_prueba.get('ubicacion'),
                datos_prueba.get('cantidad_actual'),
                id_registro
            )
        
        print(f"\n🔄 Intentando actualizar registro: {id_registro}")
        print(f"   Datos: {datos_prueba}")
        
        cursor.execute(query, params)
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ Registro actualizado exitosamente")
            return True
        else:
            print(f"⚠️  No se actualizó ningún registro (puede que no exista)")
            return False
            
    except Exception as e:
        print(f"❌ Error al actualizar: {str(e)}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def test_compatibility_queries():
    """Verificar compatibilidad de consultas con la estructura actual"""
    print_section("5. PRUEBA: COMPATIBILIDAD DE CONSULTAS")
    
    tests = [
        {
            'name': 'SELECT equipos con tipo',
            'query': 'SELECT id, nombre, tipo, estado FROM equipos LIMIT 1',
            'expected_columns': ['id', 'nombre', 'tipo', 'estado']
        },
        {
            'name': 'SELECT inventario con categoria',
            'query': 'SELECT id, nombre, categoria, cantidad_actual FROM inventario LIMIT 1',
            'expected_columns': ['id', 'nombre', 'categoria', 'cantidad_actual']
        },
        {
            'name': 'UPDATE equipos - verificar columnas',
            'query': 'SELECT id, nombre, tipo, descripcion, ubicacion, estado, laboratorio_id FROM equipos LIMIT 0',
            'expected_columns': ['id', 'nombre', 'tipo', 'descripcion', 'ubicacion', 'estado', 'laboratorio_id']
        },
        {
            'name': 'UPDATE inventario - verificar columnas',
            'query': 'SELECT id, nombre, categoria, descripcion, ubicacion, cantidad_actual, laboratorio_id FROM inventario LIMIT 0',
            'expected_columns': ['id', 'nombre', 'categoria', 'descripcion', 'ubicacion', 'cantidad_actual', 'laboratorio_id']
        }
    ]
    
    all_passed = True
    
    for test in tests:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute(test['query'])
            # Consumir todos los resultados
            cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            missing = [col for col in test['expected_columns'] if col not in columns]
            
            if missing:
                print(f"❌ {test['name']}: Faltan columnas: {missing}")
                all_passed = False
            else:
                print(f"✅ {test['name']}: OK")
                
        except Exception as e:
            print(f"❌ {test['name']}: Error - {str(e)}")
            all_passed = False
        finally:
            cursor.close()
            conn.close()
    
    return all_passed

def run_all_tests():
    """Ejecutar todas las pruebas"""
    print("\n" + "🧪 " * 30)
    print("  SCRIPT DE PRUEBA - GESTIÓN DE REGISTROS")
    print("  Centro Minero SENA")
    print("🧪 " * 30)
    
    try:
        # Test 1: Estructura de tablas
        equipos_cols, inventario_cols = test_table_structure()
        
        # Test 2: Listar registros
        equipos, items = test_list_registros()
        
        # Test 3: Obtener detalle (si hay registros)
        if equipos:
            test_get_detalle('equipo', equipos[0]['id'])
        
        if items:
            test_get_detalle('item', items[0]['id'])
        
        # Test 4: Actualizar registro (simulación sin cambios reales)
        if equipos:
            print_section("4. PRUEBA: SIMULACIÓN DE ACTUALIZACIÓN")
            print("\n⚠️  Nota: Esta es una simulación. No se realizarán cambios reales.")
            print("   Para probar actualizaciones reales, descomenta el código en el script.")
            
            # Datos de prueba
            datos_equipo = {
                'nombre': equipos[0]['nombre'],
                'tipo': equipos[0]['tipo'],
                'ubicacion': equipos[0]['ubicacion'],
                'estado': equipos[0]['estado']
            }
            print(f"\n   Datos que se enviarían para equipo {equipos[0]['id']}:")
            for key, value in datos_equipo.items():
                print(f"      {key}: {value}")
        
        # Test 5: Compatibilidad de consultas
        test_compatibility_queries()
        
        # Resumen final
        print_section("RESUMEN DE PRUEBAS")
        print("\n✅ Todas las pruebas completadas")
        print("\n📝 RECOMENDACIONES:")
        print("   1. Verificar que las columnas coincidan con las consultas del backend")
        print("   2. Usar 'tipo' para equipos y 'categoria' para inventario")
        print("   3. Usar 'cantidad_actual' en lugar de 'stock_actual' para inventario")
        print("   4. No usar columna 'descripcion' (no existe en las tablas)")
        
    except Exception as e:
        print(f"\n❌ Error general en las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
