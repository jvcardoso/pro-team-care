# Estudo de Viabilidade: Remoção do Sistema de Níveis

## Resumo Executivo

Este documento analisa a viabilidade de remover o sistema hierárquico baseado em níveis numéricos e migrar para um sistema 100% baseado em permissões granulares, visando eliminar hard code e aumentar a flexibilidade do sistema.

## 🎯 Objetivo

**Eliminar o campo `level` dos perfis (roles)** e substituir toda lógica hierárquica por **permissões granulares**, proporcionando:
- Controle mais preciso de acesso
- Eliminação de hard code
- Maior flexibilidade na gestão de perfis
- Facilidade de manutenção

## 📊 Análise do Sistema Atual

### Estrutura Hierárquica Identificada

```
📊 Níveis Atuais:
├── 10-39: Básico
├── 40-69: Intermediário
├── 60-79: Admin Estabelecimento
├── 70-89: Admin Geral
├── 80-89: Admin Empresa
└── 90-100: Sistema
```

### Locais com Hard Code Identificados

#### 🎨 **Frontend (6 arquivos)**
- **RolesPage.jsx**: Categorização visual (90/70/40)
- **RoleMobileCard.jsx**: Labels e cores por nível
- **RoleForm.jsx**: Validação de range e valores padrão

#### 🏗️ **Backend (4 arquivos)**
- **companies.py**: `@require_role_level(80)`
- **permission_required.py**: Documentação com exemplos
- **hierarchical_user_repository.py**: Queries com level >= 80/60
- **role.py**: Validação de range (10-100)

#### 🗃️ **Database (2 arquivos)**
- **migrations/001_create_hierarchical_functions.sql**: 14 permissões hardcoded
- **models.py**: Constraints de validação

## 🚨 Impactos da Remoção dos Níveis

### ✅ **Impactos POSITIVOS**

1. **Eliminação de Hard Code**
   - Fim das comparações `level >= 80`, `level >= 60`
   - Remoção de constantes mágicas
   - Código mais limpo e manutenível

2. **Flexibilidade Total**
   - Perfis customizáveis sem limitações hierárquicas
   - Combinações livres de permissões
   - Adequação a necessidades específicas

3. **Granularidade Máxima**
   - Controle preciso por funcionalidade
   - Permissões específicas por contexto
   - Auditoria detalhada de acessos

4. **Escalabilidade**
   - Fácil adição de novas permissões
   - Perfis específicos por cliente/empresa
   - Adaptação a diferentes modelos de negócio

### ⚠️ **Impactos NEGATIVOS**

1. **Migração Complexa**
   - Conversão de 14 funções PostgreSQL
   - Atualização de decorators em 20+ endpoints
   - Refatoração de componentes frontend

2. **Possível Degradação de Performance**
   - Consultas mais complexas (JOINs adicionais)
   - Verificação de múltiplas permissões
   - Cache mais sofisticado necessário

3. **Curva de Aprendizado**
   - Administradores precisam entender permissões
   - Interface mais complexa
   - Documentação extensiva necessária

4. **Gestão Mais Complexa**
   - Criação manual de combinações de permissões
   - Risco de configurações inconsistentes
   - Necessidade de templates/presets

## 📋 Análise de Viabilidade

### 🟢 **ALTA VIABILIDADE**

**Justificativas:**

1. **Sistema já possui infraestrutura de permissões**
   - Tabelas `permissions`, `role_permissions` existentes
   - Decorators `@require_role_permission` implementados
   - Interfaces de gestão já funcionais

2. **Benefícios superam custos**
   - Flexibilidade vale o esforço de migração
   - Eliminação definitiva de hard code
   - Futuro mais sustentável

3. **Migração incremental possível**
   - Pode ser feita gradualmente
   - Convivência temporária dos dois sistemas
   - Rollback possível se necessário

### 🔧 **Estratégias de Mitigação**

#### **Performance**
- Implementar cache de permissões por usuário
- Otimizar queries com índices específicos
- View materializada para permissões frequentes

#### **Complexidade**
- Templates de perfis pré-configurados
- Interface wizard para criação de perfis
- Validação automática de combinações

#### **Migração**
- Mapping automático níveis → permissões
- Período de convivência (3-6 meses)
- Testes extensivos em ambiente staging

## 🎯 Proposta de Nova Arquitetura

### **Substituição Direta por Permissões**

```python
# ANTES (Hard Code)
@require_role_level(80, "company")
def create_company(): pass

# DEPOIS (Granular)
@require_role_permission("companies.create", "company")
def create_company(): pass
```

### **Mapeamento Níveis → Permissões**

```yaml
# Equivalências propostas
Nível 80-100 (Admin Empresa):
  - companies.create
  - companies.edit
  - companies.delete
  - users.create
  - users.delete

Nível 60-79 (Admin Estabelecimento):
  - establishments.edit
  - users.list
  - users.edit
  - users.view

Nível 40-59 (Operacional):
  - users.view
  - establishments.view
  - companies.view
```

### **Templates de Perfis**

```python
ROLE_TEMPLATES = {
    "admin_empresa": [
        "companies.create", "companies.edit", "companies.delete",
        "users.create", "users.edit", "users.delete",
        "establishments.create", "establishments.edit"
    ],
    "admin_estabelecimento": [
        "establishments.edit", "users.edit", "users.view",
        "companies.view"
    ],
    "operacional": [
        "users.view", "establishments.view", "companies.view"
    ]
}
```

## 📅 Plano de Implementação

### **Fase 1: Preparação (2-3 semanas)**
1. Mapear todas as permissões necessárias
2. Criar templates de perfis equivalentes
3. Implementar sistema de cache de permissões
4. Desenvolver interface de gestão aprimorada

### **Fase 2: Migração Gradual (4-6 semanas)**
1. Substituir decorators um por vez
2. Migrar funções PostgreSQL
3. Atualizar frontend gradualmente
4. Testes intensivos

### **Fase 3: Finalização (2-3 semanas)**
1. Remover campo `level` das tabelas
2. Limpar código obsoleto
3. Documentação completa
4. Treinamento de usuários

## 🎯 Recomendação Final

### 🟢 **RECOMENDAÇÃO: PROCEDER COM A MIGRAÇÃO**

**Justificativa:**
1. **Benefícios estratégicos** superam custos temporários
2. **Infraestrutura já existe** para suportar a mudança
3. **Flexibilidade futura** justifica o investimento
4. **Eliminação de debt técnico** importante

### 🚦 **Condições para Sucesso**

1. **Commitment da equipe** para 2-3 meses de trabalho
2. **Ambiente de testes robusto** para validação
3. **Plano de rollback** bem definido
4. **Comunicação clara** com usuários finais

### 📊 **Métricas de Sucesso**

- ✅ Zero linhas de código com comparações de nível
- ✅ 100% das funcionalidades mantidas
- ✅ Performance igual ou superior
- ✅ Interface mais intuitiva
- ✅ Documentação completa

## 💡 Próximos Passos

1. **Aprovação stakeholders** para iniciar migração
2. **Detalhamento técnico** do plano de implementação
3. **Setup ambiente** de desenvolvimento dedicado
4. **Início da Fase 1** com mapeamento de permissões

---

**📝 Conclusão:** A remoção do sistema de níveis é **viável e recomendada**, proporcionando maior flexibilidade e eliminando hard code. O investimento inicial será compensado pela facilidade de manutenção e adaptabilidade futura.
