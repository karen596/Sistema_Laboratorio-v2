# -*- coding: utf-8 -*-
"""
Script de Instalación de Dependencias
Sistema de Laboratorios - Centro Minero SENA
"""

import subprocess
import sys
import os

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_warning(text):
    print(f"⚠️  {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def run_pip_install(package):
    """Instala un paquete usando pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def check_package(package_name):
    """Verifica si un paquete está instalado"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def main():
    print_header("INSTALADOR DE DEPENDENCIAS - SISTEMA DE LABORATORIOS")
    
    print_info(f"Python: {sys.version}")
    print_info(f"Pip: {subprocess.check_output([sys.executable, '-m', 'pip', '--version']).decode().strip()}")
    
    print("\nSelecciona el tipo de instalación:")
    print("1. Instalación MÍNIMA (solo funcionalidades básicas)")
    print("2. Instalación COMPLETA (con módulos de IA avanzada)")
    print("3. Instalar solo dependencias faltantes")
    print("4. Actualizar todas las dependencias")
    
    choice = input("\nOpción (1-4): ").strip()
    
    if choice == "1":
        print_header("INSTALACIÓN MÍNIMA")
        requirements_file = "requirements_minimal.txt"
    elif choice == "2":
        print_header("INSTALACIÓN COMPLETA")
        requirements_file = "requirements.txt"
    elif choice == "3":
        print_header("INSTALACIÓN DE DEPENDENCIAS FALTANTES")
        install_missing_only()
        return
    elif choice == "4":
        print_header("ACTUALIZACIÓN DE DEPENDENCIAS")
        requirements_file = "requirements.txt"
        upgrade = True
    else:
        print_error("Opción inválida")
        return
    
    if not os.path.exists(requirements_file):
        print_error(f"Archivo {requirements_file} no encontrado")
        return
    
    print_info(f"Instalando desde {requirements_file}...")
    
    try:
        cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_file]
        if choice == "4":
            cmd.append("--upgrade")
        
        subprocess.check_call(cmd)
        print_success("Instalación completada exitosamente")
        
        # Verificar instalación
        print_header("VERIFICACIÓN DE INSTALACIÓN")
        verify_installation()
        
    except subprocess.CalledProcessError as e:
        print_error(f"Error durante la instalación: {e}")
        print_warning("Algunas dependencias pueden haber fallado")
        print_info("Revisa los errores arriba para más detalles")

def install_missing_only():
    """Instala solo las dependencias que faltan"""
    essential_packages = {
        'flask': 'Flask==3.1.1',
        'flask_restful': 'Flask-RESTful==0.3.10',
        'flask_jwt_extended': 'Flask-JWT-Extended==4.7.1',
        'flask_cors': 'flask-cors==6.0.1',
        'mysql.connector': 'mysql-connector-python==9.4.0',
        'dotenv': 'python-dotenv==1.0.0',
        'cv2': 'opencv-python==4.12.0.88',
        'PIL': 'Pillow==11.3.0',
        'numpy': 'numpy==2.2.6',
        'speech_recognition': 'SpeechRecognition==3.10.0',
        'pyttsx3': 'pyttsx3==2.90',
        'psutil': 'psutil==7.1.0',
        'requests': 'requests==2.32.5',
    }
    
    optional_packages = {
        'face_recognition': 'face-recognition==1.3.0',
        'webrtcvad': 'webrtcvad==2.0.10',
        'skimage': 'scikit-image==0.24.0',
    }
    
    print_info("Verificando dependencias esenciales...")
    missing_essential = []
    
    for import_name, package_spec in essential_packages.items():
        if not check_package(import_name):
            print_warning(f"Falta: {package_spec}")
            missing_essential.append(package_spec)
        else:
            print_success(f"Instalado: {import_name}")
    
    if missing_essential:
        print_header("INSTALANDO DEPENDENCIAS FALTANTES")
        for package in missing_essential:
            print_info(f"Instalando {package}...")
            if run_pip_install(package):
                print_success(f"Instalado: {package}")
            else:
                print_error(f"Error al instalar: {package}")
    else:
        print_success("Todas las dependencias esenciales están instaladas")
    
    print_info("\nVerificando dependencias opcionales...")
    for import_name, package_spec in optional_packages.items():
        if check_package(import_name):
            print_success(f"Instalado: {import_name}")
        else:
            print_warning(f"No instalado (opcional): {package_spec}")

def verify_installation():
    """Verifica que las dependencias principales estén instaladas"""
    packages_to_check = [
        ('flask', 'Flask'),
        ('mysql.connector', 'MySQL Connector'),
        ('cv2', 'OpenCV'),
        ('numpy', 'NumPy'),
        ('PIL', 'Pillow'),
        ('speech_recognition', 'SpeechRecognition'),
        ('pyttsx3', 'pyttsx3'),
    ]
    
    all_ok = True
    for package, name in packages_to_check:
        if check_package(package):
            print_success(f"{name} instalado correctamente")
        else:
            print_error(f"{name} NO instalado")
            all_ok = False
    
    # Verificar opcionales
    print("\nDependencias opcionales:")
    optional = [
        ('face_recognition', 'Face Recognition'),
        ('webrtcvad', 'WebRTC VAD'),
        ('skimage', 'scikit-image'),
    ]
    
    for package, name in optional:
        if check_package(package):
            print_success(f"{name} instalado")
        else:
            print_info(f"{name} no instalado (opcional)")
    
    if all_ok:
        print_header("✅ INSTALACIÓN EXITOSA")
        print("El sistema está listo para ejecutarse con todas las funcionalidades básicas.")
    else:
        print_header("⚠️  INSTALACIÓN INCOMPLETA")
        print("Algunas dependencias esenciales faltan. Revisa los errores arriba.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Instalación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        sys.exit(1)
