# -*- coding: utf-8 -*-
import mysql.connector
import psutil
from datetime import datetime


class OptimizacionRendimiento:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1234',
            database='laboratorio_sistema',
        )
        self.cursor = self.conn.cursor()

    def optimizar_base_datos(self):
        print("⚡ OPTIMIZANDO BASE DE DATOS...")
        # Helper para verificar existencia de tabla
        def table_exists(table: str) -> bool:
            self.cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema=%s AND table_name=%s
                """,
                (self.conn.database, table),
            )
            return self.cursor.fetchone()[0] == 1

        # Helper para verificar si existe índice por nombre
        def index_exists(table: str, index_name: str) -> bool:
            self.cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.statistics
                WHERE table_schema=%s AND table_name=%s AND index_name=%s
                """,
                (self.conn.database, table, index_name),
            )
            return self.cursor.fetchone()[0] > 0

        # Definición de índices deseados por tabla
        index_map = {
            'usuarios': [
                ('idx_usuarios_tipo', 'CREATE INDEX idx_usuarios_tipo ON usuarios(tipo)'),
                ('idx_usuarios_activo', 'CREATE INDEX idx_usuarios_activo ON usuarios(activo)'),
                ('idx_usuarios_programa', 'CREATE INDEX idx_usuarios_programa ON usuarios(programa)'),
            ],
            'equipos': [
                ('idx_equipos_estado', 'CREATE INDEX idx_equipos_estado ON equipos(estado)'),
                ('idx_equipos_tipo', 'CREATE INDEX idx_equipos_tipo ON equipos(tipo)'),
                ('idx_equipos_ubicacion', 'CREATE INDEX idx_equipos_ubicacion ON equipos(ubicacion)'),
            ],
            'reservas': [
                ('idx_reservas_fecha_inicio', 'CREATE INDEX idx_reservas_fecha_inicio ON reservas(fecha_inicio)'),
                ('idx_reservas_estado', 'CREATE INDEX idx_reservas_estado ON reservas(estado)'),
                ('idx_reservas_usuario_equipo', 'CREATE INDEX idx_reservas_usuario_equipo ON reservas(usuario_id, equipo_id)'),
            ],
            'inventario': [
                ('idx_inventario_categoria', 'CREATE INDEX idx_inventario_categoria ON inventario(categoria)'),
                ('idx_inventario_stock', 'CREATE INDEX idx_inventario_stock ON inventario(cantidad_actual, cantidad_minima)'),
            ],
            'historial_uso': [
                ('idx_historial_fecha', 'CREATE INDEX idx_historial_fecha ON historial_uso(fecha_uso)'),
                ('idx_historial_usuario', 'CREATE INDEX idx_historial_usuario ON historial_uso(usuario_id)'),
            ],
            'comandos_voz': [
                ('idx_comandos_fecha', 'CREATE INDEX idx_comandos_fecha ON comandos_voz(fecha)'),
                ('idx_comandos_usuario', 'CREATE INDEX idx_comandos_usuario ON comandos_voz(usuario_id)'),
            ],
        }

        # Crear índices sólo si la tabla existe y el índice no existe
        for table, idx_list in index_map.items():
            if not table_exists(table):
                print(f"ℹ️ Tabla '{self.conn.database}.{table}' no existe, se omiten índices")
                continue
            for idx_name, create_sql in idx_list:
                if not index_exists(table, idx_name):
                    try:
                        self.cursor.execute(create_sql)
                        print(f"✅ Índice creado: {idx_name}")
                    except mysql.connector.Error as e:
                        print(f"⚠️ Error creando índice {idx_name}: {e.msg}")
        self.conn.commit()

        # OPTIMIZE TABLE (consumir resultados para evitar 'Unread result found')
        for t in ['usuarios', 'equipos', 'reservas', 'inventario', 'historial_uso', 'comandos_voz']:
            if not table_exists(t):
                continue
            try:
                self.cursor.execute(f"OPTIMIZE TABLE {t}")
                # Consumir todas las filas del resultado
                try:
                    _ = self.cursor.fetchall()
                except mysql.connector.Error:
                    pass
                print(f"✅ Tabla optimizada: {t}")
            except mysql.connector.Error as e:
                print(f"⚠️ Error optimizando {t}: {e.msg}")

        print("✅ Optimización completada")

    def configurar_cache_sistema(self):
        print("🚄 CONFIGURANDO SISTEMA DE CACHÉ...")
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cache_sistema (
                id VARCHAR(100) PRIMARY KEY,
                tipo VARCHAR(50),
                datos JSON,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_expiracion DATETIME,
                hits INT DEFAULT 0,
                INDEX idx_cache_tipo (tipo),
                INDEX idx_cache_expiracion (fecha_expiracion)
            )
            """
        )
        configuraciones_cache = [
            ('cache_equipos_disponibles', '300', 'Caché de equipos disponibles (5 min)'),
            ('cache_inventario_critico', '600', 'Caché de inventario crítico (10 min)'),
            ('cache_usuarios_activos', '1800', 'Caché de usuarios activos (30 min)'),
            ('cache_reportes_diarios', '3600', 'Caché de reportes diarios (1 hora)'),
        ]
        for k, v, d in configuraciones_cache:
            self.cursor.execute(
                """
                INSERT INTO configuracion_sistema (clave, valor, descripcion)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE valor=VALUES(valor), descripcion=VALUES(descripcion)
                """,
                (k, v, d),
            )
        self.conn.commit()
        print("✅ Sistema de caché configurado")

    def monitorear_recursos_sistema(self):
        print("📊 MONITOREANDO RECURSOS DEL SISTEMA...")
        cpu_percent = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        print(f"🔥 CPU: {cpu_percent}% | 🧠 Memoria: {mem.percent}% | 💾 Disco: {disk.percent}%")

    def __del__(self):
        try:
            self.cursor.close(); self.conn.close()
        except Exception:
            pass


def optimizar_sistema_produccion():
    print("⚡ OPTIMIZANDO SISTEMA PARA PRODUCCIÓN")
    print("=" * 60)
    opt = OptimizacionRendimiento()
    opt.optimizar_base_datos()
    opt.configurar_cache_sistema()
    opt.monitorear_recursos_sistema()
    print("\n🎉 OPTIMIZACIÓN COMPLETADA")


if __name__ == "__main__":
    optimizar_sistema_produccion()
