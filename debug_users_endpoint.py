#!/usr/bin/env python3
"""Debug dos endpoints users"""

import asyncio
from fastapi.testclient import TestClient
from app.main import app
import traceback

def test_users_count():
    """Testar endpoint users/count"""
    print("Testando endpoint users/count...")
    
    client = TestClient(app)
    
    # Criar token JWT simples
    import jwt
    from datetime import datetime, timedelta
    
    token = jwt.encode({
        'sub': 'admin@empresa.com',
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
        'user_id': 1,
        'email': 'admin@empresa.com',
        'is_superuser': True
    }, '79722d3f4ca30f6c8de510467e2f452d440cb42d68fc99293dc02ef81c2f9c8f', algorithm='HS256')
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = client.get("/api/v1/users/count", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 200:
            print("ERRO! Vamos investigar...")
            # Tentar acessar endpoint companies para comparar
            comp_response = client.get("/api/v1/companies/count", headers=headers)
            print(f"Companies Status: {comp_response.status_code}")
            print(f"Companies Response: {comp_response.text}")
            
    except Exception as e:
        print(f"Erro na requisição: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_users_count()