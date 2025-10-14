# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la funcionalidad de reportes
Verifica endpoints, generación de datos y estadísticas
"""

import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

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

def test_estadisticas_generales():
    """Probar obtención de estadísticas generales"""
    print_section("1. ESTADÍSTICAS GENERALES")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Total de equipos
        cursor.execute("SELECT COUNT(*) as total FROM equipos")
        total_equipos = cursor.fetchone()['total']
        print(f"✅ Total de equipos: {total_equipos}")
        
        # Equipos por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad 
            FROM equipos 
            GROUP BY estado
        """)
        equipos_estado = cursor.fetchall()
        print("\n📊 Equipos por estado:")
        for row in equipos_estado:
            print(f"   - {row['estado']}: {row['cantidad']}")
        
        # Total de items
        cursor.execute("SELECT COUNT(*) as total FROM inventario")
        total_items = cursor.fetchone()['total']
        print(f"\n✅ Total de items en inventario: {total_items}")
        
        # Items con stock bajo
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM inventario 
            WHERE cantidad_actual <= cantidad_minima
        """)
        items_bajo_stock = cursor.fetchone()['total']
        print(f"⚠️  Items con stock bajo: {items_bajo_stock}")
        
        # Total de laboratorios
        cursor.execute("SELECT COUNT(*) as total FROM laboratorios WHERE estado = 'activo'")
        total_labs = cursor.fetchone()['total']
        print(f"\n✅ Total de laboratorios activos: {total_labs}")
        
        # Total de usuarios
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE activo = TRUE")
        total_usuarios = cursor.fetchone()['total']
        print(f"✅ Total de usuarios activos: {total_usuarios}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en estadísticas generales: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def test_reservas_estadisticas():
    """Probar estadísticas de reservas"""
    print_section("2. ESTADÍSTICAS DE RESERVAS")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Total de reservas
        cursor.execute("SELECT COUNT(*) as total FROM reservas")
        total_reservas = cursor.fetchone()['total']
        print(f"✅ Total de reservas: {total_reservas}")
        
        # Reservas por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad 
            FROM reservas 
            GROUP BY estado
        """)
        reservas_estado = cursor.fetchall()
        print("\n📊 Reservas por estado:")
        for row in reservas_estado:
            print(f"   - {row['estado']}: {row['cantidad']}")
        
        # Reservas activas hoy
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM reservas 
            WHERE estado = 'activa' 
            AND DATE(fecha_inicio) <= CURDATE() 
            AND DATE(fecha_fin) >= CURDATE()
        """)
        reservas_hoy = cursor.fetchone()['total']
        print(f"\n✅ Reservas activas hoy: {reservas_hoy}")
        
        # Próximas reservas (próximos 7 días)
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM reservas 
            WHERE estado = 'programada' 
            AND fecha_inicio BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 7 DAY)
        """)
        proximas_reservas = cursor.fetchone()['total']
        print(f"📅 Próximas reservas (7 días): {proximas_reservas}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en estadísticas de reservas: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def test_logs_seguridad():
    """Probar logs de seguridad"""
    print_section("3. LOGS DE SEGURIDAD")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Primero verificar la estructura de la tabla
        cursor.execute("DESCRIBE logs_seguridad")
        columnas = cursor.fetchall()
        columnas_nombres = [col['Field'] for col in columnas]
        print(f"📋 Columnas de logs_seguridad: {', '.join(columnas_nombres)}")
        
        # Determinar el nombre de la columna de fecha
        columna_fecha = None
        for posible in ['timestamp', 'fecha_hora', 'fecha', 'created_at']:
            if posible in columnas_nombres:
                columna_fecha = posible
                break
        
        # Total de logs
        cursor.execute("SELECT COUNT(*) as total FROM logs_seguridad")
        total_logs = cursor.fetchone()['total']
        print(f"\n✅ Total de logs de seguridad: {total_logs}")
        
        # Logs por acción
        cursor.execute("""
            SELECT accion, COUNT(*) as cantidad 
            FROM logs_seguridad 
            GROUP BY accion 
            ORDER BY cantidad DESC 
            LIMIT 5
        """)
        logs_accion = cursor.fetchall()
        print("\n📊 Top 5 acciones registradas:")
        for row in logs_accion:
            print(f"   - {row['accion']}: {row['cantidad']}")
        
        # Logs exitosos vs fallidos
        cursor.execute("""
            SELECT exitoso, COUNT(*) as cantidad 
            FROM logs_seguridad 
            GROUP BY exitoso
        """)
        logs_exitoso = cursor.fetchall()
        print("\n📊 Logs por resultado:")
        for row in logs_exitoso:
            estado = "Exitosos" if row['exitoso'] else "Fallidos"
            print(f"   - {estado}: {row['cantidad']}")
        
        # Últimos 5 logs (solo si encontramos columna de fecha)
        if columna_fecha:
            query = f"""
                SELECT usuario_id, accion, detalle, {columna_fecha}, exitoso
                FROM logs_seguridad 
                ORDER BY {columna_fecha} DESC 
                LIMIT 5
            """
            cursor.execute(query)
            ultimos_logs = cursor.fetchall()
            print("\n📋 Últimos 5 logs:")
            for log in ultimos_logs:
                estado = "✅" if log['exitoso'] else "❌"
                fecha = log[columna_fecha]
                print(f"   {estado} [{fecha}] {log['usuario_id']}: {log['accion']}")
        else:
            print("\n⚠️  No se pudo determinar la columna de fecha")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en logs de seguridad: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        conn.close()

def test_objetos_ia():
    """Probar estadísticas de objetos entrenados con IA"""
    print_section("4. OBJETOS ENTRENADOS CON IA")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Total de objetos
        cursor.execute("SELECT COUNT(*) as total FROM objetos")
        total_objetos = cursor.fetchone()['total']
        print(f"✅ Total de objetos registrados: {total_objetos}")
        
        # Objetos con imágenes
        cursor.execute("""
            SELECT COUNT(DISTINCT objeto_id) as total 
            FROM objetos_imagenes
        """)
        objetos_con_imagenes = cursor.fetchone()['total']
        print(f"📸 Objetos con imágenes: {objetos_con_imagenes}")
        
        # Total de imágenes
        cursor.execute("SELECT COUNT(*) as total FROM objetos_imagenes")
        total_imagenes = cursor.fetchone()['total']
        print(f"🖼️  Total de imágenes: {total_imagenes}")
        
        # Imágenes por vista
        cursor.execute("""
            SELECT vista, COUNT(*) as cantidad 
            FROM objetos_imagenes 
            GROUP BY vista
        """)
        imagenes_vista = cursor.fetchall()
        print("\n📊 Imágenes por vista:")
        for row in imagenes_vista:
            print(f"   - {row['vista']}: {row['cantidad']}")
        
        # Objetos más fotografiados
        cursor.execute("""
            SELECT o.nombre, COUNT(oi.id) as num_fotos
            FROM objetos o
            INNER JOIN objetos_imagenes oi ON o.id = oi.objeto_id
            GROUP BY o.id, o.nombre
            ORDER BY num_fotos DESC
            LIMIT 5
        """)
        objetos_top = cursor.fetchall()
        print("\n🏆 Top 5 objetos más fotografiados:")
        for obj in objetos_top:
            print(f"   - {obj['nombre']}: {obj['num_fotos']} fotos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en objetos IA: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def test_inventario_critico():
    """Probar items con stock crítico"""
    print_section("5. INVENTARIO CRÍTICO")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Items con stock bajo
        cursor.execute("""
            SELECT nombre, categoria, cantidad_actual, cantidad_minima,
                   (cantidad_actual - cantidad_minima) as diferencia
            FROM inventario 
            WHERE cantidad_actual <= cantidad_minima
            ORDER BY diferencia ASC
        """)
        items_criticos = cursor.fetchall()
        
        if items_criticos:
            print(f"⚠️  Se encontraron {len(items_criticos)} items con stock bajo:")
            for item in items_criticos:
                print(f"\n   📦 {item['nombre']}")
                print(f"      Categoría: {item['categoria']}")
                print(f"      Stock actual: {item['cantidad_actual']}")
                print(f"      Stock mínimo: {item['cantidad_minima']}")
                print(f"      Diferencia: {item['diferencia']}")
        else:
            print("✅ No hay items con stock bajo")
        
        # Items sin stock
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM inventario 
            WHERE cantidad_actual = 0
        """)
        items_sin_stock = cursor.fetchone()['total']
        print(f"\n❌ Items sin stock: {items_sin_stock}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en inventario crítico: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def test_actividad_usuarios():
    """Probar actividad de usuarios"""
    print_section("6. ACTIVIDAD DE USUARIOS")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Usuarios más activos (por logs)
        cursor.execute("""
            SELECT u.nombre, u.tipo, COUNT(l.id) as num_acciones
            FROM usuarios u
            LEFT JOIN logs_seguridad l ON u.id = l.usuario_id
            WHERE u.activo = TRUE
            GROUP BY u.id, u.nombre, u.tipo
            ORDER BY num_acciones DESC
            LIMIT 5
        """)
        usuarios_activos = cursor.fetchall()
        
        print("👥 Top 5 usuarios más activos:")
        for user in usuarios_activos:
            print(f"   - {user['nombre']} ({user['tipo']}): {user['num_acciones']} acciones")
        
        # Usuarios por tipo
        cursor.execute("""
            SELECT tipo, COUNT(*) as cantidad 
            FROM usuarios 
            WHERE activo = TRUE
            GROUP BY tipo
        """)
        usuarios_tipo = cursor.fetchall()
        print("\n📊 Usuarios por tipo:")
        for row in usuarios_tipo:
            print(f"   - {row['tipo']}: {row['cantidad']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en actividad de usuarios: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def test_endpoint_estadisticas():
    """Simular llamada al endpoint de estadísticas"""
    print_section("7. SIMULACIÓN DE ENDPOINT /api/estadisticas")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Simular respuesta del endpoint
        estadisticas = {}
        
        # Total equipos
        cursor.execute("SELECT COUNT(*) as total FROM equipos")
        estadisticas['total_equipos'] = cursor.fetchone()['total']
        
        # Total items
        cursor.execute("SELECT COUNT(*) as total FROM inventario")
        estadisticas['total_items'] = cursor.fetchone()['total']
        
        # Total reservas
        cursor.execute("SELECT COUNT(*) as total FROM reservas")
        estadisticas['total_reservas'] = cursor.fetchone()['total']
        
        # Total usuarios
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE activo = TRUE")
        estadisticas['total_usuarios'] = cursor.fetchone()['total']
        
        # Items con stock bajo
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM inventario 
            WHERE cantidad_actual <= cantidad_minima
        """)
        estadisticas['items_stock_bajo'] = cursor.fetchone()['total']
        
        # Reservas activas
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM reservas 
            WHERE estado = 'activa'
        """)
        estadisticas['reservas_activas'] = cursor.fetchone()['total']
        
        print("📊 Respuesta simulada del endpoint:")
        print(json.dumps(estadisticas, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ Error simulando endpoint: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def run_all_tests():
    """Ejecutar todas las pruebas"""
    print("\n" + "📊 " * 30)
    print("  SCRIPT DE PRUEBA - MÓDULO DE REPORTES")
    print("  Centro Minero SENA")
    print("📊 " * 30)
    
    resultados = []
    
    try:
        # Test 1: Estadísticas generales
        resultados.append(("Estadísticas Generales", test_estadisticas_generales()))
        
        # Test 2: Reservas
        resultados.append(("Estadísticas de Reservas", test_reservas_estadisticas()))
        
        # Test 3: Logs de seguridad
        resultados.append(("Logs de Seguridad", test_logs_seguridad()))
        
        # Test 4: Objetos IA
        resultados.append(("Objetos con IA", test_objetos_ia()))
        
        # Test 5: Inventario crítico
        resultados.append(("Inventario Crítico", test_inventario_critico()))
        
        # Test 6: Actividad usuarios
        resultados.append(("Actividad de Usuarios", test_actividad_usuarios()))
        
        # Test 7: Endpoint estadísticas
        resultados.append(("Endpoint Estadísticas", test_endpoint_estadisticas()))
        
        # Resumen final
        print_section("RESUMEN DE PRUEBAS")
        
        total_tests = len(resultados)
        tests_exitosos = sum(1 for _, resultado in resultados if resultado)
        tests_fallidos = total_tests - tests_exitosos
        
        print(f"\n📊 Total de pruebas: {total_tests}")
        print(f"✅ Exitosas: {tests_exitosos}")
        print(f"❌ Fallidas: {tests_fallidos}")
        
        print("\n📋 Detalle:")
        for nombre, resultado in resultados:
            estado = "✅" if resultado else "❌"
            print(f"   {estado} {nombre}")
        
        if tests_fallidos == 0:
            print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        else:
            print(f"\n⚠️  {tests_fallidos} prueba(s) fallaron. Revisa los errores arriba.")
        
    except Exception as e:
        print(f"\n❌ Error general en las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
