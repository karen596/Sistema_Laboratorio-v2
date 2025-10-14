# -*- coding: utf-8 -*-
"""
Asegura las tablas necesarias para la Web/API que pueden faltar
al usar la BD existente.

Ejecutar:
    py -3.11 migracion_web_schema.py
"""
import mysql.connector

CFG = {
    'host': 'localhost',
    'user': 'root',        # usar root para crear tablas si faltan
    'password': '1234',
    'database': 'laboratorio_sistema',
}


def ensure_tables():
    conn = mysql.connector.connect(**CFG)
    cur = conn.cursor()

    # comandos_voz
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS comandos_voz (
            id INT AUTO_INCREMENT PRIMARY KEY,
            usuario_id VARCHAR(50),
            comando TEXT,
            respuesta TEXT,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            exito BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
        """
    )

    # historial_uso
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS historial_uso (
            id INT AUTO_INCREMENT PRIMARY KEY,
            usuario_id VARCHAR(50),
            equipo_id VARCHAR(50),
            fecha_uso DATETIME DEFAULT CURRENT_TIMESTAMP,
            duracion_minutos INT,
            proposito TEXT,
            observaciones TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (equipo_id) REFERENCES equipos(id)
        )
        """
    )

    # logs_seguridad (por si no se ejecutó configuracion_seguridad)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS logs_seguridad (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            usuario_id VARCHAR(50),
            accion VARCHAR(100),
            detalle TEXT,
            ip_origen VARCHAR(45),
            exitoso BOOLEAN,
            INDEX idx_timestamp (timestamp),
            INDEX idx_usuario (usuario_id)
        )
        """
    )

    # reservas (si falta)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reservas (
            id VARCHAR(20) PRIMARY KEY,
            usuario_id VARCHAR(50) NOT NULL,
            equipo_id VARCHAR(50) NOT NULL,
            fecha_inicio DATETIME NOT NULL,
            fecha_fin DATETIME NOT NULL,
            estado ENUM('programada','activa','completada','cancelada') DEFAULT 'programada',
            observaciones TEXT,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (equipo_id) REFERENCES equipos(id),
            INDEX idx_reservas_estado (estado),
            INDEX idx_reservas_fecha_inicio (fecha_inicio)
        )
        """
    )

    # Asegurar columnas requeridas en reservas si ya existía sin todas
    cur.execute(
        """
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA=%s AND TABLE_NAME='reservas'
        """,
        (CFG['database'],)
    )
    cols = {name for (name,) in cur.fetchall()}
    required = [
        ('observaciones', 'TEXT'),
        ('fecha_creacion', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
        ('estado', "ENUM('programada','activa','completada','cancelada') DEFAULT 'programada'"),
    ]
    for col, coltype in required:
        if col not in cols:
            cur.execute(f"ALTER TABLE reservas ADD COLUMN {col} {coltype}")

    conn.commit()

    # =============================
    # OBJETOS PARA RECONOCIMIENTO
    # =============================
    # Tabla de objetos/categorías
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS objetos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(150) NOT NULL,
            categoria VARCHAR(100),
            descripcion TEXT,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_objeto (nombre, categoria)
        )
        """
    )
    # Tabla de imágenes asociadas (almacenadas en BLOB)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS objetos_imagenes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            objeto_id INT NOT NULL,
            imagen LONGBLOB NOT NULL,
            content_type VARCHAR(50) DEFAULT 'image/jpeg',
            fuente ENUM('upload','camera') DEFAULT 'upload',
            notas TEXT,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (objeto_id) REFERENCES objetos(id) ON DELETE CASCADE,
            INDEX idx_objeto (objeto_id)
        )
        """
    )
    # Añadir columnas híbridas si faltan
    cur.execute(
        """
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA=%s AND TABLE_NAME='objetos_imagenes'
        """,
        (CFG['database'],)
    )
    cols_img = {name for (name,) in cur.fetchall()}
    if 'path' not in cols_img:
        cur.execute("ALTER TABLE objetos_imagenes ADD COLUMN path VARCHAR(255) NULL AFTER imagen")
    if 'thumb' not in cols_img:
        cur.execute("ALTER TABLE objetos_imagenes ADD COLUMN thumb MEDIUMBLOB NULL AFTER path")
    if 'vista' not in cols_img:
        cur.execute("ALTER TABLE objetos_imagenes ADD COLUMN vista VARCHAR(40) NULL AFTER fuente")
    # Asegurar columnas en objetos
    cur.execute(
        """
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA=%s AND TABLE_NAME='objetos'
        """,
        (CFG['database'],)
    )
    cols_obj = {name for (name,) in cur.fetchall()}
    if 'reconocer' not in cols_obj:
        cur.execute("ALTER TABLE objetos ADD COLUMN reconocer TINYINT(1) NOT NULL DEFAULT 1 AFTER descripcion")
    if 'slug' not in cols_obj:
        cur.execute("ALTER TABLE objetos ADD COLUMN slug VARCHAR(150) NULL AFTER nombre")
        # backfill slug desde nombre saneado
        # Nota: sanear en SQL de forma simple (minusculas y reemplazo de espacios por '_')
        cur.execute("UPDATE objetos SET slug = REPLACE(LOWER(nombre), ' ', '_') WHERE slug IS NULL OR slug='' ")
        # crear índice único opcional (nombre+categoria ya existe); slug puede repetirse si hay categorias distintas
        try:
            cur.execute("CREATE INDEX idx_objetos_slug ON objetos(slug)")
        except Exception:
            pass
    conn.commit()
    cur.close(); conn.close()
    print("✅ Migración completada: objetos/objetos_imagenes verificados")


if __name__ == "__main__":
    ensure_tables()
