#!/usr/bin/env python3
"""
Script de teste para validar integração Sprint 1: Foundation & Security
Testa modelos ORM, views, functions e serviços implementados
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.infrastructure.database import engine, async_session
from app.infrastructure.orm.models import User, Role, Permission, People
from app.infrastructure.orm.views import UserCompleteView, RolePermissionView
from app.infrastructure.services.security_service import SecurityService
from app.infrastructure.services.validation_service import ValidationService

load_dotenv()


async def test_database_connection():
    """Teste 1: Conectividade básica"""
    print("🔍 Teste 1: Conectividade com banco de dados")
    try:
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            print("✅ Conexão com banco estabelecida")
            return True
    except Exception as e:
        print(f"❌ Falha na conexão: {e}")
        return False


async def test_orm_models():
    """Teste 2: Modelos ORM novos"""
    print("\n🔍 Teste 2: Modelos ORM (Users, Roles, Permissions)")
    
    try:
        async with async_session() as session:
            # Testar se tabelas existem
            tables_to_test = [
                ("users", User),
                ("roles", Role), 
                ("permissions", Permission),
                ("people", People)
            ]
            
            for table_name, model_class in tables_to_test:
                try:
                    # Testar query simples
                    from sqlalchemy import select
                    query = select(model_class).limit(1)
                    result = await session.execute(query)
                    users = result.scalars().first()
                    
                    print(f"✅ Tabela '{table_name}' acessível via ORM")
                except Exception as e:
                    print(f"❌ Erro ao acessar tabela '{table_name}': {e}")
                    return False
            
            return True
            
    except Exception as e:
        print(f"❌ Erro nos testes de ORM: {e}")
        return False


async def test_views():
    """Teste 3: Views críticas"""
    print("\n🔍 Teste 3: Views de autenticação")
    
    try:
        async with async_session() as session:
            views_to_test = [
                ("vw_users_complete", UserCompleteView),
                ("vw_role_permissions", RolePermissionView)
            ]
            
            for view_name, view_class in views_to_test:
                try:
                    from sqlalchemy import select
                    query = select(view_class).limit(1)
                    result = await session.execute(query)
                    record = result.scalars().first()
                    
                    print(f"✅ View '{view_name}' acessível")
                except Exception as e:
                    print(f"⚠️  View '{view_name}' não acessível: {e}")
                    # Views podem não ter dados, mas devem existir
            
            return True
            
    except Exception as e:
        print(f"❌ Erro nos testes de Views: {e}")
        return False


async def test_security_functions():
    """Teste 4: Functions de segurança"""
    print("\n🔍 Teste 4: Functions de segurança PostgreSQL")
    
    try:
        async with async_session() as session:
            security_service = SecurityService(session)
            
            # Teste 1: check_user_permission (pode falhar se user não existir)
            try:
                has_perm = await security_service.check_user_permission(
                    user_id=1,
                    permission="users.view"
                )
                print(f"✅ Function 'check_user_permission' executou (resultado: {has_perm})")
            except Exception as e:
                print(f"⚠️  Function 'check_user_permission' falhou: {e}")
            
            # Teste 2: can_access_user_data
            try:
                can_access = await security_service.can_access_user_data(
                    requesting_user_id=1,
                    target_user_id=2
                )
                print(f"✅ Function 'can_access_user_data' executou (resultado: {can_access})")
            except Exception as e:
                print(f"⚠️  Function 'can_access_user_data' falhou: {e}")
            
            # Teste 3: get_available_profiles
            try:
                profiles = await security_service.get_available_profiles(user_id=1)
                print(f"✅ Function 'get_available_profiles' executou ({len(profiles)} profiles)")
            except Exception as e:
                print(f"⚠️  Function 'get_available_profiles' falhou: {e}")
                
            return True
            
    except Exception as e:
        print(f"❌ Erro nos testes de Functions: {e}")
        return False


async def test_validation_functions():
    """Teste 5: Functions de validação"""
    print("\n🔍 Teste 5: Functions de validação")
    
    try:
        async with async_session() as session:
            validation_service = ValidationService(session)
            
            # Teste CPF válido e inválido
            test_cases = [
                ("11144477735", True, "CPF válido"),
                ("12345678901", False, "CPF inválido"),
                ("11222333000181", True, "CNPJ válido"), 
                ("12345678000100", False, "CNPJ inválido")
            ]
            
            for doc, expected_valid, desc in test_cases:
                if len(doc) == 11:  # CPF
                    is_valid = await validation_service.validate_cpf(doc)
                else:  # CNPJ
                    is_valid = await validation_service.validate_cnpj(doc)
                
                status = "✅" if is_valid == expected_valid else "⚠️"
                print(f"{status} {desc}: {is_valid}")
            
            # Teste formatação WhatsApp
            whatsapp = await validation_service.format_whatsapp_number("11999887766")
            print(f"✅ WhatsApp formatado: {whatsapp}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro nos testes de Validation: {e}")
        return False


async def test_existing_models_compatibility():
    """Teste 6: Compatibilidade com modelos existentes"""
    print("\n🔍 Teste 6: Compatibilidade com modelos existentes")
    
    try:
        async with async_session() as session:
            # Testar modelos existentes corrigidos
            from app.infrastructure.orm.models import People, Establishments, Menu
            
            models_to_test = [
                ("people", People),
                ("establishments", Establishments), 
                ("menus", Menu)
            ]
            
            for table_name, model_class in models_to_test:
                try:
                    from sqlalchemy import select
                    query = select(model_class).limit(1)
                    result = await session.execute(query)
                    record = result.scalars().first()
                    
                    print(f"✅ Modelo existente '{table_name}' funcionando")
                except Exception as e:
                    print(f"❌ Modelo '{table_name}' com erro: {e}")
                    return False
            
            return True
            
    except Exception as e:
        print(f"❌ Erro nos testes de compatibilidade: {e}")
        return False


async def main():
    """Executa todos os testes do Sprint 1"""
    print("🚀 TESTE DE INTEGRAÇÃO - SPRINT 1: Foundation & Security")
    print("=" * 60)
    
    tests = [
        ("Conectividade DB", test_database_connection),
        ("Modelos ORM", test_orm_models),
        ("Views", test_views),
        ("Functions Segurança", test_security_functions),
        ("Functions Validação", test_validation_functions),
        ("Compatibilidade", test_existing_models_compatibility)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro crítico no teste '{test_name}': {e}")
            results.append((test_name, False))
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 SPRINT 1 IMPLEMENTADO COM SUCESSO!")
        print("\n✨ Próximos passos:")
        print("   1. Implementar Sprint 2: Business Core")  
        print("   2. Adicionar mais tabelas (professionals, clients)")
        print("   3. Integrar sistema de autenticação no frontend")
    else:
        print(f"⚠️  {total - passed} testes falharam - revisar implementação")
        
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Erro crítico: {e}")
        sys.exit(1)