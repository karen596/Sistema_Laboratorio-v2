#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la API de objetos
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_crear_objeto():
    """Probar creación de objeto"""
    print("=" * 70)
    print("🧪 PROBANDO API DE OBJETOS")
    print("=" * 70)
    
    # Datos del objeto
    data = {
        "nombre": "Cargador Test",
        "categoria": "EPP",
        "descripcion": "Cargador de prueba color negro"
    }
    
    print(f"\n📤 Enviando POST a {BASE_URL}/api/objetos")
    print(f"📦 Datos: {json.dumps(data, indent=2)}")
    
    try:
        # Crear sesión para mantener cookies
        session = requests.Session()
        
        # Primero hacer login
        print("\n🔐 Haciendo login...")
        login_data = {
            "usuario": "ADMIN001",
            "password": "admin123"
        }
        
        login_response = session.post(f"{BASE_URL}/login", data=login_data)
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            print("   ✅ Login exitoso")
        else:
            print(f"   ❌ Login falló: {login_response.text[:200]}")
            return
        
        # Ahora crear el objeto
        print("\n📤 Creando objeto...")
        response = session.post(
            f"{BASE_URL}/api/objetos",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📥 Respuesta:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"   Body: {json.dumps(response_data, indent=2)}")
            
            if response.status_code in [200, 201]:
                print("\n✅ ¡Objeto creado exitosamente!")
                if 'id' in response_data:
                    print(f"   ID del objeto: {response_data['id']}")
            else:
                print(f"\n❌ Error: {response_data.get('message', 'Sin mensaje')}")
                
        except Exception as e:
            print(f"   Body (texto): {response.text[:500]}")
            print(f"   ❌ Error parseando JSON: {e}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se pudo conectar al servidor")
        print("   Verifica que el servidor esté corriendo en http://127.0.0.1:5000")
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_crear_objeto()
