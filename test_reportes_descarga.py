# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la funcionalidad de descarga de reportes
Prueba la generación de PDF y Excel
"""

import os
import sys
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import_modulo():
    """Probar que el módulo se puede importar correctamente"""
    print("\n" + "="*70)
    print("  TEST 1: Importación del módulo de reportes")
    print("="*70)
    
    try:
        from utils.report_generator import report_generator
        print("✅ Módulo importado correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error al importar el módulo: {str(e)}")
        print("\n💡 Solución: Instala las dependencias con:")
        print("   pip install reportlab openpyxl xlsxwriter")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False


def test_generar_pdf():
    """Probar generación de PDF"""
    print("\n" + "="*70)
    print("  TEST 2: Generación de reporte PDF")
    print("="*70)
    
    try:
        from utils.report_generator import report_generator
        
        # Datos de prueba
        data = {
            'total_equipos': 45,
            'equipos_activos': 42,
            'total_usuarios': 28,
            'total_reservas': 156,
            'reservas_activas': 12,
            'total_items': 234,
            'items_stock_bajo': 8,
            'equipos_mas_usados': [
                {'nombre': 'Microscopio Óptico', 'usos': 45},
                {'nombre': 'Balanza Analítica', 'usos': 38},
                {'nombre': 'Osciloscopio Digital', 'usos': 32},
                {'nombre': 'Multímetro Digital', 'usos': 28},
                {'nombre': 'Centrífuga', 'usos': 25}
            ],
            'usuarios_activos': [
                {'nombre': 'Juan Pérez', 'tipo': 'estudiante', 'comandos': 42},
                {'nombre': 'María García', 'tipo': 'instructor', 'comandos': 38},
                {'nombre': 'Carlos López', 'tipo': 'estudiante', 'comandos': 31},
                {'nombre': 'Ana Martínez', 'tipo': 'admin', 'comandos': 25}
            ],
            'inventario_bajo': [
                {'nombre': 'Guantes de látex', 'categoria': 'Seguridad', 'cantidad_actual': 5, 'cantidad_minima': 20},
                {'nombre': 'Pipetas 10ml', 'categoria': 'Material', 'cantidad_actual': 8, 'cantidad_minima': 15},
                {'nombre': 'Reactivo A', 'categoria': 'Químicos', 'cantidad_actual': 2, 'cantidad_minima': 10}
            ]
        }
        
        # Generar PDF
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
        
        pdf_buffer = report_generator.generar_pdf_estadisticas(data, fecha_inicio, fecha_fin)
        
        # Guardar archivo de prueba
        output_file = 'test_reporte.pdf'
        with open(output_file, 'wb') as f:
            f.write(pdf_buffer.read())
        
        file_size = os.path.getsize(output_file)
        print(f"✅ PDF generado correctamente")
        print(f"   📄 Archivo: {output_file}")
        print(f"   📊 Tamaño: {file_size:,} bytes")
        print(f"   📅 Período: {fecha_inicio} a {fecha_fin}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {str(e)}")
        print("\n💡 Instala las dependencias: pip install reportlab")
        return False
    except Exception as e:
        print(f"❌ Error al generar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_generar_excel():
    """Probar generación de Excel"""
    print("\n" + "="*70)
    print("  TEST 3: Generación de reporte Excel")
    print("="*70)
    
    try:
        from utils.report_generator import report_generator
        
        # Datos de prueba (mismos que para PDF)
        data = {
            'total_equipos': 45,
            'equipos_activos': 42,
            'total_usuarios': 28,
            'total_reservas': 156,
            'reservas_activas': 12,
            'total_items': 234,
            'items_stock_bajo': 8,
            'equipos_mas_usados': [
                {'nombre': 'Microscopio Óptico', 'usos': 45},
                {'nombre': 'Balanza Analítica', 'usos': 38},
                {'nombre': 'Osciloscopio Digital', 'usos': 32},
                {'nombre': 'Multímetro Digital', 'usos': 28},
                {'nombre': 'Centrífuga', 'usos': 25}
            ],
            'usuarios_activos': [
                {'nombre': 'Juan Pérez', 'tipo': 'estudiante', 'comandos': 42},
                {'nombre': 'María García', 'tipo': 'instructor', 'comandos': 38},
                {'nombre': 'Carlos López', 'tipo': 'estudiante', 'comandos': 31},
                {'nombre': 'Ana Martínez', 'tipo': 'admin', 'comandos': 25}
            ],
            'inventario_bajo': [
                {'nombre': 'Guantes de látex', 'categoria': 'Seguridad', 'cantidad_actual': 5, 'cantidad_minima': 20},
                {'nombre': 'Pipetas 10ml', 'categoria': 'Material', 'cantidad_actual': 8, 'cantidad_minima': 15},
                {'nombre': 'Reactivo A', 'categoria': 'Químicos', 'cantidad_actual': 2, 'cantidad_minima': 10}
            ]
        }
        
        # Generar Excel
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
        
        excel_buffer = report_generator.generar_excel_estadisticas(data, fecha_inicio, fecha_fin)
        
        # Guardar archivo de prueba
        output_file = 'test_reporte.xlsx'
        with open(output_file, 'wb') as f:
            f.write(excel_buffer.read())
        
        file_size = os.path.getsize(output_file)
        print(f"✅ Excel generado correctamente")
        print(f"   📄 Archivo: {output_file}")
        print(f"   📊 Tamaño: {file_size:,} bytes")
        print(f"   📅 Período: {fecha_inicio} a {fecha_fin}")
        print(f"   📋 Hojas: Resumen General, Equipos Más Usados, Usuarios Más Activos, Inventario Crítico")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {str(e)}")
        print("\n💡 Instala las dependencias: pip install openpyxl xlsxwriter")
        return False
    except Exception as e:
        print(f"❌ Error al generar Excel: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Ejecutar todas las pruebas"""
    print("\n" + "📊 " * 30)
    print("  PRUEBA DE DESCARGA DE REPORTES")
    print("  Sistema de Laboratorios - Centro Minero SENA")
    print("📊 " * 30)
    
    resultados = []
    
    # Test 1: Importación
    resultados.append(("Importación del módulo", test_import_modulo()))
    
    # Test 2: Generación PDF
    if resultados[0][1]:  # Solo si la importación fue exitosa
        resultados.append(("Generación de PDF", test_generar_pdf()))
    
    # Test 3: Generación Excel
    if resultados[0][1]:  # Solo si la importación fue exitosa
        resultados.append(("Generación de Excel", test_generar_excel()))
    
    # Resumen
    print("\n" + "="*70)
    print("  RESUMEN DE PRUEBAS")
    print("="*70)
    
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
        print("\n📝 Archivos generados:")
        if os.path.exists('test_reporte.pdf'):
            print(f"   - test_reporte.pdf ({os.path.getsize('test_reporte.pdf'):,} bytes)")
        if os.path.exists('test_reporte.xlsx'):
            print(f"   - test_reporte.xlsx ({os.path.getsize('test_reporte.xlsx'):,} bytes)")
        
        print("\n✨ La funcionalidad de descarga de reportes está lista para usar")
        print("\n🚀 Próximos pasos:")
        print("   1. Instala las dependencias: pip install reportlab openpyxl xlsxwriter")
        print("   2. Inicia el servidor: python web_app.py")
        print("   3. Navega a /reportes")
        print("   4. Usa los botones 'Descargar PDF' y 'Descargar Excel'")
    else:
        print(f"\n⚠️  {tests_fallidos} prueba(s) fallaron.")
        print("\n💡 Solución:")
        print("   pip install reportlab openpyxl xlsxwriter")


if __name__ == "__main__":
    run_all_tests()
