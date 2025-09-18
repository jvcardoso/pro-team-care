# ESTUDO DE VIABILIDADE: Sistema de Permissões Simples e Seguro

## 📋 RESUMO EXECUTIVO

Estudo para implementar um sistema de permissões **simples, seguro e escalável** baseado em 5 princípios fundamentais:

1. **Eliminação de hardcoded levels** - Usar apenas permissões nomeadas
2. **Dados sempre do banco** - Zero fallbacks ou valores padrão
3. **Isolamento por contexto** - System/Company/Establishment
4. **System Admin irrestrito** - Acesso total para `is_system_admin = true`
5. **Isolamento de dados** - Usuários só veem dados de sua empresa/estabelecimento

---

## 🎯 OBJETIVOS

### ✅ Benefícios Esperados
- **Segurança**: Isolamento total de dados entre empresas
- **Simplicidade**: Lógica clara baseada em permissões nomeadas
- **Manutenibilidade**: Sem hardcoded values, fácil evolução
- **Performance**: Verificação eficiente com cache
- **Compliance**: Atende LGPD e SOX para multi-tenant

### ❌ Problemas Atuais
- Uso de `min_level` força hardcode no código
- Fallbacks permitem bypass de segurança
- Lógica complexa com múltiplos caminhos de validação
- Inconsistência entre contexts (system/company/establishment)

---

## 🏗️ ARQUITETURA PROPOSTA

### **Estrutura de Permissões**
```
Permission: {
  name: "companies.view",           // Identificador único
  context_level: "system",          // system | company | establishment
  module: "companies",              // Agrupamento lógico
  action: "view",                   // Ação específica
  resource: "companies"             // Recurso protegido
}
```

### **Fluxo de Verificação**
```
1. Usuario faz request → /api/v1/companies/
2. Decorator verifica: @require_permission("companies.view")
3. Sistema consulta: user_roles → role_permissions → permissions
4. Aplica filtro de contexto: system/company/establishment
5. Retorna dados filtrados OU 403 Forbidden
```

---

## 🔒 MATRIZ DE PERMISSÕES

### **System Level** (is_system_admin = true)
```sql
-- System Admin vê TODAS as empresas
SELECT * FROM companies WHERE is_active = true;
```

### **Company Level** (usuário normal)
```sql
-- Usuário vê apenas SUA empresa
SELECT * FROM companies
WHERE id = {user.company_id} AND is_active = true;
```

### **Establishment Level** (usuário normal)
```sql
-- Usuário vê apenas SEU estabelecimento
SELECT * FROM establishments
WHERE company_id = {user.company_id}
  AND id = {user.current_establishment_id};
```

---

## 🛡️ IMPLEMENTAÇÃO DE SEGURANÇA

### **1. Decorator Único e Simples**
```python
@require_permission("companies.view", context_type="system")
async def get_companies(current_user: User):
    # Sistema automaticamente aplica filtros baseado no usuário
    if current_user.is_system_admin:
        return await get_all_companies()  # SEM filtros
    else:
        return await get_user_companies(current_user.company_id)  # COM filtros
```

### **2. Verificação de Permissão**
```python
async def check_permission(user_id: int, permission: str, context_type: str) -> bool:
    query = """
    SELECT COUNT(*) > 0
    FROM user_roles ur
    JOIN role_permissions rp ON ur.role_id = rp.role_id
    JOIN permissions p ON rp.permission_id = p.id
    WHERE ur.user_id = :user_id
      AND p.name = :permission
      AND p.context_level = :context_type
      AND ur.status = 'active'
      AND p.is_active = true
    """
    # SEM FALLBACKS - Se não tem permissão, retorna False
    return await db.scalar(query, {
        "user_id": user_id,
        "permission": permission,
        "context_type": context_type
    }) or False
```

### **3. Filtros Automáticos por Contexto**
```python
class PermissionFilter:
    @staticmethod
    async def apply_company_filter(query, user: User):
        if user.is_system_admin:
            return query  # SEM filtros
        else:
            return query.where(Company.id == user.company_id)

    @staticmethod
    async def apply_establishment_filter(query, user: User):
        if user.is_system_admin:
            return query  # SEM filtros
        else:
            return query.where(
                Establishment.company_id == user.company_id,
                Establishment.id == user.current_establishment_id
            )
```

---

## 📊 MAPEAMENTO DE ENDPOINTS

### **System Level (Admin Global)**
| Endpoint | Permissão | Filtro System Admin | Filtro User Normal |
|----------|-----------|--------------------|--------------------|
| `GET /companies/` | `companies.view` | Todas empresas | Apenas sua empresa |
| `POST /companies/` | `companies.create` | Criar qualquer | ❌ Forbidden |
| `PUT /companies/{id}` | `companies.edit` | Editar qualquer | Apenas sua empresa |

### **Company Level (Admin Empresa)**
| Endpoint | Permissão | Filtro System Admin | Filtro User Normal |
|----------|-----------|--------------------|--------------------|
| `GET /establishments/` | `establishments.view` | Todos estabelecimentos | Apenas de sua empresa |
| `POST /establishments/` | `establishments.create` | Criar em qualquer empresa | Apenas em sua empresa |
| `GET /users/` | `users.view` | Todos usuários | Apenas de sua empresa |

### **Establishment Level (Admin Local)**
| Endpoint | Permissão | Filtro System Admin | Filtro User Normal |
|----------|-----------|--------------------|--------------------|
| `GET /patients/` | `patients.view` | Todos pacientes | Apenas de seu estabelecimento |
| `GET /professionals/` | `professionals.view` | Todos profissionais | Apenas de seu estabelecimento |

---

## 🚀 PLANO DE IMPLEMENTAÇÃO

### **FASE 1: Refatoração do Sistema de Permissões (2-3 dias)**
1. ✅ Criar decorator `@require_permission()` limpo
2. ✅ Remover todos os `min_level` e fallbacks
3. ✅ Implementar verificação única via banco
4. ✅ Adicionar filtros automáticos por contexto

### **FASE 2: Aplicação nos Endpoints Críticos (3-4 dias)**
1. ✅ `/companies/` - System level
2. ✅ `/establishments/` - Company level
3. ✅ `/users/` - Company level
4. ✅ `/patients/` - Establishment level
5. ✅ `/professionals/` - Establishment level

### **FASE 3: Testes e Validação (1-2 dias)**
1. ✅ Testes unitários para cada contexto
2. ✅ Testes de integração end-to-end
3. ✅ Validação de isolamento de dados
4. ✅ Performance benchmarks

### **FASE 4: Limpeza e Documentação (1 dia)**
1. ✅ Remover código legacy de levels
2. ✅ Documentar novas regras de segurança
3. ✅ Guia para desenvolvedores

---

## ⚡ BENEFÍCIOS DA IMPLEMENTAÇÃO

### **Segurança**
- ✅ **Isolamento total** entre empresas
- ✅ **Zero bypass** - sem fallbacks
- ✅ **Auditoria completa** de acessos
- ✅ **Compliance LGPD** e multi-tenant

### **Simplicidade**
- ✅ **Uma única regra** por endpoint
- ✅ **Sem hardcode** de levels
- ✅ **Lógica clara** e previsível
- ✅ **Fácil manutenção** e evolução

### **Performance**
- ✅ **Cache de permissões** eficiente
- ✅ **Queries otimizadas** com índices
- ✅ **Filtros aplicados** no banco
- ✅ **Redução de I/O** desnecessário

---

## 🧪 CASOS DE TESTE

### **Teste 1: System Admin**
```
Usuario: admin@system.com (is_system_admin = true)
Request: GET /companies/
Esperado: Lista TODAS as empresas (sem filtros)
Verificação: COUNT(*) = total de empresas ativas
```

### **Teste 2: Admin Empresa**
```
Usuario: admin@empresa1.com (company_id = 1)
Request: GET /companies/
Esperado: Lista APENAS empresa ID 1
Verificação: COUNT(*) = 1 AND company.id = 1
```

### **Teste 3: Usuário Sem Permissão**
```
Usuario: user@empresa1.com (sem permissão companies.view)
Request: GET /companies/
Esperado: 403 Forbidden
Verificação: Status = 403 AND response.detail = "permission_denied"
```

### **Teste 4: Isolamento de Dados**
```
Usuario: admin@empresa1.com
Request: GET /companies/2  (tentar acessar empresa 2)
Esperado: 404 Not Found (dado filtrado)
Verificação: Empresa 2 existe mas não é retornada
```

---

## ⚠️ RISCOS E MITIGAÇÕES

### **Risco 1: Quebra de Funcionalidades Existentes**
- **Mitigação**: Testes abrangentes antes do deploy
- **Plano B**: Feature flag para rollback rápido

### **Risco 2: Performance de Queries Complexas**
- **Mitigação**: Índices otimizados + cache Redis
- **Monitoramento**: APM para detectar gargalos

### **Risco 3: Complexity Creep (Retorno à Complexidade)**
- **Mitigação**: Code review rigoroso + documentação clara
- **Regra**: Qualquer exceção deve ser documentada e aprovada

---

## 📈 MÉTRICAS DE SUCESSO

### **Segurança**
- ✅ **Zero vazamentos** de dados entre empresas
- ✅ **100% dos endpoints** protegidos
- ✅ **Auditoria completa** implementada

### **Performance**
- ✅ **<100ms** tempo resposta API
- ✅ **>95%** cache hit rate permissões
- ✅ **<50** queries por request

### **Manutenibilidade**
- ✅ **Zero hardcoded** levels no código
- ✅ **100% cobertura** de testes
- ✅ **Documentação atualizada**

---

## 🎯 CONCLUSÃO

Este sistema de permissões oferece:

1. **SEGURANÇA MÁXIMA**: Isolamento absoluto de dados
2. **SIMPLICIDADE EXTREMA**: Uma regra por endpoint
3. **ZERO MANUTENÇÃO**: Sem hardcode ou fallbacks
4. **PERFORMANCE**: Cache eficiente e queries otimizadas
5. **COMPLIANCE**: Atende padrões enterprise

**Recomendação**: ✅ **IMPLEMENTAR IMEDIATAMENTE**

O sistema atual tem falhas de segurança críticas. Esta solução resolve todos os problemas mantendo simplicidade e performance.

---

**Documento gerado em**: 18/09/2025
**Autor**: Sistema de Análise de Arquitetura
**Status**: APROVADO PARA IMPLEMENTAÇÃO
