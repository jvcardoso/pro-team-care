# GUIA DO DESENVOLVEDOR: Sistema de Permissões Simples e Seguro

## 📚 VISÃO GERAL

Este guia ensina como usar o **Sistema de Permissões Simples e Seguro** implementado no projeto Pro Team Care.

### 🎯 **Princípios Fundamentais**
1. **❌ SEM LEVELS**: Apenas permissões nomeadas
2. **🏦 DADOS DO BANCO**: Zero fallbacks ou valores padrão
3. **🔍 CONTROLE POR CONTEXT**: System/Company/Establishment
4. **👑 SYSTEM ADMIN**: Acesso irrestrito para `is_system_admin = true`
5. **🔒 ISOLAMENTO**: Filtros automáticos por empresa/estabelecimento

---

## 🛠️ COMO USAR

### **1. Decorators Simples (Recomendado)**

```python
from app.presentation.decorators.simple_permissions import (
    require_companies_view,
    require_establishments_view,
    require_users_view,
    require_professionals_view,
    require_patients_view
)

# Exemplos de uso
@router.get("/companies/")
@require_companies_view()  # System level
async def get_companies(current_user: User = Depends(get_current_user)):
    pass

@router.get("/establishments/")
@require_establishments_view()  # Company level
async def get_establishments(current_user: User = Depends(get_current_user)):
    pass

@router.get("/professionals/")
@require_professionals_view()  # Establishment level
async def get_professionals(current_user: User = Depends(get_current_user)):
    pass
```

### **2. Decorator Genérico (Para Casos Especiais)**

```python
from app.presentation.decorators.simple_permissions import require_permission

# Permissão customizada
@router.post("/custom-action/")
@require_permission("custom.action", context_type="company")
async def custom_action(current_user: User = Depends(get_current_user)):
    pass

# Com context_id específico
@router.put("/establishments/{establishment_id}")
@require_permission(
    "establishments.edit",
    context_type="establishment",
    get_context_id_from_kwargs="establishment_id"
)
async def update_establishment(
    establishment_id: int,
    current_user: User = Depends(get_current_user)
):
    pass
```

### **3. Verificação Manual de Permissões**

```python
from app.presentation.decorators.simple_permissions import check_user_permission_simple

async def some_business_logic(user: User):
    # Verificar permissão dentro da lógica
    can_create = await check_user_permission_simple(
        user_id=user.id,
        permission="companies.create",
        context_type="system"
    )

    if can_create:
        # Executar ação
        pass
    else:
        # Ação alternativa
        pass
```

---

## 🔑 PERMISSÕES DISPONÍVEIS

### **System Level (Admin Global)**
| Permissão | Descrição | Contexto |
|-----------|-----------|----------|
| `companies.view` | Ver empresas | system |
| `companies.create` | Criar empresas | system |
| `companies.edit` | Editar empresas | system |
| `companies.delete` | Excluir empresas | system |
| `system.admin` | Administração total | system |

### **Company Level (Admin Empresa)**
| Permissão | Descrição | Contexto |
|-----------|-----------|----------|
| `establishments.view` | Ver estabelecimentos | company |
| `establishments.create` | Criar estabelecimentos | company |
| `establishments.edit` | Editar estabelecimentos | company |
| `establishments.delete` | Excluir estabelecimentos | company |
| `users.view` | Ver usuários | company |
| `users.create` | Criar usuários | company |
| `users.edit` | Editar usuários | company |
| `users.delete` | Excluir usuários | company |

### **Establishment Level (Admin Local)**
| Permissão | Descrição | Contexto |
|-----------|-----------|----------|
| `professionals.view` | Ver profissionais | establishment |
| `professionals.create` | Criar profissionais | establishment |
| `professionals.edit` | Editar profissionais | establishment |
| `professionals.delete` | Excluir profissionais | establishment |
| `patients.view` | Ver pacientes | establishment |
| `patients.create` | Criar pacientes | establishment |
| `patients.edit` | Editar pacientes | establishment |
| `patients.delete` | Excluir pacientes | establishment |

---

## 🔒 FILTROS AUTOMÁTICOS

### **Como Usar Filtros em Repositories**

```python
from app.infrastructure.filters.context_filters import get_auto_filter

class MyRepository:
    async def get_filtered_data(self, user: User):
        # Construir query base
        query = select(MyModel)

        # Aplicar filtros automáticos
        auto_filter = get_auto_filter(user)

        # Para empresas
        query = await auto_filter.for_companies(query, MyModel)

        # Para estabelecimentos
        query = await auto_filter.for_establishments(query, MyModel)

        # Para usuários
        query = await auto_filter.for_users(query, MyModel)

        # Executar query filtrada
        result = await self.db.execute(query)
        return result.scalars().all()
```

### **Exemplo Prático: Repository Filtrado**

```python
from app.infrastructure.repositories.company_repository_filtered import FilteredCompanyRepository

# No endpoint
@router.get("/companies/")
@require_companies_view()
async def get_companies(
    current_user: User = Depends(get_current_user),
    repository: FilteredCompanyRepository = Depends(get_filtered_company_repo)
):
    # Filtros aplicados automaticamente baseados no usuário
    companies = await repository.get_companies_filtered(
        user=current_user,
        is_active=True,
        page=1,
        size=100
    )
    return companies
```

---

## 🧪 TESTANDO PERMISSÕES

### **Teste de Permissão Básica**

```python
import pytest
from app.presentation.decorators.simple_permissions import permission_checker

@pytest.mark.asyncio
async def test_user_has_permission():
    # Mock do banco retornando permissão encontrada
    with patch('app.infrastructure.database.async_session') as mock_session:
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db
        mock_result = AsyncMock()
        mock_result.scalar.return_value = True
        mock_db.execute.return_value = mock_result

        result = await permission_checker.check_permission(
            user_id=15,
            permission="companies.view",
            context_type="system",
            is_system_admin=False
        )

        assert result is True
```

### **Teste de Isolamento**

```python
@pytest.mark.asyncio
async def test_company_isolation():
    from app.infrastructure.filters.context_filters import ContextFilter

    user_company_1 = User(id=1, company_id=1, is_system_admin=False)
    user_company_2 = User(id=2, company_id=2, is_system_admin=False)

    query = select(Company)

    filtered_1 = await ContextFilter.apply_company_filter(query, user_company_1)
    filtered_2 = await ContextFilter.apply_company_filter(query, user_company_2)

    # Devem ter filtros diferentes
    assert str(filtered_1) != str(filtered_2)
```

---

## 🚀 MELHORES PRÁTICAS

### **✅ DO (Faça)**

1. **Use decorators específicos** quando disponíveis:
   ```python
   @require_companies_view()  # ✅ Preferível
   # ao invés de
   @require_permission("companies.view", "system")  # ❌ Funciona, mas menos claro
   ```

2. **Sempre use filtros automáticos** em repositories:
   ```python
   # ✅ Com filtros
   companies = await repository.get_companies_filtered(user=current_user)

   # ❌ Sem filtros (vazamento de dados)
   companies = await repository.get_all_companies()
   ```

3. **Verifique permissões em lógica complexa**:
   ```python
   async def complex_business_logic(user: User):
       if await check_user_permission_simple(user.id, "admin.action", "system"):
           # Ação administrativa
           pass
       else:
           # Ação padrão
           pass
   ```

### **❌ DON'T (Não Faça)**

1. **Não use hardcoded levels**:
   ```python
   # ❌ NUNCA FAÇA ISSO
   if user.level >= 80:
       # Lógica
   ```

2. **Não implemente fallbacks**:
   ```python
   # ❌ NUNCA FAÇA ISSO
   has_permission = check_permission() or user.is_admin or True
   ```

3. **Não pule filtros de segurança**:
   ```python
   # ❌ PERIGOSO
   companies = await db.execute(select(Company))  # SEM FILTROS
   ```

---

## 🔍 DEBUGGING

### **Logs de Auditoria**

O sistema gera logs estruturados para auditoria:

```
2025-09-18 07:30:00 [info] ✅ Permissão concedida via banco
  user_id=15 permission=companies.view context_type=system

2025-09-18 07:30:01 [info] 🔒 Aplicando filtro de empresa
  user_id=15 company_id=65 filter_type=company

2025-09-18 07:30:02 [info] ✅ Access granted
  user_id=15 permission=companies.view endpoint=get_companies
```

### **Como Debuggar Permissões**

```python
# 1. Verificar se usuário tem a permissão
has_permission = await check_user_permission_simple(
    user_id=user.id,
    permission="companies.view",
    context_type="system"
)
print(f"Usuário {user.id} tem permissão: {has_permission}")

# 2. Verificar filtros aplicados
from app.infrastructure.filters.context_filters import get_auto_filter
auto_filter = get_auto_filter(user)
filtered_query = await auto_filter.for_companies(query, Company)
print(f"Query filtrada: {str(filtered_query)}")
```

---

## 📋 CHECKLIST PARA NOVOS ENDPOINTS

- [ ] Decorator de permissão aplicado
- [ ] Context type correto (system/company/establishment)
- [ ] Repository com filtros automáticos (se aplicável)
- [ ] Testes de permissão criados
- [ ] Testes de isolamento criados
- [ ] Logs de auditoria verificados

### **Template para Novo Endpoint**

```python
from app.presentation.decorators.simple_permissions import require_permission

@router.get("/my-endpoint/")
@require_permission("my.permission", context_type="company")
async def my_endpoint(
    current_user: User = Depends(get_current_user),
    repository: MyFilteredRepository = Depends(get_my_filtered_repo)
):
    """
    🔒 SISTEMA DE PERMISSÕES SIMPLES E SEGURO

    - System Admin: Vê todos os dados
    - Usuário Normal: Vê apenas dados de sua empresa/estabelecimento
    - Filtros aplicados automaticamente no banco
    """

    # Lógica do endpoint com filtros automáticos
    data = await repository.get_filtered_data(user=current_user)

    # Log para auditoria
    await logger.ainfo(
        "📋 Endpoint acessado",
        user_id=current_user.id,
        endpoint="my_endpoint",
        total_returned=len(data)
    )

    return data
```

---

## 🆘 TROUBLESHOOTING

### **Problema: 403 Forbidden**
```
Causa: Usuário não tem a permissão necessária
Solução: Verificar se a permissão está atribuída ao role do usuário
```

### **Problema: Usuário vê dados de outras empresas**
```
Causa: Filtros não aplicados ou repository sem filtros
Solução: Usar FilteredRepository e aplicar auto_filter
```

### **Problema: System admin não vê todos os dados**
```
Causa: Filtros aplicados incorretamente
Solução: Verificar se is_system_admin está sendo respeitado
```

---

**Documento atualizado**: 18/09/2025
**Versão**: 1.0
**Status**: ✅ **PRONTO PARA USO**
