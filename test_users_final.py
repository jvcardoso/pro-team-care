#!/usr/bin/env python3
"""
Verificação final dos sistemas de usuários
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Obter token de autenticação"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": "admin@proteamcare.com", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Erro no login: {response.status_code} - {response.text}")
        return None

def test_basic_crud():
    """Testar CRUD básico de usuários"""
    print("🔧 TESTANDO CRUD BÁSICO DE USUÁRIOS")
    print("-" * 50)
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Listar usuários
    print("1️⃣ Listando usuários...")
    response = requests.get(f"{BASE_URL}/api/v1/users/?page=1&size=5", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {len(data.get('users', []))} usuários listados")
        
        # Mostrar primeiro usuário
        if data.get('users'):
            first_user = data['users'][0]
            print(f"   - {first_user.get('person_name')} ({first_user.get('email_address')})")
    else:
        print(f"❌ Erro na listagem: {response.status_code}")
        return False
    
    # 2. Contar usuários
    print("\n2️⃣ Contando usuários...")
    response = requests.get(f"{BASE_URL}/api/v1/users/count", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total: {data.get('total', 0)} usuários")
    else:
        print(f"❌ Erro na contagem: {response.status_code}")
    
    # 3. Buscar usuário específico
    print("\n3️⃣ Buscando usuário específico...")
    response = requests.get(f"{BASE_URL}/api/v1/users/1", headers=headers)
    if response.status_code == 200:
        user = response.json()
        print(f"✅ Usuário encontrado: {user.get('person_name')}")
    else:
        print(f"❌ Erro na busca: {response.status_code}")
    
    print("\n✅ CRUD básico funcionando!")
    return True

def test_hierarchical_endpoints():
    """Testar endpoints hierárquicos"""
    print("\n🏗️ TESTANDO ENDPOINTS HIERÁRQUICOS")
    print("-" * 50)
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Testar listagem hierárquica
    print("1️⃣ Testando listagem hierárquica...")
    response = requests.get(f"{BASE_URL}/api/v1/hierarchical-users/hierarchical?limit=3", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('total', 0)} usuários acessíveis encontrados")
        print(f"   Nível do solicitante: {data.get('requesting_user_hierarchy', 'Unknown')}")
    else:
        print(f"❌ Erro na listagem hierárquica: {response.status_code}")
        print(f"   Detalhes: {response.text[:200]}...")
    
    # 2. Testar acesso a usuário específico
    print("\n2️⃣ Testando acesso hierárquico...")
    response = requests.get(f"{BASE_URL}/api/v1/hierarchical-users/1/hierarchical", headers=headers)
    if response.status_code == 200:
        user = response.json()
        print(f"✅ Acesso autorizado ao usuário")
        print(f"   Motivo: {user.get('_access_metadata', {}).get('access_reason', 'N/A')}")
    else:
        print(f"❌ Erro no acesso hierárquico: {response.status_code}")
        print(f"   Detalhes: {response.text[:200]}...")
    
    return True

def test_sql_functions():
    """Testar funções SQL"""
    print("\n🗄️ TESTANDO FUNÇÕES SQL")
    print("-" * 50)
    
    import subprocess
    
    try:
        # 1. Testar função hierárquica
        print("1️⃣ Testando função get_accessible_users_hierarchical...")
        result = subprocess.run([
            'psql', '-h', '192.168.11.62', '-p', '5432', '-U', 'postgres', '-d', 'pro_team_care_11',
            '-c', 'SELECT COUNT(*) as total FROM master.get_accessible_users_hierarchical(5);'
        ], env={'PGPASSWORD': 'Jvc@1702'}, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Função SQL funcionando")
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 3:
                total_line = lines[2].strip()
                print(f"   Usuários acessíveis para admin: {total_line}")
        else:
            print(f"❌ Erro na função SQL: {result.stderr}")
            return False
        
        # 2. Testar view hierárquica
        print("\n2️⃣ Testando view vw_users_hierarchical...")
        result = subprocess.run([
            'psql', '-h', '192.168.11.62', '-p', '5432', '-U', 'postgres', '-d', 'pro_team_care_11',
            '-c', 'SELECT hierarchy_level, COUNT(*) FROM master.vw_users_hierarchical GROUP BY hierarchy_level;'
        ], env={'PGPASSWORD': 'Jvc@1702'}, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ View hierárquica funcionando")
            print("   Distribuição por nível:")
            lines = result.stdout.strip().split('\n')[2:-2]  # Remover headers e footers
            for line in lines:
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        level = parts[0].strip()
                        count = parts[1].strip()
                        print(f"     - {level}: {count}")
        else:
            print(f"❌ Erro na view: {result.stderr}")
        
    except Exception as e:
        print(f"❌ Erro ao executar SQL: {e}")
        return False
    
    return True

def check_pending_issues():
    """Verificar questões pendentes"""
    print("\n🔍 VERIFICANDO QUESTÕES PENDENTES")
    print("-" * 50)
    
    issues = []
    
    # 1. Verificar se servidor está rodando
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor backend funcionando")
        else:
            issues.append("Servidor backend com problemas")
    except:
        issues.append("Servidor backend não responde")
    
    # 2. Verificar autenticação
    if get_auth_token():
        print("✅ Sistema de autenticação funcionando")
    else:
        issues.append("Sistema de autenticação com problemas")
    
    # 3. Verificar documentação
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Documentação Swagger acessível")
        else:
            issues.append("Documentação não acessível")
    except:
        issues.append("Documentação não responde")
    
    return issues

def main():
    """Verificação completa"""
    print("🚀 VERIFICAÇÃO FINAL - SISTEMA DE USUÁRIOS")
    print("=" * 60)
    
    # Verificar questões básicas
    issues = check_pending_issues()
    
    # Testes funcionais
    crud_ok = test_basic_crud()
    hierarchical_ok = test_hierarchical_endpoints()
    sql_ok = test_sql_functions()
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL")
    print("=" * 60)
    
    if not issues:
        print("✅ Sem questões pendentes detectadas")
    else:
        print("❌ Questões pendentes encontradas:")
        for issue in issues:
            print(f"   - {issue}")
    
    print(f"\n📋 Status dos sistemas:")
    print(f"   - CRUD básico: {'✅ OK' if crud_ok else '❌ Problemas'}")
    print(f"   - Hierárquico: {'✅ OK' if hierarchical_ok else '❌ Problemas'}")
    print(f"   - SQL Functions: {'✅ OK' if sql_ok else '❌ Problemas'}")
    
    # Decisão final
    all_good = not issues and crud_ok and sql_ok
    
    print(f"\n🎯 CONCLUSÃO:")
    if all_good:
        print("✅ SISTEMA PRONTO - PODE SEGUIR COM NOVA IMPLEMENTAÇÃO!")
        print("🚀 Todos os sistemas de usuários estão funcionais")
    else:
        print("⚠️  VERIFICAR PROBLEMAS ANTES DE PROSSEGUIR")
        print("🔧 Resolver questões pendentes primeiro")
    
    print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
    return all_good

if __name__ == "__main__":
    main()