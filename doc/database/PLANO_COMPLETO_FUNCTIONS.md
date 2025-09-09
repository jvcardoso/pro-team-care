# 🔧 Plano Completo: Integração de Functions

## 🎯 Objetivo
Integrar as **84 functions** PostgreSQL ao sistema FastAPI, aproveitando lógica de negócio, validações e controles de segurança já implementados no banco.

## 📈 Status Atual
- ✅ **84 functions identificadas**: Todas mapeadas por categoria
- ❌ **0 functions integradas**: Nenhuma function exposta no sistema
- 🎯 **Estratégia**: Exposição seletiva via SQLAlchemy e endpoints

## 🏗️ Classificação por Categoria e Prioridade

### **Categoria A: Security & Access Control (CRÍTICA)**
**Prioridade: CRÍTICA | Prazo: 3-4 dias**

| Function | Funcionalidade | Uso Imediato | Complexidade |
|----------|----------------|--------------|--------------|
| `check_user_permission` | Verificação de permissões granular | Sistema de autorização | Alta |
| `can_access_user_data` | Controle acesso hierárquico | LGPD compliance | Alta |
| `get_user_data_secure` | Busca segura de dados de usuários | APIs protegidas | Média |
| `get_accessible_users_hierarchical` | Usuários acessíveis por hierarquia | Listagens contextuais | Alta |
| `switch_user_context` | Troca de contexto (empresa/estabelecimento) | Multi-tenancy | Média |
| `validate_session_context` | Validação de sessão e contexto | Middleware de autenticação | Média |
| `get_available_profiles` | Perfis disponíveis para usuário | Gestão de roles | Baixa |

### **Categoria B: Business Logic & Validation (ALTA)**
**Prioridade: ALTA | Prazo: 4-5 dias**

| Function | Funcionalidade | Uso Imediato | Complexidade |
|----------|----------------|--------------|--------------|
| `fn_validate_cpf` | Validação de CPF | Cadastros | Baixa |
| `fn_validate_cnpj` | Validação de CNPJ | Cadastros empresas | Baixa |
| `fn_validate_phone_format` | Validação formato telefone | Cadastro contatos | Baixa |
| `fn_validate_coordinates` | Validação coordenadas geográficas | Endereços | Baixa |
| `fn_format_whatsapp_number` | Formatação número WhatsApp | Comunicações | Baixa |
| `fn_calculate_address_quality_score` | Score qualidade endereço | Geolocalização | Média |
| `fn_can_manage_role` | Controle gestão de perfis | Admin usuários | Média |

### **Categoria C: Permission Management (ALTA)**
**Prioridade: ALTA | Prazo: 3-4 dias**

| Function | Funcionalidade | Uso Imediato | Complexidade |
|----------|----------------|--------------|--------------|
| `fn_grant_permission_to_role` | Conceder permissão a perfil | Gestão permissões | Baixa |
| `fn_revoke_permission_from_role` | Revogar permissão de perfil | Gestão permissões | Baixa |
| `fn_grant_multiple_permissions` | Conceder múltiplas permissões | Admin bulk | Média |
| `fn_create_permission` | Criar nova permissão | Sistema dinâmico | Média |
| `fn_create_role` | Criar novo perfil | Gestão roles | Média |
| `fn_setup_default_role_permissions` | Setup permissões padrão | Instalação | Baixa |
| `fn_validate_role_permissions` | Validar integridade permissões | Auditoria | Média |

### **Categoria D: Geolocation & Address (MÉDIA)**
**Prioridade: MÉDIA | Prazo: 2-3 dias**

| Function | Funcionalidade | Uso Imediato | Complexidade |
|----------|----------------|--------------|--------------|
| `fn_find_addresses_within_radius` | Buscar endereços por raio | Mapas, cobertura | Alta |
| `fn_find_closest_address` | Encontrar endereço mais próximo | Logística | Alta |
| `fn_find_nearby_addresses` | Endereços próximos | Recomendações | Alta |
| `fn_calculate_distance_between_addresses` | Distância entre endereços | Cálculos logísticos | Média |
| `fn_coverage_area_stats` | Estatísticas área cobertura | Relatórios geo | Média |

### **Categoria E: LGPD & Audit (MÉDIA)**
**Prioridade: MÉDIA | Prazo: 3-4 dias**

| Function | Funcionalidade | Uso Imediato | Complexidade |
|----------|----------------|--------------|--------------|
| `log_user_data_access` | Log acesso dados usuário | Auditoria LGPD | Baixa |
| `fn_log_data_privacy_operation` | Log operações privacidade | Compliance | Baixa |
| `fn_validate_lgpd_consent` | Validar consentimento LGPD | Proteção dados | Média |
| `fn_cleanup_expired_lgpd_data` | Limpeza dados expirados | Retention policy | Alta |

### **Categoria F: Settings & Configuration (BAIXA)**
**Prioridade: BAIXA | Prazo: 1-2 dias**

| Function | Funcionalidade | Uso Imediato | Complexidade |
|----------|----------------|--------------|--------------|
| `fn_get_establishment_setting` | Buscar configuração estabelecimento | Sistema config | Baixa |
| `fn_set_establishment_setting` | Definir configuração | Admin settings | Baixa |

### **Categoria G: System Maintenance (BAIXA)**
**Prioridade: BAIXA | Prazo: 1-2 dias**

| Function | Funcionalidade | Uso Imediato | Complexidade |
|----------|----------------|--------------|--------------|
| `fn_create_activity_log_partition` | Criar partição logs | Sistema de logs | Média |
| `fn_cleanup_old_activity_log_partitions` | Limpeza partições antigas | Manutenção | Média |

## 🔧 Estratégias de Implementação

### **1. Wrapper Functions via SQLAlchemy**
```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

class SecurityService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_user_permission(
        self, 
        user_id: int, 
        permission: str,
        context_type: str = 'establishment',
        context_id: Optional[int] = None
    ) -> bool:
        """Verifica se usuário possui permissão específica"""
        query = text("""
            SELECT master.check_user_permission(
                :user_id, :permission, :context_type, :context_id
            )
        """)
        result = await self.session.execute(query, {
            "user_id": user_id,
            "permission": permission,
            "context_type": context_type,
            "context_id": context_id
        })
        return result.scalar() or False

    async def get_accessible_users(
        self, 
        requesting_user_id: int
    ) -> List[dict]:
        """Retorna usuários acessíveis hierarquicamente"""
        query = text("""
            SELECT * FROM master.get_accessible_users_hierarchical(:user_id)
        """)
        result = await self.session.execute(query, {"user_id": requesting_user_id})
        return [dict(row) for row in result.fetchall()]
```

### **2. Dependency Injection Pattern**
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_session

async def get_security_service(
    session: AsyncSession = Depends(get_session)
) -> SecurityService:
    return SecurityService(session)

async def get_validation_service(
    session: AsyncSession = Depends(get_session)
) -> ValidationService:
    return ValidationService(session)
```

### **3. Custom Decorators para Permissões**
```python
from functools import wraps
from fastapi import HTTPException, Depends
from app.infrastructure.auth import get_current_user

def require_permission(permission: str, context_type: str = 'establishment'):
    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            current_user=Depends(get_current_user),
            security_service=Depends(get_security_service),
            **kwargs
        ):
            has_permission = await security_service.check_user_permission(
                user_id=current_user.id,
                permission=permission,
                context_type=context_type
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing permission: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Uso do decorator
@router.get("/users/{user_id}")
@require_permission("users.view", "establishment")
async def get_user(user_id: int):
    # Lógica do endpoint
    pass
```

### **4. Validation Service**
```python
class ValidationService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def validate_cpf(self, cpf: str) -> bool:
        """Valida CPF usando function do banco"""
        query = text("SELECT master.fn_validate_cpf(:cpf)")
        result = await self.session.execute(query, {"cpf": cpf})
        return result.scalar() or False
    
    async def validate_cnpj(self, cnpj: str) -> bool:
        """Valida CNPJ usando function do banco"""
        query = text("SELECT master.fn_validate_cnpj(:cnpj)")
        result = await self.session.execute(query, {"cnpj": cnpj})
        return result.scalar() or False
    
    async def format_whatsapp(self, phone: str, country_code: str = "55") -> str:
        """Formata número WhatsApp"""
        query = text("SELECT master.fn_format_whatsapp_number(:phone, :country)")
        result = await self.session.execute(query, {
            "phone": phone, 
            "country": country_code
        })
        return result.scalar() or phone
```

## 📁 Estrutura de Implementação

```
app/infrastructure/services/
├── __init__.py
├── security/               # Categoria A
│   ├── __init__.py
│   ├── permission_service.py
│   ├── access_control_service.py
│   └── session_service.py
├── validation/             # Categoria B
│   ├── __init__.py
│   ├── document_validator.py
│   ├── contact_validator.py
│   └── address_validator.py
├── permission_management/  # Categoria C
│   ├── __init__.py
│   ├── role_service.py
│   └── permission_service.py
├── geolocation/           # Categoria D
│   ├── __init__.py
│   ├── address_service.py
│   └── distance_service.py
├── audit/                 # Categoria E
│   ├── __init__.py
│   ├── lgpd_service.py
│   └── privacy_service.py
└── system/                # Categorias F-G
    ├── __init__.py
    ├── settings_service.py
    └── maintenance_service.py

app/presentation/decorators/
├── __init__.py
├── permission_required.py
├── validation_required.py
└── audit_required.py

app/presentation/middleware/
├── __init__.py
├── permission_middleware.py
└── audit_middleware.py
```

## 🎯 Implementação por Fases

### **Fase 1: Security & Access Control (Crítica)**
**Duração: 3-4 dias**

**Functions prioritárias:**
- `check_user_permission` - Base do sistema de autorização
- `can_access_user_data` - Compliance LGPD
- `validate_session_context` - Middleware de autenticação

**Entregáveis:**
```python
# Middleware de autorização funcionando
@app.middleware("http")
async def permission_middleware(request: Request, call_next):
    # Validação usando functions do banco
    pass

# Decorators de permissão
@require_permission("users.create")
async def create_user(): pass
```

### **Fase 2: Business Validation**
**Duração: 2-3 dias**

**Functions prioritárias:**
- `fn_validate_cpf` / `fn_validate_cnpj`
- `fn_validate_phone_format`
- `fn_format_whatsapp_number`

**Entregáveis:**
```python
# Validadores Pydantic integrados
class UserCreate(BaseModel):
    cpf: str
    phone: str
    
    @validator('cpf')
    def validate_cpf(cls, v):
        # Usar function do banco
        pass
```

### **Fase 3: Permission Management**
**Duração: 3-4 days**

**Functions prioritárias:**
- `fn_grant_permission_to_role`
- `fn_create_role`
- `fn_setup_default_role_permissions`

**Entregáveis:**
```python
# Admin endpoints para gestão de permissões
POST /api/v1/roles
POST /api/v1/roles/{role_id}/permissions
DELETE /api/v1/roles/{role_id}/permissions/{permission_id}
```

### **Fase 4: Geolocation Features**
**Duração: 2-3 dias**

**Functions prioritárias:**
- `fn_find_addresses_within_radius`
- `fn_calculate_distance_between_addresses`

**Entregáveis:**
```python
# Endpoints geográficos
GET /api/v1/addresses/nearby?lat={lat}&lng={lng}&radius={km}
GET /api/v1/addresses/distance?from={id1}&to={id2}
```

### **Fase 5: LGPD & Audit**
**Duração: 2-3 dias**

**Functions prioritárias:**
- `log_user_data_access`
- `fn_validate_lgpd_consent`

**Entregáveis:**
```python
# Sistema de auditoria automática
# Logs transparentes de acesso a dados
# Compliance LGPD automatizado
```

## ⚙️ Padrões de Implementação

### **1. Error Handling**
```python
from app.core.exceptions import DatabaseFunctionError

async def safe_function_call(self, func_name: str, **params):
    try:
        query = text(f"SELECT master.{func_name}({', '.join([f':{k}' for k in params.keys()])})")
        result = await self.session.execute(query, params)
        return result.scalar()
    except Exception as e:
        logger.error(f"Function {func_name} failed: {str(e)}")
        raise DatabaseFunctionError(f"Error calling {func_name}")
```

### **2. Caching Strategy**
```python
from functools import lru_cache
import redis

class CachedSecurityService(SecurityService):
    def __init__(self, session: AsyncSession, redis_client):
        super().__init__(session)
        self.redis = redis_client
    
    async def check_user_permission(self, user_id: int, permission: str) -> bool:
        cache_key = f"perm:{user_id}:{permission}"
        
        # Tentar cache primeiro
        cached = await self.redis.get(cache_key)
        if cached is not None:
            return cached == 'true'
        
        # Consultar banco
        result = await super().check_user_permission(user_id, permission)
        
        # Cache por 5 minutos
        await self.redis.setex(cache_key, 300, 'true' if result else 'false')
        
        return result
```

### **3. Logging & Monitoring**
```python
import structlog
from app.core.monitoring import track_function_call

logger = structlog.get_logger()

class AuditableSecurityService(SecurityService):
    async def check_user_permission(self, user_id: int, permission: str) -> bool:
        with track_function_call("check_user_permission"):
            result = await super().check_user_permission(user_id, permission)
            
            await logger.info(
                "permission_check",
                user_id=user_id,
                permission=permission,
                result=result
            )
            
            return result
```

## 🧪 Estratégia de Testes

### **1. Unit Tests para Services**
```python
@pytest.mark.asyncio
async def test_check_user_permission():
    service = SecurityService(mock_session)
    
    # Mock da function call
    mock_session.execute.return_value.scalar.return_value = True
    
    result = await service.check_user_permission(
        user_id=1, 
        permission="users.view"
    )
    
    assert result is True
    mock_session.execute.assert_called_once()
```

### **2. Integration Tests**
```python
@pytest.mark.asyncio
async def test_permission_decorator():
    # Teste do decorator com usuário sem permissão
    with pytest.raises(HTTPException) as exc_info:
        await protected_endpoint()
    
    assert exc_info.value.status_code == 403
```

### **3. Performance Tests**
```python
async def test_permission_check_performance():
    service = SecurityService(session)
    
    start_time = time.time()
    await service.check_user_permission(1, "users.view")
    end_time = time.time()
    
    assert (end_time - start_time) < 0.1  # Menos de 100ms
```

## 📊 Monitoramento e Métricas

### **KPIs Técnicos**
- **Tempo de resposta functions**: < 50ms (95th percentile)
- **Cache hit rate**: > 85%
- **Error rate**: < 0.1%
- **Throughput**: > 1000 calls/second

### **KPIs de Segurança**
- **Tentativas de acesso negadas**: Monitoramento contínuo
- **Logs de auditoria**: 100% das operações sensíveis
- **Compliance LGPD**: 100% das operações auditadas

### **Dashboard de Monitoring**
```python
# Métricas expostas via Prometheus
permission_checks_total = Counter('permission_checks_total', ['result'])
function_call_duration = Histogram('function_call_duration_seconds', ['function_name'])
```

## 📅 Cronograma Detalhado

| Semana | Fase | Functions | Entregáveis | Status |
|--------|------|-----------|-------------|--------|
| 1 | Fase 1 | Security (7 functions) | Middleware + decorators | 🔄 |
| 2 | Fase 2 | Validation (7 functions) | Validadores integrados | 📋 |
| 3 | Fase 3 | Permissions (8 functions) | Admin endpoints | 📋 |
| 4 | Fase 4 | Geolocation (5 functions) | APIs geográficas | 📋 |
| 5 | Fase 5 | LGPD (4 functions) | Sistema auditoria | 📋 |

**Total**: 31 functions críticas integradas em 5 semanas

## ⚠️ Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Functions quebradas | Crítico | Baixa | Testes automáticos + rollback |
| Performance degradada | Alto | Média | Cache + monitoring |
| Complexidade de debug | Médio | Alta | Logging estruturado |
| Acoplamento forte com DB | Médio | Alta | Abstração via services |

---

**Documento criado em**: 2025-09-09  
**Última atualização**: 2025-09-09  
**Responsável**: Claude Code  
**Status**: 📋 Planejamento Completo