"""
Script para agregar columnas objeto_id y entrenado_ia a la tabla equipos
"""
import mysql.connector
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env_produccion si existe
if os.path.exists('.env_produccion'):
    load_dotenv('.env_produccion')

def ejecutar_migracion():
    """Ejecuta la migración para agregar columnas a equipos"""
    try:
        # Conectar a la base de datos usando la misma configuración que web_app.py
        conn = mysql.connector.connect(
            host=os.getenv('HOST', 'localhost'),
            user=os.getenv('USUARIO_PRODUCCION', 'laboratorio_prod'),
            password=os.getenv('PASSWORD_PRODUCCION', ''),
            database=os.getenv('BASE_DATOS', 'laboratorio_sistema'),
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        print("✓ Conectado a la base de datos")
        
        # Leer el archivo SQL
        sql_file = os.path.join('migrations', 'agregar_columnas_objeto_equipos.sql')
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Dividir en comandos individuales
        commands = []
        current_command = []
        in_delimiter = False
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # Ignorar comentarios y líneas vacías
            if not line or line.startswith('--'):
                continue
            
            # Detectar bloques SET @sql
            if 'SET @sql' in line:
                in_delimiter = True
            
            current_command.append(line)
            
            # Ejecutar cuando encontramos un punto y coma al final
            if line.endswith(';'):
                if in_delimiter and 'DEALLOCATE PREPARE stmt' in line:
                    in_delimiter = False
                    # Ejecutar el bloque completo
                    full_command = ' '.join(current_command)
                    commands.append(full_command)
                    current_command = []
                elif not in_delimiter:
                    full_command = ' '.join(current_command)
                    commands.append(full_command)
                    current_command = []
        
        # Ejecutar cada comando
        for i, command in enumerate(commands, 1):
            try:
                # Ejecutar comandos preparados línea por línea
                if 'SET @sql' in command:
                    # Dividir el bloque en comandos individuales
                    sub_commands = [cmd.strip() + ';' for cmd in command.split(';') if cmd.strip()]
                    for sub_cmd in sub_commands:
                        cursor.execute(sub_cmd)
                        result = cursor.fetchall() if cursor.description else None
                        if result:
                            for row in result:
                                print(f"  {row[0]}")
                else:
                    cursor.execute(command)
                    result = cursor.fetchall() if cursor.description else None
                    if result:
                        for row in result:
                            print(f"  {row[0]}")
                
                conn.commit()
            except mysql.connector.Error as e:
                # Ignorar errores de "ya existe" pero mostrar otros
                if 'already exists' not in str(e) and 'Duplicate' not in str(e):
                    print(f"⚠ Advertencia en comando {i}: {e}")
        
        print("\n✓ Migración completada exitosamente")
        
        # Verificar las columnas
        cursor.execute("DESCRIBE equipos")
        columns = cursor.fetchall()
        
        print("\n📋 Estructura actual de la tabla equipos:")
        print("-" * 80)
        for col in columns:
            print(f"  {col[0]:<25} {col[1]:<20} {col[2]:<5} {col[3]:<5} {col[4] or ''}")
        
        # Verificar si las columnas fueron agregadas
        column_names = [col[0] for col in columns]
        if 'objeto_id' in column_names and 'entrenado_ia' in column_names:
            print("\n✓ Las columnas objeto_id y entrenado_ia fueron agregadas correctamente")
        else:
            print("\n⚠ Advertencia: Algunas columnas no fueron agregadas")
            if 'objeto_id' not in column_names:
                print("  - Falta columna: objeto_id")
            if 'entrenado_ia' not in column_names:
                print("  - Falta columna: entrenado_ia")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"❌ Error de base de datos: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo de migración")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    print("=" * 80)
    print("MIGRACIÓN: Agregar columnas objeto_id y entrenado_ia a tabla equipos")
    print("=" * 80)
    print()
    
    if ejecutar_migracion():
        print("\n✓ Proceso completado exitosamente")
    else:
        print("\n❌ El proceso falló")
