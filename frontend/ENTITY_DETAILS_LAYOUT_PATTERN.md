# Padrão EntityDetailsLayout

## 📋 Visão Geral

O `EntityDetailsLayout` é um componente de layout reutilizável que padroniza a apresentação de páginas de detalhes no sistema. Ele elimina duplicação de código, garante consistência visual e centraliza a manutenção.

## ✅ Status da Implementação

### Páginas Refatoradas (2/4 concluídas)

| Página                       | Antes       | Depois      | Redução             | Status          |
| ---------------------------- | ----------- | ----------- | ------------------- | --------------- |
| **UserDetails.jsx**          | 448 linhas  | 370 linhas  | -78 linhas (-17%)   | ✅ **COMPLETO** |
| **CompanyDetails.jsx**       | 790 linhas  | 570 linhas  | -220 linhas (-28%)  | ✅ **COMPLETO** |
| **ClientDetails.tsx**        | 963 linhas  | ~550 linhas | ~-413 linhas (-43%) | ⏳ **PENDENTE** |
| **EstablishmentDetails.jsx** | 1004 linhas | ~600 linhas | ~-404 linhas (-40%) | ⏳ **PENDENTE** |

**Total Projetado**: 3.205 → ~2.090 linhas = **-1.115 linhas (-35%)**

## 🎯 Benefícios Alcançados

✅ Layout 100% padronizado em todas as páginas refatoradas
✅ **Botão "Voltar" duplicado eliminado** (problema original resolvido)
✅ Manutenção centralizada (1 único arquivo)
✅ Sidebar com métricas automatizado
✅ Estados de loading/error consistentes
✅ Tabs responsivos e consistentes
✅ Código mais limpo e DRY

## 📦 Interface do Componente

```typescript
interface EntityDetailsLayoutProps {
  // === HEADER ===
  title: string; // Nome da entidade (obrigatório)
  subtitle?: string; // Subtítulo opcional (ex: email, nome fantasia)
  icon?: React.ReactNode; // Ícone da entidade (ex: <Building />, <User />)
  statusBadge?: React.ReactNode; // Badge de status (ativo/inativo/etc)

  // === NAVEGAÇÃO ===
  backButton?: {
    // Botão "Voltar"
    onClick: () => void;
    label?: string; // Default: "Voltar"
  };
  actionButtons?: ActionButton[]; // Botões de ação (Editar, Excluir, etc)

  // === SIDEBAR METRICS ===
  metrics?: MetricCard[]; // Cards de métricas na sidebar

  // === TABS ===
  tabs: Tab[]; // Lista de abas (obrigatório)
  activeTab: string; // Aba ativa (obrigatório)
  onTabChange: (tab: string) => void; // Callback de mudança de aba (obrigatório)

  // === CONTEÚDO ===
  children: React.ReactNode; // Conteúdo das abas (obrigatório)

  // === ESTADOS ===
  loading?: boolean; // Estado de carregamento
  error?: string | null; // Mensagem de erro
  onRetry?: () => void; // Callback de retry em caso de erro
}
```

## 🔧 Exemplos de Uso

### 1. UserDetails (Exemplo Simples)

```jsx
import { EntityDetailsLayout } from "../views/EntityDetailsLayout";
import { User, Edit, Trash2 } from "lucide-react";

const UserDetails = ({ userId, onEdit, onBack, onDelete }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("informacoes");

  // Tabs configuration
  const tabs = [
    { key: "informacoes", label: "Informações", shortLabel: "Info" },
    { key: "roles", label: "Funções", shortLabel: "Funções" },
    { key: "historico", label: "Histórico", shortLabel: "Histórico" },
  ];

  // Action buttons
  const actionButtons = [
    {
      label: "Editar",
      onClick: () => onEdit?.(userId),
      variant: "primary",
      icon: <Edit className="h-4 w-4" />,
    },
    {
      label: "Excluir",
      onClick: handleDelete,
      variant: "danger",
      outline: true,
      icon: <Trash2 className="h-4 w-4" />,
    },
  ];

  // Status badge
  const statusBadge = user && (
    <span
      className={getStatusBadge(user.user_is_active ? "active" : "inactive")}
    >
      {getStatusLabel(user.user_is_active ? "active" : "inactive")}
    </span>
  );

  return (
    <EntityDetailsLayout
      title={user?.person_name || user?.user_email || "Carregando..."}
      subtitle={user?.person_name ? user.user_email : undefined}
      icon={<User className="h-6 w-6" />}
      statusBadge={statusBadge}
      backButton={{ onClick: onBack, label: "Voltar" }}
      actionButtons={actionButtons}
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      loading={loading}
      error={error}
      onRetry={loadUser}
    >
      {/* Tab content */}
      {activeTab === "informacoes" && <InformacoesTab user={user} />}
      {activeTab === "roles" && <RolesTab user={user} />}
      {activeTab === "historico" && <HistoricoTab user={user} />}
    </EntityDetailsLayout>
  );
};
```

### 2. CompanyDetails (Exemplo Complexo com Métricas)

```jsx
import { EntityDetailsLayout } from "../views/EntityDetailsLayout";
import {
  Building,
  Building2,
  Users,
  UserCog,
  Edit,
  Trash2,
} from "lucide-react";

const CompanyDetails = () => {
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get("tab") || "dados-gerais";

  const navigate = useNavigate();
  const { id } = useParams();

  // Tab change handler (URL params)
  const handleTabChange = (tab) => {
    setSearchParams({ tab });
  };

  // Tabs configuration
  const tabs = [
    { key: "dados-gerais", label: "Dados Gerais", shortLabel: "Dados" },
    {
      key: "estabelecimentos",
      label: "Estabelecimentos",
      shortLabel: "Estabelecimentos",
    },
    { key: "clientes", label: "Clientes", shortLabel: "Clientes" },
    {
      key: "profissionais",
      label: "Profissionais",
      shortLabel: "Profissionais",
    },
    { key: "usuarios", label: "Usuários", shortLabel: "Usuários" },
    { key: "contratos", label: "Contratos", shortLabel: "Contratos" },
    { key: "faturamento", label: "Faturamento", shortLabel: "Faturamento" },
    { key: "configuracoes", label: "Configurações", shortLabel: "Config" },
  ];

  // Action buttons
  const actionButtons = [
    {
      label: "Editar",
      onClick: () => navigate(`/admin/empresas/${id}/editar`),
      variant: "primary",
      icon: <Edit className="h-4 w-4" />,
    },
    {
      label: "Excluir",
      onClick: handleDelete,
      variant: "danger",
      outline: true,
      icon: <Trash2 className="h-4 w-4" />,
    },
  ];

  // Sidebar metrics
  const metrics = [
    {
      icon: <Building2 className="h-5 w-5 text-blue-600" />,
      label: "Estabelecimentos",
      value: company?.establishments_count || 0,
      onClick: () => handleTabChange("estabelecimentos"),
    },
    {
      icon: <Users className="h-5 w-5 text-green-600" />,
      label: "Clientes",
      value: company?.clients_count || 0,
      onClick: () => handleTabChange("clientes"),
    },
    {
      icon: <UserCog className="h-5 w-5 text-purple-600" />,
      label: "Profissionais",
      value: company?.professionals_count || 0,
      onClick: () => handleTabChange("profissionais"),
    },
  ];

  // Status badge
  const statusBadge = company && (
    <span
      className={getStatusBadge(
        company.people?.is_active ? "active" : "inactive"
      )}
    >
      {getStatusLabel(company.people?.is_active ? "active" : "inactive")}
    </span>
  );

  return (
    <EntityDetailsLayout
      title={company?.people?.name || "Carregando..."}
      subtitle={
        company?.people?.trade_name &&
        company.people.trade_name !== company.people.name
          ? company.people.trade_name
          : undefined
      }
      icon={<Building className="h-6 w-6" />}
      statusBadge={statusBadge}
      backButton={{
        onClick: () => navigate("/admin/empresas"),
        label: "Voltar",
      }}
      actionButtons={actionButtons}
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={handleTabChange}
      metrics={metrics}
      loading={loading}
      error={error}
      onRetry={loadCompany}
    >
      {/* Tab content */}
      {activeTab === "dados-gerais" && <DadosGeraisTab company={company} />}
      {activeTab === "estabelecimentos" && (
        <EstabelecimentosTab companyId={id} />
      )}
      {activeTab === "clientes" && <ClientesTab companyId={id} />}
      {/* ... outros tabs ... */}
    </EntityDetailsLayout>
  );
};
```

## 🛠️ Checklist de Refatoração

Use este checklist ao refatorar uma página de detalhes:

### Preparação

- [ ] Criar backup do arquivo original: `<NomeArquivo>.backup`
- [ ] Identificar estrutura atual: header, tabs, botões de ação, métricas

### Configuração

- [ ] Importar `EntityDetailsLayout` e ícones do lucide-react
- [ ] Configurar array `tabs` com todas as abas
- [ ] Configurar array `actionButtons` (Editar, Excluir, etc)
- [ ] Configurar array `metrics` (se aplicável - sidebar)
- [ ] Configurar `statusBadge` (se aplicável)

### Implementação

- [ ] Substituir estrutura de header customizada por `<EntityDetailsLayout>`
- [ ] Passar todas as props obrigatórias: `title`, `tabs`, `activeTab`, `onTabChange`, `children`
- [ ] Passar props opcionais conforme necessário
- [ ] Mover conteúdo das abas para dentro do children
- [ ] Preservar toda lógica existente (loading, modals, handlers)

### Validação

- [ ] Testar navegação entre abas (URL params se aplicável)
- [ ] Testar botão "Voltar"
- [ ] Testar botões de ação (Editar, Excluir)
- [ ] Testar estados de loading e error
- [ ] Testar métricas da sidebar (se aplicável)
- [ ] Verificar responsividade mobile

### Limpeza

- [ ] Remover código duplicado (header customizado antigo)
- [ ] Remover imports não utilizados
- [ ] Verificar contagem de linhas (redução esperada de 30-40%)

## 📂 Localização dos Arquivos

```
frontend/src/
├── components/
│   └── views/
│       ├── EntityDetailsLayout.tsx       # ⭐ Componente base
│       ├── UserDetails.jsx               # ✅ Refatorado
│       ├── CompanyDetails.jsx            # ✅ Refatorado
│       ├── ClientDetails.tsx             # ⏳ Pendente
│       └── EstablishmentDetails.jsx      # ⏳ Pendente
```

## 🐛 Problemas Resolvidos

### 1. Botão "Voltar" Duplicado ✅

**Problema**: CompanyDetails tinha dois botões "Voltar" - um no topo e outro abaixo
**Solução**: EntityDetailsLayout renderiza apenas UM botão "Voltar" no local correto (junto com action buttons)

### 2. Inconsistência Visual ✅

**Problema**: Cada página tinha seu próprio estilo de header, tabs, e botões
**Solução**: EntityDetailsLayout garante layout idêntico em todas as páginas

### 3. Código Duplicado ✅

**Problema**: Estrutura de header repetida em 4 arquivos (>200 linhas por arquivo)
**Solução**: Centralizado em 1 componente, redução média de 30-40% por arquivo

### 4. Manutenção Difícil ✅

**Problema**: Mudanças exigiam editar 4+ arquivos diferentes
**Solução**: Agora basta editar `EntityDetailsLayout.tsx`

## 📈 Métricas do Projeto

### Código Eliminado

- **UserDetails**: -78 linhas (-17%)
- **CompanyDetails**: -220 linhas (-28%)
- **Total atual**: -298 linhas
- **Projeção final**: -1.115 linhas (-35%)

### Tempo de Manutenção

- **Antes**: 4 arquivos para atualizar
- **Depois**: 1 arquivo centralizado
- **Redução**: 75% menos esforço

### Consistência

- **Antes**: 4 layouts diferentes
- **Depois**: 100% padronizado

## 🚀 Próximos Passos

1. **Refatorar ClientDetails.tsx** (963 → ~550 linhas)
2. **Refatorar EstablishmentDetails.jsx** (1004 → ~600 linhas)
3. **Testar integração completa**
4. **Documentar casos de edge encontrados**

## 💡 Dicas

1. **Use TypeScript quando possível**: Melhor autocomplete e type safety
2. **Preserve URLs com tabs**: Use `useSearchParams` para sincronizar tab com URL
3. **Não quebre funcionalidades**: Mantenha todos os modals, handlers e lógica existente
4. **Teste mobile**: EntityDetailsLayout é responsivo, mas teste sempre
5. **Cache entity names**: Use localStorage para breadcrumb (ver CompanyDetails como exemplo)

## 📞 Suporte

Se encontrar problemas ao usar o EntityDetailsLayout:

1. Verifique a interface TypeScript em `EntityDetailsLayout.tsx`
2. Compare com exemplos de UserDetails e CompanyDetails
3. Certifique-se de passar todas as props obrigatórias
4. Verifique console do browser para erros de props

---

**Última atualização**: 2025-10-01
**Autor**: Sistema de Refatoração Pro Team Care
**Status**: 🟡 Em Andamento (2/4 páginas concluídas)
