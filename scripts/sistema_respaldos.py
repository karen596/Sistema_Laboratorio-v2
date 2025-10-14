# -*- coding: utf-8 -*-
import os
import subprocess
from datetime import datetime, timedelta
import mysql.connector


class SistemaRespaldos:
    def __init__(self):
        self.directorio_respaldos = "respaldos"
        self.crear_directorio_respaldos()

    def crear_directorio_respaldos(self):
        if not os.path.exists(self.directorio_respaldos):
            os.makedirs(self.directorio_respaldos)
            print(f"📁 Directorio creado: {self.directorio_respaldos}")

    def crear_respaldo_bd(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_respaldo = os.path.join(self.directorio_respaldos, f"laboratorio_backup_{timestamp}.sql")

            # Usar variable de entorno MYSQL_PWD para no exponer contraseña en argumentos
            env = os.environ.copy()
            env['MYSQL_PWD'] = '1234'

            comando = [
                'mysqldump',
                '-h', 'localhost',
                '-u', 'root',
                '--single-transaction',
                '--routines',
                '--triggers',
                'laboratorio_sistema',
            ]

            with open(archivo_respaldo, 'w', encoding='utf-8') as f:
                subprocess.run(comando, stdout=f, check=True, env=env)

            print(f"✅ Respaldo creado: {archivo_respaldo}")
            self.limpiar_respaldos_antiguos()
            return archivo_respaldo
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creando respaldo (mysqldump): {e}")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def limpiar_respaldos_antiguos(self):
        try:
            fecha_limite = datetime.now() - timedelta(days=7)
            for archivo in os.listdir(self.directorio_respaldos):
                if archivo.startswith('laboratorio_backup_') and archivo.endswith('.sql'):
                    ruta = os.path.join(self.directorio_respaldos, archivo)
                    if datetime.fromtimestamp(os.path.getctime(ruta)) < fecha_limite:
                        os.remove(ruta)
                        print(f"🗑️ Respaldo antiguo eliminado: {archivo}")
        except Exception as e:
            print(f"⚠️ Error limpiando respaldos antiguos: {e}")

    def verificar_integridad_bd(self):
        try:
            conn = mysql.connector.connect(host='localhost', user='root', password='1234', database='laboratorio_sistema')
            cur = conn.cursor()
            cur.execute("SHOW TABLES")
            tablas = cur.fetchall()
            problemas = []
            for (t,) in tablas:
                cur.execute(f"CHECK TABLE {t}")
                res = cur.fetchone()
                if res and len(res) >= 4 and res[3] != 'OK':
                    problemas.append(f"Tabla {t}: {res[3]}")
            cur.close(); conn.close()
            if not problemas:
                print("✅ Integridad de la base de datos: OK")
                return True
            print("⚠️ Problemas de integridad:")
            for p in problemas:
                print(f"   - {p}")
            return False
        except Exception as e:
            print(f"❌ Error verificando integridad: {e}")
            return False


def configurar_respaldos():
    print("💾 CONFIGURANDO SISTEMA DE RESPALDOS...")
    s = SistemaRespaldos()
    print("🔄 Creando respaldo inicial...")
    archivo = s.crear_respaldo_bd()
    if archivo:
        print("✅ Respaldo inicial creado")
        print("🔍 Verificando integridad de la base de datos...")
        s.verificar_integridad_bd()
        print("\n📋 SISTEMA DE RESPALDOS CONFIGURADO:")
        print("   💾 Respaldo inicial: Creado")
        print("   🗑️ Limpieza automática: Activa (7 días)")
    else:
        print("❌ Error configurando respaldos")


if __name__ == "__main__":
    configurar_respaldos()
