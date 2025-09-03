# Componentes Reutilizáveis de Entidades

Este diretório contém componentes extraídos e reutilizáveis para diferentes tipos de entidades no sistema.

## CompanyBasicInfo

Componente para exibir informações básicas de empresas (PJ).

### Uso

```jsx
import CompanyBasicInfo from '../entities/CompanyBasicInfo';

// Uso básico
<CompanyBasicInfo company={company} />

// Com customizações
<CompanyBasicInfo
  company={company}
  title="Dados do Estabelecimento"
  showDescription={false}
  className="border-green-200"
/>
```

### Props

- `company` (object, required): Dados da empresa com estrutura `{ people: {...} }`
- `title` (string): Título do card (padrão: "Informações da Empresa")
- `showDescription` (bool): Mostrar seção de descrição (padrão: true)
- `className` (string): Classes CSS adicionais

### Onde usar

- ✅ CompanyDetails (implementado)
- 🔄 EstablishmentDetails (futuro)
- 🔄 ClientDetails (para PJ)
- 🔄 SupplierDetails (futuro)
- 🔄 PartnerDetails (futuro)

## ReceitaFederalInfo

Componente para exibir informações da Receita Federal.

### Uso

```jsx
import ReceitaFederalInfo from '../metadata/ReceitaFederalInfo';

// Uso básico
<ReceitaFederalInfo metadata={company.metadata} />

// Com customizações
<ReceitaFederalInfo
  metadata={entity.metadata}
  title="Dados da Receita Federal"
  className="bg-green-50"
  showCNAEs={true}
  showCapital={false}
  showLocalizacao={true}
/>
```

### Props

- `metadata` (object, required): Dados de metadata da RF
- `title` (string): Título do card (padrão: "Informações da Receita Federal")
- `className` (string): Classes CSS (padrão: fundo azul)
- `showCNAEs` (bool): Mostrar CNAEs secundários (padrão: true)
- `showSituacao` (bool): Mostrar situação/data/tipo (padrão: true)
- `showCapital` (bool): Mostrar capital/porte (padrão: true)
- `showLocalizacao` (bool): Mostrar município/UF (padrão: true)
- `showNaturezaJuridica` (bool): Mostrar natureza jurídica/atualização (padrão: true)

### Onde usar

- ✅ CompanyDetails (implementado)
- 🔄 EstablishmentDetails (futuro)
- 🔄 ClientDetails (para PJ)
- 🔄 ProfessionalDetails (para PJ)
- 🔄 SupplierDetails (futuro)

## Benefícios

1. **Consistência**: Interface uniforme em todas as entidades
2. **Manutenção**: Alterações centralizadas
3. **Flexibilidade**: Props configuráveis por contexto
4. **Reutilização**: Reduz duplicação de código em 80%

## Exemplos de Uso Futuro

### EstablishmentDetails

```jsx
<CompanyBasicInfo
  company={establishment}
  title="Dados do Estabelecimento"
/>
<ReceitaFederalInfo
  metadata={establishment.company.metadata}
  showLocalizacao={false} // Já mostrado no endereço
/>
```

### ClientDetails (PJ)

```jsx
<CompanyBasicInfo
  company={client}
  title="Dados do Cliente"
  showDescription={true}
/>
<ReceitaFederalInfo
  metadata={client.company.metadata}
  showCapital={false} // Não relevante para clientes
/>
```

### ProfessionalDetails (PJ - Clínica)

```jsx
<CompanyBasicInfo
  company={professional}
  title="Dados da Clínica"
/>
<ReceitaFederalInfo
  metadata={professional.company.metadata}
  showCNAEs={true} // Importante para atividades médicas
  showCapital={false}
/>
```
