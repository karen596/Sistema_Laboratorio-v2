# Sistema de Gestión de Laboratorios - Centro Minero SENA

Sistema web completo para la gestión de laboratorios, equipos, inventario y reservas con integración de IA.

## 🚀 Características Principales

### Gestión Completa
- **Laboratorios y Aulas**: Administración de espacios físicos
- **Equipos**: Control de equipos con estados y mantenimiento
- **Inventario**: Gestión de stock con alertas de nivel bajo
- **Reservas**: Sistema de reservas de equipos
- **Usuarios**: Control de acceso con niveles de permisos

### Inteligencia Artificial
- **Reconocimiento Facial**: Login y registro con OpenCV
- **IA Visual**: Reconocimiento de equipos por imagen
- **Entrenamiento Visual**: Sistema para entrenar modelos de reconocimiento

### Seguridad y Backup
- **Autenticación JWT**: API REST segura
- **Niveles de Usuario**: Control granular de permisos
- **Backups Automáticos**: Sistema de respaldo de base de datos
- **Descarga de Backups**: Exportación de copias de seguridad

## 📋 Requisitos

- Python 3.13+
- MySQL 8.0+
- Navegador web moderno

## 🔧 Instalación

### 1. Clonar el repositorio
```bash
git clone <url-repositorio>
cd Sistema_Laboratorio-v2
```

### 2. Crear entorno virtual
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos
Crear archivo `.env_produccion`:
```env
HOST=localhost
USUARIO_PRODUCCION=laboratorio_prod
PASSWORD_PRODUCCION=tu_password
BASE_DATOS=laboratorio_sistema
JWT_SECRET_KEY=tu_clave_secreta_aqui
```

### 5. Ejecutar migraciones
```bash
python crear_tabla_configuracion.py
```

### 6. Iniciar servidor
```bash
python web_app.py
```

Acceder a: http://localhost:5000

## 👥 Niveles de Usuario

1. **Nivel 1**: Estudiante (solo lectura)
2. **Nivel 2**: Instructor (gestión básica)
3. **Nivel 3**: Coordinador (gestión avanzada)
4. **Nivel 4**: Administrador (acceso completo)

## 🗂️ Estructura del Proyecto

```
Sistema_Laboratorio-v2/
├── web_app.py              # Aplicación principal
├── modules/                # Módulos de IA
│   ├── ai_integration.py
│   ├── facial_recognition_module.py
│   └── visual_recognition_module.py
├── templates/              # Plantillas HTML
├── static/                 # CSS, JS, imágenes
├── backups/               # Backups de BD
├── imagenes/              # Imágenes del sistema
└── requirements.txt       # Dependencias
```

## 🔑 Funcionalidades por Módulo

### Dashboard
- Estadísticas generales
- Gráficos de uso
- Alertas de stock bajo

### Equipos
- Registro con imágenes
- Control de estados
- Historial de mantenimiento

### Inventario
- Control de stock
- Alertas de vencimiento
- Gestión de proveedores

### Reservas
- Calendario de reservas
- Validación de disponibilidad
- Historial de uso

### IA Visual
- Reconocimiento de equipos
- Entrenamiento de modelos
- Estadísticas de precisión

### Backup
- Creación de backups
- Restauración
- Descarga de copias

## 🛠️ Tecnologías

- **Backend**: Flask, Flask-RESTful, Flask-JWT-Extended
- **Base de Datos**: MySQL
- **IA**: OpenCV, NumPy, Pillow
- **Frontend**: Bootstrap 5, JavaScript
- **Autenticación**: JWT, bcrypt

## 📝 Notas Importantes

- El sistema funciona sin dependencias opcionales de IA usando OpenCV
- Los backups se almacenan en la carpeta `backups/`
- Las imágenes de entrenamiento en `imagenes/entrenamiento/`
- Configurar `MYSQLDUMP_PATH` y `MYSQL_PATH` en `.env` si es necesario

## 🐛 Solución de Problemas

### Error de conexión a MySQL
Verificar credenciales en `.env_produccion`

### Error de importación de módulos
```bash
pip install -r requirements.txt --upgrade
```

### Error en reconocimiento facial
El sistema usa OpenCV como respaldo si face-recognition no está disponible

## 📄 Licencia

Centro Minero SENA - Sogamoso, Boyacá

## 👨‍💻 Autor

Sistema desarrollado para el Centro Minero SENA
