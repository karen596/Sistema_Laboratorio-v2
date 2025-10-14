# -*- coding: utf-8 -*-
import mysql.connector

def crear_usuarios_centro():
    """Crea usuarios específicos para el Centro Minero"""
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='1234',
        database='laboratorio_sistema',
    )
    cursor = conn.cursor()

    print("👥 CREANDO USUARIOS ESPECÍFICOS DEL CENTRO...")

    coordinadores = [
        ('COORD_MIN', 'Ing. Pedro Sánchez', 'instructor', 'Coordinador Tecnología en Minería', 4),
        ('COORD_MET', 'Ing. Lucía Fernández', 'instructor', 'Coordinador Tecnología en Metalurgia', 4),
        ('COORD_PROC', 'Ing. Manuel Torres', 'instructor', 'Coordinador Tecnología en Procesos', 4),
    ]

    instructores = [
        ('INST_QUI_001', 'Q.A. Sandra López', 'instructor', 'Instructor Análisis Químico', 3),
        ('INST_QUI_002', 'Q.I. Roberto Jiménez', 'instructor', 'Instructor Química Analítica', 3),
        ('INST_MET_001', 'Ing. Carlos Mejía', 'instructor', 'Instructor Metalurgia', 3),
        ('INST_MET_002', 'Ing. Diana Rojas', 'instructor', 'Instructor Ensayos de Materiales', 3),
        ('INST_PROC_001', 'Ing. Andrés Gómez', 'instructor', 'Instructor Procesamiento', 3),
        ('INST_SOLD_001', 'Téc. Miguel Herrera', 'instructor', 'Instructor Soldadura', 3),
    ]

    tecnicos = [
        ('TEC_LAB_001', 'Téc. Gloria Martínez', 'administrador', 'Técnico Lab. Análisis Químico', 3),
        ('TEC_LAB_002', 'Téc. Jorge Ruiz', 'administrador', 'Técnico Lab. Metalurgia', 3),
        ('TEC_LAB_003', 'Téc. Carmen Silva', 'administrador', 'Técnico Lab. Procesamiento', 3),
    ]

    monitores = [
        ('MON_001', 'John Díaz Pérez', 'aprendiz', 'Monitor Tecnología en Minería', 2),
        ('MON_002', 'María Rodríguez', 'aprendiz', 'Monitor Tecnología en Metalurgia', 2),
        ('MON_003', 'Carlos Vargas', 'aprendiz', 'Monitor Tecnología en Procesos', 2),
    ]

    todos = coordinadores + instructores + tecnicos + monitores

    for user_id, nombre, tipo, programa, nivel in todos:
        email = f"{user_id.lower()}@sena.edu.co"
        cursor.execute(
            """
            INSERT INTO usuarios (id, nombre, tipo, programa, nivel_acceso, email, activo)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE nombre=VALUES(nombre), programa=VALUES(programa), nivel_acceso=VALUES(nivel_acceso), email=VALUES(email), activo=TRUE
            """,
            (user_id, nombre, tipo, programa, nivel, email),
        )

    conn.commit()
    cursor.close(); conn.close()

    print(f"✅ {len(todos)} usuarios del centro configurados")
    print("📋 Usuarios por categoría:")
    print(f"   🎯 Coordinadores: {len(coordinadores)}")
    print(f"   👨‍🏫 Instructores: {len(instructores)}")
    print(f"   🔧 Técnicos: {len(tecnicos)}")
    print(f"   👨‍🎓 Monitores: {len(monitores)}")


if __name__ == "__main__":
    crear_usuarios_centro()
