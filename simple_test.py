#!/usr/bin/env python3
"""Teste simples dos endpoints users"""

import asyncio
import asyncpg
from passlib.context import CryptContext
import requests

# Config do banco
DB_CONFIG = {
    "host": "192.168.11.62",
    "port": 5432,
    "user": "postgres", 
    "password": "Jvc@1702",
    "database": "pro_team_care_11"
}

BASE_URL = "http://localhost:8000/api/v1"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_existing_user():
    """Pegar um usuário existente"""
    conn = await asyncpg.connect(**DB_CONFIG, server_settings={'search_path': 'master, public'})
    
    try:
        user = await conn.fetchrow("""
            SELECT u.id, u.email_address, p.name
            FROM users u 
            LEFT JOIN people p ON u.person_id = p.id
            WHERE u.is_active = true
            LIMIT 1
        """)
        
        if user:
            print(f"Usuário encontrado: {user['name']} ({user['email_address']})")
            
            # Resetar senha para admin123
            hashed_password = pwd_context.hash("admin123")
            await conn.execute("""
                UPDATE users SET password = $1, is_system_admin = true 
                WHERE id = $2
            """, hashed_password, user['id'])
            
            print("Senha atualizada para: admin123")
            return user['email_address'], "admin123"
        else:
            print("Nenhum usuário encontrado")
            return None, None
            
    finally:
        await conn.close()

def test_login_and_users():
    """Testar login e endpoints users"""
    
    async def setup():
        return await get_existing_user()
    
    email, password = asyncio.run(setup())
    
    if not email:
        print("❌ Nenhum usuário disponível")
        return
    
    print(f"Testando login com: {email} / {password}")
    
    # Fazer login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"username={email}&password={password}"
    )
    
    print(f"Login: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Erro no login: {response.text}")
        return
    
    token = response.json()["access_token"]
    print(f"✅ Token obtido: {token[:50]}...")
    
    # Testar endpoints
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Count
    response = requests.get(f"{BASE_URL}/users/count", headers=headers)
    print(f"GET /users/count: {response.status_code} - {response.text}")
    
    # 2. List
    response = requests.get(f"{BASE_URL}/users/?skip=0&limit=3", headers=headers)
    print(f"GET /users/: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Usuários listados: {len(data.get('users', []))}")
    
    # 3. Profile
    response = requests.get(f"{BASE_URL}/users/me/profile", headers=headers)
    print(f"GET /users/me/profile: {response.status_code}")
    if response.status_code == 200:
        profile = response.json()
        print(f"  Profile: {profile.get('name')}")

if __name__ == "__main__":
    test_login_and_users()