# -*- coding: utf-8 -*-
"""
Setup de Base de Datos para Reconocimiento Facial
Centro Minero SENA
"""

import mysql.connector
import os
from dotenv import load_dotenv

# Cargar variables de entorno
if os.path.exists('.env_produccion'):
    load_dotenv('.env_produccion')

# Configuración de base de datos
DB_CONFIG = {
    'host': os.getenv('HOST', 'localhost'),
    'user': os.getenv('USUARIO_PRODUCCION', 'laboratorio_prod'),
    'password': os.getenv('PASSWORD_PRODUCCION', ''),
    'database': os.getenv('BASE_DATOS', 'laboratorio_sistema'),
    'charset': 'utf8mb4',
}

def setup_facial_tables():
    """Crear tablas para reconocimiento facial"""
    print("🗄️ CONFIGURANDO TABLAS PARA RECONOCIMIENTO FACIAL")
    print("=" * 60)
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Crear tabla usuarios_facial
        print("📋 Creando tabla 'usuarios_facial'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios_facial (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario_id VARCHAR(20) NOT NULL,
                encoding_facial LONGTEXT NOT NULL,
                imagen_referencia LONGBLOB,
                calidad_imagen DECIMAL(5,2) DEFAULT 0.0,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                activo BOOLEAN DEFAULT TRUE,
                notas TEXT,
                
                INDEX idx_usuario_id (usuario_id),
                INDEX idx_activo (activo),
                INDEX idx_fecha_registro (fecha_registro),
                
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Tabla 'usuarios_facial' creada")
        
        # Crear tabla logs_registro_facial
        print("📋 Creando tabla 'logs_registro_facial'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs_registro_facial (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario_id VARCHAR(20) NOT NULL,
                accion ENUM('registro', 'actualizacion', 'eliminacion', 'intento_fallido') NOT NULL,
                detalle TEXT,
                calidad_imagen DECIMAL(5,2),
                ip_origen VARCHAR(45),
                user_agent TEXT,
                exitoso BOOLEAN DEFAULT FALSE,
                fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_usuario_id (usuario_id),
                INDEX idx_accion (accion),
                INDEX idx_fecha_evento (fecha_evento),
                INDEX idx_exitoso (exitoso),
                
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ Tabla 'logs_registro_facial' creada")
        
        conn.commit()
        
        # Verificar tablas
        cursor.execute("SHOW TABLES LIKE '%facial%'")
        tables = cursor.fetchall()
        
        print(f"\n📊 Tablas creadas: {len(tables)}")
        for table in tables:
            print(f"  ✅ {table[0]}")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error de base de datos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """Función principal"""
    print("🚀 SETUP DE RECONOCIMIENTO FACIAL - CENTRO MINERO SENA")
    print("=" * 60)
    
    if setup_facial_tables():
        print("\n✅ SETUP COMPLETADO EXITOSAMENTE")
        print("\n🎯 PRÓXIMOS PASOS:")
        print("  1. Instalar dependencias: pip install face-recognition opencv-python")
        print("  2. Integrar API en web_app.py")
        print("  3. Reiniciar servidor web")
        print("  4. Probar registro facial")
    else:
        print("\n❌ SETUP FALLÓ")
        print("💡 Verifica permisos de base de datos")

if __name__ == "__main__":
    main()
