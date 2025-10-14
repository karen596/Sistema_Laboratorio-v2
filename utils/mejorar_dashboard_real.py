# -*- coding: utf-8 -*-
"""
Mejora del Dashboard con Datos Reales
Centro Minero SENA - Ajustar consultas para mostrar información útil
"""

def generar_consultas_mejoradas():
    """Generar consultas más útiles para el dashboard"""
    
    consultas_mejoradas = {
        'equipos_estado': """
            SELECT estado, COUNT(*) cantidad 
            FROM equipos 
            GROUP BY estado
        """,
        
        'inventario_bajo_stock': """
            SELECT COUNT(*) cantidad 
            FROM inventario 
            WHERE cantidad_actual <= (cantidad_minima * 1.5)
        """,
        
        'reservas_proximas': """
            SELECT COUNT(*) cantidad 
            FROM reservas 
            WHERE estado IN ('activa', 'programada') 
            AND fecha_inicio >= CURDATE()
        """,
        
        'comandos_recientes': """
            SELECT COUNT(*) cantidad 
            FROM comandos_voz 
            WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAYS)
        """,
        
        'usuarios_activos_semana': """
            SELECT COUNT(DISTINCT usuario_id) cantidad 
            FROM comandos_voz 
            WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAYS)
        """,
        
        'equipos_disponibles': """
            SELECT COUNT(*) cantidad 
            FROM equipos 
            WHERE estado = 'disponible'
        """,
        
        'total_laboratorios': """
            SELECT COUNT(*) cantidad 
            FROM laboratorios 
            WHERE estado = 'activo'
        """,
        
        'items_bien_abastecidos': """
            SELECT COUNT(*) cantidad 
            FROM inventario 
            WHERE cantidad_actual > cantidad_minima
        """
    }
    
    return consultas_mejoradas

def generar_codigo_dashboard():
    """Generar el código mejorado para get_dashboard_stats()"""
    
    codigo = '''
def get_dashboard_stats():
    """Estadísticas mejoradas del dashboard con datos reales"""
    stats = {}
    
    # Equipos por estado
    eq = db_manager.execute_query("SELECT estado, COUNT(*) cantidad FROM equipos GROUP BY estado")
    stats['equipos_estado'] = {r['estado']: r['cantidad'] for r in eq} if eq else {}
    
    # Equipos disponibles (más útil que críticos)
    disp = db_manager.execute_query("SELECT COUNT(*) cantidad FROM equipos WHERE estado = 'disponible'")
    stats['equipos_disponibles'] = disp[0]['cantidad'] if disp else 0
    
    # Items con stock bajo (más flexible que crítico)
    bajo = db_manager.execute_query("SELECT COUNT(*) cantidad FROM inventario WHERE cantidad_actual <= (cantidad_minima * 1.5)")
    stats['inventario_bajo'] = bajo[0]['cantidad'] if bajo else 0
    
    # Items bien abastecidos (información positiva)
    bien = db_manager.execute_query("SELECT COUNT(*) cantidad FROM inventario WHERE cantidad_actual > cantidad_minima")
    stats['inventario_bien'] = bien[0]['cantidad'] if bien else 0
    
    # Reservas próximas (incluye programadas y activas)
    prox = db_manager.execute_query("SELECT COUNT(*) cantidad FROM reservas WHERE estado IN ('activa', 'programada') AND fecha_inicio >= CURDATE()")
    stats['reservas_proximas'] = prox[0]['cantidad'] if prox else 0
    
    # Comandos de la última semana (más realista)
    sem = db_manager.execute_query("SELECT COUNT(*) cantidad FROM comandos_voz WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAYS)")
    stats['comandos_semana'] = sem[0]['cantidad'] if sem else 0
    
    # Usuarios activos en la semana
    ua_sem = db_manager.execute_query("SELECT COUNT(DISTINCT usuario_id) cantidad FROM comandos_voz WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAYS)")
    stats['usuarios_activos_semana'] = ua_sem[0]['cantidad'] if ua_sem else 0
    
    # Total de laboratorios activos
    labs = db_manager.execute_query("SELECT COUNT(*) cantidad FROM laboratorios WHERE estado = 'activo'")
    stats['total_laboratorios'] = labs[0]['cantidad'] if labs else 0
    
    # Total de items en inventario
    total_inv = db_manager.execute_query("SELECT COUNT(*) cantidad FROM inventario")
    stats['total_inventario'] = total_inv[0]['cantidad'] if total_inv else 0
    
    return stats
'''
    
    return codigo

def main():
    """Función principal"""
    print("📊 MEJORAS PARA DASHBOARD CON DATOS REALES")
    print("=" * 60)
    
    print("🎯 CAMBIOS PROPUESTOS:")
    print("-" * 40)
    print("✅ Inventario crítico → Inventario con stock bajo (más flexible)")
    print("✅ Reservas activas → Reservas próximas (incluye programadas)")
    print("✅ Comandos hoy → Comandos última semana (más realista)")
    print("✅ Agregar: Equipos disponibles")
    print("✅ Agregar: Items bien abastecidos")
    print("✅ Agregar: Total laboratorios")
    
    print("\n📋 CÓDIGO MEJORADO PARA web_app.py:")
    print("-" * 40)
    print(generar_codigo_dashboard())
    
    print("\n💡 BENEFICIOS:")
    print("-" * 40)
    print("🔹 Muestra información útil con tus datos reales")
    print("🔹 Dashboard más informativo y positivo")
    print("🔹 Estadísticas relevantes para gestión diaria")
    print("🔹 No requiere datos artificiales")
    
    print("\n🚀 PRÓXIMO PASO:")
    print("-" * 40)
    print("Reemplaza la función get_dashboard_stats() en web_app.py")
    print("con el código mostrado arriba")

if __name__ == "__main__":
    main()
