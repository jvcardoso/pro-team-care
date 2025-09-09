# 🚀 Roadmap de Implementação - Database Integration

## 🎯 Visão Geral
Este roadmap integra os planos de **Tabelas**, **Views** e **Functions** em uma estratégia unificada para implementação completa da integração com banco PostgreSQL.

## 📊 Resumo Executivo

### **Escopo Total**
- **58 Tabelas** para mapeamento ORM
- **18 Views** para consultas otimizadas  
- **84 Functions** para lógica de negócio
- **62 Triggers** (manter funcionando)

### **Cronograma Geral**
- **Duração Total**: 8 semanas
- **Esforço Estimado**: 280 horas
- **Equipe Sugerida**: 2-3 desenvolvedores
- **Entregas**: 5 releases incrementais

## 🗓️ Cronograma Integrado

### **Sprint 1: Foundation & Security (Semana 1-2)**
**Objetivo**: Estabelecer base sólida para autenticação e autorização

#### **Semana 1: Core Authentication**
| Dia | Entregável | Tipo | Esforço |
|-----|------------|------|---------|
| 1-2 | Tabelas: `users`, `roles`, `permissions` | Tables | 16h |
| 3-4 | Views: `vw_users_complete`, `vw_role_permissions` | Views | 12h |
| 5 | Functions: `check_user_permission`, `validate_session_context` | Functions | 8h |

#### **Semana 2: Security Integration**  
| Dia | Entregável | Tipo | Esforço |
|-----|------------|------|---------|
| 1-2 | Tabelas: `user_roles`, `role_permissions` | Tables | 12h |
| 3-4 | Functions: `can_access_user_data`, `get_accessible_users_hierarchical` | Functions | 16h |
| 5 | Middleware de autorização + decorators | Integration | 8h |

**🎯 Milestone 1**: Sistema de autenticação e autorização funcionando

### **Sprint 2: Business Core (Semana 3-4)**
**Objetivo**: Implementar core business do sistema de saúde

#### **Semana 3: Business Models**
| Dia | Entregável | Tipo | Esforço |
|-----|------------|------|---------|
| 1-2 | Tabelas: `professionals`, `clients`, `user_establishments` | Tables | 16h |
| 3-4 | Views: `vw_users_hierarchical`, `vw_users_admin` | Views | 12h |
| 5 | Functions: Validação CPF/CNPJ/Phone | Functions | 8h |

#### **Semana 4: Business Integration**
| Dia | Entregável | Tipo | Esforço |
|-----|------------|------|---------|
| 1-2 | Tabelas: `sessions`, `user_sessions` | Tables | 8h |
| 3-4 | Functions: Permission management (create_role, grant_permission) | Functions | 16h |
| 5 | APIs REST para gestão de usuários e profissionais | Integration | 12h |

**🎯 Milestone 2**: Gestão completa de usuários e profissionais

### **Sprint 3: Navigation & UI (Semana 5)**
**Objetivo**: Sistema de navegação dinâmica e interface

| Dia | Entregável | Tipo | Esforço |
|-----|------------|------|---------|
| 1-2 | Views: `vw_menu_hierarchy`, `vw_menus_admin` | Views | 12h |
| 3-4 | Functions: Menu validation e hierarchy | Functions | 8h |
| 5 | APIs para sistema de menus dinâmicos | Integration | 8h |

**🎯 Milestone 3**: Navegação dinâmica funcionando

### **Sprint 4: Geolocation & Communication (Semana 6)**
**Objetivo**: Features geográficas e comunicação

| Dia | Entregável | Tipo | Esforço |
|-----|------------|------|---------|
| 1-2 | Views: `vw_addresses_with_geolocation`, `vw_whatsapp_numbers` | Views | 12h |
| 3-4 | Functions: Geolocation (radius, distance, closest) | Functions | 16h |
| 5 | APIs geográficas e WhatsApp integration | Integration | 8h |

**🎯 Milestone 4**: Sistema de geolocalização e comunicação

### **Sprint 5: Configuration & Settings (Semana 7)**
**Objetivo**: Sistema de configurações e settings

| Dia | Entregável | Tipo | Esforço |
|-----|------------|------|---------|
| 1-2 | Tabelas: `company_settings`, `establishment_settings`, `documents` | Tables | 12h |
| 3-4 | Functions: Settings management | Functions | 8h |
| 5 | Admin panel para configurações | Integration | 8h |

**🎯 Milestone 5**: Sistema de configurações completo

### **Sprint 6: LGPD & Compliance (Semana 8)**
**Objetivo**: Compliance LGPD e auditoria

| Dia | Entregável | Tipo | Esforço |
|-----|------------|------|---------|
| 1-2 | Tabelas: LGPD audit tables | Tables | 12h |
| 3-4 | Views: `vw_recent_privacy_operations` | Views | 8h |
| 3-4 | Functions: LGPD compliance functions | Functions | 12h |
| 5 | Dashboard de compliance e auditoria | Integration | 8h |

**🎯 Milestone 6**: Sistema LGPD compliant

## 🏗️ Arquitetura de Implementação

### **Estrutura de Código**
```
app/
├── infrastructure/
│   ├── orm/
│   │   ├── models/          # Tabelas SQLAlchemy
│   │   │   ├── auth/        # Sprint 1
│   │   │   ├── business/    # Sprint 2  
│   │   │   ├── config/      # Sprint 5
│   │   │   └── audit/       # Sprint 6
│   │   ├── views/           # Views read-only
│   │   │   ├── auth/
│   │   │   ├── business/
│   │   │   └── geo/
│   │   └── functions/       # Function wrappers
│   │       ├── security/
│   │       ├── validation/
│   │       └── geolocation/
│   └── services/            # Business services
│       ├── auth_service.py
│       ├── user_service.py
│       └── geo_service.py
├── presentation/
│   ├── api/v1/             # REST APIs
│   ├── middleware/         # Auth middleware
│   └── decorators/         # Permission decorators
└── domain/
    └── repositories/       # Repository pattern
```

### **Padrões de Implementação**

#### **1. Dependency Injection**
```python
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    security_service: SecurityService = Depends(get_security_service)
):
    # Verificar permissão usando function do banco
    can_access = await security_service.can_access_user_data(
        requesting_user_id=current_user.id,
        target_user_id=user_id
    )
    
    if not can_access:
        raise HTTPException(403, "Access denied")
    
    return await user_service.get_complete_user(user_id)
```

#### **2. Repository Pattern**
```python
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_complete(self, user_id: int) -> UserCompleteView:
        return await self.session.query(UserCompleteView)\
            .filter(UserCompleteView.user_id == user_id)\
            .first()
    
    async def get_hierarchical(self, company_id: int) -> List[UserHierarchicalView]:
        return await self.session.query(UserHierarchicalView)\
            .filter(UserHierarchicalView.company_id == company_id)\
            .all()
```

#### **3. Service Layer**
```python
class UserService:
    def __init__(self, 
                 user_repo: UserRepository,
                 security_service: SecurityService):
        self.user_repo = user_repo
        self.security_service = security_service
    
    async def create_user(self, user_data: UserCreateRequest) -> UserResponse:
        # Validar CPF usando function do banco
        if not await self.security_service.validate_cpf(user_data.cpf):
            raise ValueError("Invalid CPF")
        
        # Criar usuário
        user = User(**user_data.dict())
        return await self.user_repo.create(user)
```

## 📋 Critérios de Aceitação por Sprint

### **Sprint 1: Foundation & Security**
- [ ] Login/logout funcionando
- [ ] Sistema de permissões ativo
- [ ] Middleware de autorização
- [ ] Decorators `@require_permission` funcionando
- [ ] Testes de segurança passando

### **Sprint 2: Business Core**
- [ ] CRUD completo de usuários
- [ ] Gestão de profissionais
- [ ] Contexto multi-establishment
- [ ] Validações de CPF/CNPJ
- [ ] APIs REST documentadas

### **Sprint 3: Navigation & UI**
- [ ] Menus dinâmicos por perfil
- [ ] Navegação hierárquica
- [ ] Sistema de breadcrumbs
- [ ] Admin de menus funcionando

### **Sprint 4: Geolocation & Communication**  
- [ ] Busca por raio funcionando
- [ ] Cálculo de distâncias
- [ ] Integration WhatsApp
- [ ] Mapas interativos

### **Sprint 5: Configuration & Settings**
- [ ] Configurações por empresa
- [ ] Settings por estabelecimento  
- [ ] Upload de documentos
- [ ] Admin panel completo

### **Sprint 6: LGPD & Compliance**
- [ ] Logs de auditoria automáticos
- [ ] Relatórios de compliance
- [ ] Gestão de consentimentos
- [ ] Data retention policies

## 🧪 Estratégia de Testes

### **Testes por Sprint**
```python
# Sprint 1: Security Tests
async def test_user_permission_check():
    assert await security_service.check_permission(user_id=1, perm="users.view")

async def test_unauthorized_access_blocked():
    with pytest.raises(HTTPException) as exc:
        await protected_endpoint()
    assert exc.value.status_code == 403

# Sprint 2: Business Tests  
async def test_user_creation_with_cpf_validation():
    user_data = {"cpf": "11144477735"}  # CPF válido
    user = await user_service.create_user(user_data)
    assert user.id is not None

# Sprint 4: Geolocation Tests
async def test_find_addresses_within_radius():
    addresses = await geo_service.find_within_radius(
        lat=-23.550520, lng=-46.633308, radius=5.0
    )
    assert len(addresses) > 0
```

### **Coverage Goals**
- **Unit Tests**: 90% coverage
- **Integration Tests**: 80% coverage  
- **E2E Tests**: Key user journeys
- **Performance Tests**: < 200ms response time

## 📊 Monitoramento e Métricas

### **KPIs por Sprint**
| Sprint | KPI Técnico | Target | KPI Negócio | Target |
|--------|-------------|--------|-------------|--------|
| 1 | Login success rate | >99% | User satisfaction | >4.5/5 |
| 2 | API response time | <200ms | User onboarding | <5min |
| 4 | Geo query performance | <100ms | Location accuracy | >95% |
| 6 | Audit log coverage | 100% | Compliance score | 100% |

### **Dashboard de Monitoring**
```python
# Métricas Prometheus
http_requests_total = Counter('http_requests_total', ['method', 'endpoint'])
database_queries_duration = Histogram('db_queries_duration', ['table', 'operation'])
permission_checks_total = Counter('permission_checks_total', ['result'])
```

## ⚠️ Riscos e Mitigações

| Risco | Sprint | Impacto | Mitigação |
|-------|--------|---------|-----------|
| Triggers quebrados | 1-2 | Crítico | Testes em staging + rollback plan |
| Performance degradada | 2-4 | Alto | Load testing + cache strategy |
| Complexidade LGPD | 6 | Médio | Specialist review + audit |
| Dependencies conflito | 1-6 | Médio | Version lock + CI/CD |

## 🚀 Plano de Deploy

### **Estratégia Blue/Green**
1. **Blue Environment**: Produção atual
2. **Green Environment**: Nova versão com integração DB
3. **Cutover**: Switch gradual por funcionalidade

### **Rollback Plan**
- **Level 1**: Feature flags para disable rápido
- **Level 2**: Database rollback scripts  
- **Level 3**: Full environment rollback
- **SLA**: < 5 minutos para rollback crítico

## 📈 Success Criteria

### **Técnicos**
- [ ] 100% das tabelas mapeadas
- [ ] 95% das views integradas
- [ ] 80% das functions críticas expostas
- [ ] 100% dos triggers funcionando
- [ ] Performance mantida (< 200ms)

### **Negócio**
- [ ] Sistema de autenticação robusto
- [ ] Gestão completa de usuários
- [ ] Compliance LGPD automatizado
- [ ] Features geográficas ativas
- [ ] Admin panel funcional

### **Qualidade**
- [ ] Cobertura de testes > 85%
- [ ] Zero vulnerabilidades críticas
- [ ] Documentação completa
- [ ] Logs estruturados
- [ ] Monitoring ativo

---

## 📞 Pontos de Controle

### **Weekly Reviews**
- **Segunda**: Sprint planning
- **Quarta**: Mid-sprint review  
- **Sexta**: Sprint retrospective

### **Go/No-Go Decisions**
- **Sprint 1**: Foundation sólida?
- **Sprint 2**: Business core funcional?
- **Sprint 4**: Performance aceitável?
- **Sprint 6**: Compliance aprovado?

### **Stakeholder Communication**
- **Daily**: Status updates (Slack)
- **Weekly**: Progress report (Email)
- **Sprint End**: Demo + retrospective

---

**Documento criado em**: 2025-09-09  
**Última atualização**: 2025-09-09  
**Responsável**: Claude Code  
**Status**: 🚀 Roadmap Aprovado para Execução