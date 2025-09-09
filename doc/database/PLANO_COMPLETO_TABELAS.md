# 📋 Plano Completo: Mapeamento de Tabelas

## 🎯 Objetivo
Mapear todas as **58 tabelas** do banco PostgreSQL `pro_team_care_11.master` para modelos SQLAlchemy, garantindo consistência, integridade e eliminando erros futuros de desenvolvimento.

## 📊 Status Atual
- ✅ **6 tabelas já mapeadas**: `people`, `companies`, `establishments`, `phones`, `emails`, `addresses`, `menus`
- ❌ **52 tabelas pendentes**: incluindo tabelas críticas para autenticação, autorização e gestão

## 🏗️ Estrutura de Implementação por Fases

### **Fase 1: Core Authentication & Authorization (CRÍTICO)**
**Prioridade: ALTA | Prazo: 2-3 dias**

| Tabela | Descrição | Complexidade | Relacionamentos |
|--------|-----------|--------------|----------------|
| `users` | Sistema de usuários | Média | `people`, `user_roles`, `user_sessions` |
| `roles` | Perfis de acesso | Média | `role_permissions`, `user_roles` |
| `permissions` | Permissões granulares | Baixa | `role_permissions` |
| `user_roles` | Usuário ↔ Perfil | Alta | `users`, `roles`, contexto |
| `role_permissions` | Perfil ↔ Permissão | Média | `roles`, `permissions` |

**Justificativa**: Sistema não funciona sem autenticação/autorização.

### **Fase 2: Business Core (ALTO)**
**Prioridade: ALTA | Prazo: 3-4 dias**

| Tabela | Descrição | Complexidade | Relacionamentos |
|--------|-----------|--------------|----------------|
| `professionals` | Profissionais de saúde | Média | `people` (PF/PJ), `establishments` |
| `clients` | Pacientes/clientes | Baixa | `people`, `establishments` |
| `user_establishments` | Contexto usuário-estabelecimento | Alta | `users`, `establishments` |
| `sessions` | Sessões do sistema | Baixa | - |
| `user_sessions` | Sessões por usuário | Média | `users`, `sessions` |

**Justificativa**: Core business - gestão de profissionais e clientes.

### **Fase 3: Configuration & Settings (MÉDIO)**
**Prioridade: MÉDIA | Prazo: 2-3 dias**

| Tabela | Descrição | Complexidade | Relacionamentos |
|--------|-----------|--------------|----------------|
| `company_settings` | Configurações da empresa | Baixa | `companies` |
| `establishment_settings` | Configurações por estabelecimento | Baixa | `establishments` |
| `documents` | Gestão documental | Média | Polimórfico |
| `tenant_features` | Features por tenant | Baixa | - |

### **Fase 4: Audit & Compliance LGPD (MÉDIO)**
**Prioridade: MÉDIA | Prazo: 3-4 dias**

| Tabela | Descrição | Complexidade | Relacionamentos |
|--------|-----------|--------------|----------------|
| `activity_logs` | Logs de atividade | Baixa | Particionada por mês |
| `activity_logs_2025_08` | Partição atual | Baixa | - |
| `data_privacy_logs` | Logs de privacidade LGPD | Média | `people` |
| `consent_records` | Registros de consentimento | Média | `people` |
| `lgpd_audit_config` | Configuração auditoria | Baixa | - |
| `lgpd_incidents` | Incidentes LGPD | Média | `people` |
| `user_data_access_log` | Log acesso a dados | Alta | `users` |

### **Fase 5: Cache & Jobs (BAIXO)**
**Prioridade: BAIXA | Prazo: 1-2 dias**

| Tabela | Descrição | Complexidade | Relacionamentos |
|--------|-----------|--------------|----------------|
| `cache` | Cache do sistema | Baixa | - |
| `cache_locks` | Locks de cache | Baixa | - |
| `jobs` | Filas de jobs | Baixa | - |
| `job_batches` | Batches de jobs | Baixa | `jobs` |
| `failed_jobs` | Jobs falhados | Baixa | - |

### **Fase 6: Auxiliary Tables (BAIXO)**
**Prioridade: BAIXA | Prazo: 1-2 dias**

| Tabela | Descrição | Complexidade | Relacionamentos |
|--------|-----------|--------------|----------------|
| `migrations` | Controle de migrações | Baixa | - |
| `alembic_version` | Controle Alembic | Baixa | - |
| `password_reset_tokens` | Reset de senhas | Baixa | `users` |
| `context_switches` | Mudanças de contexto | Média | `users` |
| `user_contexts` | Contextos de usuário | Média | `users` |
| `menu_access_log` | Log de acesso a menus | Baixa | `users`, `menus` |

## 🔧 Estratégia de Implementação

### **1. Geração Automática Inicial**
```bash
# Gerar modelos base automaticamente
sqlacodegen postgresql+asyncpg://user:pass@192.168.11.62:5432/pro_team_care_11 \
  --schemas master --outfile generated_models.py

# Ou usando script Python personalizado
python scripts/generate_orm_models.py
```

### **2. Refinamento Manual**
- Ajustar tipos de dados específicos
- Definir relacionamentos corretos
- Configurar índices e constraints
- Adicionar validações de negócio

### **3. Validação e Testes**
```python
# Script de validação
python scripts/validate_orm_mapping.py
pytest tests/test_orm_models.py
```

## 📁 Estrutura de Arquivos

```
app/infrastructure/orm/
├── models/
│   ├── __init__.py
│   ├── auth/           # Fase 1
│   │   ├── user.py
│   │   ├── role.py
│   │   └── permission.py
│   ├── business/       # Fase 2
│   │   ├── professional.py
│   │   ├── client.py
│   │   └── session.py
│   ├── config/         # Fase 3
│   │   ├── company_settings.py
│   │   └── establishment_settings.py
│   ├── audit/          # Fase 4
│   │   ├── activity_log.py
│   │   ├── lgpd_log.py
│   │   └── consent.py
│   └── system/         # Fases 5-6
│       ├── cache.py
│       ├── jobs.py
│       └── migrations.py
├── base.py             # Base classes
└── relationships.py    # Configuração de relacionamentos
```

## ⚙️ Padrões de Implementação

### **Naming Convention**
```python
# Tabela: user_roles -> Classe: UserRole
# Tabela: company_settings -> Classe: CompanySettings
```

### **Base Model**
```python
class BaseModel:
    id = Column(BigInteger, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
```

### **Relacionamentos**
```python
# 1:N
company = relationship("Company", back_populates="establishments")

# N:M com tabela de associação
roles = relationship("Role", secondary="user_roles", back_populates="users")

# Polimórfico
addressable = relationship("People", foreign_keys="[Address.addressable_id]")
```

## 🎯 Critérios de Sucesso

### **Técnicos**
- [ ] Todos os 58 modelos mapeados e funcionais
- [ ] Relacionamentos preservados
- [ ] Índices e constraints respeitados
- [ ] Triggers continuam funcionando
- [ ] Testes de integração passando

### **Funcionais**
- [ ] Sistema de autenticação funcionando
- [ ] Gestão de usuários operacional
- [ ] Compliance LGPD mantido
- [ ] Performance preservada
- [ ] Logs de auditoria ativos

## 📈 Cronograma Estimado

| Fase | Prazo | Esforço | Dependências |
|------|-------|---------|--------------|
| Fase 1 | 3 dias | 24h | Nenhuma |
| Fase 2 | 4 dias | 30h | Fase 1 |
| Fase 3 | 3 dias | 20h | Fase 2 |
| Fase 4 | 4 dias | 32h | Fases 1-2 |
| Fase 5 | 2 dias | 12h | Nenhuma |
| Fase 6 | 2 dias | 14h | Nenhuma |
| **Total** | **18 dias** | **132h** | - |

## ⚠️ Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Relacionamentos complexos | Alta | Alto | Implementação incremental |
| Performance degradada | Média | Médio | Testes de carga contínuos |
| Triggers quebrados | Baixa | Alto | Validação em ambiente de teste |
| Compliance LGPD afetado | Baixa | Crítico | Auditoria antes da produção |

## 🔄 Processo de Deploy

1. **Desenvolvimento Local**: Implementar e testar cada fase
2. **Ambiente de Teste**: Validar com dados reais (subset)
3. **Homologação**: Testes completos de integração
4. **Produção**: Deploy incremental com rollback preparado

## 📊 Métricas de Acompanhamento

- **Cobertura de Mapeamento**: 58/58 tabelas (100%)
- **Testes Passando**: 100% dos testes de integração
- **Performance**: Tempo de resposta < 200ms
- **Compliance**: 100% dos triggers LGPD ativos

---

**Documento criado em**: 2025-09-09  
**Última atualização**: 2025-09-09  
**Responsável**: Claude Code  
**Status**: 📋 Planejamento Completo