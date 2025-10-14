#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar configuración de correo
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('.env_produccion')

print("=" * 70)
print("VERIFICACIÓN DE CONFIGURACIÓN DE CORREO")
print("=" * 70)

# Obtener variables
smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
smtp_port = os.getenv('SMTP_PORT', '587')
smtp_user = os.getenv('SMTP_USER', '')
smtp_password = os.getenv('SMTP_PASSWORD', '')

print(f"\n[CONFIGURACIÓN ACTUAL]")
print(f"SMTP_SERVER: {smtp_server}")
print(f"SMTP_PORT: {smtp_port}")
print(f"SMTP_USER: {smtp_user if smtp_user else '❌ NO CONFIGURADO'}")
print(f"SMTP_PASSWORD: {'✓ Configurado (' + str(len(smtp_password)) + ' caracteres)' if smtp_password else '❌ NO CONFIGURADO'}")

if not smtp_user or not smtp_password:
    print("\n" + "=" * 70)
    print("❌ ERROR: Faltan credenciales de correo")
    print("=" * 70)
    print("\nAgrega estas líneas a tu archivo .env_produccion:")
    print("\nSMTP_SERVER=smtp.gmail.com")
    print("SMTP_PORT=587")
    print("SMTP_USER=tu_correo@gmail.com")
    print("SMTP_PASSWORD=tu_contraseña_de_aplicacion")
    print("\n" + "=" * 70)
else:
    print("\n" + "=" * 70)
    print("✓ Configuración completa")
    print("=" * 70)
    
    # Intentar enviar correo de prueba
    print("\n¿Deseas enviar un correo de prueba? (s/n): ", end='')
    respuesta = input().strip().lower()
    
    if respuesta == 's':
        print("\nIngresa el correo destino para la prueba: ", end='')
        email_destino = input().strip()
        
        if email_destino:
            print(f"\n[ENVIANDO CORREO DE PRUEBA A: {email_destino}]")
            
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import ssl
            
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = 'Prueba de Correo - Centro Minero SENA'
                msg['From'] = f'Centro Minero SENA <{smtp_user}>'
                msg['To'] = email_destino
                
                html = """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>✓ Correo de Prueba</h2>
                    <p>Este es un correo de prueba del Sistema de Gestión de Laboratorios.</p>
                    <p>Si recibes este mensaje, la configuración de correo está funcionando correctamente.</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">Centro Minero SENA</p>
                </body>
                </html>
                """
                
                part = MIMEText(html, 'html')
                msg.attach(part)
                
                print("Conectando al servidor SMTP...")
                context = ssl.create_default_context()
                
                with smtplib.SMTP(smtp_server, int(smtp_port), timeout=10) as server:
                    print("Iniciando TLS...")
                    server.starttls(context=context)
                    
                    print("Autenticando...")
                    server.login(smtp_user, smtp_password)
                    
                    print("Enviando correo...")
                    server.send_message(msg)
                    
                print("\n" + "=" * 70)
                print("✓ CORREO ENVIADO EXITOSAMENTE")
                print("=" * 70)
                print(f"\nRevisa la bandeja de entrada de: {email_destino}")
                
            except smtplib.SMTPAuthenticationError as e:
                print("\n" + "=" * 70)
                print("❌ ERROR DE AUTENTICACIÓN")
                print("=" * 70)
                print(f"\n{str(e)}")
                print("\nVerifica que:")
                print("1. El correo sea correcto")
                print("2. Hayas creado una 'Contraseña de Aplicación' en Gmail")
                print("3. La contraseña esté copiada sin espacios")
                
            except Exception as e:
                print("\n" + "=" * 70)
                print("❌ ERROR AL ENVIAR CORREO")
                print("=" * 70)
                print(f"\n{str(e)}")

print("\n" + "=" * 70)
