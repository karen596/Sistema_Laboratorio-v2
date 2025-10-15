# -*- coding: utf-8 -*-
# Sistema Web + API REST - Centro Minero SENA
# Interfaz Web Moderna + API RESTful Completa (Flask)

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import JWTManager, create_access_token, verify_jwt_in_request, get_jwt_identity
from flask_cors import CORS
import mysql.connector
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import base64
import cv2
import numpy as np
import re
import json
import secrets
from functools import wraps

# =====================================================================
# CONFIGURACIÓN DE LA APLICACIÓN WEB
# =====================================================================

# Cargar variables de entorno desde .env_produccion si existe
if os.path.exists('.env_produccion'):
    load_dotenv('.env_produccion')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)

# Extensiones
jwt = JWTManager(app)
api = Api(app)
CORS(app)

# =====================================================================
# CONEXIÓN A BASE DE DATOS
# =====================================================================

class DatabaseManager:
    def __init__(self):
        self.config = {
            'host': os.getenv('HOST', 'localhost'),
            'user': os.getenv('USUARIO_PRODUCCION', 'laboratorio_prod'),
            'password': os.getenv('PASSWORD_PRODUCCION', ''),
            'database': os.getenv('BASE_DATOS', 'laboratorio_sistema'),
            'charset': 'utf8mb4',
        }

    def get_connection(self):
        return mysql.connector.connect(**self.config)

    def execute_query(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.rowcount
            return result
        finally:
            cursor.close()
            conn.close()


db_manager = DatabaseManager()

# =====================================================================
# AUTENTICACIÓN Y SEGURIDAD (Decoradores)
# =====================================================================

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debe iniciar sesión para acceder', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def require_level(min_level):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_level' not in session or session['user_level'] < min_level:
                flash('No tiene permisos suficientes', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Permitir API si hay JWT válido o sesión web con rol admin
def verify_jwt_or_admin():
    try:
        verify_jwt_in_request()
        return True
    except Exception:
        # Fallback a sesión web: admin
        if session.get('user_id') and (
            str(session.get('user_type','')).lower() == 'admin' or int(session.get('user_level', 0)) >= 4
        ):
            return True
        # Re-lanzar para que el endpoint responda 401 si no cumple
        raise

# =====================================================================
# RUTAS WEB - INTERFAZ DE USUARIO
# =====================================================================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validar que se ingresaron ambos campos
        if not user_id or not password:
            flash('Por favor ingresa usuario y contraseña', 'error')
            return render_template('login.html')
        
        # Buscar usuario con contraseña
        query = "SELECT id, nombre, tipo, nivel_acceso, activo, password_hash FROM usuarios WHERE id = %s AND activo = TRUE"
        users = db_manager.execute_query(query, (user_id,))
        
        if users:
            user = users[0]
            stored_password = user.get('password_hash', '')
            
            # Validar contraseña (comparación directa por ahora, en producción usar hashing)
            if stored_password and stored_password == password:
                # Login exitoso
                session['user_id'] = user['id']
                session['user_name'] = user['nombre']
                session['user_type'] = user['tipo']
                session['user_level'] = user['nivel_acceso']
                
                log_query = (
                    """
                    INSERT INTO logs_seguridad (usuario_id, accion, detalle, ip_origen, exitoso)
                    VALUES (%s, 'login_web', 'Login exitoso desde interfaz web', %s, TRUE)
                    """
                )
                try:
                    db_manager.execute_query(log_query, (user['id'], request.remote_addr))
                except Exception:
                    pass
                
                flash(f"Bienvenido {user['nombre']}", 'success')
                return redirect(url_for('dashboard'))
            else:
                # Contraseña incorrecta
                flash('Usuario o contraseña incorrectos', 'error')
                log_query = (
                    """
                    INSERT INTO logs_seguridad (usuario_id, accion, detalle, ip_origen, exitoso)
                    VALUES (%s, 'login_web_fallido', 'Contraseña incorrecta', %s, FALSE)
                    """
                )
                try:
                    db_manager.execute_query(log_query, (user_id, request.remote_addr))
                except Exception:
                    pass
        else:
            # Usuario no encontrado
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Página de registro de nuevos usuarios"""
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        user_level = request.form.get('user_level', '')
        
        # Validaciones
        if not all([user_id, nombre, email, password, user_level]):
            flash('Todos los campos son requeridos', 'error')
            return render_template('registro.html')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('registro.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('registro.html')
        
        # Verificar si el usuario ya existe
        check_query = "SELECT id FROM usuarios WHERE id = %s OR email = %s"
        existing = db_manager.execute_query(check_query, (user_id, email))
        if existing:
            flash('El ID de usuario o correo ya están registrados', 'error')
            return render_template('registro.html')
        
        # Determinar tipo según nivel
        tipo_map = {'1': 'aprendiz', '2': 'instructor', '3': 'administrador'}
        tipo = tipo_map.get(user_level, 'aprendiz')
        
        # Insertar nuevo usuario con contraseña
        insert_query = """
            INSERT INTO usuarios (id, nombre, email, password_hash, tipo, nivel_acceso, activo)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        """
        try:
            db_manager.execute_query(insert_query, (user_id, nombre, email, password, tipo, int(user_level)))
            flash(f'Cuenta creada exitosamente. Bienvenido {nombre}!', 'success')
            
            # Auto-login
            session['user_id'] = user_id
            session['user_name'] = nombre
            session['user_type'] = tipo
            session['user_level'] = int(user_level)
            
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error al crear la cuenta: {str(e)}', 'error')
            return render_template('registro.html')
    
    return render_template('registro.html')


@app.route('/login_facial', methods=['POST'])
def login_facial():
    """Login mediante reconocimiento facial usando OpenCV (sin face_recognition)"""
    try:
        data = request.get_json()
        image_base64 = data.get('image')
        
        if not image_base64:
            return jsonify({'success': False, 'message': 'No se recibió imagen'})
        
        # Remover prefijo data:image si existe
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        # Decodificar imagen
        image_data = base64.b64decode(image_base64)
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'success': False, 'message': 'No se pudo procesar la imagen'})
        
        # Detectar rostro usando Haar Cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
        
        if len(faces) == 0:
            return jsonify({'success': False, 'message': 'No se detectó ningún rostro en la imagen'})
        
        if len(faces) > 1:
            return jsonify({'success': False, 'message': 'Se detectaron múltiples rostros. Solo debe aparecer tu rostro'})
        
        # Extraer región del rostro
        (x, y, w, h) = faces[0]
        face_roi = gray[y:y+h, x:x+w]
        face_roi = cv2.resize(face_roi, (200, 200))  # Normalizar tamaño
        
        # Calcular histograma del rostro capturado
        hist_captured = cv2.calcHist([face_roi], [0], None, [256], [0, 256])
        hist_captured = cv2.normalize(hist_captured, hist_captured).flatten()
        
        # Obtener usuarios con rostro registrado
        query = "SELECT id, nombre, tipo, nivel_acceso, rostro_data FROM usuarios WHERE rostro_data IS NOT NULL AND activo = TRUE"
        users = db_manager.execute_query(query)
        
        if not users:
            return jsonify({'success': False, 'message': 'No hay usuarios con reconocimiento facial registrado'})
        
        # Comparar con cada usuario registrado
        best_match = None
        best_similarity = 0
        threshold = 0.45  # Umbral de similitud (0-1, mayor = más similar) - Reducido para ser más permisivo
        
        print(f"[DEBUG FACIAL] Comparando con {len(users)} usuarios registrados...")
        
        for user in users:
            try:
                # Decodificar imagen almacenada
                stored_image_data = user['rostro_data']
                
                # Convertir BLOB a imagen
                nparr_stored = np.frombuffer(stored_image_data, np.uint8)
                stored_img = cv2.imdecode(nparr_stored, cv2.IMREAD_GRAYSCALE)
                
                if stored_img is None:
                    print(f"[DEBUG FACIAL] Usuario {user['nombre']}: No se pudo decodificar imagen")
                    continue
                
                # Redimensionar a mismo tamaño
                stored_img = cv2.resize(stored_img, (200, 200))
                
                # Calcular histograma de la imagen almacenada
                hist_stored = cv2.calcHist([stored_img], [0], None, [256], [0, 256])
                hist_stored = cv2.normalize(hist_stored, hist_stored).flatten()
                
                # Usar múltiples métodos de comparación para mayor precisión
                correl = cv2.compareHist(hist_captured, hist_stored, cv2.HISTCMP_CORREL)
                chisqr = cv2.compareHist(hist_captured, hist_stored, cv2.HISTCMP_CHISQR)
                intersect = cv2.compareHist(hist_captured, hist_stored, cv2.HISTCMP_INTERSECT)
                
                # Normalizar chi-square (menor es mejor, invertir)
                chisqr_norm = 1.0 / (1.0 + chisqr / 1000.0)
                
                # Normalizar intersección (0-1)
                intersect_norm = intersect / 200.0  # Normalizar por tamaño de imagen
                
                # Combinar métodos (promedio ponderado)
                similarity = (correl * 0.5) + (chisqr_norm * 0.2) + (intersect_norm * 0.3)
                
                print(f"[DEBUG FACIAL] Usuario {user['nombre']}:")
                print(f"  - Correlación: {correl:.4f}")
                print(f"  - Chi-Square: {chisqr:.2f} (norm: {chisqr_norm:.4f})")
                print(f"  - Intersección: {intersect:.2f} (norm: {intersect_norm:.4f})")
                print(f"  - Similitud combinada: {similarity:.4f} (umbral: {threshold})")
                
                # Si la similitud supera el umbral y es la mejor hasta ahora
                if similarity > threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = user
                    print(f"  ✓ NUEVO MEJOR MATCH!")
                    
            except Exception as e:
                print(f"[ERROR] Error comparando con usuario {user.get('nombre', 'unknown')}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"[DEBUG FACIAL] Mejor coincidencia: {best_match['nombre'] if best_match else 'Ninguna'}")
        print(f"[DEBUG FACIAL] Similitud final: {best_similarity:.4f}")
        
        # Si se encontró una coincidencia
        if best_match:
            confidence = best_similarity * 100  # Convertir a porcentaje
            
            session['user_id'] = best_match['id']
            session['user_name'] = best_match['nombre']
            session['user_type'] = best_match['tipo']
            session['user_level'] = best_match['nivel_acceso']
            
            log_query = """
                INSERT INTO logs_seguridad (usuario_id, accion, detalle, ip_origen, exitoso)
                VALUES (%s, 'login_facial', %s, %s, TRUE)
            """
            detalle = f'Login facial exitoso (similitud: {confidence:.1f}%)'
            try:
                db_manager.execute_query(log_query, (best_match['id'], detalle, request.remote_addr))
            except Exception:
                pass
            
            return jsonify({
                'success': True, 
                'message': f'Bienvenido {best_match["nombre"]}',
                'confidence': f'{confidence:.1f}%'
            })
        
        # No se encontró coincidencia
        log_query = """
            INSERT INTO logs_seguridad (usuario_id, accion, detalle, ip_origen, exitoso)
            VALUES (NULL, 'login_facial_fallido', 'Rostro no reconocido', %s, FALSE)
        """
        try:
            db_manager.execute_query(log_query, (request.remote_addr,))
        except Exception:
            pass
        
        return jsonify({'success': False, 'message': 'Rostro no reconocido. Acceso denegado.'})
        
    except Exception as e:
        print(f"[ERROR] Error en login facial: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error en el sistema: {str(e)}'})


@app.route('/logout')
def logout():
    if 'user_id' in session:
        log_query = (
            """
            INSERT INTO logs_seguridad (usuario_id, accion, detalle, ip_origen, exitoso)
            VALUES (%s, 'logout_web', 'Logout desde interfaz web', %s, TRUE)
            """
        )
        try:
            db_manager.execute_query(log_query, (session['user_id'], request.remote_addr))
        except Exception:
            pass
    session.clear()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('login'))


@app.route('/api/accesibilidad/toggle', methods=['POST'])
def accesibilidad_toggle():
    """API para activar/desactivar opciones de accesibilidad"""
    data = request.get_json()
    opcion = data.get('opcion')
    valor = data.get('valor')
    
    if 'accesibilidad' not in session:
        session['accesibilidad'] = {}
    
    session['accesibilidad'][opcion] = valor
    session.modified = True
    
    return jsonify({'success': True, 'opcion': opcion, 'valor': valor})


@app.route('/recuperar-contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    """Módulo de recuperación de contraseña - Enviar código por correo"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Por favor ingresa tu correo electrónico', 'error')
            return render_template('recuperar_contrasena.html')
        
        # Verificar que el usuario existe
        query = "SELECT id, nombre, email FROM usuarios WHERE email = %s AND activo = TRUE"
        users = db_manager.execute_query(query, (email,))
        
        if users:
            user = users[0]
            
            # Generar código de 6 dígitos
            import random
            codigo = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            expiry = datetime.now() + timedelta(minutes=15)  # Código válido por 15 minutos
            
            # Debug: Mostrar código generado
            print(f"[DEBUG] Código generado para {user['id']}: '{codigo}' (len: {len(codigo)})")
            print(f"[DEBUG] Expira en: {expiry}")
            
            # Guardar código en sesión
            user_id = user["id"]
            session[f'reset_code_{user_id}'] = {
                'code': codigo,
                'expiry': expiry.isoformat(),
                'email': email
            }
            
            print(f"[DEBUG] Código guardado en sesión: {session.get(f'reset_code_{user_id}')}")
            
            # Intentar enviar correo con código
            try:
                enviar_codigo_recuperacion(user['email'], user['nombre'], codigo)
                flash('Se ha enviado un código de verificación a tu correo electrónico. Revisa tu bandeja de entrada.', 'success')
                # Redirigir a la página de verificación de código
                return redirect(url_for('verificar_codigo', user_id=user['id']))
            except Exception as e:
                print(f"[ERROR] Error enviando correo: {str(e)}")
                import traceback
                traceback.print_exc()
                flash(f'No se pudo enviar el correo. Error: {str(e)}', 'error')
        else:
            # Por seguridad, no revelar si el email existe o no
            flash('Si el correo está registrado, recibirás un código de verificación en tu bandeja de entrada.', 'info')
    
    return render_template('recuperar_contrasena.html')


def enviar_codigo_recuperacion(email, nombre, codigo):
    """Enviar código de verificación de 6 dígitos por correo"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import ssl
    
    # Configuración del servidor SMTP de Gmail
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    
    print(f"[DEBUG] Intentando enviar código a: {email}")
    print(f"[DEBUG] SMTP Server: {smtp_server}:{smtp_port}")
    print(f"[DEBUG] SMTP User configurado: {'Sí - ' + smtp_user if smtp_user else 'No'}")
    print(f"[DEBUG] Password configurado: {'Sí' if smtp_password else 'No'}")
    
    if not smtp_user or not smtp_password:
        error_msg = 'Configuración de correo no disponible. Verifica que SMTP_USER y SMTP_PASSWORD estén en .env_produccion'
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] SMTP_USER actual: '{smtp_user}'")
        print(f"[ERROR] SMTP_PASSWORD actual: {'configurado' if smtp_password else 'vacío'}")
        raise Exception(error_msg)
    
    # Crear mensaje
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Código de Recuperación - Centro Minero SENA'
    msg['From'] = f'Centro Minero SENA <{smtp_user}>'
    msg['To'] = email
    
    # Contenido HTML del correo con código
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #1e5128 0%, #2d6a4f 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .code-box {{ background: #fff; border: 3px dashed #2d6a4f; padding: 20px; text-align: center; margin: 20px 0; border-radius: 10px; }}
            .code {{ font-size: 36px; font-weight: bold; color: #1e5128; letter-spacing: 8px; font-family: 'Courier New', monospace; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Código de Verificación</h1>
            </div>
            <div class="content">
                <p>Hola <strong>{nombre}</strong>,</p>
                <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en el Sistema de Gestión de Laboratorios del Centro Minero SENA.</p>
                
                <div class="code-box">
                    <p style="margin: 0; font-size: 14px; color: #666;">Tu código de verificación es:</p>
                    <div class="code">{codigo}</div>
                </div>
                
                <div class="warning">
                    <strong>⏰ Este código expirará en 15 minutos.</strong>
                </div>
                
                <p>Ingresa este código en la página de recuperación de contraseña para continuar.</p>
                <p>Si no solicitaste este cambio, puedes ignorar este correo de forma segura.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                
                <p style="font-size: 12px; color: #666;">
                    <strong>Consejos de seguridad:</strong><br>
                    • No compartas este código con nadie<br>
                    • El personal de SENA nunca te pedirá este código<br>
                    • Si no reconoces esta solicitud, cambia tu contraseña inmediatamente
                </p>
            </div>
            <div class="footer">
                <p>© 2025 Centro Minero SENA - Sistema de Gestión de Laboratorios</p>
                <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    part = MIMEText(html, 'html')
    msg.attach(part)
    
    # Enviar correo con manejo de errores mejorado
    try:
        print(f"[DEBUG] Conectando a {smtp_server}:{smtp_port}...")
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            print("[DEBUG] Conexión establecida")
            server.set_debuglevel(1)
            
            print("[DEBUG] Iniciando TLS...")
            server.starttls(context=context)
            print("[DEBUG] TLS iniciado")
            
            print("[DEBUG] Autenticando...")
            server.login(smtp_user, smtp_password)
            print("[DEBUG] Autenticación exitosa")
            
            print(f"[DEBUG] Enviando correo a {email}...")
            server.send_message(msg)
            print("[OK] Correo enviado exitosamente")
            
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Error de autenticación SMTP: {str(e)}. Verifica que SMTP_USER y SMTP_PASSWORD sean correctos. Para Gmail, usa una 'Contraseña de Aplicación'."
        print(f"[ERROR] {error_msg}")
        raise Exception(error_msg)
    except smtplib.SMTPException as e:
        error_msg = f"Error SMTP: {str(e)}"
        print(f"[ERROR] {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Error enviando correo: {str(e)}"
        print(f"[ERROR] {error_msg}")
        raise Exception(error_msg)


def enviar_correo_recuperacion(email, nombre, reset_link):
    """Enviar correo de recuperación de contraseña usando Gmail"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import ssl
    
    # Configuración del servidor SMTP de Gmail
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    
    print(f"[DEBUG] Intentando enviar correo a: {email}")
    print(f"[DEBUG] SMTP Server: {smtp_server}:{smtp_port}")
    print(f"[DEBUG] SMTP User: {smtp_user}")
    print(f"[DEBUG] Password configurado: {'Sí' if smtp_password else 'No'}")
    
    if not smtp_user or not smtp_password:
        error_msg = 'Configuración de correo no disponible. Configure SMTP_USER y SMTP_PASSWORD en .env_produccion'
        print(f"[ERROR] {error_msg}")
        raise Exception(error_msg)
    
    # Crear mensaje
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Recuperación de Contraseña - Centro Minero SENA'
    msg['From'] = f'Centro Minero SENA <{smtp_user}>'
    msg['To'] = email
    
    # Contenido HTML del correo
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #1e5128 0%, #2d6a4f 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 15px 30px; background: #2d6a4f; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Recuperación de Contraseña</h1>
            </div>
            <div class="content">
                <p>Hola <strong>{nombre}</strong>,</p>
                <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en el Sistema de Gestión de Laboratorios del Centro Minero SENA.</p>
                <p>Haz clic en el siguiente botón para crear una nueva contraseña:</p>
                <p style="text-align: center;">
                    <a href="{reset_link}" class="button">Restablecer Contraseña</a>
                </p>
                <p><strong>Este enlace expirará en 1 hora.</strong></p>
                <p>Si no solicitaste este cambio, puedes ignorar este correo de forma segura.</p>
                <hr>
                <p style="font-size: 12px; color: #666;">
                    Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
                    <a href="{reset_link}">{reset_link}</a>
                </p>
            </div>
            <div class="footer">
                <p>© 2025 Centro Minero SENA - Sistema de Gestión de Laboratorios</p>
                <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    part = MIMEText(html, 'html')
    msg.attach(part)
    
    # Enviar correo con manejo de errores mejorado
    try:
        print(f"[DEBUG] Conectando a {smtp_server}:{smtp_port}...")
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            print("[DEBUG] Conexión establecida")
            server.set_debuglevel(1)  # Activar debug para ver detalles
            
            print("[DEBUG] Iniciando TLS...")
            server.starttls(context=context)
            print("[DEBUG] TLS iniciado")
            
            print("[DEBUG] Autenticando...")
            server.login(smtp_user, smtp_password)
            print("[DEBUG] Autenticación exitosa")
            
            print(f"[DEBUG] Enviando correo a {email}...")
            server.send_message(msg)
            print("[OK] Correo enviado exitosamente")
            
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Error de autenticación SMTP: {str(e)}. Verifica que SMTP_USER y SMTP_PASSWORD sean correctos. Para Gmail, usa una 'Contraseña de Aplicación'."
        print(f"[ERROR] {error_msg}")
        raise Exception(error_msg)
    except smtplib.SMTPException as e:
        error_msg = f"Error SMTP: {str(e)}"
        print(f"[ERROR] {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Error enviando correo: {str(e)}"
        print(f"[ERROR] {error_msg}")
        raise Exception(error_msg)


@app.route('/verificar-codigo/<user_id>', methods=['GET', 'POST'])
def verificar_codigo(user_id):
    """Verificar código de 6 dígitos"""
    code_data = session.get(f'reset_code_{user_id}')
    
    if not code_data:
        flash('Sesión expirada. Solicita un nuevo código.', 'error')
        return redirect(url_for('recuperar_contrasena'))
    
    # Verificar expiración
    expiry = datetime.fromisoformat(code_data['expiry'])
    if datetime.now() > expiry:
        session.pop(f'reset_code_{user_id}', None)
        flash('El código ha expirado. Solicita uno nuevo.', 'error')
        return redirect(url_for('recuperar_contrasena'))
    
    if request.method == 'POST':
        codigo_ingresado = request.form.get('codigo', '').strip().replace(' ', '').replace('-', '')
        
        if not codigo_ingresado:
            flash('Por favor ingresa el código', 'error')
            return render_template('verificar_codigo.html', user_id=user_id, email=code_data.get('email', ''))
        
        # Debug: Imprimir códigos para comparación
        codigo_esperado = str(code_data['code']).strip()
        print(f"[DEBUG] Código ingresado: '{codigo_ingresado}' (len: {len(codigo_ingresado)})")
        print(f"[DEBUG] Código esperado: '{codigo_esperado}' (len: {len(codigo_esperado)})")
        print(f"[DEBUG] Comparación: {codigo_ingresado} == {codigo_esperado} -> {codigo_ingresado == codigo_esperado}")
        
        if codigo_ingresado == codigo_esperado:
            # Código correcto, marcar como verificado
            session[f'code_verified_{user_id}'] = True
            flash('Código verificado correctamente', 'success')
            return redirect(url_for('restablecer_contrasena', user_id=user_id))
        else:
            flash(f'Código incorrecto. Verifica e intenta nuevamente.', 'error')
            return render_template('verificar_codigo.html', user_id=user_id, email=code_data.get('email', ''))
    
    return render_template('verificar_codigo.html', user_id=user_id, email=code_data.get('email', ''))


@app.route('/restablecer-contrasena/<user_id>', methods=['GET', 'POST'])
def restablecer_contrasena(user_id):
    """Restablecer contraseña después de verificar código"""
    # Verificar que el código fue verificado
    if not session.get(f'code_verified_{user_id}'):
        flash('Primero debes verificar el código', 'error')
        return redirect(url_for('recuperar_contrasena'))
    
    if request.method == 'POST':
        nueva_contrasena = request.form.get('nueva_contrasena')
        confirmar_contrasena = request.form.get('confirmar_contrasena')
        
        if not nueva_contrasena or not confirmar_contrasena:
            flash('Todos los campos son requeridos', 'error')
            return render_template('restablecer_contrasena.html', user_id=user_id)
        
        if nueva_contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('restablecer_contrasena.html', user_id=user_id)
        
        if len(nueva_contrasena) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('restablecer_contrasena.html', user_id=user_id)
        
        # Actualizar contraseña en la base de datos
        # Nota: En producción, usar bcrypt para hashear la contraseña
        try:
            update_query = "UPDATE usuarios SET password_hash = %s WHERE id = %s"
            db_manager.execute_query(update_query, (nueva_contrasena, user_id))
            
            # Limpiar sesión
            session.pop(f'reset_code_{user_id}', None)
            session.pop(f'code_verified_{user_id}', None)
            
            flash('Contraseña actualizada exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error al actualizar contraseña: {str(e)}', 'error')
    
    return render_template('restablecer_contrasena.html', user_id=user_id)


@app.route('/ayuda')
def ayuda():
    """Manual de usuario interactivo"""
    return render_template('ayuda.html', user=session if 'user_id' in session else None)


@app.route('/design-system')
@require_login
@require_level(4)
def design_system():
    """Sistema de diseño - Solo para administradores"""
    return render_template('design_system.html', user=session)


@app.route('/modulos')
def modulos():
    """Vista de todos los módulos del proyecto"""
    return render_template('modulos_proyecto.html', user=session if 'user_id' in session else None)


@app.route('/perfil', methods=['GET', 'POST'])
@require_login
def perfil():
    """Editar perfil de usuario"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        programa = request.form.get('programa')
        
        query = """
            UPDATE usuarios 
            SET nombre = %s, email = %s, telefono = %s, programa = %s
            WHERE id = %s
        """
        try:
            db_manager.execute_query(query, (nombre, email, telefono, programa, session['user_id']))
            session['user_name'] = nombre
            flash('Perfil actualizado exitosamente', 'success')
        except Exception as e:
            flash(f'Error al actualizar perfil: {str(e)}', 'error')
        return redirect(url_for('perfil'))
    
    # GET - Mostrar formulario
    query = "SELECT id, nombre, email, telefono, tipo, programa, nivel_acceso FROM usuarios WHERE id = %s"
    user_data = db_manager.execute_query(query, (session['user_id'],))
    if user_data:
        return render_template('perfil.html', usuario=user_data[0], user=session)
    return redirect(url_for('dashboard'))


@app.route('/backup', methods=['GET', 'POST'])
@require_login
@require_level(4)
def backup():
    """Gestión de backups de base de datos"""
    import subprocess
    from pathlib import Path
    
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            # Crear backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f'backup_{timestamp}.sql'
            
            try:
                # Usar ruta completa de mysqldump si está disponible
                mysqldump_path = os.getenv('MYSQLDUMP_PATH', 'mysqldump')
                
                cmd = [
                    mysqldump_path,
                    '-h', os.getenv('HOST', 'localhost'),
                    '-u', os.getenv('USUARIO_PRODUCCION', 'laboratorio_prod'),
                    f"-p{os.getenv('PASSWORD_PRODUCCION', '')}",
                    '--single-transaction',
                    '--routines',
                    '--triggers',
                    os.getenv('BASE_DATOS', 'laboratorio_sistema')
                ]
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    subprocess.run(cmd, stdout=f, check=True, stderr=subprocess.PIPE)
                
                flash(f'Backup creado exitosamente: {backup_file.name}', 'success')
            except Exception as e:
                flash(f'Error creando backup: {str(e)}', 'error')
        
        elif action == 'restore':
            # Restaurar backup
            backup_name = request.form.get('backup_file')
            backup_file = backup_dir / backup_name
            
            if backup_file.exists():
                try:
                    # Usar ruta completa de mysql si está disponible
                    mysql_path = os.getenv('MYSQL_PATH', 'mysql')
                    
                    cmd = [
                        mysql_path,
                        '-h', os.getenv('HOST', 'localhost'),
                        '-u', os.getenv('USUARIO_PRODUCCION', 'laboratorio_prod'),
                        f"-p{os.getenv('PASSWORD_PRODUCCION', '')}",
                        os.getenv('BASE_DATOS', 'laboratorio_sistema')
                    ]
                    
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        subprocess.run(cmd, stdin=f, check=True, stderr=subprocess.PIPE)
                    
                    flash(f'Backup restaurado exitosamente: {backup_name}', 'success')
                except Exception as e:
                    flash(f'Error restaurando backup: {str(e)}', 'error')
            else:
                flash('Archivo de backup no encontrado', 'error')
        
        elif action == 'delete':
            # Eliminar backup
            backup_name = request.form.get('backup_file')
            backup_file = backup_dir / backup_name
            
            if backup_file.exists():
                try:
                    backup_file.unlink()  # Eliminar archivo
                    flash(f'Backup eliminado exitosamente: {backup_name}', 'success')
                except Exception as e:
                    flash(f'Error eliminando backup: {str(e)}', 'error')
            else:
                flash('Archivo de backup no encontrado', 'error')
        
        return redirect(url_for('backup'))
    
    # GET - Listar backups disponibles
    backups = []
    if backup_dir.exists():
        backups = [
            {
                'nombre': f.name,
                'tamaño': f'{f.stat().st_size / 1024 / 1024:.2f} MB',
                'fecha': datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            }
            for f in sorted(backup_dir.glob('*.sql'), key=lambda x: x.stat().st_mtime, reverse=True)
        ]
    
    return render_template('backup.html', backups=backups, user=session)


@app.route('/backup/download/<filename>')
@require_login
@require_level(4)
def download_backup(filename):
    """Descargar un archivo de backup"""
    from flask import send_file
    from pathlib import Path
    import os
    
    # Validar que el archivo existe y es un backup válido
    backup_dir = Path('backups')
    backup_file = backup_dir / filename
    
    # Seguridad: verificar que el archivo está dentro del directorio de backups
    try:
        backup_file = backup_file.resolve()
        backup_dir = backup_dir.resolve()
        
        if not str(backup_file).startswith(str(backup_dir)):
            flash('Acceso denegado: ruta inválida', 'error')
            return redirect(url_for('backup'))
        
        if not backup_file.exists() or not backup_file.is_file():
            flash('Archivo de backup no encontrado', 'error')
            return redirect(url_for('backup'))
        
        if not filename.endswith('.sql'):
            flash('Tipo de archivo no permitido', 'error')
            return redirect(url_for('backup'))
        
        # Enviar archivo para descarga
        return send_file(
            backup_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/sql'
        )
    
    except Exception as e:
        flash(f'Error descargando backup: {str(e)}', 'error')
        return redirect(url_for('backup'))


@app.route('/dashboard')
@require_login
def dashboard():
    stats = get_dashboard_stats()
    return render_template('dashboard.html', stats=stats, user=session)


@app.route('/laboratorios')
@require_login
def laboratorios():
    query = """
        SELECT 
            l.id, l.codigo, l.nombre, l.tipo, l.ubicacion, l.capacidad_estudiantes,
            l.responsable, l.estado,
            COUNT(DISTINCT e.id) as total_equipos,
            COUNT(DISTINCT i.id) as total_items,
            COUNT(DISTINCT CASE WHEN i.cantidad_actual <= i.cantidad_minima THEN i.id END) as items_criticos
        FROM laboratorios l
        LEFT JOIN equipos e ON l.id = e.laboratorio_id
        LEFT JOIN inventario i ON l.id = i.laboratorio_id
        GROUP BY l.id, l.codigo, l.nombre, l.tipo, l.ubicacion, l.capacidad_estudiantes, l.responsable, l.estado
        ORDER BY l.tipo, l.codigo
    """
    laboratorios_list = db_manager.execute_query(query)
    return render_template('laboratorios.html', laboratorios=laboratorios_list, user=session)


@app.route('/laboratorio/<int:laboratorio_id>')
@require_login
def laboratorio_detalle(laboratorio_id):
    # Información del laboratorio con estadísticas
    query_lab = """
        SELECT l.*,
               COUNT(DISTINCT e.id) as total_equipos,
               COUNT(DISTINCT i.id) as total_items,
               COUNT(DISTINCT CASE WHEN i.cantidad_actual <= i.cantidad_minima THEN i.id END) as items_criticos,
               COUNT(DISTINCT CASE WHEN e.estado = 'disponible' THEN e.id END) as equipos_disponibles
        FROM laboratorios l
        LEFT JOIN equipos e ON l.id = e.laboratorio_id
        LEFT JOIN inventario i ON l.id = i.laboratorio_id
        WHERE l.id = %s
        GROUP BY l.id
    """
    laboratorio = db_manager.execute_query(query_lab, (laboratorio_id,))
    if not laboratorio:
        flash('Laboratorio no encontrado', 'error')
        return redirect(url_for('laboratorios'))
    
    # Equipos de ESTE laboratorio
    query_equipos = """
        SELECT id, nombre, tipo, estado, ubicacion,
               DATE_FORMAT(ultima_calibracion, '%d/%m/%Y') as calibracion,
               DATE_FORMAT(proximo_mantenimiento, '%d/%m/%Y') as mantenimiento
        FROM equipos
        WHERE laboratorio_id = %s
        ORDER BY tipo, nombre
    """
    equipos = db_manager.execute_query(query_equipos, (laboratorio_id,))
    
    # Inventario de ESTE laboratorio
    query_inventario = """
        SELECT id, nombre, categoria, cantidad_actual, cantidad_minima,
               unidad, ubicacion, proveedor,
               DATE_FORMAT(fecha_vencimiento, '%d/%m/%Y') as vencimiento,
               CASE 
                   WHEN cantidad_actual <= cantidad_minima THEN 'critico'
                   WHEN cantidad_actual <= cantidad_minima * 1.5 THEN 'bajo'
                   ELSE 'normal'
               END as nivel_stock
        FROM inventario
        WHERE laboratorio_id = %s
        ORDER BY categoria, nombre
    """
    inventario = db_manager.execute_query(query_inventario, (laboratorio_id,))
    
    return render_template('laboratorio_detalle.html', 
                         laboratorio=laboratorio[0], 
                         equipos=equipos, 
                         inventario=inventario, 
                         user=session)


@app.route('/equipos')
@require_login
def equipos():
    query = """
        SELECT e.id, e.nombre, e.tipo, e.estado, e.ubicacion,
               e.laboratorio_id,
               l.nombre as laboratorio_nombre,
               l.codigo as laboratorio_codigo,
               DATE_FORMAT(e.ultima_calibracion, '%d/%m/%Y') as calibracion,
               DATE_FORMAT(e.proximo_mantenimiento, '%d/%m/%Y') as mantenimiento,
               e.especificaciones
        FROM equipos e
        INNER JOIN laboratorios l ON e.laboratorio_id = l.id
        ORDER BY l.nombre, e.tipo, e.nombre
    """
    equipos_list = db_manager.execute_query(query)
    for equipo in equipos_list:
        if equipo.get('especificaciones'):
            try:
                specs_obj = json.loads(equipo['especificaciones'])
                # Si tiene el formato nuevo con "descripcion", extraer el texto
                if isinstance(specs_obj, dict) and 'descripcion' in specs_obj:
                    equipo['especificaciones'] = specs_obj['descripcion']
                else:
                    equipo['especificaciones'] = specs_obj
            except Exception:
                equipo['especificaciones'] = {}
    return render_template('equipos.html', equipos=equipos_list, user=session)

@app.route('/equipos/crear', methods=['POST'])
@require_login
def crear_equipo_web():
    """Crear equipo desde interfaz web (sin JWT)"""
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        tipo = data.get('tipo')
        ubicacion = data.get('ubicacion')
        laboratorio_id = data.get('laboratorio_id', 1)  # Por defecto laboratorio 1
        especificaciones_texto = data.get('especificaciones', '')
        
        if not nombre or not tipo:
            return jsonify({'success': False, 'message': 'Nombre y tipo son requeridos'}), 400
        
        # Generar ID único
        import uuid
        equipo_id = f"EQ-{uuid.uuid4().hex[:8].upper()}"
        
        # Convertir texto a JSON válido
        especificaciones_json = json.dumps({"descripcion": especificaciones_texto})
        
        query = """
            INSERT INTO equipos (id, nombre, tipo, estado, ubicacion, laboratorio_id, especificaciones)
            VALUES (%s, %s, %s, 'disponible', %s, %s, %s)
        """
        db_manager.execute_query(query, (equipo_id, nombre, tipo, ubicacion, laboratorio_id, especificaciones_json))
        
        return jsonify({'success': True, 'message': 'Equipo creado exitosamente', 'id': equipo_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/inventario')
@require_login
def inventario():
    # Obtener todos los equipos con información del laboratorio
    query_equipos = """
        SELECT e.id, e.nombre, e.tipo, e.estado, e.ubicacion,
               e.laboratorio_id,
               l.nombre as laboratorio_nombre,
               l.codigo as laboratorio_codigo,
               DATE_FORMAT(e.ultima_calibracion, '%d/%m/%Y') as calibracion,
               DATE_FORMAT(e.proximo_mantenimiento, '%d/%m/%Y') as mantenimiento
        FROM equipos e
        INNER JOIN laboratorios l ON e.laboratorio_id = l.id
        ORDER BY l.nombre, e.tipo, e.nombre
    """
    equipos_list = db_manager.execute_query(query_equipos)
    
    # Obtener todos los items con información del laboratorio
    query_items = """
        SELECT i.id, i.nombre, i.categoria, i.cantidad_actual, i.cantidad_minima,
               i.unidad, i.ubicacion, i.proveedor, i.costo_unitario,
               i.laboratorio_id,
               l.nombre as laboratorio_nombre,
               l.codigo as laboratorio_codigo,
               DATE_FORMAT(i.fecha_vencimiento, '%d/%m/%Y') as vencimiento,
               CASE
                   WHEN i.cantidad_actual <= i.cantidad_minima THEN 'critico'
                   WHEN i.cantidad_actual <= i.cantidad_minima * 1.5 THEN 'bajo'
                   ELSE 'normal'
               END as nivel_stock
        FROM inventario i
        INNER JOIN laboratorios l ON i.laboratorio_id = l.id
        ORDER BY l.nombre, i.categoria, i.nombre
    """
    inventario_list = db_manager.execute_query(query_items)
    
    # Obtener lista de laboratorios para el filtro
    query_labs = "SELECT id, codigo, nombre FROM laboratorios WHERE estado = 'activo' ORDER BY nombre"
    laboratorios_list = db_manager.execute_query(query_labs)
    
    return render_template('inventario.html', 
                         equipos=equipos_list,
                         inventario=inventario_list, 
                         laboratorios=laboratorios_list,
                         user=session)


@app.route('/inventario/crear', methods=['POST'])
@require_login
def crear_item_inventario_web():
    """Crear item de inventario desde interfaz web (sin JWT)"""
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        categoria = data.get('categoria')
        cantidad_actual = data.get('cantidad_actual', 0)
        cantidad_minima = data.get('cantidad_minima', 0)
        unidad = data.get('unidad', 'unidad')
        ubicacion = data.get('ubicacion')
        laboratorio_id = data.get('laboratorio_id', 1)  # Por defecto laboratorio 1
        proveedor = data.get('proveedor')
        costo_unitario = data.get('costo_unitario', 0)
        
        if not nombre:
            return jsonify({'success': False, 'message': 'Nombre es requerido'}), 400
        
        # Generar ID único
        import uuid
        item_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        
        query = """
            INSERT INTO inventario (id, nombre, categoria, cantidad_actual, cantidad_minima, 
                                  unidad, ubicacion, laboratorio_id, proveedor, costo_unitario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        db_manager.execute_query(query, (item_id, nombre, categoria, cantidad_actual, 
                                        cantidad_minima, unidad, ubicacion, laboratorio_id,
                                        proveedor, costo_unitario))
        
        return jsonify({'success': True, 'message': 'Item de inventario creado exitosamente', 'id': item_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/reservas')
@require_login
def reservas():
    # Obtener lista de equipos disponibles para el formulario
    equipos_query = """
        SELECT id, nombre, tipo, estado 
        FROM equipos 
        WHERE estado IN ('disponible', 'en_uso')
        ORDER BY nombre
    """
    equipos_list = db_manager.execute_query(equipos_query) or []
    
    if session.get('user_level', 1) >= 3:
        query = (
            """
            SELECT r.id, 
                   DATE_FORMAT(r.fecha_inicio, '%d/%m/%Y %H:%i') as fecha_inicio,
                   DATE_FORMAT(r.fecha_fin, '%d/%m/%Y %H:%i') as fecha_fin,
                   r.estado,
                   u.nombre as usuario_nombre, 
                   e.nombre as equipo_nombre
            FROM reservas r
            JOIN usuarios u ON r.usuario_id = u.id
            JOIN equipos e ON r.equipo_id = e.id
            ORDER BY r.fecha_inicio DESC
            """
        )
        reservas_list = db_manager.execute_query(query) or []
    else:
        query = (
            """
            SELECT r.id,
                   DATE_FORMAT(r.fecha_inicio, '%d/%m/%Y %H:%i') as fecha_inicio,
                   DATE_FORMAT(r.fecha_fin, '%d/%m/%Y %H:%i') as fecha_fin,
                   r.estado,
                   u.nombre as usuario_nombre, 
                   e.nombre as equipo_nombre
            FROM reservas r
            JOIN usuarios u ON r.usuario_id = u.id
            JOIN equipos e ON r.equipo_id = e.id
            WHERE r.usuario_id = %s
            ORDER BY r.fecha_inicio DESC
            """
        )
        reservas_list = db_manager.execute_query(query, (session['user_id'],)) or []
    
    return render_template('reservas.html', reservas=reservas_list, equipos=equipos_list, user=session)


@app.route('/reservas/crear', methods=['POST'])
@require_login
def crear_reserva_web():
    """Crear reserva desde interfaz web (sin JWT)"""
    try:
        data = request.get_json()
        equipo_id = data.get('equipo_id')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        proposito = data.get('proposito')
        usuario_id = session.get('user_id')
        
        if not all([equipo_id, fecha_inicio, fecha_fin, proposito]):
            return jsonify({'success': False, 'message': 'Todos los campos son requeridos'}), 400
        
        # Verificar que el equipo existe
        query_equipo = "SELECT id FROM equipos WHERE id = %s"
        equipo = db_manager.execute_query(query_equipo, (equipo_id,))
        if not equipo:
            return jsonify({'success': False, 'message': 'El equipo no existe'}), 404
        
        # Generar ID único
        import uuid
        reserva_id = f"RES-{uuid.uuid4().hex[:8].upper()}"
        
        # Crear la reserva (usar 'notas' en lugar de 'proposito')
        query = """
            INSERT INTO reservas (id, equipo_id, usuario_id, fecha_inicio, fecha_fin, estado, notas)
            VALUES (%s, %s, %s, %s, %s, 'programada', %s)
        """
        db_manager.execute_query(query, (reserva_id, equipo_id, usuario_id, fecha_inicio, fecha_fin, proposito))
        
        return jsonify({'success': True, 'message': 'Reserva creada exitosamente'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/usuarios')
@require_login
@require_level(3)
def usuarios():
    query = (
        """
        SELECT id, nombre, tipo, programa, nivel_acceso, activo, email, telefono,
               DATE_FORMAT(fecha_registro, '%d/%m/%Y') as registro,
               CASE WHEN rostro_data IS NOT NULL THEN 'Sí' ELSE 'No' END as tiene_rostro
        FROM usuarios
        ORDER BY tipo, nombre
        """
    )
    usuarios_list = db_manager.execute_query(query)
    return render_template('usuarios.html', usuarios=usuarios_list, user=session)


@app.route('/reportes')
@require_login
@require_level(2)
def reportes():
    reportes_data = get_reportes_data()
    return render_template('reportes.html', reportes=reportes_data, user=session)


@app.route('/configuracion')
@require_login
@require_level(4)
def configuracion():
    query = "SELECT clave, valor, descripcion FROM configuracion_sistema ORDER BY clave"
    config_list = db_manager.execute_query(query) or []
    return render_template('configuracion.html', configuraciones=config_list, user=session)

@app.route('/entrenamiento-visual')
@require_login
def entrenamiento_visual():
    """Página para entrenar la IA de reconocimiento visual"""
    return render_template('entrenamiento_visual.html', user=session)


@app.route('/registro-facial')
@require_login
def registro_facial():
    """Página para registro facial de usuarios"""
    return render_template('registro_facial.html', user=session)


# =====================================================================
# FUNCIONES DE APOYO PARA VISTAS
# =====================================================================

def get_dashboard_stats():
    """Estadísticas mejoradas del dashboard con datos reales"""
    stats = {}
    
    # Equipos por estado
    eq = db_manager.execute_query("SELECT estado, COUNT(*) cantidad FROM equipos GROUP BY estado")
    stats['equipos_estado'] = {r['estado']: r['cantidad'] for r in eq} if eq else {}
    
    # Total de equipos activos (excluyendo fuera de servicio)
    activos = db_manager.execute_query("SELECT COUNT(*) cantidad FROM equipos WHERE estado != 'fuera_servicio'")
    stats['equipos_activos'] = activos[0]['cantidad'] if activos else 0
    
    # Equipos disponibles (más útil que críticos)
    disp = db_manager.execute_query("SELECT COUNT(*) cantidad FROM equipos WHERE estado = 'disponible'")
    stats['equipos_disponibles'] = disp[0]['cantidad'] if disp else 0
    
    # Items con stock bajo (más flexible que crítico)
    bajo = db_manager.execute_query("SELECT COUNT(*) cantidad FROM inventario WHERE cantidad_actual <= (cantidad_minima * 1.5)")
    stats['inventario_bajo'] = bajo[0]['cantidad'] if bajo else 0
    
    # Items bien abastecidos (información positiva)
    bien = db_manager.execute_query("SELECT COUNT(*) cantidad FROM inventario WHERE cantidad_actual > cantidad_minima")
    stats['inventario_bien'] = bien[0]['cantidad'] if bien else 0
    
    # Reservas próximas (incluye programadas y activas, sin filtro de fecha estricto)
    prox = db_manager.execute_query("SELECT COUNT(*) cantidad FROM reservas WHERE estado IN ('activa', 'programada')")
    stats['reservas_proximas'] = prox[0]['cantidad'] if prox else 0
    
    # Total de laboratorios activos
    labs = db_manager.execute_query("SELECT COUNT(*) cantidad FROM laboratorios WHERE estado = 'activo'")
    stats['total_laboratorios'] = labs[0]['cantidad'] if labs else 0
    
    # Total de items en inventario
    total_inv = db_manager.execute_query("SELECT COUNT(*) cantidad FROM inventario")
    stats['total_inventario'] = total_inv[0]['cantidad'] if total_inv else 0
    
    return stats


def get_reportes_data():
    data = {}
    q1 = (
        """
        SELECT e.nombre, COUNT(h.id) usos
        FROM equipos e
        LEFT JOIN historial_uso h ON e.id = h.equipo_id AND h.fecha_uso >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY e.id, e.nombre
        ORDER BY usos DESC
        LIMIT 10
        """
    )
    data['uso_equipos'] = db_manager.execute_query(q1)
    q2 = (
        """
        SELECT nombre, categoria, cantidad_actual, cantidad_minima
        FROM inventario
        WHERE cantidad_actual <= cantidad_minima
        ORDER BY (cantidad_actual - cantidad_minima)
        """
    )
    data['inventario_bajo'] = db_manager.execute_query(q2)
    q3 = (
        """
        SELECT u.nombre, u.tipo, COUNT(c.id) comandos
        FROM usuarios u
        LEFT JOIN comandos_voz c ON u.id = c.usuario_id AND c.fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY u.id, u.nombre, u.tipo
        ORDER BY comandos DESC
        LIMIT 10
        """
    )
    data['usuarios_activos'] = db_manager.execute_query(q3)
    return data

# =====================================================================
# API REST - ENDPOINTS PRINCIPALES
# =====================================================================

class AuthAPI(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', required=True, help='ID de usuario requerido')
        args = parser.parse_args()
        query = "SELECT id, nombre, tipo, nivel_acceso FROM usuarios WHERE id = %s AND activo = TRUE"
        users = db_manager.execute_query(query, (args['user_id'],))
        if users:
            user = users[0]
            access_token = create_access_token(
                identity=user['id'],
                additional_claims={'nombre': user['nombre'], 'tipo': user['tipo'], 'nivel': user['nivel_acceso']},
            )
            try:
                log_query = (
                    """
                    INSERT INTO logs_seguridad (usuario_id, accion, detalle, ip_origen, exitoso)
                    VALUES (%s, 'login_api', 'Login exitoso desde API', %s, TRUE)
                    """
                )
                db_manager.execute_query(log_query, (user['id'], request.remote_addr))
            except Exception:
                pass
            return {
                'access_token': access_token,
                'user': {
                    'id': user['id'],
                    'nombre': user['nombre'],
                    'tipo': user['tipo'],
                    'nivel_acceso': user['nivel_acceso'],
                },
            }, 200
        return {'message': 'Usuario no encontrado o inactivo'}, 401


class EquiposAPI(Resource):
    def get(self):
        # Permitir acceso con JWT o sesión web
        try:
            verify_jwt_in_request()
        except:
            # Fallback a sesión web
            if 'user_id' not in session:
                return {'message': 'Autenticación requerida'}, 401
        
        # Obtener todos los equipos (sin filtro de laboratorio ya que la columna no existe)
        query = """
            SELECT e.id, e.nombre, e.tipo, e.estado, e.ubicacion, e.especificaciones,
                   DATE_FORMAT(e.ultima_calibracion, '%Y-%m-%d') as ultima_calibracion,
                   DATE_FORMAT(e.proximo_mantenimiento, '%Y-%m-%d') as proximo_mantenimiento
            FROM equipos e
            ORDER BY e.tipo, e.nombre
        """
        params = []
        
        equipos = db_manager.execute_query(query, params)
        
        for e in equipos:
            if e.get('especificaciones'):
                try:
                    e['especificaciones'] = json.loads(e['especificaciones'])
                except Exception:
                    e['especificaciones'] = {}
        
        return {'equipos': equipos}, 200

    def post(self):
        verify_jwt_or_admin()
        data = request.get_json(silent=True) or {}
        
        # Validar campos requeridos
        if not data.get('nombre'):
            return {'message': 'nombre es requerido'}, 400
        if not data.get('tipo'):
            return {'message': 'tipo es requerido'}, 400
        
        import uuid
        equipo_id = f"EQ_{str(uuid.uuid4())[:8].upper()}"
        
        query = """
            INSERT INTO equipos (id, nombre, tipo, estado, ubicacion, especificaciones)
            VALUES (%s, %s, %s, 'disponible', %s, %s)
        """
        
        specs_json = json.dumps(data.get('especificaciones')) if data.get('especificaciones') else None
        
        try:
            db_manager.execute_query(query, (
                equipo_id, data['nombre'], data['tipo'], 
                data.get('ubicacion'), specs_json
            ))
            return {'message': 'Equipo creado exitosamente', 'id': equipo_id}, 201
        except Exception as e:
            return {'message': f'Error creando equipo: {str(e)}'}, 500


class EquipoAPI(Resource):
    def get(self, equipo_id):
        verify_jwt_in_request()
        query = (
            """
            SELECT id, nombre, tipo, estado, ubicacion, especificaciones,
                   DATE_FORMAT(ultima_calibracion, '%Y-%m-%d') as ultima_calibracion,
                   DATE_FORMAT(proximo_mantenimiento, '%Y-%m-%d') as proximo_mantenimiento
            FROM equipos WHERE id = %s
            """
        )
        rs = db_manager.execute_query(query, (equipo_id,))
        if not rs:
            return {'message': 'Equipo no encontrado'}, 404
        e = rs[0]
        if e.get('especificaciones'):
            try:
                e['especificaciones'] = json.loads(e['especificaciones'])
            except Exception:
                e['especificaciones'] = {}
        return {'equipo': e}, 200

    def put(self, equipo_id):
        # Permitir acceso con JWT o sesión web
        try:
            verify_jwt_in_request()
        except:
            # Fallback a sesión web
            if 'user_id' not in session:
                return {'message': 'Autenticación requerida'}, 401
        
        data = request.get_json(silent=True) or {}
        args = {
            'estado': data.get('estado'),
            'ubicacion': data.get('ubicacion'),
            'especificaciones': data.get('especificaciones')
        }
        updates, params = [], []
        if args['estado']:
            updates.append('estado = %s'); params.append(args['estado'])
        if args['ubicacion'] is not None:
            updates.append('ubicacion = %s'); params.append(args['ubicacion'])
        if args['especificaciones']:
            # Manejar especificaciones como string o dict
            if isinstance(args['especificaciones'], str):
                # Si es string, intentar parsear como JSON, si falla usar como texto
                try:
                    specs_dict = json.loads(args['especificaciones'])
                    updates.append('especificaciones = %s'); params.append(json.dumps(specs_dict))
                except:
                    # No es JSON válido, guardar como descripción
                    updates.append('especificaciones = %s'); params.append(json.dumps({'descripcion': args['especificaciones']}))
            else:
                updates.append('especificaciones = %s'); params.append(json.dumps(args['especificaciones']))
        if not updates:
            return {'message': 'No hay datos para actualizar'}, 400
        query = f"UPDATE equipos SET {', '.join(updates)} WHERE id = %s"
        params.append(equipo_id)
        try:
            affected = db_manager.execute_query(query, params)
            return ({'message': 'Equipo actualizado exitosamente'}, 200) if affected else ({'message': 'Equipo no encontrado'}, 404)
        except Exception as e:
            return {'message': f'Error actualizando equipo: {str(e)}'}, 500


class LaboratoriosAPI(Resource):
    def get(self):
        verify_jwt_in_request()
        tipo = request.args.get('tipo')
        estado = request.args.get('estado', 'activo')
        
        query = """
            SELECT l.id, l.codigo, l.nombre, l.tipo, l.ubicacion, l.capacidad_estudiantes,
                   l.area_m2, l.responsable, l.estado, l.equipamiento_especializado,
                   COUNT(DISTINCT e.id) as total_equipos,
                   COUNT(DISTINCT i.id) as total_items,
                   COUNT(DISTINCT CASE WHEN e.estado = 'disponible' THEN e.id END) as equipos_disponibles,
                   COUNT(DISTINCT CASE WHEN i.cantidad_actual <= i.cantidad_minima THEN i.id END) as items_criticos
            FROM laboratorios l
            LEFT JOIN equipos e ON l.id = e.laboratorio_id
            LEFT JOIN inventario i ON l.id = i.laboratorio_id
        """
        
        params, conds = [], []
        if tipo:
            conds.append('l.tipo = %s'); params.append(tipo)
        if estado:
            conds.append('l.estado = %s'); params.append(estado)
        
        if conds:
            query += ' WHERE ' + ' AND '.join(conds)
        
        query += ' GROUP BY l.id ORDER BY l.tipo, l.codigo'
        
        laboratorios = db_manager.execute_query(query, params)
        return {'laboratorios': laboratorios}, 200
    
    def post(self):
        verify_jwt_or_admin()
        data = request.get_json(silent=True) or {}
        
        campos_requeridos = ['codigo', 'nombre', 'tipo']
        for campo in campos_requeridos:
            if not data.get(campo):
                return {'message': f'{campo} es requerido'}, 400
        
        # Validar que codigo no sea vacío
        if not data['codigo'].strip():
            return {'message': 'codigo no puede estar vacío'}, 400
        
        # Verificar que el código no exista ya
        check_query = "SELECT id FROM laboratorios WHERE codigo = %s"
        existing = db_manager.execute_query(check_query, (data['codigo'],))
        if existing:
            return {'message': 'Ya existe un laboratorio con ese código'}, 400
        
        query = """
            INSERT INTO laboratorios (codigo, nombre, tipo, ubicacion, capacidad_estudiantes,
                                    area_m2, responsable, equipamiento_especializado, normas_seguridad)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            db_manager.execute_query(query, (
                data['codigo'], data['nombre'], data['tipo'],
                data.get('ubicacion', ''), data.get('capacidad_estudiantes', 0),
                data.get('area_m2'), data.get('responsable', ''),
                data.get('equipamiento_especializado', ''), data.get('normas_seguridad', '')
            ))
            return {'message': 'Laboratorio creado exitosamente'}, 201
        except Exception as e:
            return {'message': f'Error creando laboratorio: {str(e)}'}, 500


class LaboratorioAPI(Resource):
    def get(self, laboratorio_id):
        verify_jwt_in_request()
        
        # Información del laboratorio
        query_lab = """
            SELECT l.*, 
                   COUNT(DISTINCT e.id) as total_equipos,
                   COUNT(DISTINCT i.id) as total_items,
                   SUM(DISTINCT i.cantidad_actual * IFNULL(i.costo_unitario, 0)) as valor_inventario
            FROM laboratorios l
            LEFT JOIN equipos e ON l.id = e.laboratorio_id
            LEFT JOIN inventario i ON l.id = i.laboratorio_id
            WHERE l.id = %s
            GROUP BY l.id
        """
        
        laboratorio = db_manager.execute_query(query_lab, (laboratorio_id,))
        if not laboratorio:
            return {'message': 'Laboratorio no encontrado'}, 404
        
        return {'laboratorio': laboratorio[0]}, 200
    
    def put(self, laboratorio_id):
        verify_jwt_or_admin()
        data = request.get_json(silent=True) or {}
        
        campos_actualizables = [
            'nombre', 'ubicacion', 'capacidad_estudiantes', 'area_m2',
            'responsable', 'equipamiento_especializado', 'normas_seguridad', 'estado'
        ]
        
        updates, params = [], []
        for campo in campos_actualizables:
            if campo in data:
                updates.append(f'{campo} = %s')
                params.append(data[campo])
        
        if not updates:
            return {'message': 'No hay datos para actualizar'}, 400
        
        query = f"UPDATE laboratorios SET {', '.join(updates)} WHERE id = %s"
        params.append(laboratorio_id)
        
        try:
            affected = db_manager.execute_query(query, params)
            return ({'message': 'Laboratorio actualizado'}, 200) if affected else ({'message': 'Laboratorio no encontrado'}, 404)
        except Exception as e:
            return {'message': f'Error actualizando laboratorio: {str(e)}'}, 500


class InventarioAPI(Resource):
    def get(self):
        # Permitir acceso con JWT o sesión web
        try:
            verify_jwt_in_request()
        except:
            # Fallback a sesión web
            if 'user_id' not in session:
                return {'message': 'Autenticación requerida'}, 401
        
        laboratorio_id = request.args.get('laboratorio_id')
        categoria = request.args.get('categoria')
        stock_bajo = request.args.get('stock_bajo', 'false').lower() == 'true'
        
        if laboratorio_id:
            # Inventario específico de un laboratorio
            query = """
                SELECT i.id, i.nombre, i.categoria, i.cantidad_actual, i.cantidad_minima,
                       i.unidad, i.ubicacion, i.proveedor, i.costo_unitario,
                       DATE_FORMAT(i.fecha_vencimiento, '%Y-%m-%d') as fecha_vencimiento,
                       l.codigo as laboratorio_codigo, l.nombre as laboratorio_nombre
                FROM inventario i
                INNER JOIN laboratorios l ON i.laboratorio_id = l.id
                WHERE i.laboratorio_id = %s
            """
            params = [laboratorio_id]
        else:
            # Vista general con información de laboratorio
            query = """
                SELECT i.id, i.nombre, i.categoria, i.cantidad_actual, i.cantidad_minima,
                       i.unidad, i.ubicacion, i.proveedor, i.costo_unitario,
                       DATE_FORMAT(i.fecha_vencimiento, '%Y-%m-%d') as fecha_vencimiento,
                       l.codigo as laboratorio_codigo, l.nombre as laboratorio_nombre,
                       l.tipo as laboratorio_tipo
                FROM inventario i
                INNER JOIN laboratorios l ON i.laboratorio_id = l.id
            """
            params = []
        
        conds = []
        if categoria:
            conds.append('i.categoria = %s'); params.append(categoria)
        if stock_bajo:
            conds.append('i.cantidad_actual <= i.cantidad_minima')
        
        if conds:
            query += ' AND ' + ' AND '.join(conds)
        
        query += ' ORDER BY l.codigo, i.categoria, i.nombre'
        
        inventario = db_manager.execute_query(query, params)
        
        # Calcular nivel de stock
        for item in inventario:
            if item['cantidad_actual'] <= item['cantidad_minima']:
                item['nivel_stock'] = 'critico'
            elif item['cantidad_actual'] <= item['cantidad_minima'] * 1.5:
                item['nivel_stock'] = 'bajo'
            else:
                item['nivel_stock'] = 'normal'
        
        return {'inventario': inventario}, 200
    
    def post(self):
        verify_jwt_in_request()
        data = request.get_json(silent=True) or {}
        
        campos_requeridos = ['nombre', 'laboratorio_id', 'cantidad_actual', 'cantidad_minima']
        for campo in campos_requeridos:
            if not data.get(campo):
                return {'message': f'{campo} es requerido'}, 400
        
        # Verificar que el laboratorio existe
        lab_exists = db_manager.execute_query("SELECT id FROM laboratorios WHERE id = %s", (data['laboratorio_id'],))
        if not lab_exists:
            return {'message': 'Laboratorio no encontrado'}, 404
        
        query = """
            INSERT INTO inventario (nombre, categoria, cantidad_actual, cantidad_minima, unidad,
                                  ubicacion, proveedor, costo_unitario, fecha_vencimiento, laboratorio_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            db_manager.execute_query(query, (
                data['nombre'], data.get('categoria'), data['cantidad_actual'],
                data['cantidad_minima'], data.get('unidad'), data.get('ubicacion'),
                data.get('proveedor'), data.get('costo_unitario'),
                data.get('fecha_vencimiento'), data['laboratorio_id']
            ))
            return {'message': 'Item de inventario creado exitosamente'}, 201
        except Exception as e:
            return {'message': f'Error creando item: {str(e)}'}, 500


class ReservasAPI(Resource):
    def get(self):
        verify_jwt_in_request()
        current_user = get_jwt_identity()
        usuario_nivel = request.args.get('nivel_usuario', '1')
        if int(usuario_nivel) >= 3:
            query = (
                """
                SELECT r.id, r.usuario_id, r.equipo_id, r.fecha_inicio, r.fecha_fin,
                       r.estado, r.notas,
                       u.nombre as usuario_nombre, e.nombre as equipo_nombre
                FROM reservas r
                JOIN usuarios u ON r.usuario_id = u.id
                JOIN equipos e ON r.equipo_id = e.id
                ORDER BY r.fecha_inicio DESC
                """
            )
            reservas = db_manager.execute_query(query)
        else:
            query = (
                """
                SELECT r.id, r.usuario_id, r.equipo_id, r.fecha_inicio, r.fecha_fin,
                       r.estado, r.notas,
                       u.nombre as usuario_nombre, e.nombre as equipo_nombre
                FROM reservas r
                JOIN usuarios u ON r.usuario_id = u.id
                JOIN equipos e ON r.equipo_id = e.id
                WHERE r.usuario_id = %s
                ORDER BY r.fecha_inicio DESC
                """
            )
            reservas = db_manager.execute_query(query, (current_user,))
        return {'reservas': reservas}, 200

    def post(self):
        verify_jwt_in_request()
        current_user = get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('equipo_id', required=True)
        parser.add_argument('fecha_inicio', required=True)
        parser.add_argument('fecha_fin', required=True)
        parser.add_argument('notas')
        args = parser.parse_args()
        # Normalizar fechas (aceptar 'YYYY-MM-DDTHH:mm' de inputs HTML)
        def normalize(dt: str) -> str:
            dt = dt.replace('T', ' ').strip()
            # agregar segundos si faltan
            if len(dt) == 16:  # 'YYYY-MM-DD HH:MM'
                dt = dt + ":00"
            return dt
        fecha_inicio = normalize(args['fecha_inicio'])
        fecha_fin = normalize(args['fecha_fin'])
        # Validación simple de orden temporal
        try:
            dt_ini = datetime.strptime(fecha_inicio, '%Y-%m-%d %H:%M:%S')
            dt_fin = datetime.strptime(fecha_fin, '%Y-%m-%d %H:%M:%S')
            if dt_fin <= dt_ini:
                return {'message': 'La fecha fin debe ser posterior al inicio'}, 400
        except Exception:
            return {'message': 'Formato de fecha inválido'}, 400

        # Validar equipo
        try:
            rs = db_manager.execute_query("SELECT estado FROM equipos WHERE id=%s", (args['equipo_id'],))
        except Exception as e:
            return {'message': f'Error consultando equipo: {str(e)}'}, 500
        if not rs:
            return {'message': 'Equipo no encontrado'}, 404
        if rs[0]['estado'] != 'disponible':
            return {'message': 'Equipo no disponible'}, 400

        import uuid
        reserva_id = f"RES{str(uuid.uuid4())[:8].upper()}"
        try:
            db_manager.execute_query(
                """
                INSERT INTO reservas (id, usuario_id, equipo_id, fecha_inicio, fecha_fin, estado, notas)
                VALUES (%s, %s, %s, %s, %s, 'programada', %s)
                """,
                (reserva_id, current_user, args['equipo_id'], fecha_inicio, fecha_fin, args['notas']),
            )
            db_manager.execute_query("UPDATE equipos SET estado='en_uso' WHERE id=%s", (args['equipo_id'],))
            return {'message': 'Reserva creada exitosamente', 'reserva_id': reserva_id}, 201
        except Exception as e:
            return {'message': f'Error creando reserva: {str(e)}'}, 500


class ReservaAPI(Resource):
    def delete(self, reserva_id):
        verify_jwt_in_request()
        rs = db_manager.execute_query("SELECT usuario_id, equipo_id, estado FROM reservas WHERE id=%s", (reserva_id,))
        if not rs:
            return {'message': 'Reserva no encontrada'}, 404
        reserva = rs[0]
        if reserva['estado'] not in ['programada', 'activa']:
            return {'message': 'No se puede cancelar esta reserva'}, 400
        try:
            db_manager.execute_query("UPDATE reservas SET estado='cancelada' WHERE id=%s", (reserva_id,))
            db_manager.execute_query("UPDATE equipos SET estado='disponible' WHERE id=%s", (reserva['equipo_id'],))
            return {'message': 'Reserva cancelada exitosamente'}, 200
        except Exception as e:
            return {'message': f'Error cancelando reserva: {str(e)}'}, 500


class UsuariosAPI(Resource):
    def get(self):
        verify_jwt_in_request()
        query = (
            """
            SELECT id, nombre, tipo, programa, nivel_acceso, activo, email,
                   DATE_FORMAT(fecha_registro, '%Y-%m-%d') as fecha_registro,
                   CASE WHEN rostro_data IS NOT NULL THEN true ELSE false END as tiene_rostro
            FROM usuarios
            ORDER BY tipo, nombre
            """
        )
        usuarios = db_manager.execute_query(query)
        return {'usuarios': usuarios}, 200


class EstadisticasAPI(Resource):
    def get(self):
        verify_jwt_in_request()
        stats = get_dashboard_stats()
        q1 = (
            """
            SELECT u.programa, COUNT(DISTINCT h.id) usos
            FROM usuarios u
            LEFT JOIN historial_uso h ON u.id = h.usuario_id AND h.fecha_uso >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY u.programa
            ORDER BY usos DESC
            """
        )
        stats['uso_por_programa'] = db_manager.execute_query(q1)
        q2 = (
            """
            SELECT e.nombre, e.tipo, COUNT(h.id) usos
            FROM equipos e
            LEFT JOIN historial_uso h ON e.id = h.equipo_id AND h.fecha_uso >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY e.id, e.nombre, e.tipo
            ORDER BY usos DESC
            LIMIT 10
            """
        )
        stats['equipos_mas_usados'] = db_manager.execute_query(q2)
        return {'estadisticas': stats}, 200


class ComandosVozAPI(Resource):
    def post(self):
        # Comandos de voz sin autenticación para navegación simple
        parser = reqparse.RequestParser()
        parser.add_argument('comando', required=True)
        args = parser.parse_args()
        
        respuesta = procesar_comando_voz(args['comando'].lower().strip())
        
        # Intentar registrar el comando (opcional, sin fallar si no hay usuario)
        try:
            # Verificar si hay usuario logueado (opcional)
            current_user = None
            try:
                verify_jwt_in_request()
                current_user = get_jwt_identity()
            except:
                current_user = 'anonimo'  # Usuario anónimo para comandos de navegación
            
            db_manager.execute_query(
                """
                INSERT INTO comandos_voz (usuario_id, comando, respuesta, exito)
                VALUES (%s, %s, %s, %s)
                """,
                (current_user, args['comando'], respuesta['mensaje'], respuesta['exito']),
            )
        except Exception as e:
            # No fallar si no se puede registrar el comando
            print(f"No se pudo registrar comando de voz: {e}")
            pass
        
        return respuesta, 200


def procesar_comando_voz(comando: str):
    """
    Procesador de comandos de voz - Navegación entre módulos del sistema
    """
    comando = comando.lower().strip()
    
    # =============================
    # COMANDOS DE NAVEGACIÓN
    # =============================
    
    # Dashboard / Inicio
    if any(p in comando for p in ['dashboard', 'inicio', 'home', 'principal', 'tablero']):
        return {'mensaje': '📊 Navegando al dashboard...', 'exito': True, 'accion': 'navegar', 'url': '/dashboard'}
    
    # Laboratorios
    if any(p in comando for p in ['laboratorios', 'laboratorio', 'labs', 'lab']):
        return {'mensaje': '🔬 Navegando a laboratorios...', 'exito': True, 'accion': 'navegar', 'url': '/laboratorios'}
    
    # Equipos
    if any(p in comando for p in ['equipos', 'equipo', 'maquinaria', 'herramientas']):
        return {'mensaje': '⚙️ Navegando a equipos...', 'exito': True, 'accion': 'navegar', 'url': '/equipos'}
    
    # Inventario
    if any(p in comando for p in ['inventario', 'stock', 'almacén', 'almacen', 'reactivos', 'materiales']):
        return {'mensaje': '📦 Navegando a inventario...', 'exito': True, 'accion': 'navegar', 'url': '/inventario'}
    
    # Reservas
    if any(p in comando for p in ['reservas', 'reserva', 'reservaciones', 'reservación']):
        return {'mensaje': '📅 Navegando a reservas...', 'exito': True, 'accion': 'navegar', 'url': '/reservas'}
    
    # Usuarios
    if any(p in comando for p in ['usuarios', 'usuario', 'personas', 'estudiantes']):
        return {'mensaje': '👥 Navegando a usuarios...', 'exito': True, 'accion': 'navegar', 'url': '/usuarios'}
    
    # Reportes
    if any(p in comando for p in ['reportes', 'reporte', 'informes', 'estadísticas', 'estadisticas']):
        return {'mensaje': '📈 Navegando a reportes...', 'exito': True, 'accion': 'navegar', 'url': '/reportes'}
    
    # Configuración
    if any(p in comando for p in ['configuración', 'configuracion', 'ajustes', 'settings']):
        return {'mensaje': '⚙️ Navegando a configuración...', 'exito': True, 'accion': 'navegar', 'url': '/configuracion'}
    
    # Ayuda / Manual
    if any(p in comando for p in ['manual', 'ayuda general', 'documentación', 'documentacion', 'guía', 'guia']):
        return {'mensaje': '📖 Abriendo manual de usuario...', 'exito': True, 'accion': 'navegar', 'url': '/ayuda'}
    
    # Módulos del proyecto
    if any(p in comando for p in ['módulos', 'modulos', 'funcionalidades', 'características', 'caracteristicas']):
        return {'mensaje': '🧩 Navegando a módulos del proyecto...', 'exito': True, 'accion': 'navegar', 'url': '/modulos'}
    
    # Cerrar sesión
    if any(p in comando for p in ['cerrar sesión', 'cerrar sesion', 'salir', 'logout', 'desconectar']):
        return {'mensaje': '👋 Cerrando sesión...', 'exito': True, 'accion': 'navegar', 'url': '/logout'}
    
    # =============================
    # COMANDOS DE AYUDA
    # =============================
    
    if any(p in comando for p in ['ayuda', 'help', 'comandos', 'qué puedo decir', 'que puedo decir', 'opciones']):
        return {
            'mensaje': """🎤 Comandos de voz disponibles:
            
📍 NAVEGACIÓN:
• "Dashboard" o "Inicio" - Panel principal
• "Laboratorios" - Gestión de laboratorios
• "Equipos" - Gestión de equipos
• "Inventario" - Control de inventario y reactivos
• "Reservas" - Sistema de reservas
• "Usuarios" - Gestión de usuarios
• "Reportes" - Informes y estadísticas
• "Configuración" - Ajustes del sistema
• "Ayuda" - Manual de usuario
• "Módulos" - Ver funcionalidades del proyecto

🚪 SESIÓN:
• "Cerrar sesión" - Salir del sistema

💡 Tip: Puede decir variaciones como "ir a equipos", "mostrar inventario", etc.""", 
            'exito': True
        }
    
    # =============================
    # COMANDO NO RECONOCIDO
    # =============================
    
    return {
        'mensaje': f'❌ Comando "{comando}" no reconocido. Diga "ayuda" para ver todos los comandos disponibles.', 
        'exito': False
    }

# =====================================================================
# API DE RECONOCIMIENTO VISUAL
# =====================================================================

class VisualTrainingAPI(Resource):
    """API para entrenar el reconocimiento visual (versión mejorada con metadata completa)"""
    
    def post(self):
        """Agregar imagen de entrenamiento para un equipo o item"""
        data = request.get_json(silent=True) or {}
        item_type = data.get('item_type')  # 'equipo' o 'item'
        item_id = data.get('item_id')
        image_base64 = data.get('image_base64')
        description = data.get('description', '')
        view_angle = data.get('view_angle', 'frontal')
        
        if not item_type or item_type not in ['equipo', 'item']:
            return {'message': 'item_type debe ser "equipo" o "item"'}, 400
        if not item_id:
            return {'message': 'item_id es requerido'}, 400
        if not image_base64:
            return {'message': 'image_base64 es requerido'}, 400
        
        try:
            # Decodificar imagen base64
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            
            image_data = base64.b64decode(image_base64)
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return {'message': 'No se pudo decodificar la imagen'}, 400
            
            # Obtener detalles del item desde la base de datos
            item_details = {}
            if item_type == 'equipo':
                query = "SELECT id, nombre, tipo, estado, ubicacion, especificaciones FROM equipos WHERE id = %s"
                result = db_manager.execute_query(query, (item_id,))
                if result:
                    item_details = result[0]
                    # Parsear especificaciones JSON
                    if item_details.get('especificaciones'):
                        try:
                            item_details['especificaciones'] = json.loads(item_details['especificaciones'])
                        except:
                            item_details['especificaciones'] = {}
            else:
                query = "SELECT id, nombre, categoria, cantidad_actual, unidad, ubicacion FROM inventario WHERE id = %s"
                result = db_manager.execute_query(query, (item_id,))
                if result:
                    item_details = result[0]
            
            if not item_details:
                return {'message': f'{item_type} con ID {item_id} no encontrado en la base de datos'}, 404
            
            # Guardar imagen de entrenamiento
            base_dir = os.path.join('imagenes', 'entrenamiento', item_type, str(item_id))
            os.makedirs(base_dir, exist_ok=True)
            
            filename = f"{view_angle}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(base_dir, filename)
            cv2.imwrite(filepath, image)
            
            # Extraer características ORB para verificación
            orb = cv2.ORB_create(nfeatures=500)
            keypoints, descriptors = orb.detectAndCompute(image, None)
            num_features = len(keypoints) if keypoints else 0
            
            # Guardar metadatos completos incluyendo detalles del item
            metadata = {
                'description': description,
                'view_angle': view_angle,
                'filepath': filepath,
                'training_date': datetime.now().isoformat(),
                'num_features': num_features,
                'item_details': item_details  # Incluir todos los detalles del item
            }
            
            metadata_file = os.path.join(base_dir, 'metadata.json')
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    all_metadata = json.load(f)
            else:
                all_metadata = []
            
            all_metadata.append(metadata)
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(all_metadata, f, indent=2, ensure_ascii=False)
            
            return {
                'message': 'Imagen de entrenamiento guardada exitosamente',
                'filepath': filepath,
                'num_features': num_features,
                'total_images': len(all_metadata),
                'item_details': item_details
            }, 200
                
        except Exception as e:
            print(f"[ERROR] Error en entrenamiento visual: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'message': f'Error procesando imagen: {str(e)}'}, 500

class VisualRecognitionAPI(Resource):
    """API para reconocer equipos e items por imagen (versión simplificada)"""
    
    def post(self):
        """Reconocer equipo o item en una imagen"""
        data = request.get_json(silent=True) or {}
        image_base64 = data.get('image_base64')
        confidence_threshold = data.get('confidence_threshold', 0.3)
        
        if not image_base64:
            return {'message': 'image_base64 es requerido'}, 400
        
        try:
            # Decodificar imagen base64
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            
            image_data = base64.b64decode(image_base64)
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return {'message': 'No se pudo decodificar la imagen'}, 400
            
            # Buscar coincidencias en imágenes de entrenamiento usando comparación simple
            result = self._simple_recognition(image, confidence_threshold)
            
            if not result['success']:
                return {'message': result['message']}, 400
            
            # Si se reconoció algo, obtener detalles actualizados de la base de datos
            if result['recognized']:
                item_details = None
                
                # Primero intentar usar metadata guardada (tiene toda la info)
                if result.get('metadata'):
                    metadata = result['metadata']
                    
                    # Si tiene item_details (formato antiguo de entrenamiento)
                    if metadata.get('item_details'):
                        item_details = metadata['item_details']
                        item_details['tipo_item'] = result['item_type']
                        item_details['from_cache'] = True
                    
                    # Si tiene la metadata del registro (formato nuevo)
                    elif metadata.get('id') or metadata.get('nombre'):
                        item_details = {
                            'id': metadata.get('id'),
                            'nombre': metadata.get('nombre'),
                            'categoria': metadata.get('categoria'),
                            'descripcion': metadata.get('descripcion'),
                            'ubicacion': metadata.get('ubicacion'),
                            'laboratorio_id': metadata.get('laboratorio_id'),
                            'tipo_item': result['item_type'],
                            'from_cache': True
                        }
                        
                        # Agregar campos específicos según tipo
                        if result['item_type'] == 'equipo':
                            item_details['estado'] = metadata.get('estado', 'disponible')
                            item_details['equipo_id'] = metadata.get('equipo_id')
                        else:
                            item_details['cantidad_actual'] = metadata.get('cantidad')
                
                # Intentar obtener datos actualizados de la base de datos
                # Primero necesitamos el ID real del item
                db_id = None
                
                # Si metadata tiene el ID, usarlo
                if result.get('metadata') and result['metadata'].get('id'):
                    db_id = result['metadata']['id']
                # Si item_id es numérico, usarlo directamente
                elif result['item_id'].isdigit():
                    db_id = result['item_id']
                # Si no, buscar por nombre en la metadata
                elif result.get('metadata') and result['metadata'].get('nombre'):
                    nombre = result['metadata']['nombre']
                    if result['item_type'] == 'equipo':
                        search_query = "SELECT id FROM equipos WHERE nombre = %s LIMIT 1"
                    else:
                        search_query = "SELECT id FROM inventario WHERE nombre = %s LIMIT 1"
                    search_result = db_manager.execute_query(search_query, (nombre,))
                    if search_result:
                        db_id = search_result[0]['id']
                
                # Obtener datos frescos de la BD si tenemos el ID
                if db_id:
                    if result['item_type'] == 'equipo':
                        equipo_query = """
                            SELECT e.id, e.nombre, e.tipo, e.estado, e.ubicacion, e.especificaciones,
                                   e.laboratorio_id, l.nombre as laboratorio_nombre, l.ubicacion as laboratorio_ubicacion,
                                   e.equipo_id, e.marca, e.modelo, e.numero_serie, e.observaciones,
                                   DATE_FORMAT(e.fecha_creacion, '%Y-%m-%d %H:%i') as fecha_creacion
                            FROM equipos e
                            LEFT JOIN laboratorios l ON e.laboratorio_id = l.id
                            WHERE e.id = %s
                        """
                        equipo_data = db_manager.execute_query(equipo_query, (db_id,))
                        if equipo_data:
                            fresh_details = equipo_data[0]
                            # Parsear especificaciones JSON
                            if fresh_details.get('especificaciones'):
                                try:
                                    fresh_details['especificaciones'] = json.loads(fresh_details['especificaciones'])
                                except:
                                    fresh_details['especificaciones'] = {}
                            fresh_details['tipo_item'] = 'equipo'
                            fresh_details['from_cache'] = False
                            item_details = fresh_details
                    
                    elif result['item_type'] == 'item':
                        item_query = """
                            SELECT i.id, i.nombre, i.categoria, i.cantidad_actual, i.unidad, i.ubicacion,
                                   i.laboratorio_id, l.nombre as laboratorio_nombre, l.ubicacion as laboratorio_ubicacion,
                                   i.cantidad_minima, i.descripcion, i.proveedor,
                                   DATE_FORMAT(i.fecha_registro, '%Y-%m-%d %H:%i') as fecha_registro
                            FROM inventario i
                            LEFT JOIN laboratorios l ON i.laboratorio_id = l.id
                            WHERE i.id = %s
                        """
                        item_data = db_manager.execute_query(item_query, (db_id,))
                        if item_data:
                            fresh_details = item_data[0]
                            fresh_details['tipo_item'] = 'item'
                            fresh_details['from_cache'] = False
                            item_details = fresh_details
                
                # Si no se pudo obtener de BD pero tenemos metadata, enriquecer con info de laboratorio
                if not item_details or item_details.get('from_cache'):
                    if item_details and item_details.get('laboratorio_id'):
                        lab_query = "SELECT id, nombre, ubicacion FROM laboratorios WHERE id = %s"
                        lab_data = db_manager.execute_query(lab_query, (item_details['laboratorio_id'],))
                        if lab_data:
                            item_details['laboratorio_nombre'] = lab_data[0]['nombre']
                            item_details['laboratorio_ubicacion'] = lab_data[0]['ubicacion']
                
                return {
                    'recognized': True,
                    'confidence': result['confidence'],
                    'item_type': result['item_type'],
                    'item_id': result['item_id'],
                    'details': item_details,
                    'matches': result.get('matches', 0),
                    'training_metadata': result.get('metadata', {})  # Metadata del entrenamiento
                }, 200
            else:
                return {
                    'recognized': False,
                    'message': 'No se encontraron coincidencias suficientes. Entrene más imágenes de este item.',
                    'best_score': result.get('best_score', 0)
                }, 200
                
        except Exception as e:
            print(f"[ERROR] Error en reconocimiento: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'message': f'Error en reconocimiento: {str(e)}'}, 500
    
    def _simple_recognition(self, query_image, threshold=0.3):
        """Reconocimiento mejorado usando ORB con metadata completa"""
        try:
            print(f"\n[DEBUG RECONOCIMIENTO] Iniciando reconocimiento visual...")
            print(f"[DEBUG] Umbral de confianza: {threshold}")
            
            # Usar ORB para detectar características
            orb = cv2.ORB_create(nfeatures=500)
            kp1, des1 = orb.detectAndCompute(query_image, None)
            
            print(f"[DEBUG] Características detectadas en imagen query: {len(kp1) if kp1 else 0} keypoints")
            
            if des1 is None:
                return {'success': True, 'recognized': False, 'message': 'No se detectaron características en la imagen'}
            
            best_match = None
            best_score = 0
            best_metadata = None
            
            # BUSCAR EN DOS UBICACIONES:
            # 1. imagenes/entrenamiento/{tipo}/{id}/ (imágenes de entrenamiento manual)
            # 2. imagenes/{tipo}/{nombre}/ (imágenes del módulo de registro)
            
            search_paths = []
            
            # Crear directorios si no existen
            os.makedirs('imagenes/entrenamiento/equipo', exist_ok=True)
            os.makedirs('imagenes/entrenamiento/item', exist_ok=True)
            os.makedirs('imagenes/equipo', exist_ok=True)
            os.makedirs('imagenes/item', exist_ok=True)
            
            # Ruta 1: Entrenamiento manual
            training_base = 'imagenes/entrenamiento'
            if os.path.exists(training_base):
                for item_type in ['equipo', 'item']:
                    type_dir = os.path.join(training_base, item_type)
                    if os.path.exists(type_dir):
                        try:
                            for item_id in os.listdir(type_dir):
                                item_dir = os.path.join(type_dir, item_id)
                                if os.path.isdir(item_dir):
                                    search_paths.append({
                                        'path': item_dir,
                                        'type': item_type,
                                        'id': item_id,
                                        'source': 'training'
                                    })
                        except (OSError, PermissionError) as e:
                            print(f"[WARN] Error accediendo a {type_dir}: {e}")
                            continue
            
            # Ruta 2: Registro de equipos/items
            registro_base = 'imagenes'
            for item_type in ['equipo', 'item']:
                type_dir = os.path.join(registro_base, item_type)
                if os.path.exists(type_dir):
                    try:
                        for nombre_carpeta in os.listdir(type_dir):
                            item_dir = os.path.join(type_dir, nombre_carpeta)
                            if os.path.isdir(item_dir):
                                search_paths.append({
                                    'path': item_dir,
                                    'type': item_type,
                                    'id': nombre_carpeta,
                                    'source': 'registro'
                                })
                    except (OSError, PermissionError) as e:
                        print(f"[WARN] Error accediendo a {type_dir}: {e}")
                        continue
            
            print(f"[DEBUG] Total de carpetas a buscar: {len(search_paths)}")
            for sp in search_paths:
                print(f"  - {sp['type']}/{sp['id']} (fuente: {sp['source']})")
            
            if not search_paths:
                return {'success': True, 'recognized': False, 'message': 'No hay imágenes registradas. Registre equipos/items con fotos primero.'}
            
            # Buscar en todas las rutas
            total_comparisons = 0
            for search_info in search_paths:
                item_dir = search_info['path']
                item_type = search_info['type']
                item_id = search_info['id']
                
                print(f"\n[DEBUG] Buscando en: {item_dir}")
                
                # Cargar metadata del item
                metadata_file = os.path.join(item_dir, 'metadata.json')
                item_metadata = None
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata_content = json.load(f)
                            # Si es una lista (formato entrenamiento), usar el último
                            if isinstance(metadata_content, list):
                                item_metadata = metadata_content[-1] if metadata_content else None
                            # Si es un dict (formato registro), usar directamente
                            elif isinstance(metadata_content, dict):
                                item_metadata = metadata_content
                        print(f"[DEBUG] Metadata cargada: {item_metadata.get('nombre', 'N/A') if item_metadata else 'None'}")
                    except Exception as e:
                        print(f"[WARN] Error leyendo metadata de {metadata_file}: {e}")
                
                # Comparar con todas las imágenes de este item
                try:
                    images_in_dir = [f for f in os.listdir(item_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
                    print(f"[DEBUG] Imágenes encontradas: {len(images_in_dir)} -> {images_in_dir}")
                except (OSError, PermissionError) as e:
                    print(f"[WARN] Error listando imágenes en {item_dir}: {e}")
                    continue
                
                for img_file in images_in_dir:
                    img_path = os.path.join(item_dir, img_file)
                    train_img = cv2.imread(img_path)
                    if train_img is None:
                        print(f"[WARN] No se pudo leer imagen: {img_path}")
                        continue
                    
                    kp2, des2 = orb.detectAndCompute(train_img, None)
                    if des2 is None:
                        print(f"[WARN] No se detectaron características en: {img_file}")
                        continue
                    
                    # Comparar características
                    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                    matches = bf.match(des1, des2)
                    
                    # Calcular score basado en número de coincidencias
                    score = len(matches) / max(len(kp1), len(kp2))
                    total_comparisons += 1
                    
                    print(f"[DEBUG]   {img_file}: {len(matches)} matches, score={score:.4f} (kp_train={len(kp2)})")
                    
                    if score > best_score:
                        best_score = score
                        best_match = {
                            'item_type': item_type,
                            'item_id': item_id,
                            'matches': len(matches),
                            'score': score,
                            'source': search_info['source'],
                            'image_path': img_path
                        }
                        best_metadata = item_metadata
                        print(f"[DEBUG]   *** NUEVO MEJOR MATCH! ***")
            
            print(f"\n[DEBUG] Total de comparaciones realizadas: {total_comparisons}")
            print(f"[DEBUG] Mejor score encontrado: {best_score:.4f}")
            print(f"[DEBUG] Umbral requerido: {threshold:.4f}")
            print(f"[DEBUG] ¿Supera umbral?: {best_score >= threshold}")
            
            if best_match and best_score >= threshold:
                return {
                    'success': True,
                    'recognized': True,
                    'item_type': best_match['item_type'],
                    'item_id': best_match['item_id'],
                    'confidence': best_score,
                    'matches': best_match['matches'],
                    'metadata': best_metadata  # Incluir metadata guardada
                }
            else:
                return {
                    'success': True,
                    'recognized': False,
                    'best_score': best_score,
                    'message': f'Mejor coincidencia: {best_score:.2%} (umbral: {threshold:.2%}). Entrena más imágenes del item.'
                }
                
        except Exception as e:
            return {'success': False, 'message': str(e)}

class VisualStatsAPI(Resource):
    """API para estadísticas del sistema visual (simplificado)"""
    
    def get(self):
        """Obtener estadísticas del entrenamiento y registro"""
        try:
            stats = {
                'equipos_entrenados': 0,
                'items_entrenados': 0,
                'equipos_registrados': 0,
                'items_registrados': 0,
                'total_imagenes': 0,
                'imagenes_entrenamiento': 0,
                'imagenes_registro': 0
            }
            
            # Crear directorios si no existen
            os.makedirs('imagenes/entrenamiento/equipo', exist_ok=True)
            os.makedirs('imagenes/entrenamiento/item', exist_ok=True)
            os.makedirs('imagenes/equipo', exist_ok=True)
            os.makedirs('imagenes/item', exist_ok=True)
            
            # Contar imágenes de entrenamiento manual
            training_base = 'imagenes/entrenamiento'
            if os.path.exists(training_base):
                for item_type in ['equipo', 'item']:
                    type_dir = os.path.join(training_base, item_type)
                    if os.path.exists(type_dir):
                        try:
                            items = [d for d in os.listdir(type_dir) if os.path.isdir(os.path.join(type_dir, d))]
                            if item_type == 'equipo':
                                stats['equipos_entrenados'] = len(items)
                            else:
                                stats['items_entrenados'] = len(items)
                            
                            for item_id in items:
                                item_dir = os.path.join(type_dir, item_id)
                                try:
                                    images = [f for f in os.listdir(item_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
                                    count = len(images)
                                    stats['imagenes_entrenamiento'] += count
                                    stats['total_imagenes'] += count
                                except (OSError, PermissionError):
                                    continue
                        except (OSError, PermissionError):
                            continue
            
            # Contar imágenes de registro
            registro_base = 'imagenes'
            for item_type in ['equipo', 'item']:
                type_dir = os.path.join(registro_base, item_type)
                if os.path.exists(type_dir):
                    try:
                        items = [d for d in os.listdir(type_dir) if os.path.isdir(os.path.join(type_dir, d))]
                        if item_type == 'equipo':
                            stats['equipos_registrados'] = len(items)
                        else:
                            stats['items_registrados'] = len(items)
                        
                        for nombre_carpeta in items:
                            item_dir = os.path.join(type_dir, nombre_carpeta)
                            try:
                                images = [f for f in os.listdir(item_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
                                count = len(images)
                                stats['imagenes_registro'] += count
                                stats['total_imagenes'] += count
                            except (OSError, PermissionError):
                                continue
                    except (OSError, PermissionError):
                        continue
            
            return {'stats': stats}, 200
        except Exception as e:
            print(f"[ERROR] Error en VisualStatsAPI: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'message': f'Error obteniendo estadísticas: {str(e)}'}, 500

class VisualManagementAPI(Resource):
    """API para gestión de datos de entrenamiento (simplificado)"""
    
    def delete(self):
        """Eliminar datos de entrenamiento"""
        data = request.get_json(silent=True) or {}
        item_type = data.get('item_type')
        item_id = data.get('item_id')
        
        if not item_type or item_type not in ['equipo', 'item']:
            return {'message': 'item_type debe ser "equipo" o "item"'}, 400
        if not item_id:
            return {'message': 'item_id es requerido'}, 400
        
        try:
            import shutil
            item_dir = os.path.join('imagenes', 'entrenamiento', item_type, str(item_id))
            
            if not os.path.exists(item_dir):
                return {'message': 'No se encontraron datos de entrenamiento para este item'}, 404
            
            # Contar archivos antes de eliminar
            files = [f for f in os.listdir(item_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
            deleted_count = len(files)
            
            # Eliminar directorio completo
            shutil.rmtree(item_dir)
            
            return {
                'message': f'Datos de entrenamiento eliminados exitosamente',
                'deleted_files': deleted_count
            }, 200
                
        except Exception as e:
            return {'message': f'Error eliminando datos: {str(e)}'}, 500

# =====================================================================
# IMPORTAR MÓDULOS EXTERNOS ANTES DE REGISTRAR ENDPOINTS
# =====================================================================

# Implementación de API de registro facial
class FacialRegistrationAPI(Resource):
    """API para registrar rostro de usuario"""
    
    def post(self):
        """Registrar rostro de usuario"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            image_base64 = data.get('image')
            
            if not user_id or not image_base64:
                return {'success': False, 'message': 'Faltan datos requeridos (user_id, image)'}, 400
            
            # Remover prefijo data:image si existe
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            
            # Decodificar imagen
            image_data = base64.b64decode(image_base64)
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return {'success': False, 'message': 'No se pudo procesar la imagen'}, 400
            
            # Detectar rostro
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
            
            if len(faces) == 0:
                return {'success': False, 'message': 'No se detectó ningún rostro en la imagen'}, 400
            
            if len(faces) > 1:
                return {'success': False, 'message': 'Se detectaron múltiples rostros. Solo debe aparecer un rostro'}, 400
            
            # Extraer rostro y guardar
            (x, y, w, h) = faces[0]
            face_roi = img[y:y+h, x:x+w]
            
            # Redimensionar para almacenamiento
            face_roi = cv2.resize(face_roi, (200, 200))
            
            # Convertir a JPEG para almacenar
            _, buffer = cv2.imencode('.jpg', face_roi)
            face_blob = buffer.tobytes()
            
            # Actualizar usuario en la base de datos
            update_query = """
                UPDATE usuarios 
                SET rostro_data = %s
                WHERE id = %s
            """
            
            try:
                db_manager.execute_query(update_query, (face_blob, user_id))
                
                # Log de auditoría
                log_query = """
                    INSERT INTO logs_seguridad (usuario_id, accion, detalle, ip_origen, exitoso)
                    VALUES (%s, 'registro_facial', 'Rostro registrado exitosamente', %s, TRUE)
                """
                try:
                    db_manager.execute_query(log_query, (user_id, request.remote_addr))
                except:
                    pass
                
                return {
                    'success': True,
                    'message': 'Rostro registrado exitosamente',
                    'user_id': user_id
                }, 200
                
            except Exception as e:
                print(f"[ERROR] Error guardando rostro en BD: {e}")
                return {'success': False, 'message': f'Error guardando en base de datos: {str(e)}'}, 500
                
        except Exception as e:
            print(f"[ERROR] Error en registro facial: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'Error desconocido: {str(e)}'}, 500

FACIAL_API_AVAILABLE = True
print("[OK] Modulo de reconocimiento facial cargado (OpenCV)")

# =====================================================================
# REGISTRO DE ENDPOINTS API
# =====================================================================

api.add_resource(AuthAPI, '/api/auth')
api.add_resource(LaboratoriosAPI, '/api/laboratorios')
api.add_resource(LaboratorioAPI, '/api/laboratorios/<int:laboratorio_id>')
api.add_resource(EquiposAPI, '/api/equipos')
api.add_resource(EquipoAPI, '/api/equipos/<string:equipo_id>')
api.add_resource(InventarioAPI, '/api/inventario')
api.add_resource(ReservasAPI, '/api/reservas')
api.add_resource(ReservaAPI, '/api/reservas/<string:reserva_id>')
api.add_resource(UsuariosAPI, '/api/usuarios')
api.add_resource(EstadisticasAPI, '/api/estadisticas')
api.add_resource(ComandosVozAPI, '/api/voz/comando')
api.add_resource(FacialRegistrationAPI, '/api/facial/register')
api.add_resource(VisualTrainingAPI, '/api/visual/training')
api.add_resource(VisualRecognitionAPI, '/api/visual/recognize')
api.add_resource(VisualStatsAPI, '/api/visual/stats')
api.add_resource(VisualManagementAPI, '/api/visual/management')

# =============================
# VISIÓN POR CÁMARA (MVP)
# =============================

# Rutas absolutas seguras para imágenes
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_ROOT = os.path.join(BASE_DIR, 'imagenes')

# =============================
# INTEGRACIÓN DE IA AVANZADA
# =============================

# Inicializar sistema de IA avanzada
AI_MANAGER = None

try:
    from modules.ai_integration import create_ai_manager, enhance_vision_match_endpoint
    
    # Crear gestor de IA (se inicializará después de definir procesar_comando_voz)
    def initialize_ai_system():
        global AI_MANAGER
        if AI_MANAGER is None:
            AI_MANAGER = create_ai_manager(procesar_comando_voz, IMG_ROOT)
            if AI_MANAGER:
                print("[OK] Sistema de IA avanzada inicializado")
                # Iniciar control por voz si está disponible
                if AI_MANAGER.voice_ai_enabled:
                    AI_MANAGER.start_voice_control()
                    print("[OK] Control por voz avanzado activado")
            else:
                print("[WARN] Sistema de IA no disponible, usando metodos tradicionales")
        return AI_MANAGER
    
    AI_AVAILABLE = True
    
except ImportError as e:
    print(f"[WARN] Modulos de IA no disponibles: {e}")
    AI_AVAILABLE = False
    AI_MANAGER = None
    
    def initialize_ai_system():
        return None

def _decode_image_base64(img_b64: str):
    try:
        if ',' in img_b64:  # dataURL
            img_b64 = img_b64.split(',')[1]
        img_bytes = base64.b64decode(img_b64)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return frame
    except Exception:
        return None

def _safe_imread(path: str):
    try:
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is not None:
            return img
        # Fallback: leer bytes y decodificar
        with open(path, 'rb') as f:
            buf = f.read()
        arr = np.frombuffer(buf, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        return None


def _load_template_images():
    templates = []

    # Utilidad para sanitizar carpeta->nombre
    import re
    def san(s: str) -> str:
        s = (s or '').lower().replace('..','').replace('/','').replace('\\','')
        s = re.sub(r"[^a-z0-9_\- ]+", '', s).strip()
        s = re.sub(r"\s+", '_', s)
        return s

    # 1) Plantillas de EQUIPOS por nombre (mapeadas a id)
    base_eq = os.path.join(IMG_ROOT, 'equipos')
    if os.path.isdir(base_eq):
        try:
            rs = db_manager.execute_query("SELECT id, nombre FROM equipos") or []
        except Exception:
            rs = []
        name_to_id = { san(r['nombre']): str(r['id']) for r in rs }
        for entry in os.listdir(base_eq):
            folder_path = os.path.join(base_eq, entry)
            if not os.path.isdir(folder_path):
                continue
            eid_or_key = name_to_id.get(san(entry))  # si None, trataremos como OBJETO por nombre de carpeta
            for root, _, files in os.walk(folder_path):
                for fn in files:
                    if not fn.lower().endswith(('.jpg', '.jpeg', '.png')):
                        continue
                    path = os.path.join(root, fn)
                    img = _safe_imread(path)
                    if img is None:
                        continue
                    templates.append((eid_or_key if eid_or_key else san(entry), img))
            # no hacer break: recorrer todas las subcarpetas (superior/inferior/etc.)

    # 2) Plantillas de OBJETOS por nombre (clave = nombre carpeta)
    base_obj = os.path.join(IMG_ROOT, 'objetos')
    if os.path.isdir(base_obj):
        for entry in os.listdir(base_obj):
            folder_path = os.path.join(base_obj, entry)
            if not os.path.isdir(folder_path):
                continue
            key = entry  # usamos nombre de carpeta
            for root, _, files in os.walk(folder_path):
                for fn in files:
                    if not fn.lower().endswith(('.jpg', '.jpeg', '.png')):
                        continue
                    path = os.path.join(root, fn)
                    img = _safe_imread(path)
                    if img is None:
                        continue
                    templates.append((key, img))
            # no hacer break: recorrer todas las subcarpetas (superior/inferior/etc.)

    # 3) Plantillas de OBJETOS desde BD (BLOB)
    try:
        rows = db_manager.execute_query(
            """
            SELECT o.nombre, oi.imagen
            FROM objetos_imagenes oi
            JOIN objetos o ON o.id = oi.objeto_id
            """
        ) or []
        for r in rows:
            blob = r.get('imagen')
            if not blob:
                continue
            img_arr = np.frombuffer(blob, dtype=np.uint8)
            img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
            if img is None:
                continue
            templates.append((san(r['nombre']), img))
    except Exception:
        pass

    # 4) Plantillas desde cualquier otra carpeta top-level dentro de 'imagenes/'
    base_root = IMG_ROOT
    if os.path.isdir(base_root):
        for entry in os.listdir(base_root):
            if entry in ('equipos','objetos'):
                continue
            folder_path = os.path.join(base_root, entry)
            if not os.path.isdir(folder_path):
                continue
            key = san(entry)
            for root, _, files in os.walk(folder_path):
                for fn in files:
                    if not fn.lower().endswith(('.jpg', '.jpeg', '.png')):
                        continue
                    path = os.path.join(root, fn)
                    img = cv2.imread(path, cv2.IMREAD_COLOR)
                    if img is None:
                        continue
                    templates.append((key, img))

    return templates

# Endpoint de diagnóstico: lista carpetas y archivos detectados por visión
@app.get('/api/vision/debug_templates')
def vision_debug_templates():
    report = {'equipos': {}, 'objetos': {}, 'otros': {}}
    import re
    def san(s: str) -> str:
        s = (s or '').lower().replace('..','').replace('/','').replace('\\','')
        s = re.sub(r"[^a-z0-9_\- ]+", '', s).strip()
        s = re.sub(r"\s+", '_', s)
        return s
    # Equipos
    base_eq = os.path.join('imagenes', 'equipos')
    if os.path.isdir(base_eq):
        try:
            rs = db_manager.execute_query("SELECT id, nombre FROM equipos") or []
        except Exception:
            rs = []
        name_to_id = { san(r['nombre']): str(r['id']) for r in rs }
        for entry in os.listdir(base_eq):
            folder_path = os.path.join(base_eq, entry)
            if not os.path.isdir(folder_path):
                continue
            eid = name_to_id.get(san(entry))
            info = {'equipo_id': eid, 'path': folder_path, 'files': []}
            for root, _, files in os.walk(folder_path):
                for fn in files:
                    if fn.lower().endswith(('.jpg','.jpeg','.png')):
                        info['files'].append(os.path.join(root, fn).replace('\\','/'))
            report['equipos'][entry] = info
    # Objetos (FS y BD)
    base_obj = os.path.join('imagenes', 'objetos')
    if os.path.isdir(base_obj):
        for entry in os.listdir(base_obj):
            folder_path = os.path.join(base_obj, entry)
            if not os.path.isdir(folder_path):
                continue
            info = {'path': folder_path, 'files': []}
            for root, _, files in os.walk(folder_path):
                for fn in files:
                    if fn.lower().endswith(('.jpg','.jpeg','.png')):
                        info['files'].append(os.path.join(root, fn).replace('\\','/'))
            report['objetos'][entry] = info
    # Otros top-level bajo imagenes/
    base_root = 'imagenes'
    if os.path.isdir(base_root):
        for entry in os.listdir(base_root):
            if entry in ('equipos','objetos'):
                continue
            folder_path = os.path.join(base_root, entry)
            if not os.path.isdir(folder_path):
                continue
            info = {'path': folder_path, 'files': []}
            for root, _, files in os.walk(folder_path):
                for fn in files:
                    if fn.lower().endswith(('.jpg','.jpeg','.png')):
                        info['files'].append(os.path.join(root, fn).replace('\\','/'))
            report['otros'][entry] = info
    # Resumen desde BD
    try:
        db_rows = db_manager.execute_query("SELECT o.nombre, COUNT(oi.id) c FROM objetos o LEFT JOIN objetos_imagenes oi ON oi.objeto_id=o.id GROUP BY o.id, o.nombre") or []
        report['objetos_db'] = { r['nombre']: r['c'] for r in db_rows }
    except Exception:
        report['objetos_db'] = {}
    return jsonify(report), 200

# Conteo de plantillas cargadas (para depurar casos "no se encontraron plantillas")
@app.get('/api/vision/debug_counts')
def vision_debug_counts():
    templates = _load_template_images_slim(max_per_key=12)
    return jsonify({
        'total_templates': len(templates),
        'cwd': os.getcwd(),
        'img_root': IMG_ROOT,
    }), 200


def _match_orb_flann(frame: np.ndarray, templates, min_good=10):
    try:
        orb = cv2.ORB_create(nfeatures=1500)
        kp1, des1 = orb.detectAndCompute(frame, None)
        if des1 is None:
            return None
        index_params = dict(algorithm=6,  # FLANN_INDEX_LSH
                            table_number=12, key_size=20, multi_probe_level=2)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        best = None  # (key, score)
        for eid, tmpl in templates:
            kp2, des2 = orb.detectAndCompute(tmpl, None)
            if des2 is None:
                continue
            matches = flann.knnMatch(des1, des2, k=2)
            good = []
            for m, n in matches:
                if m.distance < 0.7 * n.distance:
                    good.append(m)
            score = len(good)
            if best is None or score > best[1]:
                best = (eid, score)
        if best:
            if best[1] >= min_good:
                return {'equipo_id': best[0], 'score': int(best[1]), 'passed': True}
            else:
                return {'equipo_id': best[0], 'score': int(best[1]), 'passed': False}
        return None
    except Exception:
        return None


@app.post('/api/vision/match')
def vision_match():
    # No exigimos JWT por ahora, pero se puede agregar verify_jwt_in_request()
    data = request.get_json(silent=True) or {}
    img_b64 = data.get('image_base64')
    if not img_b64:
        return jsonify({'message': 'image_base64 requerido'}), 400
    
    # Intentar con IA avanzada primero
    if AI_MANAGER and AI_MANAGER.vision_ai_enabled:
        try:
            ai_result = AI_MANAGER.detect_objects_advanced(img_b64)
            if ai_result.get('success'):
                detection = ai_result['detection_result']
                if detection.get('detected'):
                    # Buscar en BD si es un objeto conocido
                    key = detection['class']
                    import re
                    def san(s: str) -> str:
                        s = (s or '').lower().replace('..','').replace('/','').replace('\\','')
                        s = re.sub(r"[^a-z0-9_\- ]+", '', s).strip()
                        s = re.sub(r"\s+", '_', s)
                        return s
                    
                    # Buscar objeto por nombre
                    objs = db_manager.execute_query("SELECT id, nombre, categoria, descripcion FROM objetos") or []
                    found = None
                    for o in objs:
                        if san(o['nombre']) == san(key):
                            found = o; break
                    
                    if found:
                        return jsonify({
                            'tipo': 'objeto',
                            'objeto': found,
                            'match': {
                                'equipo_id': key,
                                'score': int(detection['confidence'] * 100),
                                'passed': detection['confidence'] > 0.5,
                                'ai_enhanced': True,
                                'method': 'tensorflow'
                            },
                            'message': f'🤖 IA: {detection["class"]} (confianza: {detection["confidence"]:.2f})'
                        }), 200
                    else:
                        return jsonify({
                            'tipo': 'sugerencia',
                            'categoria': 'objeto',
                            'key': key,
                            'match': {
                                'equipo_id': key,
                                'score': int(detection['confidence'] * 100),
                                'passed': False,
                                'ai_enhanced': True,
                                'method': 'tensorflow'
                            },
                            'message': f'🤖 IA detectó: {key} (no registrado en BD)'
                        }), 200
        except Exception as e:
            print(f"Error en IA de visión: {e}")
    
    # Fallback a método tradicional
    frame = _decode_image_base64(img_b64)
    frame = _preprocess_for_orb(frame)
    if frame is None:
        return jsonify({'message': 'Imagen inválida'}), 400
    templates = _load_template_images_slim(max_per_key=12)
    if not templates:
        return jsonify({'message': 'No hay plantillas en imagenes/equipos u objetos'}), 404
    match = _match_orb_flann(frame, templates)
    if not match:
        return jsonify({'message': 'Sin coincidencias'}), 200

    key = str(match.get('equipo_id'))
    # Si key es numérica, tratamos como equipo
    if key.isdigit():
        rs = db_manager.execute_query("SELECT id, nombre, estado, ubicacion FROM equipos WHERE id=%s", (key,))
        if not rs:
            if match and match.get('passed') is False:
                return jsonify({'tipo': 'sugerencia', 'categoria': 'equipo', 'key': key, 'score': match.get('score'), 'message': 'Sugerencia de equipo (baja confianza)'}), 200
            return jsonify({'match': match, 'message': 'Coincidencia de equipo, pero no encontrado en BD'}), 200
        if match.get('passed'):
            return jsonify({'tipo': 'equipo', 'equipo': rs[0], 'match': match, 'message': 'Coincidencia de equipo encontrada'}), 200
        else:
            return jsonify({'tipo': 'sugerencia', 'categoria': 'equipo', 'equipo': rs[0], 'match': match, 'message': 'Sugerencia de equipo (baja confianza)'}), 200

    # Caso objeto: key es nombre de carpeta. Buscar objeto por nombre saneado
    import re
    def san(s: str) -> str:
        s = (s or '').lower().replace('..','').replace('/','').replace('\\','')
        s = re.sub(r"[^a-z0-9_\- ]+", '', s).strip()
        s = re.sub(r"\s+", '_', s)
        return s
    objs = db_manager.execute_query("SELECT id, nombre, categoria, descripcion FROM objetos") or []
    found = None
    for o in objs:
        if san(o['nombre']) == san(key):
            found = o; break
    if found:
        if match.get('passed'):
            return jsonify({'tipo': 'objeto', 'objeto': found, 'match': match, 'message': 'Coincidencia de objeto encontrada'}), 200
        else:
            return jsonify({'tipo': 'sugerencia', 'categoria': 'objeto', 'objeto': found, 'match': match, 'message': 'Sugerencia de objeto (baja confianza)'}), 200
    # No está en BD pero hay key (nombre de carpeta)
    if not key.isdigit():
        return jsonify({'tipo': 'sugerencia', 'categoria': 'objeto', 'key': key, 'match': match, 'message': 'Sugerencia de objeto por carpeta (no mapeada a BD)'}), 200
    return jsonify({'match': match, 'message': 'Coincidencia encontrada, pero no mapeada a BD'}), 200

# =============================
# OBJETOS: Registro unificado (crear + imagen)
# =============================

@app.post('/api/objetos/crear_con_imagen')
def crear_objeto_con_imagen():
    try:
        verify_jwt_or_admin()
    except Exception:
        return jsonify({'message': 'No autorizado'}), 401

    data = request.get_json(silent=True) or {}
    nombre = (data.get('nombre') or '').strip()
    categoria = (data.get('categoria') or '').strip() or None
    descripcion = data.get('descripcion')
    img_b64 = data.get('image_base64')
    vista = (data.get('vista') or '').strip()
    notas = data.get('notas')
    fuente = data.get('fuente', 'upload')
    if not nombre:
        return jsonify({'message': 'nombre requerido'}), 400
    if not img_b64:
        return jsonify({'message': 'image_base64 requerido'}), 400
    if not vista:
        return jsonify({'message': 'vista requerida'}), 400

    # crear/obtener objeto
    try:
        rs_exist = db_manager.execute_query(
            "SELECT id FROM objetos WHERE nombre=%s AND (categoria=%s OR (categoria IS NULL AND %s IS NULL))",
            (nombre, categoria, categoria)
        ) or []
        if rs_exist:
            objeto_id = rs_exist[0]['id']
            print(f"[DEBUG] Objeto existente encontrado: ID={objeto_id}")
        else:
            print(f"[DEBUG] Creando nuevo objeto: nombre='{nombre}', categoria='{categoria}'")
            db_manager.execute_query(
                "INSERT INTO objetos (nombre, categoria, descripcion) VALUES (%s,%s,%s)",
                (nombre, categoria, descripcion)
            )
            rs_new = db_manager.execute_query("SELECT LAST_INSERT_ID() as id")
            print(f"[DEBUG] Resultado LAST_INSERT_ID: {rs_new}")
            
            if not rs_new or not rs_new[0].get('id'):
                return jsonify({'message': 'Error: No se pudo obtener el ID del objeto creado'}), 500
            
            objeto_id = rs_new[0]['id']
            print(f"[DEBUG] Nuevo objeto creado: ID={objeto_id}")
        
        if not objeto_id:
            return jsonify({'message': 'Error: objeto_id es nulo'}), 500
            
    except Exception as e:
        print(f"[ERROR] Error creando/consultando objeto: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Error creando/consultando objeto: {e}'}), 500

    # Guardar imagen en FS y BD (igual a ObjetoImagenAPI.post)
    try:
        # decode base64
        if ',' in img_b64:
            _, img_b64 = img_b64.split(',', 1)
        blob = base64.b64decode(img_b64)
        content_type = 'image/jpeg'
        import re
        def san(s: str) -> str:
            s = (s or '').lower().replace('..','').replace('/','').replace('\\','')
            s = re.sub(r"[^a-z0-9_\- ]+", '', s).strip()
            s = re.sub(r"\s+", '_', s)
            return s
        base_dir = os.path.join('imagenes', 'objetos', san(nombre), vista)
        os.makedirs(base_dir, exist_ok=True)
        filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        file_path = os.path.join(base_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(blob)
        # thumbnail
        thumb_blob = None
        try:
            img_arr = np.frombuffer(blob, dtype=np.uint8)
            im = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
            if im is not None:
                h, w = im.shape[:2]
                scale = 320.0 / max(1.0, w)
                if scale < 1.0:
                    im_res = cv2.resize(im, (int(w*scale), int(h*scale)))
                else:
                    im_res = im
                ok, enc = cv2.imencode('.jpg', im_res, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if ok:
                    thumb_blob = enc.tobytes()
        except Exception:
            thumb_blob = None
        # insert BD
        print(f"[DEBUG] Insertando imagen: objeto_id={objeto_id}, path={file_path}, vista={vista}")
        db_manager.execute_query(
            """
            INSERT INTO objetos_imagenes (objeto_id, path, thumbnail, fuente, notas, vista)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (objeto_id, file_path.replace('\\','/'), thumb_blob, fuente, notas, vista)
        )
        print(f"[OK] Imagen guardada exitosamente")
    except Exception as e:
        print(f"[ERROR] Error guardando imagen: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Error guardando imagen: {e}'}), 500

    return jsonify({'message': 'Objeto e imagen guardados', 'id': objeto_id}), 201

# =============================
# OBJETOS: Registro y Gestión
# =============================

class ObjetosAPI(Resource):
    def get(self):
        verify_jwt_or_admin()
        q = request.args.get('q')
        sql = (
            "SELECT o.id, o.nombre, o.categoria, o.descripcion, "
            "DATE_FORMAT(o.fecha_creacion, '%Y-%m-%d %H:%i') as fecha_creacion, "
            "(SELECT COUNT(*) FROM objetos_imagenes oi WHERE oi.objeto_id=o.id) AS img_count, "
            "(SELECT oi2.id FROM objetos_imagenes oi2 WHERE oi2.objeto_id=o.id ORDER BY oi2.id ASC LIMIT 1) AS first_img_id "
            "FROM objetos o"
        )
        params = []
        if q:
            sql += " WHERE o.nombre LIKE %s OR o.categoria LIKE %s"
            params = [f"%{q}%", f"%{q}%"]
        sql += " ORDER BY o.categoria, o.nombre"
        rs = db_manager.execute_query(sql, params)
        return {'objetos': rs}, 200

    def post(self):
        try:
            print("[DEBUG] Iniciando POST /api/objetos")
            
            # Permitir acceso con JWT o sesión web
            try:
                verify_jwt_in_request()
                print("[OK] JWT verificado")
            except Exception as e:
                print(f"[WARN] JWT no valido: {e}")
                # Fallback a sesión web
                if 'user_id' not in session:
                    print("[ERROR] No hay sesion web")
                    return {'message': 'Autenticación requerida'}, 401
                print(f"[OK] Sesion web valida: user_id={session.get('user_id')}")
            
            data = request.get_json(silent=True) or {}
            print(f"[DATA] Datos recibidos: {data}")
            
            nombre = (data.get('nombre') or '').strip()
            categoria = (data.get('categoria') or '').strip()
            descripcion = data.get('descripcion')
            
            if not nombre:
                print("[ERROR] Nombre vacio")
                return {'message': 'nombre requerido'}, 400
            
            print(f"[OK] Datos validados: nombre='{nombre}', categoria='{categoria}'")
        except Exception as e:
            print(f"[ERROR] ERROR CRITICO en inicio de POST: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'message': f'Error crítico: {str(e)}'}, 500
        
        try:
            print(f"[DEBUG] POST /api/objetos - nombre: '{nombre}', categoria: '{categoria}'")
            
            # Verificar si ya existe
            rs_exist = db_manager.execute_query(
                "SELECT id FROM objetos WHERE nombre=%s AND (categoria=%s OR (categoria IS NULL AND %s IS NULL))",
                (nombre, categoria or None, categoria or None)
            )
            print(f"[DEBUG] Verificacion existencia: {rs_exist}")
            
            if rs_exist:
                return {'message': f'Ya existe un objeto "{nombre}" en la categoría "{categoria or "Sin categoría"}". Use el registro existente o cambie el nombre.', 'id': rs_exist[0]['id'], 'existe': True}, 200
            
            # Crear nuevo objeto
            print(f"[DEBUG] Insertando objeto...")
            db_manager.execute_query(
                "INSERT INTO objetos (nombre, categoria, descripcion) VALUES (%s, %s, %s)",
                (nombre, categoria or None, descripcion),
            )
            print(f"[OK] Objeto insertado")
            
            rs = db_manager.execute_query("SELECT id FROM objetos WHERE nombre=%s AND (categoria=%s OR (categoria IS NULL AND %s IS NULL)) ORDER BY id DESC LIMIT 1", (nombre, categoria or None, categoria or None))
            print(f"[DEBUG] ID recuperado: {rs}")
            
            return {'message': 'Objeto creado exitosamente', 'id': rs[0]['id'] if rs else None}, 201
        except Exception as e:
            print(f"[ERROR] ERROR en POST /api/objetos: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            if '1062' in str(e) or 'Duplicate entry' in str(e):
                return {'message': f'Ya existe un objeto con ese nombre y categoría. Use un nombre diferente o seleccione el existente de la lista.', 'duplicado': True}, 409
            return {'message': f'Error creando objeto: {str(e)}'}, 500


class ObjetoImagenAPI(Resource):
    def get(self, objeto_id):
        """Obtener lista de imágenes de un objeto"""
        # Permitir acceso con JWT o sesión web
        try:
            verify_jwt_in_request()
        except:
            # Fallback a sesión web
            if 'user_id' not in session:
                return {'message': 'Autenticación requerida'}, 401
        
        try:
            print(f"[DEBUG] GET imagenes para objeto_id={objeto_id}")
            rs = db_manager.execute_query(
                "SELECT id, path, vista, notas, fuente, DATE_FORMAT(fecha_subida, '%Y-%m-%d %H:%i') as fecha_creacion FROM objetos_imagenes WHERE objeto_id=%s ORDER BY id DESC",
                (objeto_id,)
            )
            print(f"[DEBUG] Imagenes encontradas: {len(rs) if rs else 0}")
            return {'imagenes': rs or []}, 200
        except Exception as e:
            print(f"[ERROR] Error obteniendo imagenes: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'message': f'Error obteniendo imágenes: {str(e)}'}, 500
    
    def post(self, objeto_id):
        # Permitir acceso con JWT o sesión web
        try:
            verify_jwt_in_request()
        except:
            # Fallback a sesión web
            if 'user_id' not in session:
                return {'message': 'Autenticación requerida'}, 401
        
        data = request.get_json(silent=True) or {}
        img_b64 = data.get('image_base64')
        notas = data.get('notas')
        fuente = data.get('fuente', 'upload')
        carpeta = (data.get('carpeta') or '').strip()
        tipo_registro = data.get('tipo_registro', 'objeto')  # 'equipo' o 'objeto'
        vista = (data.get('vista') or '').strip()  # superior/inferior/lateral_izquierda/lateral_derecha
        if not img_b64:
            return {'message': 'image_base64 requerido'}, 400
        try:
            print(f"[DEBUG] Iniciando guardado de imagen para objeto {objeto_id}")
            print(f"[DEBUG] Tipo registro: {tipo_registro}")
            print(f"[DEBUG] Carpeta solicitada: '{carpeta}'")
            
            # Si no hay carpeta especificada, usar nombre del objeto
            rs_obj = None
            if not carpeta:
                rs_obj = db_manager.execute_query("SELECT nombre FROM objetos WHERE id=%s", (objeto_id,))
                if rs_obj:
                    carpeta = rs_obj[0]['nombre']
                    print(f"[DEBUG] Carpeta obtenida del objeto: '{carpeta}'")
            # Normalizar dataURL
            if ',' in img_b64:
                header, img_b64 = img_b64.split(',', 1)
            blob = base64.b64decode(img_b64)
            content_type = 'image/jpeg'
            if 'data:image/' in (locals().get('header') or ''):
                try:
                    content_type = header.split(';')[0].split(':')[1]
                except Exception:
                    pass
            # Guardar en disco
            ext = '.jpg' if content_type=='image/jpeg' else ('.png' if content_type=='image/png' else '.img')
            # Sanitizar subcarpeta opcional
            def _sanitize_folder(name: str) -> str:
                import re
                name = name.replace('..','').replace('/', '').replace('\\','')
                name = re.sub(r"[^A-Za-z0-9_\- ]+", '', name).strip()
                name = re.sub(r"\s+", '_', name)
                return name[:80]

            safe_sub = _sanitize_folder(carpeta) if carpeta else ''
            if vista:
                safe_sub = _sanitize_folder(vista)
            # si viene 'vista', usarla como subcarpeta (tiene prioridad)
            if vista:
                safe_sub = _sanitize_folder(vista)
            # Determinar ruta base según tipo de registro y nombre
            base_folder = 'equipos' if tipo_registro == 'equipo' else 'objetos'
            # usar nombre del objeto/equipo como carpeta principal
            if carpeta:
                base_name = _sanitize_folder(carpeta)
            elif rs_obj and len(rs_obj) > 0:
                base_name = _sanitize_folder(rs_obj[0]['nombre'])
            else:
                base_name = f'objeto_{objeto_id}'
            
            dir_path = os.path.join('imagenes', base_folder, base_name)
            if safe_sub:
                dir_path = os.path.join(dir_path, safe_sub)
            
            print(f"[DEBUG] Ruta completa calculada: {dir_path}")
            print(f"[DEBUG] Directorio de trabajo actual: {os.getcwd()}")
            print(f"[DEBUG] Ruta absoluta: {os.path.abspath(dir_path)}")
            
            # Crear directorio con manejo de errores
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"[OK] Directorio creado/verificado: {dir_path}")
            except PermissionError:
                return {'message': f'Sin permisos para crear directorio: {dir_path}'}, 500
            except Exception as e:
                return {'message': f'Error creando directorio {dir_path}: {str(e)}'}, 500
            
            # Guardar archivo con manejo de errores
            filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
            file_path = os.path.join(dir_path, filename)
            try:
                with open(file_path, 'wb') as f:
                    f.write(blob)
                print(f"[OK] Archivo guardado: {file_path} ({len(blob)} bytes)")
                
                # Verificar que el archivo realmente existe
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    print(f"[OK] Verificacion: archivo existe con {size} bytes")
                else:
                    print(f"[ERROR] ERROR: archivo NO existe despues de guardarlo: {file_path}")
                    return {'message': f'Error: archivo no se guardó correctamente en {file_path}'}, 500
                    
            except PermissionError:
                print(f"[ERROR] ERROR de permisos: {file_path}")
                return {'message': f'Sin permisos para escribir archivo: {file_path}'}, 500
            except OSError as e:
                print(f"[ERROR] ERROR del sistema: {str(e)}")
                return {'message': f'Error del sistema guardando {file_path}: {str(e)}'}, 500
            except Exception as e:
                print(f"[ERROR] ERROR inesperado: {str(e)}")
                return {'message': f'Error inesperado guardando archivo: {str(e)}'}, 500
            # Generar thumbnail (320px ancho máx) con manejo de errores
            thumb_blob = None
            try:
                img_arr = np.frombuffer(blob, dtype=np.uint8)
                im = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
                if im is not None:
                    h, w = im.shape[:2]
                    scale = 320.0 / max(1.0, w)
                    if scale < 1.0:
                        im_res = cv2.resize(im, (int(w*scale), int(h*scale)))
                    else:
                        im_res = im
                    ok, enc = cv2.imencode('.jpg', im_res, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                    if ok:
                        thumb_blob = enc.tobytes()
                        print(f"[OK] Thumbnail generado: {len(thumb_blob)} bytes")
                    else:
                        print("[WARN] No se pudo codificar thumbnail")
                else:
                    print("[WARN] No se pudo decodificar imagen para thumbnail")
            except Exception as e:
                print(f"[WARN] Error generando thumbnail: {str(e)}")
                # Continuar sin thumbnail
            
            # Guardar registro en BD con manejo de errores
            try:
                db_manager.execute_query(
                    """
                    INSERT INTO objetos_imagenes (objeto_id, path, thumbnail, fuente, notas, vista)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (objeto_id, file_path.replace('\\','/'), thumb_blob, fuente, notas, vista),
                )
                print(f"[OK] Registro guardado en BD para objeto {objeto_id}")
                
                # Listar contenido de la carpeta para verificar
                try:
                    parent_dir = os.path.dirname(file_path)
                    files = os.listdir(parent_dir)
                    print(f"[DEBUG] Contenido de {parent_dir}: {files}")
                except Exception as e:
                    print(f"[WARN] No se pudo listar directorio: {str(e)}")
                
                return {'message': 'Imagen almacenada exitosamente', 'path': file_path.replace('\\','/'), 'size_bytes': len(blob)}, 201
            except Exception as e:
                # Si falla BD, intentar eliminar archivo para evitar inconsistencias
                try:
                    os.remove(file_path)
                    print(f"[WARN] Archivo eliminado por error BD: {file_path}")
                except:
                    pass
                return {'message': f'Error guardando en base de datos: {str(e)}'}, 500
        except Exception as e:
            return {'message': f'Error guardando imagen: {str(e)}'}, 500


api.add_resource(ObjetosAPI, '/api/objetos')

@app.route('/objetos/registrar')
@require_login
@require_level(4)  # Solo Administrador puede entrenar IA
def objetos_registrar():
    return render_template('objetos_registrar.html', user=session)

@app.route('/registro-completo')
@require_login
@require_level(4)  # Solo Administrador
def registro_completo():
    """Formulario unificado de registro de equipos/items con IA"""
    # Obtener lista de laboratorios
    query = "SELECT id, codigo, nombre FROM laboratorios WHERE estado = 'activo' ORDER BY nombre"
    laboratorios = db_manager.execute_query(query)
    return render_template('registro_completo.html', user=session, laboratorios=laboratorios)

@app.route('/registros-gestion')
@require_login
@require_level(4)  # Solo Administrador
def registros_gestion():
    """Página de gestión de registros"""
    query = "SELECT id, codigo, nombre FROM laboratorios WHERE estado = 'activo' ORDER BY nombre"
    laboratorios = db_manager.execute_query(query)
    return render_template('registros_gestion.html', user=session, laboratorios=laboratorios)

@app.route('/api/registro-completo', methods=['POST'])
@require_login
@require_level(4)
def api_registro_completo():
    """API para guardar registro completo (equipo/item + fotos + IA)"""
    import json
    import uuid
    import re
    import base64
    import io
    from PIL import Image
    
    try:
        # Obtener datos JSON
        data = request.get_json()
        
        tipo_registro = data.get('tipo_registro')
        nombre = data.get('nombre')
        categoria = data.get('tipo_categoria')  # El frontend envía 'tipo_categoria'
        descripcion = data.get('descripcion', '')
        laboratorio_id = data.get('laboratorio_id')
        ubicacion = data.get('ubicacion', '')
        estado = data.get('estado', 'disponible')
        cantidad = data.get('cantidad', 1)
        fotos = data.get('fotos', {})
        
        # Validar campos obligatorios
        if not all([nombre, categoria, laboratorio_id]):
            return jsonify({'success': False, 'message': 'Faltan campos obligatorios'}), 400
        
        # Validar que tenga al menos la foto frontal
        if 'frontal' not in fotos:
            return jsonify({'success': False, 'message': 'Debe capturar al menos la foto frontal'}), 400
        
        # Iniciar transacción
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # PASO 1: Crear registro en equipos o inventario
            if tipo_registro == 'equipo':
                # Crear equipo
                equipo_id = f"EQ_{str(uuid.uuid4())[:8].upper()}"
                
                query_equipo = """
                    INSERT INTO equipos (id, nombre, tipo, estado, ubicacion, laboratorio_id, especificaciones)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query_equipo, (
                    equipo_id, nombre, categoria, estado, ubicacion, laboratorio_id,
                    json.dumps({'descripcion': descripcion})
                ))
                registro_id = equipo_id
                
            else:  # item de inventario
                # Generar ID único para el item
                item_id = f"ITEM_{str(uuid.uuid4())[:8].upper()}"
                
                # Intentar insertar con ID generado
                query_item = """
                    INSERT INTO inventario (id, nombre, categoria, laboratorio_id)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query_item, (
                    item_id, nombre, categoria, laboratorio_id
                ))
                registro_id = item_id
            
            # PASO 2: Si hay fotos, crear objeto para IA
            objeto_id = None
            if fotos:
                query_objeto = """
                    INSERT INTO objetos (nombre, categoria, descripcion, equipo_id)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query_objeto, (
                    nombre, categoria, descripcion,
                    equipo_id if tipo_registro == 'equipo' else None
                ))
                objeto_id = cursor.lastrowid
                
                # PASO 3: Guardar imágenes
                # Estructura: imagenes/{tipo}/{nombre_objeto}/
                
                # Crear nombre de carpeta seguro
                nombre_carpeta = nombre.lower().replace(' ', '_')
                nombre_carpeta = re.sub(r'[^a-z0-9_]', '', nombre_carpeta)
                
                # Determinar directorio según tipo
                tipo_dir = 'equipo' if tipo_registro == 'equipo' else 'item'
                objeto_dir = os.path.join('imagenes', tipo_dir, nombre_carpeta)
                os.makedirs(objeto_dir, exist_ok=True)
                
                for vista, imagen_base64 in fotos.items():
                    # Decodificar imagen
                    # Remover prefijo data:image
                    if ',' in imagen_base64:
                        imagen_base64 = imagen_base64.split(',')[1]
                    
                    imagen_data = base64.b64decode(imagen_base64)
                    imagen = Image.open(io.BytesIO(imagen_data))
                    
                    # Guardar imagen con nombre de vista
                    # Ejemplo: imagenes/equipo/microscopio_olympus/frontal.jpg
                    filename = f"{vista}.jpg"
                    filepath = os.path.join(objeto_dir, filename)
                    imagen.save(filepath, 'JPEG', quality=85)
                    
                    # Insertar en base de datos
                    query_imagen = """
                        INSERT INTO objetos_imagenes (objeto_id, path, vista)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(query_imagen, (objeto_id, filepath, vista))
                
                # PASO 3.5: Crear archivo de metadatos para IA
                # Obtener información del laboratorio
                lab_query = "SELECT nombre, ubicacion FROM laboratorios WHERE id = %s"
                lab_result = db_manager.execute_query(lab_query, (laboratorio_id,))
                laboratorio_nombre = lab_result[0]['nombre'] if lab_result else None
                laboratorio_ubicacion = lab_result[0]['ubicacion'] if lab_result else None
                
                metadatos = {
                    'id': objeto_id,
                    'nombre': nombre,
                    'tipo': tipo_registro,
                    'categoria': categoria,
                    'descripcion': descripcion,
                    'ubicacion': ubicacion,
                    'laboratorio_id': laboratorio_id,
                    'laboratorio_nombre': laboratorio_nombre,
                    'laboratorio_ubicacion': laboratorio_ubicacion,
                    'cantidad': cantidad if tipo_registro == 'item' else None,
                    'estado': estado if tipo_registro == 'equipo' else None,
                    'equipo_id': equipo_id if tipo_registro == 'equipo' else None,
                    'fotos_capturadas': list(fotos.keys()),
                    'total_fotos': len(fotos),
                    'entrenado_ia': len(fotos) == 6,
                    'ruta_imagenes': objeto_dir
                }
                
                metadata_path = os.path.join(objeto_dir, 'metadata.json')
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadatos, f, indent=2, ensure_ascii=False)
                
                # PASO 4: Actualizar equipo con objeto_id y entrenado_ia
                if tipo_registro == 'equipo' and objeto_id:
                    entrenado_ia = len(fotos) == 6  # Solo si tiene las 6 vistas
                    query_update = """
                        UPDATE equipos 
                        SET objeto_id = %s, entrenado_ia = %s
                        WHERE id = %s
                    """
                    cursor.execute(query_update, (objeto_id, entrenado_ia, equipo_id))
            
            # Commit de la transacción
            conn.commit()
            
            # Log de auditoría
            try:
                log_query = """
                    INSERT INTO logs_seguridad (usuario_id, accion, detalle, ip_origen, exitoso)
                    VALUES (%s, 'registro_completo', %s, %s, TRUE)
                """
                cursor.execute(log_query, (
                    session.get('user_id'),
                    f"Registro completo: {nombre} ({tipo_registro})",
                    request.remote_addr
                ))
                conn.commit()
            except:
                pass
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Registro guardado exitosamente',
                'id': registro_id,
                'objeto_id': objeto_id,
                'entrenado_ia': len(fotos) == 6 if fotos else False
            }), 201
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            raise e
            
    except Exception as e:
        print(f"[ERROR] Error en registro completo: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error al guardar: {str(e)}'}), 500

@app.route('/api/registros-completos')
@require_login
@require_level(4)
def api_registros_completos():
    """API para listar todos los registros (equipos + items)"""
    try:
        registros = []
        
        # Obtener equipos - solo columnas básicas
        try:
            query_equipos = """
                SELECT e.id, e.nombre, e.tipo as categoria, e.estado,
                    e.laboratorio_id, l.nombre as laboratorio_nombre
                FROM equipos e
                LEFT JOIN laboratorios l ON e.laboratorio_id = l.id
                ORDER BY e.nombre
            """
            equipos = db_manager.execute_query(query_equipos) or []
            
            for eq in equipos:
                eq['tipo'] = 'equipo'
                # El estado ya viene de la BD, no lo sobrescribimos
                eq['entrenado_ia'] = False
                eq['foto_frontal'] = None
                
                # Buscar objeto asociado
                query_obj = "SELECT id FROM objetos WHERE nombre = %s LIMIT 1"
                obj = db_manager.execute_query(query_obj, (eq['nombre'],))
                if obj:
                    objeto_id = obj[0]['id']
                    # Buscar foto frontal
                    query_foto = "SELECT id FROM objetos_imagenes WHERE objeto_id = %s AND vista = 'frontal' LIMIT 1"
                    foto = db_manager.execute_query(query_foto, (objeto_id,))
                    if foto:
                        eq['foto_frontal'] = f'/imagenes_objeto/{foto[0]["id"]}'
                        eq['entrenado_ia'] = True
                
                registros.append(eq)
        except Exception as e:
            print(f"[WARN] Error obteniendo equipos: {e}")
        
        # Obtener items - solo columnas básicas
        try:
            query_items = """
                SELECT i.id, i.nombre, i.categoria, i.cantidad_actual as stock_actual,
                       i.laboratorio_id, l.nombre as laboratorio_nombre
                FROM inventario i
                LEFT JOIN laboratorios l ON i.laboratorio_id = l.id
                ORDER BY i.nombre
            """
            items = db_manager.execute_query(query_items) or []
            
            for item in items:
                item['tipo'] = 'item'
                # El stock_actual ya viene de la BD, no lo sobrescribimos
                item['entrenado_ia'] = False
                item['foto_frontal'] = None
                
                # Buscar objeto asociado
                query_obj = "SELECT id FROM objetos WHERE nombre = %s LIMIT 1"
                obj = db_manager.execute_query(query_obj, (item['nombre'],))
                if obj:
                    objeto_id = obj[0]['id']
                    # Buscar foto frontal
                    query_foto = "SELECT id FROM objetos_imagenes WHERE objeto_id = %s AND vista = 'frontal' LIMIT 1"
                    foto = db_manager.execute_query(query_foto, (objeto_id,))
                    if foto:
                        item['foto_frontal'] = f'/imagenes_objeto/{foto[0]["id"]}'
                        item['entrenado_ia'] = True
                
                registros.append(item)
        except Exception as e:
            print(f"[WARN] Error obteniendo items: {e}")
        
        print(f"[INFO] Total registros encontrados: {len(registros)}")
        return jsonify({'success': True, 'registros': registros})
        
    except Exception as e:
        print(f"[ERROR] Error listando registros: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/registro-detalle/<tipo>/<id>')
@require_login
@require_level(4)
def api_registro_detalle(tipo, id):
    """API para obtener detalles de un registro"""
    try:
        if tipo == 'equipo':
            query = """
                SELECT e.*, l.nombre as laboratorio_nombre, o.id as objeto_id
                FROM equipos e
                LEFT JOIN laboratorios l ON e.laboratorio_id = l.id
                LEFT JOIN objetos o ON e.objeto_id = o.id
                WHERE e.id = %s
            """
            registro = db_manager.execute_query(query, (id,))
        else:
            query = """
                SELECT i.*, l.nombre as laboratorio_nombre, o.id as objeto_id
                FROM inventario i
                LEFT JOIN laboratorios l ON i.laboratorio_id = l.id
                LEFT JOIN objetos o ON o.nombre = i.nombre
                WHERE i.id = %s
            """
            registro = db_manager.execute_query(query, (id,))
        
        if not registro:
            return jsonify({'success': False, 'message': 'Registro no encontrado'}), 404
        
        registro = registro[0]
        registro['tipo'] = tipo
        
        # Obtener fotos
        if registro.get('objeto_id'):
            query_fotos = "SELECT id, path, vista FROM objetos_imagenes WHERE objeto_id = %s"
            fotos = db_manager.execute_query(query_fotos, (registro['objeto_id'],))
            registro['fotos'] = fotos
        else:
            registro['fotos'] = []
        
        return jsonify({'success': True, 'registro': registro})
        
    except Exception as e:
        print(f"[ERROR] Error obteniendo detalle: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/registro-editar/<tipo>/<id>', methods=['GET'])
@require_login
@require_level(4)
def api_registro_editar(tipo, id):
    """API para obtener datos de un registro para edición"""
    try:
        if tipo == 'equipo':
            query = """
                SELECT e.*, l.nombre as laboratorio_nombre, o.id as objeto_id
                FROM equipos e
                LEFT JOIN laboratorios l ON e.laboratorio_id = l.id
                LEFT JOIN objetos o ON e.objeto_id = o.id
                WHERE e.id = %s
            """
        else:
            query = """
                SELECT i.*, l.nombre as laboratorio_nombre
                FROM inventario i
                LEFT JOIN laboratorios l ON i.laboratorio_id = l.id
                WHERE i.id = %s
            """
        
        result = db_manager.execute_query(query, (id,))
        
        if not result:
            return jsonify({'success': False, 'message': 'Registro no encontrado'}), 404
        
        registro = result[0]
        
        # Obtener fotos si existen
        if tipo == 'equipo' and registro.get('objeto_id'):
            query_fotos = "SELECT id, path, vista FROM objetos_imagenes WHERE objeto_id = %s"
            fotos = db_manager.execute_query(query_fotos, (registro['objeto_id'],))
            registro['fotos'] = fotos
        else:
            registro['fotos'] = []
        
        return jsonify({'success': True, 'registro': registro})
        
    except Exception as e:
        print(f"[ERROR] Error obteniendo registro para editar: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/registro-actualizar/<tipo>/<id>', methods=['PUT'])
@require_login
@require_level(4)
def api_registro_actualizar(tipo, id):
    """API para actualizar un registro"""
    try:
        data = request.get_json()
        
        if tipo == 'equipo':
            query = """
                UPDATE equipos 
                SET nombre = %s, tipo = %s, descripcion = %s,
                    ubicacion = %s, estado = %s, laboratorio_id = %s
                WHERE id = %s
            """
            params = (
                data.get('nombre'),
                data.get('categoria'),  # Se mapea a 'tipo' en equipos
                data.get('descripcion'),
                data.get('ubicacion'),
                data.get('estado'),
                data.get('laboratorio_id'),
                id
            )
        else:
            query = """
                UPDATE inventario 
                SET nombre = %s, categoria = %s, descripcion = %s,
                    ubicacion = %s, cantidad_actual = %s, laboratorio_id = %s
                WHERE id = %s
            """
            params = (
                data.get('nombre'),
                data.get('categoria'),
                data.get('descripcion'),
                data.get('ubicacion'),
                data.get('stock_actual'),
                data.get('laboratorio_id'),
                id
            )
        
        db_manager.execute_query(query, params)
        
        return jsonify({'success': True, 'message': 'Registro actualizado exitosamente'})
        
    except Exception as e:
        print(f"[ERROR] Error actualizando registro: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/registro-eliminar/<tipo>/<id>', methods=['DELETE'])
@require_login
@require_level(4)
def api_registro_eliminar(tipo, id):
    """API para eliminar un registro"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        if tipo == 'equipo':
            # Obtener objeto_id antes de eliminar
            query_obj = "SELECT objeto_id FROM equipos WHERE id = %s"
            result = db_manager.execute_query(query_obj, (id,))
            objeto_id = result[0]['objeto_id'] if result and result[0].get('objeto_id') else None
            
            # Eliminar equipo
            cursor.execute("DELETE FROM equipos WHERE id = %s", (id,))
        else:
            # Buscar objeto asociado
            query_obj = "SELECT o.id FROM objetos o INNER JOIN inventario i ON o.nombre = i.nombre WHERE i.id = %s"
            result = db_manager.execute_query(query_obj, (id,))
            objeto_id = result[0]['id'] if result else None
            
            # Eliminar item
            cursor.execute("DELETE FROM inventario WHERE id = %s", (id,))
        
        # Si tiene objeto asociado, eliminar imágenes y objeto
        if objeto_id:
            cursor.execute("DELETE FROM objetos_imagenes WHERE objeto_id = %s", (objeto_id,))
            cursor.execute("DELETE FROM objetos WHERE id = %s", (objeto_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Registro eliminado exitosamente'})
        
    except Exception as e:
        print(f"[ERROR] Error eliminando registro: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/imagenes_objeto/<int:imagen_id>')
@require_login
def servir_imagen_objeto(imagen_id):
    """Servir imagen de objeto por ID"""
    from flask import send_file
    try:
        query = "SELECT path FROM objetos_imagenes WHERE id = %s"
        result = db_manager.execute_query(query, (imagen_id,))
        if result and result[0].get('path'):
            path = result[0]['path']
            # Asegurar que la ruta sea absoluta
            if not os.path.isabs(path):
                path = os.path.join(os.getcwd(), path)
            if os.path.exists(path):
                return send_file(path, mimetype='image/jpeg')
        return "Imagen no encontrada", 404
    except Exception as e:
        print(f"[ERROR] Error sirviendo imagen: {str(e)}")
        return "Error al cargar imagen", 500


@app.route('/api/reemplazar-imagen', methods=['POST'])
@require_login
@require_level(4)
def api_reemplazar_imagen():
    """API para reemplazar una imagen existente"""
    try:
        # Obtener datos del formulario
        imagen_id = request.form.get('imagen_id')
        vista = request.form.get('vista')
        objeto_id = request.form.get('objeto_id')
        archivo = request.files.get('imagen')
        
        if not all([imagen_id, vista, objeto_id, archivo]):
            return jsonify({'success': False, 'message': 'Faltan datos requeridos'}), 400
        
        # Obtener la ruta actual de la imagen
        query_old = "SELECT path FROM objetos_imagenes WHERE id = %s"
        result = db_manager.execute_query(query_old, (imagen_id,))
        
        if not result:
            return jsonify({'success': False, 'message': 'Imagen no encontrada'}), 404
        
        old_path = result[0]['path']
        
        # Crear directorio si no existe
        objeto_dir = os.path.join('imagenes', 'objetos')
        os.makedirs(objeto_dir, exist_ok=True)
        
        # Generar nombre de archivo único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"obj_{objeto_id}_{vista}_{timestamp}.jpg"
        new_path = os.path.join(objeto_dir, filename)
        
        # Guardar nueva imagen
        archivo.save(new_path)
        
        # Actualizar ruta en base de datos
        query_update = "UPDATE objetos_imagenes SET path = %s WHERE id = %s"
        db_manager.execute_query(query_update, (new_path, imagen_id))
        
        # Eliminar imagen antigua si existe y es diferente
        if old_path and os.path.exists(old_path) and old_path != new_path:
            try:
                os.remove(old_path)
                print(f"[INFO] Imagen antigua eliminada: {old_path}")
            except Exception as e:
                print(f"[WARN] No se pudo eliminar imagen antigua: {e}")
        
        print(f"[INFO] Imagen reemplazada: {imagen_id} -> {new_path}")
        
        return jsonify({
            'success': True, 
            'message': 'Imagen reemplazada exitosamente',
            'new_path': new_path
        })
        
    except Exception as e:
        print(f"[ERROR] Error reemplazando imagen: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================
# OBJETOS: Gestión individual (GET, PUT, DELETE)
# =============================

class ObjetoAPI(Resource):
    def get(self, objeto_id: int):
        # Permitir acceso con JWT o sesión web
        try:
            verify_jwt_in_request()
        except:
            # Fallback a sesión web
            if 'user_id' not in session:
                return {'message': 'Autenticación requerida'}, 401
        
        rs = db_manager.execute_query(
            "SELECT id, nombre, categoria, descripcion, DATE_FORMAT(fecha_creacion, '%Y-%m-%d %H:%i') as fecha_creacion FROM objetos WHERE id=%s",
            (objeto_id,)
        )
        if not rs:
            return {'message': 'Objeto no encontrado'}, 404
        return {'objeto': rs[0]}, 200

    def put(self, objeto_id: int):
        verify_jwt_in_request()
        data = request.get_json(silent=True) or {}
        nombre = (data.get('nombre') or '').strip()
        categoria = (data.get('categoria') or '').strip() or None
        descripcion = data.get('descripcion')
        if not nombre:
            return {'message': 'nombre requerido'}, 400
        # Verificar duplicado con otro ID
        rs_exist = db_manager.execute_query(
            "SELECT id FROM objetos WHERE nombre=%s AND (categoria=%s OR (categoria IS NULL AND %s IS NULL)) AND id<>%s",
            (nombre, categoria, categoria, objeto_id)
        )
        if rs_exist:
            return {'message': 'Ya existe otro objeto con ese nombre y categoría'}, 409
        db_manager.execute_query(
            "UPDATE objetos SET nombre=%s, categoria=%s, descripcion=%s WHERE id=%s",
            (nombre, categoria, descripcion, objeto_id)
        )
        return {'message': 'Objeto actualizado'}, 200

    def delete(self, objeto_id: int):
        verify_jwt_in_request()
        # Obtener imágenes para limpiar archivos
        rs = db_manager.execute_query("SELECT path FROM objetos_imagenes WHERE objeto_id=%s", (objeto_id,))
        for row in rs or []:
            p = row.get('path')
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                    print(f"🗑️ Archivo eliminado: {p}")
                except Exception as e:
                    print(f"⚠️ No se pudo eliminar archivo {p}: {e}")
        # Borrar objeto (CASCADE borra objetos_imagenes)
        db_manager.execute_query("DELETE FROM objetos WHERE id=%s", (objeto_id,))
        # Intentar eliminar carpeta base si queda vacía
        for base in ('imagenes/objetos', 'imagenes/equipos'):
            base_dir = os.path.join(base, str(objeto_id))
            try:
                os.rmdir(base_dir)
            except Exception:
                pass
        return {'message': 'Objeto eliminado'}, 200

api.add_resource(ObjetoAPI, '/api/objetos/<int:objeto_id>')

@app.route('/objetos/gestion')
@require_login
@require_level(3)
def objetos_gestion():
    return render_template('objetos_gestion.html', user=session)

# =============================
# OBJETOS: Listado de imágenes y thumbnails
# =============================

# Unificar ObjetoImagenAPI (POST) y ObjetoImagenesAPI (GET) en una sola clase
# Ya está definida arriba como ObjetoImagenAPI con método post()
# Ahora agregamos el método get() a la misma clase
# Buscar la clase ObjetoImagenAPI arriba y agregar el método get()

api.add_resource(ObjetoImagenAPI, '/api/objetos/<int:objeto_id>/imagenes')

@app.get('/api/objetos/imagen_thumb/<int:img_id>')
def objeto_imagen_thumb(img_id: int):
    # No requiere JWT para facilitar renderizado de miniaturas; restringe a logged-in vía sesión si se desea
    row = db_manager.execute_query("SELECT thumbnail, content_type FROM objetos_imagenes WHERE id=%s", (img_id,))
    if not row or row[0]['thumbnail'] is None:
        return jsonify({'message': 'Thumbnail no disponible'}), 404
    ct = row[0]['content_type'] or 'image/jpeg'
    return app.response_class(response=row[0]['thumbnail'], status=200, mimetype=ct)

# =============================
# VISION: Guardar plantilla de equipo
# =============================

@app.get('/api/objetos/<int:objeto_id>/vistas_status')
def objeto_vistas_status(objeto_id: int):
    try:
        rs = db_manager.execute_query("SELECT nombre FROM objetos WHERE id=%s", (objeto_id,))
        if not rs:
            return jsonify({'message': 'Objeto no encontrado'}), 404
        nombre = rs[0]['nombre']
    except Exception as e:
        return jsonify({'message': f'Error consultando objeto: {e}'}), 500

    import re
    def san(s: str) -> str:
        s = (s or '').lower().replace('..','').replace('/','').replace('\\','')
        s = re.sub(r"[^a-z0-9_\- ]+", '', s).strip()
        s = re.sub(r"\s+", '_', s)
        return s

    base = os.path.join('imagenes', 'objetos', san(nombre))
    required = ['frontal','posterior','superior','inferior','lateral_derecha','lateral_izquierda']
    completed = []
    files = {}
    if os.path.isdir(base):
        for v in required:
            vdir = os.path.join(base, v)
            if os.path.isdir(vdir):
                imgs = [f for f in os.listdir(vdir) if f.lower().endswith(('.jpg','.jpeg','.png'))]
                if imgs:
                    completed.append(v)
                    files[v] = [os.path.join(vdir, f).replace('\\','/') for f in imgs]
    missing = [v for v in required if v not in completed]
    return jsonify({
        'objeto_id': objeto_id,
        'nombre': nombre,
        'required': required,
        'completed': completed,
        'missing': missing,
        'count': len(completed),
        'files': files,
    }), 200
@app.post('/api/vision/equipos/<int:equipo_id>/plantilla')
def vision_equipo_plantilla(equipo_id: int):
    try:
        verify_jwt_in_request()
    except Exception:
        # permitir sin JWT si se desea, pero en producción es mejor exigirlo
        pass
    data = request.get_json(silent=True) or {}
    img_b64 = data.get('image_base64')
    carpeta = (data.get('carpeta') or '').strip()
    if not img_b64:
        return jsonify({'message': 'image_base64 requerido'}), 400
    # decode
    try:
        if ',' in img_b64:
            _, img_b64 = img_b64.split(',', 1)
        blob = base64.b64decode(img_b64)
    except Exception as e:
        return jsonify({'message': f'Base64 inválido: {e}'}), 400

    # sanitize folder
    def _sanitize(name: str) -> str:
        import re
        name = (name or '').replace('..','').replace('/','').replace('\\','')
        name = re.sub(r"[^A-Za-z0-9_\- ]+", '', name).strip()
        name = re.sub(r"\s+", '_', name)
        return name[:80]

    sub = _sanitize(carpeta)
    # obtener nombre del equipo para usarlo como carpeta
    try:
        rs_eq = db_manager.execute_query("SELECT nombre FROM equipos WHERE id=%s", (equipo_id,))
        eq_name = rs_eq[0]['nombre'] if rs_eq else str(equipo_id)
    except Exception:
        eq_name = str(equipo_id)
    eq_folder = _sanitize(eq_name)
    dir_path = os.path.join('imagenes', 'equipos', eq_folder)
    if sub:
        dir_path = os.path.join(dir_path, sub)
    try:
        os.makedirs(dir_path, exist_ok=True)
    except Exception as e:
        return jsonify({'message': f'No se pudo crear carpeta {dir_path}: {e}'}), 500

    filename = f"tpl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    file_path = os.path.join(dir_path, filename)
    try:
        with open(file_path, 'wb') as f:
            f.write(blob)
    except Exception as e:
        return jsonify({'message': f'No se pudo escribir archivo: {e}'}), 500

    return jsonify({'message': 'Plantilla guardada', 'path': file_path.replace('\\','/')}), 201

@app.get('/api/vision/equipos/<int:equipo_id>/plantillas')
def vision_equipo_listar_plantillas(equipo_id: int):
    # mapear id -> nombre carpeta
    try:
        rs = db_manager.execute_query("SELECT nombre FROM equipos WHERE id=%s", (equipo_id,))
        name = rs[0]['nombre'] if rs else str(equipo_id)
    except Exception:
        name = str(equipo_id)
    import re
    name_sanitized = re.sub(r"\s+", '_', re.sub(r"[^A-Za-z0-9_\- ]+", '', name)).strip()
    base_dir = os.path.join('imagenes', 'equipos', name_sanitized)
    resultado = []
    if not os.path.exists(base_dir):
        return jsonify({'plantillas': []}), 200
    for root, _, files in os.walk(base_dir):
        for fn in files:
            if fn.lower().endswith(('.jpg', '.jpeg', '.png')):
                rel_dir = os.path.relpath(root, base_dir)
                rel_path = fn if rel_dir == '.' else os.path.join(rel_dir, fn)
                resultado.append({'file': rel_path.replace('\\','/')})
    return jsonify({'plantillas': resultado}), 200

@app.get('/api/vision/equipos/plantilla_image')
def vision_equipo_plantilla_image():
    from urllib.parse import unquote
    equipo_id = request.args.get('equipo_id')
    rel_file = request.args.get('f') or ''
    try:
        eid = int(equipo_id)
    except Exception:
        return jsonify({'message': 'equipo_id inválido'}), 400
    safe_rel = unquote(rel_file).replace('..','').replace('\\','/')
    # traducir a carpeta por nombre
    try:
        rs = db_manager.execute_query("SELECT nombre FROM equipos WHERE id=%s", (eid,))
        name = rs[0]['nombre'] if rs else str(eid)
    except Exception:
        name = str(eid)
    import re
    name_sanitized = re.sub(r"\s+", '_', re.sub(r"[^A-Za-z0-9_\- ]+", '', name)).strip()
    base_dir = os.path.join('imagenes', 'equipos', name_sanitized)
    abs_path = os.path.abspath(os.path.join(base_dir, safe_rel))
    if not abs_path.startswith(os.path.abspath(base_dir)):
        return jsonify({'message': 'Ruta no permitida'}), 400
    if not os.path.exists(abs_path):
        return jsonify({'message': 'Archivo no encontrado'}), 404
    try:
        with open(abs_path, 'rb') as f:
            data = f.read()
        ct = 'image/jpeg' if abs_path.lower().endswith(('.jpg','.jpeg')) else 'image/png'
        return app.response_class(response=data, status=200, mimetype=ct)
    except Exception as e:
        return jsonify({'message': f'Error leyendo archivo: {e}'}), 500

def _preprocess_for_orb(img: np.ndarray) -> np.ndarray:
    try:
        if img is None:
            return img
        h, w = img.shape[:2]
        maxw = 640
        if w > maxw:
            scale = maxw/float(w)
            img = cv2.resize(img, (int(w*scale), int(h*scale)))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape)==3 else img
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        eq = clahe.apply(gray)
        return eq
    except Exception:
        return img


def _load_template_images_slim(max_per_key: int = 12):
    """
    Carga plantillas SOLO de objetos registrados por admin (si existe reconocer=1),
    primero desde BD (objetos_imagenes.imagen) y luego desde FS imagenes/objetos/<slug>/...
    Limita el número de imágenes por objeto para evitar sobrecarga.
    Devuelve lista de tuplas (key, img_preprocesada_grayscale).
    """
    import re, os, cv2, numpy as np
    templates = []
    allow = set()
    # construir allow desde BD si es posible
    try:
        rows = db_manager.execute_query("SELECT nombre FROM objetos WHERE reconocer=1") or []
        allow = { re.sub(r"\s+", '_', re.sub(r"[^a-z0-9_\- ]+", '', (r['nombre'] or '').lower())).strip() for r in rows }
    except Exception:
        try:
            rows = db_manager.execute_query("SELECT nombre FROM objetos") or []
            allow = { re.sub(r"\s+", '_', re.sub(r"[^a-z0-9_\- ]+", '', (r['nombre'] or '').lower())).strip() for r in rows }
        except Exception:
            allow = set()

    counts = {}

    # 1) Desde BD
    try:
        rows = db_manager.execute_query("""
            SELECT o.nombre, oi.imagen
            FROM objetos_imagenes oi
            JOIN objetos o ON o.id = oi.objeto_id
        """) or []
        for r in rows:
            nm = (r.get('nombre') or '').lower()
            key = re.sub(r"\s+", '_', re.sub(r"[^a-z0-9_\- ]+", '', nm)).strip()
            if allow and key not in allow:
                continue
            if counts.get(key, 0) >= max_per_key:
                continue
            blob = r.get('imagen')
            if not blob:
                continue
            arr = np.frombuffer(blob, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                continue
            img = _preprocess_for_orb(img)
            templates.append((key, img))
            counts[key] = counts.get(key, 0) + 1
    except Exception:
        pass

    # 2) Desde FS: imagenes/objetos/<carpeta>/**
    try:
        base = os.path.join(IMG_ROOT, 'objetos')
        if os.path.isdir(base):
            for entry in os.listdir(base):
                folder_path = os.path.join(base, entry)
                if not os.path.isdir(folder_path):
                    continue
                key = re.sub(r"\s+", '_', re.sub(r"[^a-z0-9_\- ]+", '', (entry or '').lower())).strip()
                if allow and key not in allow:
                    continue
                for root, _, files in os.walk(folder_path):
                    for fn in files:
                        if not fn.lower().endswith(('.jpg', '.jpeg', '.png')):
                            continue
                        if counts.get(key, 0) >= max_per_key:
                            break
                        path = os.path.join(root, fn)
                        img = cv2.imread(path, cv2.IMREAD_COLOR)
                        if img is None:
                            continue
                        img = _preprocess_for_orb(img)
                        templates.append((key, img))
                        counts[key] = counts.get(key, 0) + 1
    except Exception:
        pass

    # 3) Desde FS: imagenes/equipo/<carpeta>/**
    try:
        base_equipo = os.path.join(IMG_ROOT, 'equipo')
        if os.path.isdir(base_equipo):
            for entry in os.listdir(base_equipo):
                folder_path = os.path.join(base_equipo, entry)
                if not os.path.isdir(folder_path):
                    continue
                key = re.sub(r"\s+", '_', re.sub(r"[^a-z0-9_\- ]+", '', (entry or '').lower())).strip()
                for root, _, files in os.walk(folder_path):
                    for fn in files:
                        if not fn.lower().endswith(('.jpg', '.jpeg', '.png')):
                            continue
                        if counts.get(key, 0) >= max_per_key:
                            break
                        path = os.path.join(root, fn)
                        img = cv2.imread(path, cv2.IMREAD_COLOR)
                        if img is None:
                            continue
                        img = _preprocess_for_orb(img)
                        templates.append((key, img))
                        counts[key] = counts.get(key, 0) + 1
                        print(f"[DEBUG] Plantilla cargada: {key} desde {path}")
    except Exception as e:
        print(f"[WARN] Error cargando plantillas de equipos: {e}")

    # 4) Desde FS: imagenes/item/<carpeta>/**
    try:
        base_item = os.path.join(IMG_ROOT, 'item')
        if os.path.isdir(base_item):
            for entry in os.listdir(base_item):
                folder_path = os.path.join(base_item, entry)
                if not os.path.isdir(folder_path):
                    continue
                key = re.sub(r"\s+", '_', re.sub(r"[^a-z0-9_\- ]+", '', (entry or '').lower())).strip()
                for root, _, files in os.walk(folder_path):
                    for fn in files:
                        if not fn.lower().endswith(('.jpg', '.jpeg', '.png')):
                            continue
                        if counts.get(key, 0) >= max_per_key:
                            break
                        path = os.path.join(root, fn)
                        img = cv2.imread(path, cv2.IMREAD_COLOR)
                        if img is None:
                            continue
                        img = _preprocess_for_orb(img)
                        templates.append((key, img))
                        counts[key] = counts.get(key, 0) + 1
                        print(f"[DEBUG] Plantilla cargada: {key} desde {path}")
    except Exception as e:
        print(f"[WARN] Error cargando plantillas de items: {e}")

    print(f"[INFO] Total plantillas cargadas: {len(templates)}")
    return templates


@app.get('/api/vision/debug_counts_fast')
def vision_debug_counts_fast():
    ...
    """
    Recorre imagenes/ y cuenta archivos sin decodificarlos. Responde rápido.
    """
    import os
    report = {'root': IMG_ROOT, 'objetos': {}, 'equipos': {}, 'otros': {}}
    base = IMG_ROOT
    if not os.path.isdir(base):
        return jsonify({'root': IMG_ROOT, 'message': 'IMG_ROOT no existe'}), 200

    def count_dir(d):
        c = 0
        for _, _, files in os.walk(d):
            for fn in files:
                if fn.lower().endswith(('.jpg', '.jpeg', '.png')):
                    c += 1
        return c

    # objetos
    obj_dir = os.path.join(base, 'objetos')
    if os.path.isdir(obj_dir):
        for entry in os.listdir(obj_dir):
            f = os.path.join(obj_dir, entry)
            if os.path.isdir(f):
                report['objetos'][entry] = count_dir(f)

    # equipos
    eq_dir = os.path.join(base, 'equipos')
    if os.path.isdir(eq_dir):
        for entry in os.listdir(eq_dir):
            f = os.path.join(eq_dir, entry)
            if os.path.isdir(f):
                report['equipos'][entry] = count_dir(f)

    # otros
    for entry in os.listdir(base):
        if entry in ('objetos','equipos'):
            continue
        f = os.path.join(base, entry)
        if os.path.isdir(f):
            report['otros'][entry] = count_dir(f)

    # desde BD
    try:
        db_rows = db_manager.execute_query("SELECT o.nombre, COUNT(oi.id) c FROM objetos o LEFT JOIN objetos_imagenes oi ON oi.objeto_id=o.id GROUP BY o.id, o.nombre") or []
        report['objetos_db'] = { r['nombre']: r['c'] for r in db_rows }
    except Exception:
        report['objetos_db'] = {}

    return jsonify(report), 200


# =============================
# ENDPOINTS DE IA AVANZADA
# =============================

@app.get('/api/ai/status')
def ai_status():
    """Estado del sistema de IA avanzada"""
    if AI_MANAGER:
        status = AI_MANAGER.get_ai_status()
        return jsonify(status), 200
    else:
        return jsonify({
            'ai_available': False,
            'message': 'Sistema de IA no inicializado'
        }), 200


@app.post('/api/ai/voice/process')
def ai_voice_process():
    """Procesar comando de voz con IA avanzada"""
    try:
        verify_jwt_in_request()
    except Exception:
        return jsonify({'message': 'Token requerido'}), 401
    
    data = request.get_json(silent=True) or {}
    audio_b64 = data.get('audio_base64')
    
    if not audio_b64:
        return jsonify({'message': 'audio_base64 requerido'}), 400
    
    if AI_MANAGER and AI_MANAGER.voice_ai_enabled:
        try:
            # Decodificar audio
            if ',' in audio_b64:
                audio_b64 = audio_b64.split(',')[1]
            
            audio_bytes = base64.b64decode(audio_b64)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Procesar con IA
            result = AI_MANAGER.process_voice_command(audio_array)
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error procesando audio: {str(e)}',
                'ai_enhanced': True
            }), 500
    else:
        return jsonify({
            'success': False,
            'error': 'IA de voz no disponible',
            'ai_enhanced': False
        }), 503


@app.post('/api/ai/vision/train')
def ai_vision_train():
    """Entrenar modelo de visión personalizado"""
    try:
        verify_jwt_or_admin()
    except Exception:
        return jsonify({'message': 'Permisos de admin requeridos'}), 401
    
    data = request.get_json(silent=True) or {}
    training_path = data.get('training_data_path', 'training_data')
    epochs = data.get('epochs', 10)
    
    if AI_MANAGER and AI_MANAGER.vision_ai_enabled:
        try:
            result = AI_MANAGER.train_custom_vision_model(training_path, epochs)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error entrenando modelo: {str(e)}'
            }), 500
    else:
        return jsonify({
            'success': False,
            'error': 'IA de visión no disponible'
        }), 503


@app.get('/api/ai/stats')
def ai_stats():
    """Estadísticas detalladas del sistema de IA"""
    try:
        verify_jwt_in_request()
    except Exception:
        return jsonify({'message': 'Token requerido'}), 401
    
    if AI_MANAGER:
        stats = AI_MANAGER.get_ai_status()
        
        # Añadir estadísticas adicionales
        stats['system_info'] = {
            'ai_modules_available': AI_AVAILABLE,
            'tensorflow_available': 'tensorflow' in str(type(AI_MANAGER.vision_detector)) if AI_MANAGER.vision_detector else False,
            'deepspeech_available': 'deepspeech' in str(type(AI_MANAGER.voice_processor)) if AI_MANAGER.voice_processor else False
        }
        
        return jsonify(stats), 200
    else:
        return jsonify({
            'ai_available': False,
            'message': 'Sistema de IA no disponible'
        }), 200


# =====================================================================
# MANEJO DE ERRORES
# =====================================================================

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'message': 'Endpoint no encontrado'}), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    # Imprimir el error completo en consola
    print(f"[ERROR] ERROR 500 en {request.path}")
    print(f"[ERROR] Error: {str(error)}")
    import traceback
    traceback.print_exc()
    
    if request.path.startswith('/api/'):
        # Siempre devolver el error completo para debugging
        return jsonify({
            'message': 'Error interno del servidor',
            'error': str(error),
            'type': type(error).__name__
        }), 500
    return render_template('500.html'), 500


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'message': 'Token expirado'}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'message': 'Token inválido'}), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'message': 'Token de autorización requerido'}), 401


# =====================================================================
# MAIN
# =====================================================================

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('models', exist_ok=True)  # Para modelos de IA

    print("[SISTEMA] WEB + API REST - CENTRO MINERO SENA")
    print("=" * 60)
    print("[WEB] Interfaz Web: http://localhost:5000")
    print("[API] REST: http://localhost:5000/api/")
    
    # Inicializar sistema de IA después de definir todas las funciones
    if AI_AVAILABLE:
        try:
            initialize_ai_system()
        except Exception as e:
            print(f"[WARN] Error inicializando IA: {e}")
    
    # Activar debug temporalmente para ver errores
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
