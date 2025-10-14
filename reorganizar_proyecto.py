#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para reorganizar la estructura del proyecto
"""
import os
import shutil
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent

# Definir estructura de carpetas
ESTRUCTURA = {
    'config': [
        'configuracion_seguridad.py',
        'configuracion_sena.py',
        'configurar_hardware.py',
        'configurar_horarios.py',
        'configurar_red.py',
        'ai_config.py',
        '.env.example',
        '.env_email_example',
        '.env_produccion.example',
        'web.config',
    ],
    'scripts': [
        'activar_entorno.bat',
        'iniciar_servidor.bat',
        'iniciar_servidor.ps1',
        'iniciar_con_logs.bat',
        'iniciar_sistema_completo.bat',
        'instalar_opencv.bat',
        'generar_claves.py',
        'generar_documentacion.py',
        'sistema_respaldos.py',
        'backup_produccion.sh',
        'crear_usuarios_centro.py',
        'crear_tablas_automatico.py',
        'instalacion_rapida.py',
    ],
    'tests': [
        'test_api_objetos.py',
        'test_camara.py',
        'test_consultas_rapido.py',
        'test_dependencias.py',
        'test_email.py',
        'test_facial_rapido.py',
        'test_microfono_device.py',
        'test_mysql_especifico.py',
        'test_simple.py',
        'test_sistema_visual.py',
        'test_voz.py',
        'listar_dispositivos_pyaudio.py',
        'listar_microfonos.py',
        'listar_microfonos_sd.py',
        'verificar_columnas.py',
        'verificar_dependencias.py',
        'verificar_entorno.py',
        'verificar_imagenes.py',
        'verificar_imagenes_detallado.py',
        'verificar_proyecto.py',
        'verificar_tabla_equipos.py',
        'verificar_tabla_reservas.py',
        'diagnostico_dashboard.py',
    ],
    'docs': [
        'README.md',
        'DESPLIEGUE.md',
        'GUIA_DESPLIEGUE.md',
        'GUIA_RECONOCIMIENTO_VISUAL.md',
        'INICIO_RAPIDO.txt',
        'INSTRUCCIONES_INTEGRACION.md',
        'README_DESPLIEGUE.md',
        'RESUMEN_DESPLIEGUE.txt',
        'RESUMEN_SISTEMA_COMPLETO.md',
        'crear_tablas_vision.txt',
    ],
    'modules': [
        'ai_integration.py',
        'facial_recognition_module.py',
        'speech_ai_module.py',
        'vision_ai_module.py',
        'visual_recognition_module.py',
        'sistema_laboratorio.py',
    ],
    'api': [
        'facial_api.py',
    ],
    'migrations': [
        'migracion_esquema.py',
        'migracion_laboratorios.py',
        'migracion_laboratorios.sql',
        'migracion_simple.py',
        'migracion_web_schema.py',
        'facial_tables_admin.sql',
        'setup_facial_db.py',
    ],
    'deployment': [
        'desplegar_produccion.ps1',
        'verificar_despliegue.ps1',
        'wsgi.py',
    ],
    'utils': [
        'aplicar_cambios_facial.py',
        'apply_vision_patch.py',
        'corregir_asociaciones.py',
        'corregir_dashboard.py',
        'fix_cors.py',
        'mejorar_dashboard_real.py',
        'optimizacion_rendimiento.py',
        'probar_dashboard_mejorado.py',
    ],
}

def crear_carpetas():
    """Crear las carpetas necesarias"""
    for carpeta in ESTRUCTURA.keys():
        carpeta_path = BASE_DIR / carpeta
        carpeta_path.mkdir(exist_ok=True)
        print(f"✓ Carpeta creada: {carpeta}/")

def mover_archivos():
    """Mover archivos a sus carpetas correspondientes"""
    movidos = 0
    errores = 0
    
    for carpeta, archivos in ESTRUCTURA.items():
        for archivo in archivos:
            origen = BASE_DIR / archivo
            destino = BASE_DIR / carpeta / archivo
            
            if origen.exists():
                try:
                    shutil.move(str(origen), str(destino))
                    print(f"  ✓ {archivo} → {carpeta}/")
                    movidos += 1
                except Exception as e:
                    print(f"  ✗ Error moviendo {archivo}: {e}")
                    errores += 1
            else:
                print(f"  - {archivo} no encontrado (puede estar ya movido)")
    
    return movidos, errores

def crear_readme_carpetas():
    """Crear README en cada carpeta explicando su contenido"""
    descripciones = {
        'config': 'Archivos de configuración del sistema',
        'scripts': 'Scripts de utilidad, instalación y mantenimiento',
        'tests': 'Scripts de prueba y verificación',
        'docs': 'Documentación del proyecto',
        'modules': 'Módulos de IA y funcionalidades principales',
        'api': 'APIs REST del sistema',
        'migrations': 'Scripts de migración de base de datos',
        'deployment': 'Scripts de despliegue en producción',
        'utils': 'Utilidades y herramientas de corrección',
    }
    
    for carpeta, descripcion in descripciones.items():
        readme_path = BASE_DIR / carpeta / 'README.md'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"# {carpeta.capitalize()}\n\n")
            f.write(f"{descripcion}\n\n")
            f.write(f"## Archivos en esta carpeta:\n\n")
            
            if carpeta in ESTRUCTURA:
                for archivo in ESTRUCTURA[carpeta]:
                    f.write(f"- `{archivo}`\n")
        
        print(f"✓ README creado en {carpeta}/")

def crear_estructura_info():
    """Crear archivo con información de la nueva estructura"""
    info_path = BASE_DIR / 'ESTRUCTURA_PROYECTO.md'
    
    with open(info_path, 'w', encoding='utf-8') as f:
        f.write("# Estructura del Proyecto\n\n")
        f.write("## Organización de Carpetas\n\n")
        
        f.write("```\n")
        f.write("Gil_Project/\n")
        f.write("├── config/          # Configuración del sistema\n")
        f.write("├── scripts/         # Scripts de utilidad\n")
        f.write("├── tests/           # Pruebas y verificación\n")
        f.write("├── docs/            # Documentación\n")
        f.write("├── modules/         # Módulos de IA\n")
        f.write("├── api/             # APIs REST\n")
        f.write("├── migrations/      # Migraciones de BD\n")
        f.write("├── deployment/      # Despliegue\n")
        f.write("├── utils/           # Utilidades\n")
        f.write("├── templates/       # Templates HTML\n")
        f.write("├── static/          # Archivos estáticos\n")
        f.write("├── imagenes/        # Imágenes del sistema\n")
        f.write("├── logs/            # Logs del sistema\n")
        f.write("├── backups/         # Respaldos\n")
        f.write("├── models/          # Modelos de IA\n")
        f.write("└── web_app.py       # Aplicación principal\n")
        f.write("```\n\n")
        
        f.write("## Archivos Principales (Raíz)\n\n")
        f.write("- `web_app.py` - Aplicación web principal\n")
        f.write("- `requirements.txt` - Dependencias del proyecto\n")
        f.write("- `.env_produccion` - Variables de entorno (no versionado)\n")
        f.write("- `.gitignore` - Archivos ignorados por Git\n\n")
        
        for carpeta, descripcion in {
            'config': 'Configuración del sistema',
            'scripts': 'Scripts de utilidad',
            'tests': 'Pruebas y verificación',
            'docs': 'Documentación',
            'modules': 'Módulos de IA',
            'api': 'APIs REST',
            'migrations': 'Migraciones de BD',
            'deployment': 'Despliegue',
            'utils': 'Utilidades',
        }.items():
            f.write(f"## {carpeta}/\n\n")
            f.write(f"{descripcion}\n\n")
    
    print(f"✓ Archivo ESTRUCTURA_PROYECTO.md creado")

def main():
    print("=" * 70)
    print("REORGANIZACIÓN DEL PROYECTO")
    print("=" * 70)
    print()
    
    # Paso 1: Crear carpetas
    print("[1/4] Creando carpetas...")
    crear_carpetas()
    print()
    
    # Paso 2: Mover archivos
    print("[2/4] Moviendo archivos...")
    movidos, errores = mover_archivos()
    print()
    
    # Paso 3: Crear READMEs
    print("[3/4] Creando READMEs en carpetas...")
    crear_readme_carpetas()
    print()
    
    # Paso 4: Crear info de estructura
    print("[4/4] Creando documentación de estructura...")
    crear_estructura_info()
    print()
    
    # Resumen
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"✓ Carpetas creadas: {len(ESTRUCTURA)}")
    print(f"✓ Archivos movidos: {movidos}")
    if errores > 0:
        print(f"✗ Errores: {errores}")
    print()
    print("¡Reorganización completada!")
    print("=" * 70)

if __name__ == '__main__':
    main()
