#!/usr/bin/env python3
"""Debug específico do erro de schema users"""

import asyncio
from fastapi.testclient import TestClient
from app.main import app
import traceback

def test_users_endpoint():
    """Testar endpoint users para encontrar erro específico"""
    print("🔍 Testando endpoint users para debug...")
    
    client = TestClient(app)
    
    # Criar token JWT simples
    import jwt
    from datetime import datetime, timedelta
    
    token = jwt.encode({
        'sub': 'admin@proteamcare.com',
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
        'user_id': 1,
        'email': 'admin@proteamcare.com',
        'is_superuser': True
    }, '79722d3f4ca30f6c8de510467e2f452d440cb42d68fc99293dc02ef81c2f9c8f', algorithm='HS256')
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 1. Testar endpoint de contagem
        print("\n1️⃣ Testando users/count...")
        response = client.get("/api/v1/users/count", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code != 200:
            print("❌ Erro no count!")
            return
        
        # 2. Testar endpoint de listagem
        print("\n2️⃣ Testando users (listagem)...")
        response = client.get("/api/v1/users/?skip=0&limit=5", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code != 200:
            print("❌ Erro na listagem!")
            return
            
        # 3. Testar busca de usuário específico
        print("\n3️⃣ Testando users/1 (detalhes)...")
        response = client.get("/api/v1/users/1", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code != 200:
            print("❌ Erro nos detalhes!")
            print("Full error:", response.text)
            return
            
        print("✅ Tudo funcionando!")
        
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_users_endpoint()