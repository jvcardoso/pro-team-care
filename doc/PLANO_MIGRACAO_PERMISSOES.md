# Plano de Migração: Níveis → Permissões Granulares

## 🎯 Objetivo do Plano

Migrar do sistema hierárquico baseado em níveis para um sistema 100% baseado em permissões granulares, eliminando hard code e proporcionando flexibilidade total.

## 📋 Resumo Executivo

| **Aspecto** | **Detalhes** |
|-------------|--------------|
| **Duração Total** | 10-12 semanas |
| **Fases** | 3 fases incrementais |
| **Equipe** | 2-3 desenvolvedores |
| **Risco** | Médio (migração pode ser revertida) |
| **Impacto** | Alto (flexibilidade máxima) |

## 🗓️ Cronograma Detalhado

### **📌 Fase 1: Preparação e Infraestrutura (4 semanas)**

#### **Semana 1-2: Setup e Mapeamento**

**Objetivos:**
- Mapear todas as permissões necessárias
- Criar estrutura de dados para nova arquitetura
- Setup de ambiente de desenvolvimento

**Entregas:**
- [x] Mapeamento completo de permissões (ATUAL ↔ NOVA)
- [ ] Scripts de criação de permissões no banco
- [ ] Templates de perfis equivalentes
- [ ] Ambiente de desenvolvimento isolado

**Tarefas Técnicas:**
```sql
-- 1. Criar tabela de mapeamento temporária
CREATE TABLE master.level_permission_mapping (
    level_min INT,
    level_max INT,
    permission_name VARCHAR(100),
    context_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Popular mapeamento baseado na análise
INSERT INTO master.level_permission_mapping VALUES
(90, 100, 'system.admin', 'system'),
(90, 100, 'system.settings', 'system'),
(80, 100, 'companies.create', 'company'),
(80, 100, 'companies.delete', 'company'),
(80, 100, 'users.create', 'establishment'),
(80, 100, 'users.delete', 'establishment'),
(60, 100, 'establishments.edit', 'establishment'),
(60, 100, 'users.edit', 'establishment'),
(40, 100, 'users.view', 'establishment'),
(40, 100, 'establishments.view', 'establishment'),
(40, 100, 'companies.view', 'company');
```

#### **Semana 3-4: Sistema de Cache e Performance**

**Objetivos:**
- Implementar cache de permissões
- Otimizar consultas de verificação
- Criar sistema de invalidação

**Entregas:**
- [ ] Classe `PermissionCache` implementada
- [ ] Redis configurado para cache
- [ ] Benchmarks de performance
- [ ] Sistema de invalidação automática

**Tarefas Técnicas:**
```python
# Implementar sistema de cache
class PermissionCacheService:
    async def get_user_permissions(self, user_id, context_type, context_id=None):
        # Implementação com Redis

    async def has_permission(self, user_id, permission, context_type, context_id=None):
        # Verificação rápida

    async def invalidate_cache(self, user_id):
        # Limpar cache do usuário
```

### **📌 Fase 2: Implementação Gradual (5 semanas)**

#### **Semana 5-6: Novos Decorators e Middleware**

**Objetivos:**
- Criar novos decorators baseados em permissões
- Implementar middleware de verificação
- Manter compatibilidade com sistema atual

**Entregas:**
- [ ] Decorators `@require_permission()` implementados
- [ ] Middleware de cache funcionando
- [ ] Testes de compatibilidade 100%
- [ ] Documentação dos novos decorators

**Tarefas Técnicas:**
```python
# Novos decorators com fallback para níveis
@require_permission_or_level("users.create", min_level=80)
async def create_user():
    # Funciona com ambos os sistemas temporariamente
```

#### **Semana 7-8: Migração do Backend (50%)**

**Objetivos:**
- Migrar 50% dos endpoints para novo sistema
- Focar em funcionalidades menos críticas primeiro
- Testes extensivos de regressão

**Prioridade de Migração:**
1. **Módulo Users** (menos crítico)
2. **Módulo Roles** (preparação)
3. **APIs de listagem** (baixo risco)
4. **Funcionalidades de visualização** (read-only)

**Entregas:**
- [ ] 20+ endpoints migrados
- [ ] Sistema duplo funcionando
- [ ] Testes de regressão passando
- [ ] Logs detalhados de uso

#### **Semana 9: Migração do Frontend**

**Objetivos:**
- Atualizar interfaces de gestão de perfis
- Implementar seletor de permissões
- Manter backward compatibility

**Entregas:**
- [ ] Interface de gestão de permissões
- [ ] Templates de perfis funcionais
- [ ] Validação de formulários
- [ ] Migração gradual de componentes

### **📌 Fase 3: Finalização e Cleanup (3 semanas)**

#### **Semana 10-11: Migração Completa**

**Objetivos:**
- Migrar 100% dos endpoints restantes
- Migrar funcionalidades críticas (companies, establishments)
- Testes intensivos de produção

**Prioridade Final:**
1. **Módulo Companies** (crítico)
2. **Módulo Establishments** (crítico)
3. **Sistema de autenticação** (core)
4. **Funções PostgreSQL** (database)

**Entregas:**
- [ ] 100% dos endpoints migrados
- [ ] Funções PostgreSQL atualizadas
- [ ] Performance equivalente ou superior
- [ ] Todos os testes passando

#### **Semana 12: Cleanup e Documentação**

**Objetivos:**
- Remover campo `level` das tabelas
- Limpar código obsoleto
- Documentação completa
- Treinamento de usuários

**Entregas:**
- [ ] Campo `level` removido do banco
- [ ] Código legacy removido
- [ ] Documentação atualizada
- [ ] Treinamento realizado

## 🔧 Estratégia de Implementação

### **1. Migração Incremental com Convivência**

```python
# Período de transição - ambos os sistemas funcionando
class HybridPermissionChecker:
    async def check_access(self, user_id, permission=None, min_level=None, context_type="establishment"):
        # Tentar novo sistema primeiro
        if permission:
            has_permission = await PermissionCache.has_permission(user_id, permission, context_type)
            if has_permission:
                return True

        # Fallback para sistema antigo
        if min_level:
            user_level = await self.get_user_level(user_id, context_type)
            return user_level >= min_level

        return False

# Decorator híbrido
def require_permission_or_level(permission: str = None, min_level: int = None, context_type: str = "establishment"):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
            checker = HybridPermissionChecker()
            has_access = await checker.check_access(
                current_user.id, permission, min_level, context_type
            )

            if not has_access:
                raise HTTPException(status_code=403, detail="Access denied")

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

### **2. Mapeamento Automático de Níveis → Permissões**

```python
# Script de migração automática
class LevelToPermissionMigrator:
    LEVEL_MAPPINGS = {
        (90, 100): [  # Sistema
            "system.admin", "system.settings", "system.logs",
            "companies.create", "companies.delete",
            "users.create", "users.delete", "users.permissions"
        ],
        (80, 89): [   # Admin Empresa
            "companies.edit", "companies.settings",
            "establishments.create", "establishments.edit",
            "users.create", "users.edit", "users.delete"
        ],
        (60, 79): [   # Admin Estabelecimento
            "establishments.edit", "establishments.settings",
            "users.edit", "users.view", "users.list"
        ],
        (40, 59): [   # Operacional
            "users.view", "establishments.view", "companies.view"
        ]
    }

    async def migrate_user_permissions(self, user_id: int):
        """Migra permissões baseado no nível atual do usuário"""

        # Buscar nível atual
        user_roles = await db.execute("""
            SELECT r.level, ur.context_type, ur.context_id
            FROM master.user_roles ur
            JOIN master.roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id AND ur.status = 'active'
        """, {"user_id": user_id})

        for role in user_roles:
            level = role['level']
            context_type = role['context_type']
            context_id = role['context_id']

            # Encontrar permissões equivalentes
            permissions = self.get_permissions_for_level(level)

            # Criar/atribuir perfil equivalente
            role_name = f"migrated_level_{level}_{context_type}"
            new_role_id = await self.create_role_with_permissions(role_name, permissions)

            # Atribuir novo perfil ao usuário
            await self.assign_role_to_user(user_id, new_role_id, context_type, context_id)

    def get_permissions_for_level(self, level: int) -> List[str]:
        """Retorna permissões baseado no nível"""
        for (min_level, max_level), permissions in self.LEVEL_MAPPINGS.items():
            if min_level <= level <= max_level:
                return permissions
        return []
```

### **3. Sistema de Rollback**

```python
# Plano de rollback se necessário
class RollbackManager:
    async def create_rollback_point(self):
        """Criar backup antes da migração"""
        await db.execute("""
            CREATE TABLE master.roles_backup AS SELECT * FROM master.roles;
            CREATE TABLE master.user_roles_backup AS SELECT * FROM master.user_roles;
            CREATE TABLE master.role_permissions_backup AS SELECT * FROM master.role_permissions;
        """)

    async def rollback_to_levels(self):
        """Reverter para sistema de níveis se necessário"""
        # Restaurar tabelas
        await db.execute("""
            DROP TABLE master.roles;
            DROP TABLE master.user_roles;
            DROP TABLE master.role_permissions;

            ALTER TABLE master.roles_backup RENAME TO roles;
            ALTER TABLE master.user_roles_backup RENAME TO user_roles;
            ALTER TABLE master.role_permissions_backup RENAME TO role_permissions;
        """)

        # Reativar decorators antigos
        # Limpar cache Redis
        await redis.flushdb()
```

## 🧪 Estratégia de Testes

### **1. Testes de Compatibilidade**

```python
# Testes para garantir equivalência funcional
class MigrationCompatibilityTests:
    async def test_permission_equivalence(self):
        """Garantir que novo sistema dá os mesmos acessos"""

        test_cases = [
            {"user_level": 90, "expected_permissions": ["system.admin", "companies.create"]},
            {"user_level": 80, "expected_permissions": ["companies.edit", "users.create"]},
            {"user_level": 60, "expected_permissions": ["establishments.edit", "users.edit"]},
            {"user_level": 40, "expected_permissions": ["users.view", "companies.view"]},
        ]

        for case in test_cases:
            # Sistema antigo
            old_access = await check_level_access(user_id, case["user_level"])

            # Sistema novo
            permissions = case["expected_permissions"]
            new_access = all(await has_permission(user_id, perm) for perm in permissions)

            assert old_access == new_access, f"Inconsistência para nível {case['user_level']}"

    async def test_performance_regression(self):
        """Garantir que performance não degradou"""
        import time

        # Teste sistema antigo
        start = time.time()
        for _ in range(100):
            await check_level_access(user_id, 80)
        old_time = time.time() - start

        # Teste sistema novo
        start = time.time()
        for _ in range(100):
            await has_permission(user_id, "companies.create")
        new_time = time.time() - start

        # Performance deve ser equivalente (tolerância 20%)
        assert new_time <= old_time * 1.2, f"Performance degradou: {new_time:.3f}s vs {old_time:.3f}s"
```

### **2. Testes de Integração**

```python
# Testes end-to-end
class EndToEndMigrationTests:
    async def test_user_workflow(self):
        """Testar fluxo completo de usuário"""

        # Criar usuário com perfil migrado
        user = await create_test_user_with_migrated_role(level=80)

        # Testar endpoints críticos
        endpoints = [
            {"method": "POST", "url": "/api/v1/companies", "should_work": True},
            {"method": "DELETE", "url": "/api/v1/companies/1", "should_work": True},
            {"method": "POST", "url": "/api/v1/system/settings", "should_work": False},
        ]

        for endpoint in endpoints:
            response = await test_client.request(
                endpoint["method"],
                endpoint["url"],
                headers=get_auth_headers(user)
            )

            if endpoint["should_work"]:
                assert response.status_code != 403
            else:
                assert response.status_code == 403
```

## 📊 Métricas e Monitoramento

### **1. KPIs de Migração**

```python
# Dashboard de acompanhamento
MIGRATION_METRICS = {
    "endpoints_migrated": 0,        # Meta: 100
    "performance_ratio": 1.0,       # Meta: <= 1.2 (20% tolerância)
    "error_rate": 0.0,             # Meta: <= 0.1%
    "user_satisfaction": 0.0,       # Meta: >= 8.0/10
    "cache_hit_rate": 0.0,         # Meta: >= 90%
}

class MigrationDashboard:
    async def get_migration_status(self):
        return {
            "phase": await self.get_current_phase(),
            "completion_percentage": await self.calculate_completion(),
            "issues": await self.get_open_issues(),
            "performance": await self.get_performance_metrics(),
            "next_milestone": await self.get_next_milestone()
        }
```

### **2. Alertas Automáticos**

```python
# Sistema de alertas
class MigrationAlerts:
    async def check_error_rate(self):
        if await self.get_error_rate() > 0.1:
            await self.send_alert("🚨 Error rate above threshold!")

    async def check_performance(self):
        if await self.get_avg_response_time() > baseline * 1.5:
            await self.send_alert("⚠️ Performance degradation detected!")

    async def check_cache_efficiency(self):
        if await self.get_cache_hit_rate() < 0.8:
            await self.send_alert("📉 Cache hit rate below 80%!")
```

## 🎯 Critérios de Sucesso

### **✅ Obrigatórios (Go/No-Go)**
- [ ] 100% dos endpoints funcionando
- [ ] Zero degradação de funcionalidade
- [ ] Performance dentro de 20% do baseline
- [ ] Todos os testes de regressão passando
- [ ] Sistema de rollback testado e funcional

### **🎖️ Desejáveis (Melhorias)**
- [ ] Performance superior ao sistema atual
- [ ] Interface mais intuitiva
- [ ] Redução de código em 30%+
- [ ] Cache hit rate > 90%
- [ ] Satisfação do usuário > 8/10

## 🚀 Próximos Passos Imediatos

### **Esta Semana**
1. [ ] **Aprovação do plano** pelos stakeholders
2. [ ] **Setup do ambiente** de desenvolvimento
3. [ ] **Criação da branch** `feature/permission-migration`
4. [ ] **Início do mapeamento** de permissões

### **Próxima Semana**
1. [ ] **Scripts de criação** de permissões
2. [ ] **Templates de perfis** implementados
3. [ ] **Sistema de cache** básico
4. [ ] **Primeiros testes** de conceito

---

**🎯 Conclusão:** Este plano detalhado garante uma migração segura, incremental e reversível, eliminando o hard code de níveis e proporcionando flexibilidade total através de permissões granulares.
