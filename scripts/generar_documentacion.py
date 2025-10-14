# -*- coding: utf-8 -*-
from datetime import datetime


def generar_manual_usuario():
    manual = f"""
# MANUAL DE USUARIO
## Sistema de Gestión Inteligente de Laboratorios
### Centro Minero - Regional Boyacá - SENA

**Versión:** 1.0  
**Fecha:** {datetime.now().strftime('%d/%m/%Y')}  
**Desarrollado para:** Centro Minero - Regional Boyacá

---

[Contenido abreviado: ver guía del Paso 4 en el proyecto para la versión extendida]

## Inicio rápido
- Activar entorno virtual y ejecutar `sistema_laboratorio.py`
- Navegar con el menú o comandos de voz (ayuda, equipos, inventario)

## Soporte
- soporte.laboratorio@sena.edu.co | +57 (8) 770 6565
"""
    with open('MANUAL_USUARIO.md', 'w', encoding='utf-8') as f:
        f.write(manual)
    print("✅ Manual de usuario generado: MANUAL_USUARIO.md")


def generar_guia_rapida():
    guia = """
# GUÍA RÁPIDA - CENTRO MINERO SENA

## Comandos de voz
- "Estado de equipos"
- "Inventario bajo mínimo"
- "Reservar microscopio"
- "Ayuda"

## Usuarios ejemplo
- COORD_MIN, INST_QUI_001, TEC_LAB_001
"""
    with open('GUIA_RAPIDA.md', 'w', encoding='utf-8') as f:
        f.write(guia)
    print("✅ Guía rápida generada: GUIA_RAPIDA.md")


if __name__ == "__main__":
    print("📖 GENERANDO DOCUMENTACIÓN DEL SISTEMA...")
    generar_manual_usuario()
    generar_guia_rapida()
    print("✅ Documentación completa generada")
