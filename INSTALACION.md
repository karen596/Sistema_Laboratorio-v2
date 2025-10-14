# 📦 Guía de Instalación - Sistema de Laboratorios SENA

## 🎯 Requisitos Previos

- **Python 3.13.5** (o superior)
- **MySQL Server** (8.0 o superior)
- **Git** (opcional, para clonar el repositorio)
- **Visual C++ Build Tools** (para Windows, si se instalan módulos de IA)

## 🚀 Instalación Rápida

### Opción 1: Instalación Automática (Recomendada)

```powershell
# 1. Navegar al directorio del proyecto
cd Gil_Project

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar entorno virtual
.venv\Scripts\activate

# 4. Ejecutar instalador automático
python instalar_dependencias.py
```

### Opción 2: Instalación Manual

#### A. Instalación Mínima (Solo funcionalidades básicas)

```powershell
pip install -r requirements_minimal.txt
```

**Incluye:**
- ✅ Interfaz web y API REST
- ✅ Gestión de laboratorios, equipos y reservas
- ✅ Reconocimiento visual básico (OpenCV)
- ✅ Reconocimiento de voz básico
- ✅ Base de datos MySQL

#### B. Instalación Completa (Con módulos de IA)

```powershell
pip install -r requirements.txt
```

**Incluye todo lo anterior más:**
- 🤖 Reconocimiento facial avanzado
- 🎤 Reconocimiento de voz avanzado (DeepSpeech)
- 👁️ Visión por computadora (TensorFlow)

## 🔧 Instalación de Dependencias Problemáticas

### 1. Face Recognition (Windows)

El módulo `face-recognition` requiere `dlib`, que puede ser difícil de instalar en Windows.

**Solución:**

```powershell
# Opción A: Usar wheel precompilado
# 1. Descargar dlib wheel desde:
#    https://github.com/z-mahmud22/Dlib_Windows_Python3.x
# 2. Instalar el wheel descargado
pip install dlib-19.24.6-cp313-cp313-win_amd64.whl

# 3. Instalar face-recognition
pip install face-recognition==1.3.0
```

**Opción B: Instalar Visual C++ Build Tools**

1. Descargar desde: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Instalar "Desktop development with C++"
3. Reiniciar y ejecutar: `pip install face-recognition`

### 2. PyAudio (Captura de audio en tiempo real)

```powershell
# Opción A: Usar pipwin
pip install pipwin
pipwin install pyaudio

# Opción B: Usar wheel precompilado
# Descargar desde: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install PyAudio-0.2.14-cp313-cp313-win_amd64.whl
```

### 3. TensorFlow (IA Avanzada)

```powershell
# Para instalación completa
pip install tensorflow==2.16.1

# Para instalación ligera (solo inferencia)
pip install tflite-runtime==2.14.0
```

## ⚙️ Configuración del Sistema

### 1. Configurar Base de Datos

```powershell
# Crear archivo .env_produccion
copy .env_ejemplo .env_produccion

# Editar .env_produccion con tus credenciales
```

**Contenido de `.env_produccion`:**

```env
# Base de Datos
HOST=localhost
USUARIO_PRODUCCION=root
PASSWORD_PRODUCCION=tu_password
BASE_DATOS=laboratorio_sistema

# Seguridad
FLASK_SECRET_KEY=tu_clave_secreta_aqui
JWT_SECRET_KEY=tu_jwt_secret_aqui

# Configuración
FLASK_ENV=production
DEBUG=False
```

### 2. Crear Base de Datos

```powershell
# Ejecutar script de creación de tablas
python scripts/crear_tablas_automatico.py
```

### 3. Crear Usuarios Iniciales

```powershell
# Crear usuarios del centro
python scripts/crear_usuarios_centro.py
```

## 🧪 Verificar Instalación

### Ejecutar Tests

```powershell
# Test completo de todos los módulos
python test_all_modules.py

# Test de dependencias
python tests/verificar_dependencias.py

# Test de entorno
python tests/verificar_entorno.py
```

### Iniciar el Sistema

```powershell
# Iniciar servidor web
python web_app.py
```

El sistema estará disponible en: `http://localhost:5000`

## 📋 Verificación de Dependencias

### Dependencias Esenciales (Requeridas)

| Paquete | Versión | Estado | Función |
|---------|---------|--------|---------|
| Flask | 3.1.1 | ✅ | Framework web |
| mysql-connector-python | 9.4.0 | ✅ | Base de datos |
| opencv-python | 4.12.0.88 | ✅ | Visión computacional |
| numpy | 2.2.6 | ✅ | Procesamiento numérico |
| Pillow | 11.3.0 | ✅ | Procesamiento de imágenes |
| SpeechRecognition | 3.10.0 | ✅ | Reconocimiento de voz |
| pyttsx3 | 2.90 | ✅ | Síntesis de voz |

### Dependencias Opcionales

| Paquete | Versión | Función |
|---------|---------|---------|
| face-recognition | 1.3.0 | Reconocimiento facial avanzado |
| webrtcvad | 2.0.10 | Detección de actividad de voz |
| tensorflow | 2.16.1 | IA y visión avanzada |
| scikit-image | 0.24.0 | Procesamiento de imágenes avanzado |

## 🐛 Solución de Problemas

### Error: "No module named 'face_recognition'"

**Solución:** El módulo es opcional. El sistema funcionará sin él usando OpenCV.

Para instalarlo, sigue las instrucciones en la sección "Face Recognition (Windows)".

### Error: "No module named 'webrtcvad'"

**Solución:**

```powershell
pip install webrtcvad==2.0.10
```

### Error: "MySQL Connection Failed"

**Solución:**

1. Verifica que MySQL esté ejecutándose
2. Verifica las credenciales en `.env_produccion`
3. Verifica que la base de datos exista

```sql
CREATE DATABASE IF NOT EXISTS laboratorio_sistema;
```

### Error: "Port 5000 already in use"

**Solución:**

```powershell
# Cambiar puerto en web_app.py o usar:
$env:FLASK_RUN_PORT=5001
python web_app.py
```

### Error al importar OpenCV

**Solución:**

```powershell
# Reinstalar OpenCV
pip uninstall opencv-python opencv-python-headless
pip install opencv-python==4.12.0.88
```

## 📊 Estado de Módulos

Después de la instalación, ejecuta `python test_all_modules.py` para ver el estado:

```
Reconocimiento Visual............................. ✅ PASS
Integración IA.................................... ✅ PASS
Visión Avanzada................................... ✅ PASS
Sistema de Laboratorio............................ ✅ PASS
Reconocimiento Facial............................. ⚠️  OPCIONAL
Voz Avanzada...................................... ⚠️  OPCIONAL
```

## 📚 Archivos de Dependencias

- **`requirements.txt`** - Instalación completa con todas las características
- **`requirements_minimal.txt`** - Instalación mínima solo con lo esencial
- **`requirements_working.txt`** - Snapshot de dependencias actualmente instaladas
- **`instalar_dependencias.py`** - Script de instalación interactivo

## 🔄 Actualizar Dependencias

```powershell
# Actualizar todas las dependencias
pip install -r requirements.txt --upgrade

# Actualizar solo una dependencia específica
pip install --upgrade nombre-paquete
```

## 💡 Recomendaciones

1. **Usa un entorno virtual** para evitar conflictos de dependencias
2. **Instala primero la versión mínima** y luego agrega módulos opcionales
3. **Verifica la instalación** con `test_all_modules.py` antes de usar en producción
4. **Mantén actualizadas** las dependencias de seguridad (Flask, JWT, etc.)
5. **Documenta** cualquier cambio en las dependencias

## 📞 Soporte

Si encuentras problemas durante la instalación:

1. Revisa los logs de error
2. Ejecuta `python tests/verificar_dependencias.py`
3. Consulta la documentación oficial de cada paquete
4. Verifica que tu versión de Python sea compatible

---

**Sistema de Laboratorios - Centro Minero SENA**  
Versión: 2.0  
Última actualización: Octubre 2025
