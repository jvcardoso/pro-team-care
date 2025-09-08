#!/usr/bin/env python3
"""
Debug detalhado do frontend - verificar se componentes de segurança estão carregando
"""
import requests
import time

def debug_frontend():
    print("🔍 DEBUG: Verificando componentes de segurança no frontend")
    print("=" * 60)
    
    frontend_url = "http://localhost:3001"
    backend_url = "http://localhost:8000/api/v1"
    
    print(f"🌐 Frontend URL: {frontend_url}")
    print(f"🔧 Backend URL: {backend_url}")
    print()
    
    # 1. Verificar se frontend responde
    try:
        print("1️⃣ Testando conectividade frontend...")
        response = requests.get(frontend_url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Frontend acessível")
            
            # Verificar se há JavaScript errors no console (simulado)
            if "vite" in response.text.lower():
                print("   ✅ Vite detectado - servidor de desenvolvimento ativo")
            else:
                print("   ⚠️ Vite não detectado")
                
        else:
            print(f"   ❌ Frontend retornou: {response.status_code}")
            return
            
    except Exception as e:
        print(f"   ❌ Frontend inacessível: {e}")
        return
    
    # 2. Testar backend
    print("\n2️⃣ Testando backend...")
    try:
        # Login
        login_response = requests.post(f"{backend_url}/auth/login", data={
            "username": "admin@proteamcare.com", 
            "password": "password"
        })
        
        if login_response.status_code == 200:
            print("   ✅ Backend login funcionando")
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Testar endpoints de segurança
            security_endpoints = [
                "/secure-sessions/available-profiles",
                "/secure-sessions/current-context"
            ]
            
            for endpoint in security_endpoints:
                try:
                    resp = requests.get(f"{backend_url}{endpoint}", headers=headers)
                    print(f"   📡 {endpoint}: {resp.status_code}")
                except Exception as e:
                    print(f"   ❌ {endpoint}: Erro - {e}")
                    
        else:
            print(f"   ❌ Backend login falhou: {login_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Backend inacessível: {e}")
    
    # 3. Instruções para debug manual
    print("\n3️⃣ INSTRUÇÕES PARA DEBUG MANUAL:")
    print("=" * 40)
    
    print("\n📋 Para ver se os componentes estão carregando:")
    print("1. Abra: http://192.168.11.83:3001")
    print("2. Pressione F12 (Developer Tools)")
    print("3. Vá na aba Console")
    print("4. Procure por:")
    print("   - ✅ '🔐 Inicializando serviço de sessão segura...'")
    print("   - ✅ '✅ Serviço de sessão segura inicializado com sucesso'")
    print("   - ❌ Qualquer erro vermelho")
    
    print("\n📍 ONDE PROCURAR os componentes:")
    print("▸ HEADER (topo): Deve ter botão 'Trocar Perfil' se você for ROOT")
    print("▸ BANNER: Faixa laranja aparece APENAS quando personificando")  
    print("▸ DASHBOARD: Seletor de contexto no canto superior direito")
    
    print("\n🔑 MOTIVOS pelos quais podem NÃO aparecer:")
    print("• Você não é ROOT - ProfileSwitcher só aparece para ROOT")
    print("• Não há outros usuários - sem usuários para personificar")
    print("• Não há sessão segura ativa - funcionalidade opcional")
    print("• Erro de JavaScript - check console do navegador")
    
    print("\n📊 COMO TESTAR se está funcionando:")
    print("1. Faça login como admin@proteamcare.com")
    print("2. Se você ver 'Trocar Perfil' no header = ✅ Funcionando")
    print("3. Se clicar e aparecer dropdown = ✅ Componente carregou")
    print("4. Se lista estiver vazia = Normal (sem dados ainda)")
    
    print("\n🎯 TESTE FINAL:")
    print("Execute no console do navegador:")
    print("   window.secureSessionService || 'Serviço não carregado'")
    
    print(f"\n✅ Debug concluído - Acesse: {frontend_url}")

if __name__ == "__main__":
    debug_frontend()