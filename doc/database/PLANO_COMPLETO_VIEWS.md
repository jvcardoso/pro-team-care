# 📊 Plano Completo: Mapeamento de Views

## 🎯 Objetivo
Mapear e integrar as **18 views** do banco PostgreSQL para o sistema FastAPI, aproveitando consultas otimizadas e lógica de negócio já implementada no banco.

## 📈 Status Atual
- ✅ **18 views identificadas**: Todas mapeadas e analisadas
- ❌ **0 views integradas**: Nenhuma view integrada ao sistema atual
- 🎯 **Estratégia**: Mapeamento incremental por criticidade

## 🏗️ Classificação e Priorização

### **Categoria A: Views Críticas para Sistema (ALTA)**
**Prioridade: CRÍTICA | Prazo: 2-3 dias**

| View | Funcionalidade | Uso no Sistema | Complexidade |
|------|----------------|----------------|--------------|
| `vw_users_complete` | Dados completos de usuários | Login, perfil, dashboard | Alta |
| `vw_users_hierarchical` | Hierarquia organizacional | Controle de acesso contextual | Alta |
| `vw_role_permissions` | Mapeamento permissões×roles | Autorização, controle de acesso | Média |
| `vw_active_sessions` | Sessões ativas com contexto | Monitoramento, segurança | Média |

### **Categoria B: Views de Gestão (MÉDIA)**
**Prioridade: ALTA | Prazo: 3-4 dias**

| View | Funcionalidade | Uso no Sistema | Complexidade |
|------|----------------|----------------|--------------|
| `vw_menu_hierarchy` | Estrutura hierárquica de menus | Navegação dinâmica | Alta |
| `vw_users_admin` | Painel administrativo usuários | Gestão de usuários | Média |
| `vw_roles_hierarchy` | Hierarquia de perfis | Gestão de permissões | Média |
| `vw_roles_with_context` | Perfis com contexto | Atribuição de roles | Baixa |

### **Categoria C: Views de Negócio (MÉDIA)**
**Prioridade: MÉDIA | Prazo: 2-3 dias**

| View | Funcionalidade | Uso no Sistema | Complexidade |
|------|----------------|----------------|--------------|
| `vw_addresses_with_geolocation` | Endereços com coordenadas | Mapas, geolocalização | Média |
| `vw_whatsapp_numbers` | Números WhatsApp válidos | Comunicação, marketing | Baixa |
| `vw_permissions_by_module` | Permissões agrupadas por módulo | Dashboard de permissões | Baixa |
| `vw_permissions_hierarchy` | Hierarquia de permissões | Controle granular | Média |

### **Categoria D: Views Públicas e Simplificadas (BAIXA)**
**Prioridade: BAIXA | Prazo: 1-2 dias**

| View | Funcionalidade | Uso no Sistema | Complexidade |
|------|----------------|----------------|--------------|
| `vw_users_public` | Dados públicos de usuários | APIs públicas, listagens | Baixa |
| `vw_menus_admin` | Menus para administração | Painel admin | Baixa |
| `vw_menus_public` | Menus públicos | Interface usuário | Baixa |
| `vw_menus_by_level` | Estatísticas de menu | Relatórios | Baixa |

### **Categoria E: Views de Auditoria LGPD (BAIXA)**
**Prioridade: BAIXA | Prazo: 1-2 dias**

| View | Funcionalidade | Uso no Sistema | Complexidade |
|------|----------------|----------------|--------------|
| `vw_recent_privacy_operations` | Operações de privacidade recentes | Auditoria LGPD | Baixa |
| `vw_role_permission_stats` | Estatísticas de permissões | Relatórios compliance | Baixa |

## 🔧 Estratégias de Implementação

### **1. Mapeamento Read-Only (Recomendado)**
```python
from sqlalchemy import Column, String, BigInteger, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserCompleteView(Base):
    """View somente leitura - dados completos de usuários"""
    __tablename__ = "vw_users_complete"
    __table_args__ = {"schema": "master"}
    
    # Campos principais
    user_id = Column(BigInteger, primary_key=True)
    user_email = Column(String)
    user_is_active = Column(Boolean)
    person_name = Column(String)
    # ... outros campos
    
    # Desabilitar operações de escrita
    __mapper_args__ = {
        'confirm_deleted_rows': False,
    }
```

### **2. Repository Pattern para Views**
```python
from typing import List, Optional
from sqlalchemy.orm import Session

class UserViewRepository:
    def __init__(self, session: Session):
        self.session = session
    
    async def get_complete_user(self, user_id: int) -> Optional[UserCompleteView]:
        return await self.session.query(UserCompleteView)\
            .filter(UserCompleteView.user_id == user_id)\
            .first()
    
    async def get_users_hierarchical(self, company_id: int) -> List[UserHierarchicalView]:
        return await self.session.query(UserHierarchicalView)\
            .filter(UserHierarchicalView.company_id == company_id)\
            .all()
```

### **3. Integração com Pydantic**
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCompleteResponse(BaseModel):
    user_id: int
    user_email: str
    user_is_active: bool
    person_name: str
    company_name: Optional[str]
    establishment_name: Optional[str]
    
    class Config:
        from_attributes = True
```

## 📁 Estrutura de Implementação

```
app/infrastructure/orm/views/
├── __init__.py
├── auth/                    # Categoria A
│   ├── user_complete.py
│   ├── user_hierarchical.py
│   ├── role_permissions.py
│   └── active_sessions.py
├── business/                # Categoria B
│   ├── menu_hierarchy.py
│   ├── user_admin.py
│   └── role_hierarchy.py
├── location/                # Categoria C
│   ├── addresses_geo.py
│   └── whatsapp_numbers.py
├── public/                  # Categoria D
│   ├── users_public.py
│   └── menus_public.py
└── audit/                   # Categoria E
    ├── privacy_operations.py
    └── permission_stats.py

app/domain/repositories/views/
├── __init__.py
├── user_view_repository.py
├── menu_view_repository.py
├── permission_view_repository.py
└── audit_view_repository.py

app/presentation/api/v1/views/
├── __init__.py
├── user_views.py
├── menu_views.py
└── dashboard_views.py
```

## 🎯 Implementação por Fases

### **Fase 1: Views Críticas de Autenticação**
**Duração: 2-3 dias**
- `vw_users_complete` - Dados completos para login/perfil
- `vw_users_hierarchical` - Controle de acesso hierárquico
- `vw_role_permissions` - Sistema de permissões
- `vw_active_sessions` - Monitoramento de sessões

**Endpoints a serem criados:**
```python
GET /api/v1/users/{user_id}/complete
GET /api/v1/users/hierarchical?company_id={id}
GET /api/v1/permissions/by-role/{role_id}
GET /api/v1/sessions/active
```

### **Fase 2: Views de Navegação e Gestão**
**Duração: 3-4 dias**
- `vw_menu_hierarchy` - Sistema de menus dinâmicos
- `vw_users_admin` - Painel administrativo
- `vw_roles_hierarchy` - Gestão de perfis

**Endpoints a serem criados:**
```python
GET /api/v1/menus/hierarchy
GET /api/v1/admin/users
GET /api/v1/roles/hierarchy
```

### **Fase 3: Views de Negócio**
**Duração: 2-3 dias**
- `vw_addresses_with_geolocation` - Funcionalidades geográficas
- `vw_whatsapp_numbers` - Sistema de comunicação
- `vw_permissions_by_module` - Dashboard de permissões

### **Fase 4: Views Públicas e Auditoria**
**Duração: 2-3 dias**
- Views públicas para APIs externas
- Views de auditoria LGPD
- Views de relatórios

## 🔍 Padrões de Uso

### **1. Consultas Otimizadas**
```python
# ✅ Usar views para consultas complexas
users_with_context = await user_view_repo.get_users_hierarchical(company_id=1)

# ❌ Evitar múltiplas consultas
# user = await user_repo.get(id)
# person = await person_repo.get(user.person_id)
# company = await company_repo.get_by_person(person.id)
```

### **2. Cache Strategy**
```python
from functools import lru_cache
from typing import List

@lru_cache(maxsize=128)
async def get_menu_hierarchy(user_id: int) -> List[MenuHierarchyView]:
    """Cache de 5 minutos para hierarquia de menus"""
    return await menu_view_repo.get_hierarchy_for_user(user_id)
```

### **3. Paginação de Views**
```python
async def get_users_paginated(
    page: int = 1, 
    per_page: int = 50,
    company_id: Optional[int] = None
) -> PaginatedResponse[UserCompleteResponse]:
    
    query = session.query(UserCompleteView)
    if company_id:
        query = query.filter(UserCompleteView.company_id == company_id)
    
    total = await query.count()
    items = await query.offset((page - 1) * per_page).limit(per_page).all()
    
    return PaginatedResponse(
        items=[UserCompleteResponse.from_orm(item) for item in items],
        total=total,
        page=page,
        per_page=per_page
    )
```

## ⚙️ Considerações Técnicas

### **Performance**
- Views já possuem índices otimizados no banco
- Usar cache Redis para consultas frequentes
- Implementar paginação em views com muitos registros

### **Segurança**
- Views respeitam as regras de negócio do banco
- Filtros de segurança já aplicados nas views
- Logs de acesso automáticos via triggers

### **Manutenibilidade**
- Views são mantidas pela equipe de banco de dados
- Mudanças no schema são refletidas automaticamente
- Versionamento através do banco de dados

## 🧪 Estratégia de Testes

### **Testes Unitários**
```python
async def test_user_complete_view():
    user_view = await user_view_repo.get_complete_user(user_id=1)
    assert user_view.user_email == "admin@example.com"
    assert user_view.person_name is not None
```

### **Testes de Integração**
```python
async def test_menu_hierarchy_endpoint():
    response = await client.get("/api/v1/menus/hierarchy")
    assert response.status_code == 200
    assert len(response.json()["items"]) > 0
```

### **Testes de Performance**
```python
async def test_view_performance():
    start_time = time.time()
    users = await user_view_repo.get_users_hierarchical(company_id=1)
    end_time = time.time()
    
    assert (end_time - start_time) < 0.2  # Menos de 200ms
    assert len(users) > 0
```

## 📊 Métricas e Monitoramento

### **KPIs Técnicos**
- **Tempo de resposta**: < 200ms para 95% das consultas
- **Cache hit rate**: > 80% para views frequentes
- **Cobertura de testes**: 100% dos endpoints de views
- **Disponibilidade**: 99.9%

### **KPIs de Negócio**
- **Redução de queries complexas**: -60%
- **Tempo de carregamento de dashboards**: -50%
- **Satisfação do desenvolvedor**: Melhoria na manutenibilidade

## 📅 Cronograma Detalhado

| Semana | Fase | Entregáveis | Testes |
|--------|------|-------------|--------|
| 1 | Fase 1 | Views críticas + endpoints | Testes unitários |
| 2 | Fase 2 | Views de gestão + admin | Testes integração |
| 3 | Fase 3 | Views de negócio + geo | Testes performance |
| 4 | Fase 4 | Views públicas + auditoria | Testes E2E |

## ⚠️ Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Views quebradas por mudança no schema | Alto | Baixa | Versionamento + testes contínuos |
| Performance degradada | Médio | Média | Cache + monitoramento |
| Complexidade de manutenção | Baixo | Alta | Documentação + padrões |

---

**Documento criado em**: 2025-09-09  
**Última atualização**: 2025-09-09  
**Responsável**: Claude Code  
**Status**: 📋 Planejamento Completo