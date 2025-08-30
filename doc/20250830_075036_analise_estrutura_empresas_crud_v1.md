# Análise da Estrutura do Banco - CRUD de Empresas

**Data/Hora**: 30/08/2024 - 07:50:36  
**Assunto**: Análise da estrutura de banco para implementação do CRUD de Empresas  
**Versão**: v1.0  
**Schema**: master  
**Database**: pro_team_care_11  

---

## 📊 **Resumo Executivo**

A tabela de empresas no sistema Pro Team Care apresenta uma **arquitetura complexa e bem estruturada** com múltiplos relacionamentos polimórficos. A estrutura segue padrões enterprise com:

- **Arquitetura polimórfica** avançada para telefones, emails e endereços
- **Sistema de auditoria LGPD** automático em todas as tabelas
- **Triggers robustos** para validação e integridade de dados
- **Geocoding automático** e análise de cobertura geográfica
- **46 funções customizadas** para business rules

**Total de registros atuais**: 13 empresas, 15 pessoas jurídicas

---

## 🏗️ **Estrutura Principal: Tabela COMPANIES**

### **Campos Core**
```sql
- id (bigint, PK, auto-increment)
- person_id (bigint, FK -> people.id) [OBRIGATÓRIO]
- settings (jsonb) - Configurações específicas da empresa
- metadata (jsonb) - Dados adicionais flexíveis  
- created_at, updated_at, deleted_at (soft delete)
- display_order (integer, default 0)
```

### **Relacionamentos**
- **1:1 com PEOPLE** (person_id) - Dados básicos da empresa
- **1:N com ESTABLISHMENTS** - Filiais/unidades da empresa
- **1:N com COMPANY_SETTINGS** - Configurações avançadas

### **Índices Estratégicos**
- `companies_person_id_unique` - Garante 1:1 com people
- `companies_metadata_fulltext` - Busca textual em JSON
- `companies_settings_fulltext` - Busca textual em configurações

---

## 👤 **Tabela PEOPLE - Entidade Central**

### **Campos Essenciais**
```sql
- id (bigint, PK)
- person_type (VARCHAR) - 'PF' ou 'PJ' [OBRIGATÓRIO]
- name (VARCHAR 200) - Razão Social [OBRIGATÓRIO]
- trade_name (VARCHAR 200) - Nome Fantasia
- tax_id (VARCHAR 14) - CNPJ (único) [OBRIGATÓRIO]
- secondary_tax_id (VARCHAR 20) - Inscrição Estadual
- incorporation_date (DATE) - Data de constituição
- tax_regime (VARCHAR 50) - Regime tributário
- legal_nature (VARCHAR 100) - Natureza jurídica
- municipal_registration (VARCHAR 20)
- website (TEXT)
- description (TEXT)
- status (ENUM) - 'active', 'inactive', 'pending', 'suspended', 'blocked'
```

### **Campos LGPD**
```sql
- lgpd_consent_version (VARCHAR 10)
- lgpd_consent_given_at (TIMESTAMP)
- lgpd_data_retention_expires_at (TIMESTAMP)
```

### **Validações**
- **Check Constraints**: person_type, status, gender, marital_status
- **Unique**: tax_id (CNPJ único no sistema)
- **Full-text search**: metadata indexado para busca

---

## 📞 **TELEFONES - Estrutura Polimórfica Avançada**

### **Arquitetura Polimórfica**
```sql
- phoneable_type (VARCHAR) - Classe do modelo ('App\Models\Company')
- phoneable_id (BIGINT) - ID da empresa
```

### **Campos WhatsApp Business**
```sql
- is_whatsapp (BOOLEAN)
- whatsapp_formatted (VARCHAR 15) - +5511999999999
- whatsapp_verified (BOOLEAN)
- whatsapp_business (BOOLEAN)
- whatsapp_name (VARCHAR 100) - Nome do perfil business
- accepts_whatsapp_marketing (BOOLEAN)
- whatsapp_preferred_time_start/end (TIME)
```

### **Gestão de Contato**
```sql
- type (ENUM) - 'landline', 'mobile', 'whatsapp', 'commercial', 'emergency', 'fax'
- carrier (VARCHAR 30) - Operadora
- line_type (ENUM) - 'prepaid', 'postpaid', 'corporate'
- contact_priority (INTEGER) - Prioridade 1-10
- last_contact_attempt/success (TIMESTAMP)
- contact_attempts_count (INTEGER)
```

### **Triggers Automáticos**
- `tr_phones_format_whatsapp` - Formata número automaticamente
- `tr_phones_single_principal` - Garante apenas 1 telefone principal

---

## 📧 **EMAILS - Sistema Polimórfico Simples**

### **Campos Core**
```sql
- emailable_type/emailable_id - Polimorfismo
- type (ENUM) - 'personal', 'work', 'billing', 'contact'
- email_address (VARCHAR 255) [OBRIGATÓRIO]
- is_principal (BOOLEAN) - Email principal
- verified_at (TIMESTAMP)
```

### **Regras de Negócio**
- **Trigger**: `tr_emails_single_principal` - 1 email principal por entidade
- **Auditoria LGPD**: Automática via trigger

---

## 🏠 **ENDEREÇOS - Geocoding Avançado**

### **Campos Básicos**
```sql
- street, number, details, neighborhood, city, state, zip_code, country
- type (ENUM) - 'residential', 'commercial', 'correspondence', 'billing', 'delivery'
```

### **Geocoding e Inteligência Geográfica**
```sql
- latitude, longitude (NUMERIC)
- google_place_id (VARCHAR)
- formatted_address (TEXT)
- ibge_city_code, ibge_state_code (INTEGER)
- region, microregion, mesoregion (VARCHAR)
```

### **Análise de Cobertura Home Care**
```sql
- within_coverage (BOOLEAN)
- distance_to_establishment (INTEGER) - metros
- estimated_travel_time (INTEGER) - minutos
- access_difficulty (ENUM) - 'easy', 'medium', 'hard', 'unknown'
- access_notes (TEXT)
```

### **Qualidade de Dados**
```sql
- quality_score (INTEGER 0-100)
- is_validated, last_validated_at
- validation_source (VARCHAR)
- api_data (JSONB) - Dados brutos APIs
```

### **Funções Geográficas Disponíveis**
- `fn_find_addresses_within_radius()` - Busca por raio
- `fn_calculate_distance_between_addresses()` - Distância entre endereços
- `fn_coverage_area_stats()` - Estatísticas de cobertura

---

## 🔧 **TRIGGERS E FUNÇÕES CRÍTICAS**

### **Triggers por Tabela**
```sql
COMPANIES:
- tr_companies_update_timestamp - Atualiza updated_at
- tr_lgpd_audit_companies - Auditoria automática

PEOPLE:
- tr_people_update_timestamp
- tr_lgpd_audit_people

PHONES:
- tr_phones_format_whatsapp - Formata WhatsApp
- tr_phones_single_principal - Unicidade principal
- tr_lgpd_audit_phones

EMAILS:
- tr_emails_single_principal
- tr_emails_update_timestamp
- tr_lgpd_audit_emails

ADDRESSES:
- tr_addresses_quality_score - Calcula qualidade
- tr_addresses_single_principal
- tr_addresses_validate_coordinates
- tr_lgpd_audit_addresses
```

### **Funções de Validação**
- `fn_check_single_principal_*()` - Garante unicidade de principal
- `fn_addresses_quality_score()` - Score 0-100 de qualidade
- `fn_validate_coordinates()` - Valida lat/lng

---

## 🛡️ **Sistema LGPD e Auditoria**

### **Auditoria Automática**
- **Trigger global**: `fn_lgpd_automatic_audit()` em todas as tabelas
- **Log de operações**: Registra INSERT/UPDATE/DELETE
- **Retenção de dados**: Sistema automático de limpeza
- **Query audit**: `fn_lgpd_query_audit()` para consultas

### **Gestão de Consentimento**
- Campos LGPD em people para controle de consentimento
- Sistema de versionamento de consentimento
- Expiração automática de dados

---

## 📈 **Dados Atuais do Sistema**

### **Estatísticas**
- **Companies**: 13 registros
- **People (PJ)**: 15 registros  
- **Total de tabelas**: 36 no schema master

### **Relacionamentos Identificados**
```
COMPANIES (13) 
    ↳ 1:1 PEOPLE (15 PJ)
        ↳ 1:N PHONES (polimórfico)
        ↳ 1:N EMAILS (polimórfico) 
        ↳ 1:N ADDRESSES (polimórfico)
    ↳ 1:N ESTABLISHMENTS (filiais)
    ↳ 1:N COMPANY_SETTINGS
```

---

## 🚀 **Recomendações para CRUD de Empresas**

### **1. Estratégia de Implementação**
- **Transações**: Usar transações para operações multi-tabela
- **Validação**: Implementar validação de CNPJ, status, etc.
- **Soft Delete**: Utilizar deleted_at (não DELETE físico)

### **2. Campos Obrigatórios Mínimos**
```sql
PEOPLE:
- person_type = 'PJ'
- name (Razão Social)
- tax_id (CNPJ válido)
- status = 'active'

COMPANIES:  
- person_id (FK válida)
```

### **3. Operações Críticas**
- **CREATE**: Validar CNPJ único, criar person + company
- **UPDATE**: Manter integridade referencial
- **DELETE**: Soft delete + auditoria LGPD
- **LIST**: Joins com people + contadores de relacionados

### **4. APIs Sugeridas**
```
GET    /api/companies                 - Listagem com filtros
GET    /api/companies/{id}            - Detalhes + relacionados
POST   /api/companies                 - Criação completa
PUT    /api/companies/{id}            - Atualização
DELETE /api/companies/{id}            - Soft delete
GET    /api/companies/{id}/contacts   - Telefones + emails
POST   /api/companies/{id}/addresses  - Adicionar endereço
```

### **5. Considerações de Performance**
- **Índices**: Utilizar índices existentes (person_id, tax_id)
- **Full-text**: Aproveitar índices GIN para busca
- **Paginação**: Implementar para listagens grandes
- **Cache**: Considerar cache para dados frequentemente acessados

---

## ⚠️ **Pontos de Atenção**

### **1. Complexidade da Arquitetura**
- Sistema polimórfico requer cuidado nas consultas
- Múltiplos triggers podem impactar performance
- Validações rigorosas de integridade

### **2. LGPD e Compliance**
- Auditoria automática em todas as operações
- Necessário respeitar políticas de retenção
- Logs detalhados de acesso aos dados

### **3. Geocoding e Endereços**
- Sistema complexo de validação geográfica
- APIs externas podem falhar (ter fallbacks)
- Score de qualidade precisa ser mantido

### **4. WhatsApp Business Integration**
- Campos específicos para integração WhatsApp
- Verificação automática de números
- Preferências de horário para contato

---

## 🎯 **Próximos Passos**

1. **Implementar modelos FastAPI** para todas as entidades
2. **Criar validadores Pydantic** com regras de negócio
3. **Desenvolver repositories** com transações seguras
4. **Implementar endpoints REST** seguindo padrões
5. **Criar testes unitários** para validações críticas
6. **Documentar APIs** com exemplos práticos

---

**📝 Conclusão**: A estrutura está **enterprise-ready** com recursos avançados. O CRUD de empresas pode ser implementado aproveitando toda a robustez existente, respeitando os padrões arquiteturais já estabelecidos.