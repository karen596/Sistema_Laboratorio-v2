# -*- coding: utf-8 -*-
"""
Script para aplicar cambios de reconocimiento facial a web_app.py
Centro Minero SENA
"""

import os
import shutil
from datetime import datetime

def aplicar_cambios_facial():
    """Aplicar cambios necesarios para reconocimiento facial"""
    
    archivo_original = 'web_app.py'
    archivo_backup = f'web_app_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
    
    print("🔧 APLICANDO CAMBIOS PARA RECONOCIMIENTO FACIAL")
    print("=" * 60)
    
    # Verificar que existe el archivo
    if not os.path.exists(archivo_original):
        print(f"❌ No se encontró {archivo_original}")
        return False
    
    # Crear backup
    print(f"📋 Creando backup: {archivo_backup}")
    shutil.copy2(archivo_original, archivo_backup)
    
    # Leer archivo original
    with open(archivo_original, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Verificar si ya tiene los cambios
    if 'FacialRegistrationAPI' in contenido and '/api/facial/register' in contenido:
        print("✅ Los cambios ya están aplicados")
        return True
    
    # Aplicar cambios
    cambios_realizados = 0
    
    # 1. Agregar import si no existe
    if 'from facial_api import FacialRegistrationAPI' not in contenido:
        # Buscar donde agregar el import
        if 'import json' in contenido and 'from facial_api import FacialRegistrationAPI' not in contenido:
            contenido = contenido.replace(
                'import json',
                'import json\nfrom facial_api import FacialRegistrationAPI'
            )
            cambios_realizados += 1
            print("✅ Import agregado")
    
    # 2. Agregar registro de API si no existe
    if "api.add_resource(FacialRegistrationAPI, '/api/facial/register')" not in contenido:
        # Buscar la línea de ComandosVozAPI
        if "api.add_resource(ComandosVozAPI, '/api/voz/comando')" in contenido:
            contenido = contenido.replace(
                "api.add_resource(ComandosVozAPI, '/api/voz/comando')",
                "api.add_resource(ComandosVozAPI, '/api/voz/comando')\napi.add_resource(FacialRegistrationAPI, '/api/facial/register')"
            )
            cambios_realizados += 1
            print("✅ Registro de API agregado")
    
    if cambios_realizados > 0:
        # Escribir archivo modificado
        with open(archivo_original, 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        print(f"✅ {cambios_realizados} cambios aplicados exitosamente")
        print(f"📋 Backup guardado como: {archivo_backup}")
        return True
    else:
        print("⚠️ No se pudieron aplicar los cambios automáticamente")
        return False

def verificar_archivos():
    """Verificar que todos los archivos necesarios existen"""
    archivos_necesarios = [
        'facial_api.py',
        'facial_recognition_module.py',
        'templates/registro_facial.html'
    ]
    
    print("\n🔍 VERIFICANDO ARCHIVOS NECESARIOS:")
    todos_existen = True
    
    for archivo in archivos_necesarios:
        if os.path.exists(archivo):
            print(f"  ✅ {archivo}")
        else:
            print(f"  ❌ {archivo} - FALTA")
            todos_existen = False
    
    return todos_existen

def main():
    """Función principal"""
    print("🚀 CONFIGURADOR DE RECONOCIMIENTO FACIAL")
    print("=" * 60)
    
    # Verificar archivos
    if not verificar_archivos():
        print("\n❌ Faltan archivos necesarios")
        return
    
    # Aplicar cambios
    if aplicar_cambios_facial():
        print("\n🎉 ¡CONFIGURACIÓN COMPLETADA!")
        print("\n🎯 PRÓXIMOS PASOS:")
        print("  1. Instalar dependencias:")
        print("     pip install face-recognition opencv-python pillow")
        print("  2. Iniciar servidor:")
        print("     py -3.11 web_app.py")
        print("  3. Acceder a:")
        print("     http://localhost:5000/registro-facial")
        print("\n💡 Si hay errores, restaura desde el backup creado")
    else:
        print("\n❌ No se pudieron aplicar los cambios automáticamente")
        print("💡 Aplica los cambios manualmente siguiendo INSTRUCCIONES_INTEGRACION.md")

if __name__ == "__main__":
    main()
