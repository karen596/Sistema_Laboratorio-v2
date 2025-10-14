# -*- coding: utf-8 -*-
"""
Fix para agregar import de CORS
"""

def fix_cors_import():
    """Agregar import de CORS si no existe"""
    
    with open('web_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si ya tiene el import
    if 'from flask_cors import CORS' in content:
        print("✅ CORS ya está importado")
        return True
    
    # Agregar import después de flask_jwt_extended
    if 'from flask_jwt_extended import' in content:
        content = content.replace(
            'from flask_jwt_extended import JWTManager, create_access_token, verify_jwt_in_request, get_jwt_identity',
            'from flask_jwt_extended import JWTManager, create_access_token, verify_jwt_in_request, get_jwt_identity\nfrom flask_cors import CORS'
        )
        
        with open('web_app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Import de CORS agregado")
        return True
    
    return False

if __name__ == "__main__":
    fix_cors_import()
