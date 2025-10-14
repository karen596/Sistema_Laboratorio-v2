# -*- coding: utf-8 -*-
"""
Actualiza el esquema de la base de datos para alinear la tabla 'equipos'
con los campos requeridos por la configuración del SENA.

Ejecutar:
    py -3.11 migracion_esquema.py
"""
import mysql.connector

DB_CFG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'laboratorio_sistema',
}

# Columnas requeridas en 'equipos'
NEEDED_COLUMNS_EQUIPOS = [
    ("ultima_calibracion", "DATETIME NULL"),
    ("proximo_mantenimiento", "DATETIME NULL"),
    ("especificaciones", "JSON NULL"),
    ("fecha_adquisicion", "DATE NULL"),
    ("proveedor", "VARCHAR(100) NULL"),
    ("costo", "DECIMAL(10,2) NULL"),
    ("imagen_path", "VARCHAR(255) NULL"),
]

# Columnas requeridas en 'inventario'
NEEDED_COLUMNS_INVENTARIO = [
    ("proveedor", "VARCHAR(100) NULL"),
    ("fecha_vencimiento", "DATE NULL"),
    ("costo_unitario", "DECIMAL(8,2) NULL"),
    ("ubicacion", "VARCHAR(100) NULL"),
    ("descripcion", "TEXT NULL"),
]


def ensure_columns():
    conn = mysql.connector.connect(**DB_CFG)
    cur = conn.cursor()

    # Asegurar base de datos seleccionada
    cur.execute("USE laboratorio_sistema")

    # Ver columnas existentes
    cur.execute(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA=%s AND TABLE_NAME='equipos'
        """,
        (DB_CFG['database'],),
    )
    existing = {name for (name,) in cur.fetchall()}

    added = []
    for col, coltype in NEEDED_COLUMNS_EQUIPOS:
        if col not in existing:
            # Agregar columna solo si no existe (ya validado arriba)
            alter = f"ALTER TABLE equipos ADD COLUMN {col} {coltype}"
            cur.execute(alter)
            added.append(col)

    if added:
        conn.commit()
        print(f"✅ Columnas agregadas en 'equipos': {', '.join(added)}")
    else:
        print("ℹ️ Esquema 'equipos' ya está completo")

    # ----- Inventario -----
    cur.execute(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA=%s AND TABLE_NAME='inventario'
        """,
        (DB_CFG['database'],),
    )
    inv_existing = {name for (name,) in cur.fetchall()}
    inv_added = []
    for col, coltype in NEEDED_COLUMNS_INVENTARIO:
        if col not in inv_existing:
            alter = f"ALTER TABLE inventario ADD COLUMN {col} {coltype}"
            cur.execute(alter)
            inv_added.append(col)

    if inv_added:
        conn.commit()
        print(f"✅ Columnas agregadas en 'inventario': {', '.join(inv_added)}")
    else:
        print("ℹ️ Esquema 'inventario' ya está completo")

    cur.close(); conn.close()


if __name__ == "__main__":
    ensure_columns()
