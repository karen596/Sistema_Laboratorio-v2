# -*- coding: utf-8 -*-
# Sistema Web + API REST - Centro Minero SENA
# Interfaz Web Moderna + API RESTful Completa (Flask)

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import JWTManager, create_access_token, verify_jwt_in_request, get_jwt_identity
import mysql.connector
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import base64
import cv2
import numpy as np
import re
import json
from facial_api import FacialRegistrationAPI
import mysql.connector
from datetime import datetime, timedelta
import json
import secrets
import os
from functools import wraps
from dotenv import load_dotenv

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
        query = "SELECT id, nombre, tipo, nivel_acceso, activo FROM usuarios WHERE id = %s AND activo = TRUE"
        users = db_manager.execute_query(query, (user_id,))
        if users:
            user = users[0]
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
            flash('Usuario no encontrado o inactivo', 'error')
    return render_template('login.html')


@app.route('/registro-facial')
@require_login
def registro_facial():
    return render_template('registro_facial.html', user=session)


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


@app.route('/dashboard')
@require_login
def dashboard():
    stats = get_dashboard_stats()
    return render_template('dashboard.html', stats=stats, user=session)


@app.route('/laboratorios')
@require_login
def laboratorios():
    query = """
        SELECT l.id, l.codigo, l.nombre, l.tipo, l.ubicacion, l.capacidad_estudiantes,
               l.responsable, l.estado,
               COALESCE(eq.total_equipos, 0) as total_equipos,
               COALESCE(inv.total_items, 0) as total_items,
               COALESCE(eq.equipos_disponibles, 0) as equipos_disponibles,
               COALESCE(inv.items_criticos, 0) as items_criticos
        FROM laboratorios l
        LEFT JOIN (
            SELECT laboratorio_id, 
                   COUNT(*) as total_equipos,
                   COUNT(CASE WHEN estado = 'disponible' THEN 1 END) as equipos_disponibles
            FROM equipos 
            GROUP BY laboratorio_id
        ) eq ON l.id = eq.laboratorio_id
        LEFT JOIN (
            SELECT laboratorio_id, 
                   COUNT(*) as total_items,
                   COUNT(CASE WHEN cantidad_actual <= cantidad_minima THEN 1 END) as items_criticos
            FROM inventario 
            GROUP BY laboratorio_id
        ) inv ON l.id = inv.laboratorio_id
        WHERE l.estado = 'activo'
        ORDER BY l.tipo, l.codigo
    """
    laboratorios_list = db_manager.execute_query(query)
    return render_template('laboratorios.html', laboratorios=laboratorios_list, user=session)


@app.route('/laboratorio/<int:laboratorio_id>')
@require_login
def laboratorio_detalle(laboratorio_id):
    # Información del laboratorio
    query_lab = """
        SELECT l.*, 
               COALESCE(eq.total_equipos, 0) as total_equipos,
               COALESCE(inv.total_items, 0) as total_items,
               COALESCE(inv.valor_inventario, 0) as valor_inventario
        FROM laboratorios l
        LEFT JOIN (
            SELECT laboratorio_id, COUNT(*) as total_equipos
            FROM equipos 
            WHERE laboratorio_id = %s
            GROUP BY laboratorio_id
        ) eq ON l.id = eq.laboratorio_id
        LEFT JOIN (
            SELECT laboratorio_id, 
                   COUNT(*) as total_items,
                   SUM(cantidad_actual * IFNULL(costo_unitario, 0)) as valor_inventario
            FROM inventario 
            WHERE laboratorio_id = %s
            GROUP BY laboratorio_id
        ) inv ON l.id = inv.laboratorio_id
        WHERE l.id = %s
    """
    laboratorio = db_manager.execute_query(query_lab, (laboratorio_id, laboratorio_id, laboratorio_id))
    if not laboratorio:
        flash('Laboratorio no encontrado', 'error')
        return redirect(url_for('laboratorios'))
    
    # Equipos del laboratorio
    query_equipos = """
        SELECT id, nombre, tipo, estado, ubicacion,
               DATE_FORMAT(ultima_calibracion, '%d/%m/%Y') as calibracion,
               DATE_FORMAT(proximo_mantenimiento, '%d/%m/%Y') as mantenimiento
        FROM equipos
        WHERE laboratorio_id = %s
        ORDER BY tipo, nombre
    """
    equipos = db_manager.execute_query(query_equipos, (laboratorio_id,))
    
    # Inventario del laboratorio
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
               DATE_FORMAT(e.ultima_calibracion, '%d/%m/%Y') as calibracion,
               DATE_FORMAT(e.proximo_mantenimiento, '%d/%m/%Y') as mantenimiento,
               e.especificaciones,
               l.codigo as laboratorio_codigo, l.nombre as laboratorio_nombre
        FROM equipos e
        INNER JOIN laboratorios l ON e.laboratorio_id = l.id
        ORDER BY l.codigo, e.tipo, e.nombre
    """
    equipos_list = db_manager.execute_query(query)
    for equipo in equipos_list:
        if equipo.get('especificaciones'):
            try:
                equipo['especificaciones'] = json.loads(equipo['especificaciones'])
            except Exception:
                equipo['especificaciones'] = {}
    return render_template('equipos.html', equipos=equipos_list, user=session)


@app.route('/inventario')
@require_login
def inventario():
    query = """
        SELECT i.id, i.nombre, i.categoria, i.cantidad_actual, i.cantidad_minima,
               i.unidad, i.ubicacion, i.proveedor,
               DATE_FORMAT(i.fecha_vencimiento, '%d/%m/%Y') as vencimiento,
               CASE 
                   WHEN i.cantidad_actual <= i.cantidad_minima THEN 'critico'
                   WHEN i.cantidad_actual <= i.cantidad_minima * 1.5 THEN 'bajo'
                   ELSE 'normal'
               END as nivel_stock,
               COALESCE(l.codigo, 'SIN-LAB') as laboratorio_codigo, 
               COALESCE(l.nombre, 'Sin Laboratorio Asignado') as laboratorio_nombre
        FROM inventario i
        LEFT JOIN laboratorios l ON i.laboratorio_id = l.id
        ORDER BY COALESCE(l.codigo, 'ZZZ'), i.categoria, i.nombre
    """
    inventario_list = db_manager.execute_query(query)
    return render_template('inventario.html', inventario=inventario_list, user=session)


@app.route('/reservas')
@require_login
def reservas():
    if session.get('user_level', 1) >= 3:
        query = (
            """
            SELECT r.id, r.fecha_inicio, r.fecha_fin, r.estado, r.observaciones,
                   u.nombre as usuario_nombre, e.nombre as equipo_nombre
            FROM reservas r
            JOIN usuarios u ON r.usuario_id = u.id
            JOIN equipos e ON r.equipo_id = e.id
            WHERE r.estado IN ('programada', 'activa')
            ORDER BY r.fecha_inicio DESC
            """
        )
        reservas_list = db_manager.execute_query(query)
    else:
        query = (
            """
            SELECT r.id, r.fecha_inicio, r.fecha_fin, r.estado, r.observaciones,
                   u.nombre as usuario_nombre, e.nombre as equipo_nombre
            FROM reservas r
            JOIN usuarios u ON r.usuario_id = u.id
            JOIN equipos e ON r.equipo_id = e.id
            WHERE r.usuario_id = %s AND r.estado IN ('programada', 'activa')
            ORDER BY r.fecha_inicio DESC
            """
        )
        reservas_list = db_manager.execute_query(query, (session['user_id'],))
    return render_template('reservas.html', reservas=reservas_list, user=session)


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
    config_list = db_manager.execute_query(query)
    return render_template('configuracion.html', configuraciones=config_list, user=session)

# =====================================================================
# FUNCIONES DE APOYO PARA VISTAS
# =====================================================================

def get_dashboard_stats():
    stats = {}
    eq = db_manager.execute_query("SELECT estado, COUNT(*) cantidad FROM equipos GROUP BY estado")
    stats['equipos_estado'] = {r['estado']: r['cantidad'] for r in eq} if eq else {}
    ic = db_manager.execute_query("SELECT COUNT(*) cantidad FROM inventario WHERE cantidad_actual <= cantidad_minima")
    stats['inventario_critico'] = ic[0]['cantidad'] if ic else 0
    ra = db_manager.execute_query("SELECT COUNT(*) cantidad FROM reservas WHERE estado = 'activa'")
    stats['reservas_activas'] = ra[0]['cantidad'] if ra else 0
    ua = db_manager.execute_query("SELECT COUNT(DISTINCT usuario_id) cantidad FROM comandos_voz WHERE DATE(fecha) = CURDATE()")
    stats['usuarios_activos_hoy'] = ua[0]['cantidad'] if ua else 0
    cv = db_manager.execute_query("SELECT COUNT(*) cantidad FROM comandos_voz WHERE DATE(fecha) = CURDATE()")
    stats['comandos_hoy'] = cv[0]['cantidad'] if cv else 0
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
        verify_jwt_in_request()
        laboratorio_id = request.args.get('laboratorio_id')
        
        if laboratorio_id:
            # Equipos específicos de un laboratorio
            query = """
                SELECT e.id, e.nombre, e.tipo, e.estado, e.ubicacion, e.especificaciones,
                       DATE_FORMAT(e.ultima_calibracion, '%Y-%m-%d') as ultima_calibracion,
                       DATE_FORMAT(e.proximo_mantenimiento, '%Y-%m-%d') as proximo_mantenimiento,
                       l.codigo as laboratorio_codigo, l.nombre as laboratorio_nombre
                FROM equipos e
                INNER JOIN laboratorios l ON e.laboratorio_id = l.id
                WHERE e.laboratorio_id = %s
                ORDER BY e.tipo, e.nombre
            """
            params = [laboratorio_id]
        else:
            # Vista general con información de laboratorio
            query = """
                SELECT e.id, e.nombre, e.tipo, e.estado, e.ubicacion, e.especificaciones,
                       DATE_FORMAT(e.ultima_calibracion, '%Y-%m-%d') as ultima_calibracion,
                       DATE_FORMAT(e.proximo_mantenimiento, '%Y-%m-%d') as proximo_mantenimiento,
                       l.codigo as laboratorio_codigo, l.nombre as laboratorio_nombre,
                       l.tipo as laboratorio_tipo
                FROM equipos e
                INNER JOIN laboratorios l ON e.laboratorio_id = l.id
                ORDER BY l.codigo, e.tipo, e.nombre
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
        
        campos_requeridos = ['nombre', 'tipo', 'laboratorio_id']
        for campo in campos_requeridos:
            if not data.get(campo):
                return {'message': f'{campo} es requerido'}, 400
        
        # Verificar que el laboratorio existe
        lab_exists = db_manager.execute_query("SELECT id FROM laboratorios WHERE id = %s", (data['laboratorio_id'],))
        if not lab_exists:
            return {'message': 'Laboratorio no encontrado'}, 404
        
        import uuid
        equipo_id = f"EQ_{str(uuid.uuid4())[:8].upper()}"
        
        query = """
            INSERT INTO equipos (id, nombre, tipo, estado, ubicacion, especificaciones, laboratorio_id)
            VALUES (%s, %s, %s, 'disponible', %s, %s, %s)
        """
        
        specs_json = json.dumps(data.get('especificaciones')) if data.get('especificaciones') else None
        
        try:
            db_manager.execute_query(query, (
                equipo_id, data['nombre'], data['tipo'], 
                data.get('ubicacion'), specs_json, data['laboratorio_id']
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
        verify_jwt_in_request()
        parser = reqparse.RequestParser()
        parser.add_argument('estado', choices=['disponible', 'en_uso', 'mantenimiento', 'fuera_servicio'])
        parser.add_argument('ubicacion')
        parser.add_argument('especificaciones', type=dict)
        args = parser.parse_args()
        updates, params = [], []
        if args['estado']:
            updates.append('estado = %s'); params.append(args['estado'])
        if args['ubicacion']:
            updates.append('ubicacion = %s'); params.append(args['ubicacion'])
        if args['especificaciones']:
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
        
        query = """
            INSERT INTO laboratorios (codigo, nombre, tipo, ubicacion, capacidad_estudiantes,
                                    area_m2, responsable, equipamiento_especializado, normas_seguridad)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            db_manager.execute_query(query, (
                data['codigo'], data['nombre'], data['tipo'],
                data.get('ubicacion'), data.get('capacidad_estudiantes', 0),
                data.get('area_m2'), data.get('responsable'),
                data.get('equipamiento_especializado'), data.get('normas_seguridad')
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
        verify_jwt_in_request()
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
                       r.estado, r.observaciones, r.fecha_creacion,
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
                       r.estado, r.observaciones, r.fecha_creacion,
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
        parser.add_argument('observaciones')
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
                INSERT INTO reservas (id, usuario_id, equipo_id, fecha_inicio, fecha_fin, estado, observaciones)
                VALUES (%s, %s, %s, %s, %s, 'programada', %s)
                """,
                (reserva_id, current_user, args['equipo_id'], fecha_inicio, fecha_fin, args['observaciones']),
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
    Procesador de comandos de voz simplificado - Solo navegación
    """
    comando = comando.lower().strip()
    
    # =============================
    # COMANDOS DE NAVEGACIÓN
    # =============================
    
    # Dashboard / Inicio
    if any(p in comando for p in ['dashboard', 'inicio', 'home', 'principal']):
        return {'mensaje': 'Navegando al dashboard...', 'exito': True, 'accion': 'navegar', 'url': '/dashboard'}
    
    # Laboratorios
    if any(p in comando for p in ['laboratorios', 'laboratorio', 'labs']):
        return {'mensaje': 'Navegando a laboratorios...', 'exito': True, 'accion': 'navegar', 'url': '/laboratorios'}
    
    # Equipos
    if any(p in comando for p in ['equipos', 'equipo']):
        return {'mensaje': 'Navegando a equipos...', 'exito': True, 'accion': 'navegar', 'url': '/equipos'}
    
    # Inventario
    if any(p in comando for p in ['inventario', 'stock', 'almacén', 'almacen']):
        return {'mensaje': 'Navegando a inventario...', 'exito': True, 'accion': 'navegar', 'url': '/inventario'}
    
    # Reservas
    if any(p in comando for p in ['reservas', 'reserva']):
        return {'mensaje': 'Navegando a reservas...', 'exito': True, 'accion': 'navegar', 'url': '/reservas'}
    
    # Usuarios (solo para admins)
    if any(p in comando for p in ['usuarios', 'usuario']):
        return {'mensaje': 'Navegando a usuarios...', 'exito': True, 'accion': 'navegar', 'url': '/usuarios'}
    
    # =============================
    # COMANDOS DE AYUDA
    # =============================
    
    if any(p in comando for p in ['ayuda', 'help', 'comandos', 'qué puedo decir', 'que puedo decir']):
        return {
            'mensaje': """Comandos de navegación disponibles:
            • "Dashboard" o "Inicio" - Ir al panel principal
            • "Laboratorios" - Ver todos los laboratorios
            • "Equipos" - Gestión de equipos
            • "Inventario" - Control de inventario
            • "Reservas" - Sistema de reservas
            • "Usuarios" - Gestión de usuarios""", 
            'exito': True
        }
    
    # =============================
    # COMANDO NO RECONOCIDO
    # =============================
    
    return {
        'mensaje': f'Comando "{comando}" no reconocido. Diga "ayuda" para ver comandos disponibles.', 
        'exito': False
    }

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
    from ai_integration import create_ai_manager, enhance_vision_match_endpoint
    
    # Crear gestor de IA (se inicializará después de definir procesar_comando_voz)
    def initialize_ai_system():
        global AI_MANAGER
        if AI_MANAGER is None:
            AI_MANAGER = create_ai_manager(procesar_comando_voz, IMG_ROOT)
            if AI_MANAGER:
                print("🤖 Sistema de IA avanzada inicializado")
                # Iniciar control por voz si está disponible
                if AI_MANAGER.voice_ai_enabled:
                    AI_MANAGER.start_voice_control()
                    print("🎤 Control por voz avanzado activado")
            else:
                print("⚠️ Sistema de IA no disponible, usando métodos tradicionales")
        return AI_MANAGER
    
    AI_AVAILABLE = True
    
except ImportError as e:
    print(f"⚠️ Módulos de IA no disponibles: {e}")
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
        else:
            db_manager.execute_query(
                "INSERT INTO objetos (nombre, categoria, descripcion) VALUES (%s,%s,%s)",
                (nombre, categoria, descripcion)
            )
            rs_new = db_manager.execute_query("SELECT LAST_INSERT_ID() as id")
            objeto_id = rs_new[0]['id'] if rs_new else None
    except Exception as e:
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
        db_manager.execute_query(
            """
            INSERT INTO objetos_imagenes (objeto_id, imagen, path, thumb, content_type, fuente, notas)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (objeto_id, blob, file_path.replace('\\','/'), thumb_blob, content_type, fuente, notas)
        )
    except Exception as e:
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
        verify_jwt_in_request()
        data = request.get_json(silent=True) or {}
        nombre = (data.get('nombre') or '').strip()
        categoria = (data.get('categoria') or '').strip()
        descripcion = data.get('descripcion')
        if not nombre:
            return {'message': 'nombre requerido'}, 400
        try:
            # Verificar si ya existe
            rs_exist = db_manager.execute_query(
                "SELECT id FROM objetos WHERE nombre=%s AND (categoria=%s OR (categoria IS NULL AND %s IS NULL))",
                (nombre, categoria or None, categoria or None)
            )
            if rs_exist:
                return {'message': f'Ya existe un objeto "{nombre}" en la categoría "{categoria or "Sin categoría"}". Use el registro existente o cambie el nombre.', 'id': rs_exist[0]['id'], 'existe': True}, 200
            
            # Crear nuevo objeto
            db_manager.execute_query(
                "INSERT INTO objetos (nombre, categoria, descripcion) VALUES (%s, %s, %s)",
                (nombre, categoria or None, descripcion),
            )
            rs = db_manager.execute_query("SELECT id FROM objetos WHERE nombre=%s AND (categoria=%s OR (categoria IS NULL AND %s IS NULL)) ORDER BY id DESC LIMIT 1", (nombre, categoria or None, categoria or None))
            return {'message': 'Objeto creado exitosamente', 'id': rs[0]['id'] if rs else None}, 201
        except Exception as e:
            if '1062' in str(e) or 'Duplicate entry' in str(e):
                return {'message': f'Ya existe un objeto con ese nombre y categoría. Use un nombre diferente o seleccione el existente de la lista.', 'duplicado': True}, 409
            return {'message': f'Error creando objeto: {str(e)}'}, 500


class ObjetoImagenAPI(Resource):
    def post(self, objeto_id):
        verify_jwt_in_request()
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
            print(f"🔍 Iniciando guardado de imagen para objeto {objeto_id}")
            print(f"🔍 Tipo registro: {tipo_registro}")
            print(f"🔍 Carpeta solicitada: '{carpeta}'")
            
            # Si no hay carpeta especificada, usar nombre del objeto
            if not carpeta:
                rs_obj = db_manager.execute_query("SELECT nombre FROM objetos WHERE id=%s", (objeto_id,))
                if rs_obj:
                    carpeta = rs_obj[0]['nombre']
                    print(f"🔍 Carpeta obtenida del objeto: '{carpeta}'")
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
            base_name = _sanitize_folder(carpeta) if carpeta else _sanitize_folder(rs_obj[0]['nombre'] if 'rs_obj' in locals() and rs_obj else 'item')
            dir_path = os.path.join('imagenes', base_folder, base_name)
            if safe_sub:
                dir_path = os.path.join(dir_path, safe_sub)
            
            print(f"🔍 Ruta completa calculada: {dir_path}")
            print(f"🔍 Directorio de trabajo actual: {os.getcwd()}")
            print(f"🔍 Ruta absoluta: {os.path.abspath(dir_path)}")
            
            # Crear directorio con manejo de errores
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"✅ Directorio creado/verificado: {dir_path}")
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
                print(f"✅ Archivo guardado: {file_path} ({len(blob)} bytes)")
                
                # Verificar que el archivo realmente existe
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    print(f"✅ Verificación: archivo existe con {size} bytes")
                else:
                    print(f"❌ ERROR: archivo NO existe después de guardarlo: {file_path}")
                    return {'message': f'Error: archivo no se guardó correctamente en {file_path}'}, 500
                    
            except PermissionError:
                print(f"❌ ERROR de permisos: {file_path}")
                return {'message': f'Sin permisos para escribir archivo: {file_path}'}, 500
            except OSError as e:
                print(f"❌ ERROR del sistema: {str(e)}")
                return {'message': f'Error del sistema guardando {file_path}: {str(e)}'}, 500
            except Exception as e:
                print(f"❌ ERROR inesperado: {str(e)}")
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
                        print(f"✅ Thumbnail generado: {len(thumb_blob)} bytes")
                    else:
                        print("⚠️ No se pudo codificar thumbnail")
                else:
                    print("⚠️ No se pudo decodificar imagen para thumbnail")
            except Exception as e:
                print(f"⚠️ Error generando thumbnail: {str(e)}")
                # Continuar sin thumbnail
            
            # Guardar registro en BD con manejo de errores
            try:
                db_manager.execute_query(
                    """
                    INSERT INTO objetos_imagenes (objeto_id, imagen, path, thumb, content_type, fuente, notas)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (objeto_id, blob, file_path.replace('\\','/'), thumb_blob, content_type, fuente, notas),
                )
                print(f"✅ Registro guardado en BD para objeto {objeto_id}")
                
                # Listar contenido de la carpeta para verificar
                try:
                    parent_dir = os.path.dirname(file_path)
                    files = os.listdir(parent_dir)
                    print(f"📁 Contenido de {parent_dir}: {files}")
                except Exception as e:
                    print(f"⚠️ No se pudo listar directorio: {str(e)}")
                
                return {'message': 'Imagen almacenada exitosamente', 'path': file_path.replace('\\','/'), 'size_bytes': len(blob)}, 201
            except Exception as e:
                # Si falla BD, intentar eliminar archivo para evitar inconsistencias
                try:
                    os.remove(file_path)
                    print(f"🗑️ Archivo eliminado por error BD: {file_path}")
                except:
                    pass
                return {'message': f'Error guardando en base de datos: {str(e)}'}, 500
        except Exception as e:
            return {'message': f'Error guardando imagen: {str(e)}'}, 500


api.add_resource(ObjetosAPI, '/api/objetos')
api.add_resource(ObjetoImagenAPI, '/api/objetos/<int:objeto_id>/imagenes')

@app.route('/objetos/registrar')
@require_login
@require_level(3)
def objetos_registrar():
    return render_template('objetos_registrar.html', user=session)

# =============================
# OBJETOS: Gestión individual (GET, PUT, DELETE)
# =============================

class ObjetoAPI(Resource):
    def get(self, objeto_id: int):
        verify_jwt_in_request()
        rs = db_manager.execute_query(
            "SELECT id, nombre, categoria, descripcion, DATE_FORMAT(fecha_creacion, '%Y-%m-%d %H:%i') as fecha_creacion FROM objetos WHERE id=%s",
            (objeto_id,)
        )
        if not rs:
            return {'message': 'Objeto no encontrado'}, 404
        return rs[0], 200

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

class ObjetoImagenesAPI(Resource):
    def get(self, objeto_id: int):
        verify_jwt_in_request()
        rs = db_manager.execute_query(
            "SELECT id, path, content_type, DATE_FORMAT(fecha_creacion, '%Y-%m-%d %H:%i') as fecha_creacion FROM objetos_imagenes WHERE objeto_id=%s ORDER BY id DESC",
            (objeto_id,)
        )
        return {'imagenes': rs}, 200

@app.get('/api/objetos/imagen_thumb/<int:img_id>')
def objeto_imagen_thumb(img_id: int):
    # No requiere JWT para facilitar renderizado de miniaturas; restringe a logged-in vía sesión si se desea
    row = db_manager.execute_query("SELECT thumb, content_type FROM objetos_imagenes WHERE id=%s", (img_id,))
    if not row or row[0]['thumb'] is None:
        return jsonify({'message': 'Thumbnail no disponible'}), 404
    ct = row[0]['content_type'] or 'image/jpeg'
    return app.response_class(response=row[0]['thumb'], status=200, mimetype=ct)

api.add_resource(ObjetoImagenesAPI, '/api/objetos/<int:objeto_id>/imagenes')

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

    return templates


@app.get('/api/vision/debug_counts_fast')
def vision_debug_counts_fast():
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
    if request.path.startswith('/api/'):
        return jsonify({'message': 'Error interno del servidor'}), 500
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

    print("🌐 SISTEMA WEB + API REST - CENTRO MINERO SENA")
    print("=" * 60)
    print("🔗 Interfaz Web: http://localhost:5000")
    print("🔌 API REST: http://localhost:5000/api/")
    
    # Inicializar sistema de IA después de definir todas las funciones
    if AI_AVAILABLE:
        try:
            initialize_ai_system()
        except Exception as e:
            print(f"⚠️ Error inicializando IA: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
