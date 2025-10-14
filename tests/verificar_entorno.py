# -*- coding: utf-8 -*-
"""
Script de verificación de entorno para el Sistema de Gestión de Laboratorios
Ejecutar: python verificar_entorno.py
"""

import sys

def verificar_python():
    v = sys.version_info
    if v.major >= 3 and v.minor >= 8:
        print(f"✅ Python {v.major}.{v.minor}.{v.micro} - OK")
        return True
    print(f"❌ Python {v.major}.{v.minor}.{v.micro} - Necesita 3.8+")
    return False


def verificar_pip():
    try:
        import pip  # noqa: F401
        print("✅ pip disponible - OK")
        return True
    except Exception:
        print("❌ pip no encontrado")
        return False


def verificar_mysql():
    try:
        import mysql.connector  # noqa: F401
        import mysql.connector as mc
        conn = mc.connect(host='localhost', user='root', password='1234')
        conn.close()
        print("✅ MySQL conexión exitosa - OK")
        return True
    except ImportError:
        print("❌ mysql-connector-python no instalado (se instalará después)")
        return True
    except Exception as e:
        print(f"❌ MySQL no accesible: {e}")
        return False


def main():
    print("🔍 VERIFICANDO ENTORNO PARA SISTEMA DE LABORATORIOS")
    print("=" * 60)
    resultados = [
        verificar_python(),
        verificar_pip(),
        verificar_mysql(),
    ]
    print("\n" + "=" * 60)
    if all(resultados):
        print("✅ ENTORNO LISTO PARA CONTINUAR")
        print("Siguiente paso: pip install -r requirements.txt")
    else:
        print("❌ RESOLVER PROBLEMAS ANTES DE CONTINUAR")
    print("=" * 60)


if __name__ == "__main__":
    main()
