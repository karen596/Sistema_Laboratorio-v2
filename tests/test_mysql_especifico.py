# -*- coding: utf-8 -*-
import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost', user='root', password='1234', connect_timeout=10
    )
    cur = conn.cursor()
    cur.execute("SELECT VERSION()")
    ver = cur.fetchone()
    print(f"✅ MySQL conectado - Versión: {ver[0]}")
    cur.close(); conn.close()
except mysql.connector.Error as e:
    print(f"❌ Error MySQL: {e}")
    print("💡 Verifica servicio, usuario/contraseña y puerto 3306")
