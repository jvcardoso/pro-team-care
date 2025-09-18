# ESTRATÉGIA DE ISOLAMENTO: EMPRESA → ESTABELECIMENTO

## 🎯 ARQUITETURA RECOMENDADA: ISOLAMENTO DUPLO

**Baseado na observação correta**: O melhor é isolamento por **empresa** E **estabelecimento**

---

## 🏗️ HIERARQUIA DE ISOLAMENTO PROPOSTA

```
NÍVEL 1: EMPRESA (TENANT PRINCIPAL)
├── company_id: Isolamento primário
├── Cada empresa = tenant independente
└── Zero vazamento entre empresas

    NÍVEL 2: ESTABELECIMENTO (SUB-TENANT)
    ├── establishment_id: Isolamento secundário
    ├── Dentro da empresa, isolamento por unidade
    └── Dados compartilháveis entre estabelecimentos da mesma empresa
```

---

## 📊 ARQUITETURA DETALHADA

### ESTRATÉGIA HÍBRIDA: COMPANY-SCOPED + ESTABLISHMENT-AWARE

```sql
-- TABELA PEOPLE (CORRIGIDA)
master.people
├── id (PK)
├── company_id (FK -> companies.id) ⚡ ISOLAMENTO LEVEL 1
├── tax_id (STRING(14))
├── name, trade_name, person_type...
├── CONSTRAINT: UNIQUE(company_id, tax_id) ✅ CORRETO
└── RLS Policy: WHERE company_id = current_company_id()

-- TABELA CLIENTS (JÁ CORRETA)
master.clients
├── id (PK)
├── person_id (FK -> people.id)
├── establishment_id (FK -> establishments.id) ⚡ ISOLAMENTO LEVEL 2
├── client_code
├── CONSTRAINT: UNIQUE(establishment_id, person_id) ✅ CORRETO
└── Permite: Mesma pessoa como cliente em múltiplos estabelecimentos

-- TABELA ESTABLISHMENTS
master.establishments
├── id (PK)
├── company_id (FK -> companies.id) ⚡ LINK COMPANY-ESTABLISHMENT
├── person_id (FK -> people.id)
├── code (UNIQUE per company_id) ✅ CORRETO
└── RLS Policy: WHERE company_id = current_company_id()
```

---

## 🔐 REGRAS DE ISOLAMENTO

### NÍVEL 1: EMPRESA (TENANT ISOLATION)
```sql
-- Pessoas são únicas por EMPRESA
UNIQUE(company_id, tax_id)

-- Uma pessoa pode existir em múltiplas empresas
-- João Silva CPF 123 pode ser:
-- - Cliente da Empresa A (Hospital)
-- - Cliente da Empresa B (Clínica)
```

### NÍVEL 2: ESTABELECIMENTO (SUB-TENANT ISOLATION)
```sql
-- Cliente é único por ESTABELECIMENTO
UNIQUE(establishment_id, person_id)

-- Dentro da mesma empresa:
-- - João Silva pode ser cliente do Hospital Central (estabelecimento 1)
-- - João Silva pode ser cliente da Filial Norte (estabelecimento 2)
```

---

## 💼 CENÁRIOS DE NEGÓCIO SUPORTADOS

### ✅ CENÁRIO 1: FORNECEDOR COMUM
```
Hospital A (empresa_id=1):
├── João Silva CPF 123 (person_id=100, company_id=1)
└── Cliente no Estabelecimento Central (establishment_id=10)

Hospital B (empresa_id=2):
├── João Silva CPF 123 (person_id=200, company_id=2)
└── Cliente no Estabelecimento Principal (establishment_id=20)

Resultado: ✅ Ambos os hospitais podem cadastrar João Silva
```

### ✅ CENÁRIO 2: MULTI-ESTABELECIMENTO NA MESMA EMPRESA
```
Hospital A (empresa_id=1):
├── João Silva CPF 123 (person_id=100, company_id=1)
├── Cliente no Hospital Central (establishment_id=10)
├── Cliente na Filial Norte (establishment_id=11)
└── Cliente no Ambulatório Sul (establishment_id=12)

Resultado: ✅ Mesmo cliente pode ser atendido em múltiplas unidades
```

### ✅ CENÁRIO 3: ISOLAMENTO TOTAL ENTRE EMPRESAS
```
Consulta da Empresa A:
SELECT * FROM people WHERE company_id = 1;
-- Retorna apenas pessoas da Empresa A

Consulta da Empresa B:
SELECT * FROM people WHERE company_id = 2;
-- Retorna apenas pessoas da Empresa B

Resultado: ✅ Zero vazamento entre empresas
```

---

## 🚀 IMPLEMENTAÇÃO TÉCNICA

### MIGRAÇÃO DE TABELAS

```sql
-- 1. ADICIONAR COMPANY_ID EM PEOPLE
ALTER TABLE master.people
ADD COLUMN company_id BIGINT,
ADD CONSTRAINT fk_people_company
    FOREIGN KEY (company_id) REFERENCES master.companies(id);

-- 2. ALTERAR CONSTRAINT TAX_ID
ALTER TABLE master.people
DROP CONSTRAINT people_tax_id_unique,
ADD CONSTRAINT people_company_tax_id_unique
    UNIQUE(company_id, tax_id);

-- 3. ADICIONAR COMPANY_ID EM USERS
ALTER TABLE master.users
ADD COLUMN company_id BIGINT,
ADD CONSTRAINT fk_users_company
    FOREIGN KEY (company_id) REFERENCES master.companies(id);

-- 4. ALTERAR CONSTRAINT EMAIL
ALTER TABLE master.users
DROP CONSTRAINT users_email_unique,
ADD CONSTRAINT users_company_email_unique
    UNIQUE(company_id, email_address);
```

### ROW-LEVEL SECURITY

```sql
-- POLICY PARA PEOPLE
CREATE POLICY people_company_isolation ON master.people
    FOR ALL TO application_role
    USING (company_id = current_setting('app.current_company_id')::bigint);

-- POLICY PARA ESTABLISHMENTS
CREATE POLICY establishments_company_isolation ON master.establishments
    FOR ALL TO application_role
    USING (company_id = current_setting('app.current_company_id')::bigint);

-- POLICY PARA CLIENTS (via establishment)
CREATE POLICY clients_company_isolation ON master.clients
    FOR ALL TO application_role
    USING (establishment_id IN (
        SELECT id FROM master.establishments
        WHERE company_id = current_setting('app.current_company_id')::bigint
    ));
```

---

## 📱 IMPACTO NO CÓDIGO DA APLICAÇÃO

### MIDDLEWARE DE CONTEXTO

```python
# app/infrastructure/middleware/tenant_context.py
class TenantContextMiddleware:
    async def __call__(self, request, call_next):
        # Extrair company_id do token JWT
        company_id = extract_company_from_token(request)

        # Definir contexto global
        await set_company_context(company_id)

        response = await call_next(request)
        return response

async def set_company_context(company_id: int):
    """Define o contexto da empresa para RLS"""
    async with engine.begin() as conn:
        await conn.execute(text(f"SET app.current_company_id = {company_id}"))
```

### ATUALIZAÇÃO DOS REPOSITORIES

```python
# app/infrastructure/repositories/people_repository.py
class PeopleRepository:
    async def create(self, person_data: PersonCreate):
        # ✅ Incluir company_id automaticamente
        current_company_id = await get_current_company_id()

        person = People(
            company_id=current_company_id,  # ⚡ ISOLAMENTO AUTOMÁTICO
            tax_id=person_data.tax_id,
            name=person_data.name,
            # ... outros campos
        )

    async def find_by_tax_id(self, tax_id: str):
        # ✅ Busca apenas dentro da empresa atual
        return await self.db.execute(
            select(People).where(
                and_(
                    People.tax_id == tax_id,
                    People.company_id == await get_current_company_id()
                )
            )
        )
```

---

## 🎯 BENEFÍCIOS DA ARQUITETURA PROPOSTA

### ✅ ISOLAMENTO PERFEITO
- **Zero vazamento** entre empresas
- **Flexibilidade total** dentro da empresa
- **Compliance automático** com LGPD

### ✅ FLEXIBILIDADE DE NEGÓCIO
- Cliente único pode atender múltiplos estabelecimentos
- Fornecedor comum pode servir múltiplas empresas
- Relatórios consolidados por empresa

### ✅ PERFORMANCE OTIMIZADA
- Índices por company_id extremamente eficientes
- RLS elimina dados desnecessários automaticamente
- Queries sempre contextualizadas

### ✅ ESCALABILIDADE
- Backup/restore por empresa
- Sharding futuro por company_id
- Migração para schema-per-tenant facilitada

---

## 📈 PLANO DE MIGRAÇÃO ESPECÍFICO

### FASE 1: PREPARAÇÃO (1 semana)
- [ ] Identificar todas as empresas existentes
- [ ] Mapear dados órfãos sem company_id
- [ ] Criar scripts de migração de dados
- [ ] Definir empresa "default" para dados órfãos

### FASE 2: ESTRUTURAL (1 semana)
- [ ] Adicionar company_id em tabelas críticas
- [ ] Migrar constraints UNIQUE
- [ ] Implementar foreign keys
- [ ] Criar índices otimizados

### FASE 3: DADOS (1 semana)
- [ ] Executar migração de dados existentes
- [ ] Associar pessoas às empresas corretas
- [ ] Validar integridade referencial
- [ ] Testes de isolamento

### FASE 4: APLICAÇÃO (1 semana)
- [ ] Implementar middleware de contexto
- [ ] Atualizar todos os repositories
- [ ] Implementar RLS policies
- [ ] Testes end-to-end

---

## 🏁 RESULTADO FINAL

### ANTES (PROBLEMÁTICO)
```sql
-- Uma pessoa para todo o sistema
people: João Silva CPF 123 (ÚNICO GLOBALMENTE) ❌

-- Bloqueio entre empresas
Hospital A: ❌ "CPF já existe"
Hospital B: ✅ "João Silva cadastrado"
```

### DEPOIS (CORRETO)
```sql
-- Uma pessoa por empresa
company_1.people: João Silva CPF 123 ✅
company_2.people: João Silva CPF 123 ✅

-- Liberdade total para cada empresa
Hospital A: ✅ "João Silva cadastrado"
Hospital B: ✅ "João Silva cadastrado"
```

---

## 🎉 CONCLUSÃO

A estratégia de **isolamento por empresa E estabelecimento** resolve completamente:

1. ✅ **Problemas de Multi-Tenancy**: Isolamento perfeito entre empresas
2. ✅ **Flexibilidade de Negócio**: Cliente pode existir em múltiplos contextos
3. ✅ **Compliance**: LGPD e SOC2 automaticamente atendidos
4. ✅ **Escalabilidade**: Arquitetura preparada para crescimento
5. ✅ **Performance**: Queries sempre otimizadas por contexto

**Esta é a arquitetura correta para um SaaS Multi-Tenant do setor de saúde.**

---

**📞 Próximo Passo**: Aprovação para iniciar implementação da migração estrutural.
