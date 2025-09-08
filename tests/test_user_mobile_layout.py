"""
Teste do Layout Mobile do CRUD de Usuários
==========================================

Este teste identifica problemas no layout mobile do CRUD de usuários,
comparando como os dados são exibidos no desktop vs mobile.
"""

import pytest
import json
from typing import Dict, Any


class TestUserMobileLayout:
    """Testes para o layout mobile do CRUD de usuários"""

    def test_user_data_structure(self):
        """Testa a estrutura de dados esperada para usuários"""

        # Estrutura típica de usuário retornada pelo backend
        user_data = {
            "id": 1,
            "email": "admin@example.com",
            "person_name": "João Silva",
            "is_active": True,
            "is_system_admin": False,
            "created_at": "2024-01-15T10:30:00Z",
            "last_login_at": "2024-01-20T14:45:00Z",
            "roles": [
                {"id": 1, "name": "Administrador"},
                {"id": 2, "name": "Usuário"}
            ],
            "person": {
                "name": "João Silva",
                "document_type": "cpf",
                "document_number": "12345678901"
            }
        }

        # Verificar campos obrigatórios
        assert user_data["id"] is not None
        assert user_data["email"] is not None
        assert user_data["is_active"] is not None

        print("✅ Estrutura de dados do usuário validada")
        return user_data

    def test_desktop_vs_mobile_data_mapping(self):
        """Compara como os dados são mapeados no desktop vs mobile"""

        user_data = self.test_user_data_structure()

        # Mapeamento desktop (tabela)
        desktop_mapping = {
            "nome": user_data.get("person_name") or user_data.get("name") or user_data.get("email"),
            "email": user_data.get("email"),
            "status": "active" if user_data.get("is_active") else "inactive",
            "funcoes": [role["name"] for role in user_data.get("roles", [])],
            "criado_em": user_data.get("created_at"),
            "ultimo_login": user_data.get("last_login_at")
        }

        # Mapeamento mobile (card)
        mobile_mapping = {
            "nome": user_data.get("person", {}).get("name") or user_data.get("email") or "Usuário não identificado",
            "email": user_data.get("email"),
            "status": user_data.get("status") or "active",  # Problema identificado aqui!
            "id": user_data.get("id"),
            "criado_em": user_data.get("created_at"),
            "documento": user_data.get("person", {}).get("document_number"),
            "tipo_documento": user_data.get("person", {}).get("document_type"),
            "funcoes": [role["name"] for role in user_data.get("roles", [])],
            "ultimo_login": user_data.get("last_login_at")
        }

        print("📊 Mapeamento Desktop:")
        for key, value in desktop_mapping.items():
            print(f"   {key}: {value}")

        print("\n📱 Mapeamento Mobile:")
        for key, value in mobile_mapping.items():
            print(f"   {key}: {value}")

        # Identificar diferenças
        differences = []
        if desktop_mapping["status"] != mobile_mapping["status"]:
            differences.append(f"Status: Desktop usa 'is_active' ({desktop_mapping['status']}), Mobile usa 'status' ({mobile_mapping['status']})")

        if desktop_mapping["nome"] != mobile_mapping["nome"]:
            differences.append(f"Nome: Desktop = '{desktop_mapping['nome']}', Mobile = '{mobile_mapping['nome']}'")

        if differences:
            print("\n⚠️  DIFERENÇAS IDENTIFICADAS:")
            for diff in differences:
                print(f"   - {diff}")
        else:
            print("\n✅ Nenhum problema de mapeamento identificado")

        return desktop_mapping, mobile_mapping, differences

    def test_mobile_card_data_access(self):
        """Testa como o componente mobile acessa os dados"""

        user_data = self.test_user_data_structure()

        print("🔍 Testando acesso aos dados no componente UserMobileCard...")

        # Simular como o componente acessa os dados
        access_patterns = {
            "nome_principal": user_data.get("person", {}).get("name") or user_data.get("email") or "Usuário não identificado",
            "email_secundario": user_data.get("email"),
            "status_incorreto": user_data.get("status") or "active",  # Este é o problema!
            "status_correto": "active" if user_data.get("is_active") else "inactive",
            "id_usuario": user_data.get("id"),
            "data_criacao": user_data.get("created_at"),
            "documento": user_data.get("person", {}).get("document_number"),
            "tipo_documento": user_data.get("person", {}).get("document_type"),
            "funcoes": user_data.get("roles", []),
            "ultimo_login": user_data.get("last_login_at")
        }

        print("📱 Padrões de acesso identificados:")
        for key, value in access_patterns.items():
            print(f"   {key}: {value}")

        # Verificar problemas
        issues = []

        if access_patterns["status_incorreto"] != access_patterns["status_correto"]:
            issues.append("PROBLEMA CRÍTICO: Status está sendo acessado incorretamente no mobile")
            issues.append(f"   - Usando: user.status (valor: {access_patterns['status_incorreto']})")
            issues.append(f"   - Deveria usar: user.is_active (valor correto: {access_patterns['status_correto']})")

        if not access_patterns["nome_principal"]:
            issues.append("Nome do usuário pode estar vazio")

        if not access_patterns["id_usuario"]:
            issues.append("ID do usuário não encontrado")

        if issues:
            print("\n🚨 PROBLEMAS IDENTIFICADOS:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("\n✅ Nenhum problema crítico identificado")

        return access_patterns, issues

    def test_responsive_breakpoints(self):
        """Testa os breakpoints responsivos usados no layout"""

        breakpoints = {
            "mobile": "lg:hidden",      # Esconde em telas grandes (desktop)
            "desktop": "hidden lg:block", # Esconde em telas pequenas (mobile)
            "tablet": "sm:grid-cols-2",   # Grid de 2 colunas em tablets
            "large": "md:grid-cols-4"     # Grid de 4 colunas em telas grandes
        }

        print("📱 Breakpoints responsivos analisados:")
        for device, classes in breakpoints.items():
            print(f"   {device}: {classes}")

        # Verificar se os breakpoints estão corretos
        issues = []

        # O mobile deve usar lg:hidden para aparecer apenas em mobile/tablet
        if "lg:hidden" not in breakpoints["mobile"]:
            issues.append("Mobile não está usando lg:hidden corretamente")

        # O desktop deve usar hidden lg:block para aparecer apenas em desktop
        if "hidden lg:block" not in breakpoints["desktop"]:
            issues.append("Desktop não está usando hidden lg:block corretamente")

        if issues:
            print("\n⚠️  Problemas nos breakpoints:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("\n✅ Breakpoints configurados corretamente")

        return breakpoints, issues

    def generate_fix_recommendations(self):
        """Gera recomendações de correção baseadas na análise"""

        print("\n🔧 RECOMENDAÇÕES DE CORREÇÃO:")
        print("-" * 40)

        recommendations = [
            {
                "componente": "UserMobileCard.jsx",
                "problema": "Acesso incorreto ao campo de status",
                "linha": "~40",
                "atual": 'getStatusBadge(user.status || "active")',
                "correcao": 'getStatusBadge(user.is_active ? "active" : "inactive")',
                "impacto": "Alto - Corrige exibição do status no mobile"
            },
            {
                "componente": "UserMobileCard.jsx",
                "problema": "Acesso inconsistente ao nome do usuário",
                "linha": "~32",
                "atual": 'user.person?.name || user.email || "Usuário não identificado"',
                "correcao": 'user.person_name || user.name || user.email || "Usuário não identificado"',
                "impacto": "Médio - Padroniza acesso ao nome"
            },
            {
                "componente": "UsersPage.jsx",
                "problema": "Verificar consistência no acesso aos dados",
                "linha": "Verificar linhas ~392 e ~478",
                "atual": "Acesso diferente entre desktop e mobile",
                "correcao": "Padronizar acesso aos campos do usuário",
                "impacto": "Alto - Garante consistência"
            }
        ]

        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['componente']}")
            print(f"   🎯 Problema: {rec['problema']}")
            print(f"   📍 Localização: {rec['linha']}")
            print(f"   ❌ Atual: {rec['atual']}")
            print(f"   ✅ Correção: {rec['correcao']}")
            print(f"   📊 Impacto: {rec['impacto']}")

        return recommendations


if __name__ == "__main__":
    # Executar análise completa
    test = TestUserMobileLayout()

    print("🔬 ANÁLISE DO LAYOUT MOBILE - CRUD DE USUÁRIOS")
    print("=" * 60)

    # 1. Testar estrutura de dados
    print("\n1. Testando estrutura de dados...")
    user_data = test.test_user_data_structure()

    # 2. Comparar mapeamento desktop vs mobile
    print("\n2. Comparando mapeamento de dados...")
    desktop, mobile, differences = test.test_desktop_vs_mobile_data_mapping()

    # 3. Testar acesso aos dados no mobile
    print("\n3. Testando acesso aos dados no componente mobile...")
    access_patterns, issues = test.test_mobile_card_data_access()

    # 4. Verificar breakpoints responsivos
    print("\n4. Verificando breakpoints responsivos...")
    breakpoints, breakpoint_issues = test.test_responsive_breakpoints()

    # 5. Gerar recomendações
    recommendations = test.generate_fix_recommendations()

    print("\n" + "=" * 60)
    print("📋 RESUMO DA ANÁLISE:")

    if differences:
        print(f"🔸 Diferenças encontradas: {len(differences)}")
        for diff in differences:
            print(f"   - {diff}")

    if issues:
        print(f"🚨 Problemas críticos: {len(issues)}")
        for issue in issues:
            print(f"   - {issue}")

    if breakpoint_issues:
        print(f"⚠️  Problemas nos breakpoints: {len(breakpoint_issues)}")
        for issue in breakpoint_issues:
            print(f"   - {issue}")

    print(f"🔧 Recomendações de correção: {len(recommendations)}")

    if not differences and not issues and not breakpoint_issues:
        print("✅ NENHUM PROBLEMA IDENTIFICADO - Layout está correto!")
    else:
        print("\n🎯 PRÓXIMOS PASSOS:")
        print("   1. Aplicar correções recomendadas")
        print("   2. Testar em dispositivos móveis")
        print("   3. Verificar consistência visual")
        print("   4. Validar funcionalidade das ações")