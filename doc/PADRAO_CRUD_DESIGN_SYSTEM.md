# Padrão CRUD - Design System & Arquitetura Full Stack

Este documento estabelece os padrões visuais e arquiteturais para implementação de CRUDs no sistema Pro Team Care. Todos os novos CRUDs devem seguir essa estrutura para manter consistência e qualidade tanto no Frontend quanto no Backend.

## 📋 Índice

### Frontend
1. [Estrutura Arquitetural Frontend](#estrutura-arquitetural-frontend)
2. [Padrões Visuais](#padrões-visuais)
3. [Responsividade](#responsividade)
4. [Estados e Navegação](#estados-e-navegação)
5. [Componentes Reutilizáveis](#componentes-reutilizáveis)
6. [Hooks Customizados](#hooks-customizados)

### Backend
7. [Arquitetura Backend](#arquitetura-backend)
8. [Estrutura de APIs](#estrutura-de-apis)
9. [Schemas e Validações](#schemas-e-validações)
10. [Repositories e Use Cases](#repositories-e-use-cases)
11. [Padrões de Response](#padrões-de-response)

### Integração
12. [Checklist de Implementação](#checklist-de-implementação)
13. [Exemplos Completos](#exemplos-completos)

---

## 🏗️ Estrutura Arquitetural Frontend

### Organização de Arquivos

```
frontend/src/
├── pages/
│   └── [Entity]Page.jsx           # Página principal do CRUD
├── components/
│   ├── forms/
│   │   ├── [Entity]Form.tsx       # Formulário principal
│   │   └── [Entity]FormSections.tsx # Seções do formulário
│   ├── views/
│   │   └── [Entity]Details.jsx    # Visualização de detalhes
│   └── mobile/
│       └── [Entity]MobileCard.jsx # Card responsivo mobile
├── hooks/
│   └── use[Entity]Form.ts         # Hook customizado para o formulário
├── services/
│   └── [entity]Service.ts         # Serviços de API
└── types/
    └── index.ts                   # Definições de tipos
```

### Padrão de Nomenclatura

- **Páginas**: `[Entity]Page.jsx` (ex: `EmpresasPage.jsx`)
- **Formulários**: `[Entity]Form.tsx` (ex: `CompanyForm.tsx`)
- **Detalhes**: `[Entity]Details.jsx` (ex: `CompanyDetails.jsx`)
- **Hooks**: `use[Entity]Form.ts` (ex: `useCompanyForm.ts`)
- **Services**: `[entity]Service.ts` (ex: `companiesService.ts`)

---

## 🎨 Padrões Visuais

### Layout Base da Página

```jsx
const [Entity]Page = () => {
  return (
    <PageErrorBoundary pageName="[Entity]">
      <[Entity]PageContent />
    </PageErrorBoundary>
  );
};

const [Entity]PageContent = () => {
  // Estados do CRUD
  const [currentView, setCurrentView] = useState("list"); // 'list', 'create', 'edit', 'details'

  // Renderização condicional baseada no estado
  switch (currentView) {
    case "create":
    case "edit":
      return <[Entity]Form />;
    case "details":
      return <[Entity]Details />;
    default:
      return <[Entity]List />;
  }
};
```

### Design System - Três Camadas Responsivas

#### 1. **Desktop Layout** (lg+ ≥ 1024px)
```jsx
{/* Desktop - Tabela Completa */}
<div className="hidden lg:block">
  <table className="w-full">
    <thead className="bg-gray-50 dark:bg-gray-800">
      <tr>
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
          Nome
        </th>
        {/* Mais colunas */}
      </tr>
    </thead>
    <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
      {items.map((item) => (
        <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
          <td className="px-6 py-4 whitespace-nowrap">
            <div className="text-sm font-medium text-gray-900 dark:text-white">
              {item.name}
            </div>
          </td>
          {/* Mais células */}
          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
            <ActionDropdown options={actionOptions} />
          </td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

#### 2. **Tablet Layout** (md-lg: 768px-1023px)
```jsx
{/* Tablet - Cards Compactos */}
<div className="hidden md:block lg:hidden space-y-3 p-4">
  {items.map((item) => (
    <Card key={item.id} className="p-4">
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {item.name}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {item.subtitle}
              </p>
            </div>
            <div>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(item.status)}`}>
                {getStatusLabel(item.status)}
              </span>
            </div>
          </div>
        </div>
        <div className="ml-4 flex-shrink-0">
          <ActionDropdown options={actionOptions} />
        </div>
      </div>
    </Card>
  ))}
</div>
```

#### 3. **Mobile Layout** (sm- ≤ 767px)
```jsx
{/* Mobile - Cards Completos */}
<div className="md:hidden space-y-4 p-4">
  {items.map((item) => (
    <[Entity]MobileCard
      key={item.id}
      item={item}
      onView={handleView}
      onEdit={handleEdit}
      onDelete={handleDelete}
    />
  ))}
</div>
```

---

## 📱 Responsividade

### Breakpoints Padronizados

| Dispositivo | Breakpoint | Classes Tailwind |
|-------------|------------|------------------|
| **Mobile**  | ≤ 767px    | Base classes (sem prefixo) |
| **Tablet**  | 768px-1023px | `md:` a `lg:hidden` |
| **Desktop** | ≥ 1024px   | `lg:` |

### Grid System

```jsx
{/* Formulários */}
<div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
  {/* Campos do formulário */}
</div>

{/* Seções que ocupam largura total */}
<div className="lg:col-span-2">
  {/* Componente de largura total */}
</div>
```

### Headers Responsivos

```jsx
<header
  className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
  role="banner"
>
  <div className="min-w-0">
    <h1 className="text-2xl font-bold text-foreground">
      Título da Página
    </h1>
    <p className="text-muted-foreground">
      Descrição da funcionalidade
    </p>
  </div>
  <div className="flex gap-3 shrink-0">
    {/* Botões de ação */}
  </div>
</header>
```

---

## ⚡ Estados e Navegação

### Estados do CRUD

```jsx
const [currentView, setCurrentView] = useState("list");
// Valores: "list" | "create" | "edit" | "details"

const [selectedItemId, setSelectedItemId] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);
```

### Navegação URL-Based

```jsx
// React Router setup
const navigate = useNavigate();
const { id } = useParams();
const [searchParams] = useSearchParams();

// Navegação para detalhes
const handleView = (itemId) => {
  navigate(`/admin/[entities]/${itemId}?tab=informacoes`);
};

// Detecção de parâmetros URL
useEffect(() => {
  if (id) {
    setSelectedItemId(parseInt(id));
    setCurrentView("details");
  }
}, [id]);
```

### Modal vs URL Navigation

- **Modais**: Para ações rápidas (create/edit)
- **URL Navigation**: Para detalhes (shareable/bookmarkable)

---

## 🧩 Componentes Reutilizáveis

### FormErrorBoundary

```jsx
const [Entity]Form = ({ entityId, onSave, onCancel }) => {
  return (
    <FormErrorBoundary formName="[Entity]Form">
      <[Entity]FormContent
        entityId={entityId}
        onSave={onSave}
        onCancel={onCancel}
      />
    </FormErrorBoundary>
  );
};
```

### ActionDropdown

```jsx
<ActionDropdown
  options={[
    {
      label: "Ver detalhes",
      icon: <Eye className="h-4 w-4" />,
      onClick: () => handleView(item.id),
    },
    {
      label: "Editar",
      icon: <Edit className="h-4 w-4" />,
      onClick: () => handleEdit(item.id),
    },
    {
      label: "Excluir",
      icon: <Trash2 className="h-4 w-4" />,
      onClick: () => handleDelete(item.id),
      variant: "destructive",
    },
  ]}
/>
```

### Card Wrapper

```jsx
<Card>
  <div className="p-6">
    {/* Conteúdo do card */}
  </div>
</Card>
```

---

## 🎣 Hooks Customizados

### Estrutura do Hook

```typescript
export const use[Entity]Form = ({ entityId, onSave }: Props) => {
  // Estados
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState(initialFormData);

  // Computed values
  const isEditing = !!entityId;

  // Handlers
  const updateEntity = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      entity: { ...prev.entity, [field]: value }
    }));
  };

  const save = async () => {
    try {
      setLoading(true);
      setError(null);

      if (isEditing) {
        await entityService.update(entityId, formData);
      } else {
        await entityService.create(formData);
      }

      if (onSave) onSave();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    formData,
    isEditing,
    updateEntity,
    save,
    // ... outros handlers
  };
};
```

---

## 🔧 Padrões de Formulário

### Header do Formulário

```jsx
<header
  className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
  role="banner"
>
  <div className="min-w-0">
    <h1
      id="form-title"
      className="text-2xl font-bold text-foreground"
      tabIndex={-1}
    >
      {isEditing ? "Editar [Entity]" : "Nova [Entity]"}
    </h1>
    <p className="text-muted-foreground" id="form-description">
      {isEditing
        ? "Atualize as informações da [entity]"
        : "Cadastre uma nova [entity] no sistema"}
    </p>
  </div>
  <div
    className="flex gap-3 shrink-0"
    role="group"
    aria-label="Ações do formulário"
  >
    <Button
      variant="secondary"
      outline
      onClick={onCancel}
      icon={<X className="h-4 w-4" />}
      className="flex-1 sm:flex-none"
    >
      <span className="hidden sm:inline">Cancelar</span>
      <span className="sm:hidden">Cancelar</span>
    </Button>
    <Button
      type="submit"
      disabled={loading}
      icon={<Save className="h-4 w-4" />}
      className="flex-1 sm:flex-none"
    >
      <span className="hidden sm:inline">
        {loading ? "Salvando..." : "Salvar"}
      </span>
      <span className="sm:hidden">
        {loading ? "Salvando..." : "Salvar"}
      </span>
    </Button>
  </div>
</header>
```

### Estrutura do Form

```jsx
<form
  onSubmit={handleSubmit}
  className="space-y-6"
  aria-labelledby="form-title"
  aria-describedby="form-description"
  noValidate
>
  {/* Error Display */}
  {error && (
    <div
      className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
      role="alert"
      aria-live="polite"
    >
      <p className="text-red-600 dark:text-red-400">{error}</p>
    </div>
  )}

  {/* Form Sections */}
  <Card>
    <[Entity]BasicDataSection />
  </Card>

  <Card>
    <PhoneInputGroup />
  </Card>

  <Card>
    <EmailInputGroup />
  </Card>

  <Card>
    <AddressInputGroup />
  </Card>
</form>
```

---

## 📊 Status e Estados Visuais

### Status Badge

```jsx
const getStatusBadge = (status) => {
  const statusConfig = {
    active: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
    inactive: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
    pending: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
  };
  return statusConfig[status] || statusConfig.active;
};
```

### Loading States

```jsx
{loading ? (
  <div className="text-center py-12">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
    <p className="mt-4 text-muted-foreground">Carregando...</p>
  </div>
) : (
  <ContentComponent />
)}
```

---

## ✅ Checklist de Implementação

### Arquitetura
- [ ] Estrutura de arquivos seguindo o padrão
- [ ] Error boundaries implementados
- [ ] Hook customizado criado
- [ ] Service layer implementado
- [ ] Tipos TypeScript definidos

### Visual
- [ ] Três layouts responsivos (Desktop/Tablet/Mobile)
- [ ] Headers padronizados
- [ ] Cards consistentes
- [ ] ActionDropdown implementado
- [ ] Status badges padronizados

### Funcionalidade
- [ ] CRUD completo (Create, Read, Update, Delete)
- [ ] Navegação URL-based para detalhes
- [ ] Modals para create/edit
- [ ] Busca e filtros
- [ ] Paginação
- [ ] Loading states
- [ ] Error handling

### Responsividade
- [ ] Breakpoints lg: para desktop
- [ ] Breakpoints md: para tablet
- [ ] Layout mobile-first
- [ ] Grids responsivos
- [ ] Botões adaptativos

### Acessibilidade
- [ ] ARIA labels
- [ ] Roles semânticos
- [ ] Navegação por teclado
- [ ] Focus management
- [ ] Error announcements

### Performance
- [ ] React.memo para componentes
- [ ] Debounce na busca
- [ ] Lazy loading quando aplicável
- [ ] Otimização de re-renders

---

## 📝 Exemplo Completo

Para referência completa, consulte a implementação em:
- `frontend/src/pages/EmpresasPage.jsx`
- `frontend/src/components/forms/CompanyForm.tsx`
- `frontend/src/hooks/useCompanyForm.ts`

---

---

## 🔧 Arquitetura Backend

### Clean Architecture Structure

O backend segue arquitetura hexagonal (Clean Architecture) com separação clara de responsabilidades:

```
app/
├── domain/
│   ├── entities/              # Entidades de negócio puras
│   │   ├── company.py
│   │   ├── user.py
│   │   └── menu.py
│   └── repositories/          # Interfaces dos repositórios
├── application/
│   ├── dto/                   # Data Transfer Objects
│   ├── interfaces/            # Interfaces de serviços
│   └── use_cases/             # Casos de uso de negócio
│       ├── create_company_use_case.py
│       ├── get_company_use_case.py
│       └── update_company_use_case.py
├── infrastructure/
│   ├── orm/                   # Modelos SQLAlchemy
│   │   ├── models.py
│   │   └── views.py
│   ├── repositories/          # Implementações dos repositórios
│   │   ├── company_repository.py
│   │   └── user_repository.py
│   ├── services/              # Serviços externos
│   │   ├── auth_service.py
│   │   └── address_enrichment_service.py
│   └── database.py
└── presentation/
    ├── api/v1/                # Endpoints REST
    │   ├── companies.py
    │   ├── users.py
    │   └── auth.py
    └── schemas/               # Schemas Pydantic
        ├── company.py
        ├── user.py
        └── response.py
```

---

## 🛠️ Estrutura de APIs

### Router Principal

```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from structlog import get_logger

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.repositories.[entity]_repository import [Entity]Repository
from app.presentation.schemas.[entity] import (
    [Entity]Create,
    [Entity]Detailed,
    [Entity]List,
    [Entity]Update,
)

router = APIRouter()
logger = get_logger()

async def get_[entity]_repository(db=Depends(get_db)) -> [Entity]Repository:
    """Dependency to get [entity] repository"""
    return [Entity]Repository(db)
```

### Endpoints Padrão

#### 1. **CREATE** - POST /
```python
@router.post(
    "/",
    response_model=[Entity]Detailed,
    status_code=status.HTTP_201_CREATED,
    summary="Criar [Entity]",
    description="""
    Cria uma nova [entity] com todos os dados relacionados.

    **Validações automáticas:**
    - Campos obrigatórios validados
    - Dados únicos verificados
    - Relacionamentos validados
    """,
    tags=["[Entities]"],
)
async def create_[entity](
    [entity]_data: [Entity]Create,
    repository: [Entity]Repository = Depends(get_[entity]_repository),
    current_user: User = Depends(get_current_user),
):
    try:
        logger.info(f"Creating [entity]", user_id=current_user.id)

        new_[entity] = await repository.create([entity]_data)

        logger.info(f"[Entity] created successfully", [entity]_id=new_[entity].id)
        return new_[entity]

    except ValidationException as e:
        logger.error(f"Validation error creating [entity]", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating [entity]", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
```

#### 2. **READ LIST** - GET /
```python
@router.get(
    "/",
    response_model=List[[Entity]List],
    summary="Listar [Entities]",
    tags=["[Entities]"],
)
async def list_[entities](
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    search: Optional[str] = Query(None, description="Termo de busca"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    repository: [Entity]Repository = Depends(get_[entity]_repository),
    current_user: User = Depends(get_current_user),
):
    try:
        logger.info(f"Listing [entities]", user_id=current_user.id, skip=skip, limit=limit)

        [entities] = await repository.get_list(
            skip=skip,
            limit=limit,
            search=search,
            status=status,
        )

        return [entities]

    except Exception as e:
        logger.error(f"Error listing [entities]", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
```

#### 3. **READ DETAIL** - GET /{id}
```python
@router.get(
    "/{[entity]_id}",
    response_model=[Entity]Detailed,
    summary="Obter [Entity] por ID",
    tags=["[Entities]"],
)
async def get_[entity](
    [entity]_id: int,
    repository: [Entity]Repository = Depends(get_[entity]_repository),
    current_user: User = Depends(get_current_user),
):
    try:
        logger.info(f"Getting [entity]", [entity]_id=[entity]_id, user_id=current_user.id)

        [entity] = await repository.get_by_id([entity]_id)
        if not [entity]:
            raise HTTPException(status_code=404, detail="[Entity] não encontrada")

        return [entity]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting [entity]", [entity]_id=[entity]_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
```

#### 4. **UPDATE** - PUT /{id}
```python
@router.put(
    "/{[entity]_id}",
    response_model=[Entity]Detailed,
    summary="Atualizar [Entity]",
    tags=["[Entities]"],
)
async def update_[entity](
    [entity]_id: int,
    [entity]_data: [Entity]Update,
    repository: [Entity]Repository = Depends(get_[entity]_repository),
    current_user: User = Depends(get_current_user),
):
    try:
        logger.info(f"Updating [entity]", [entity]_id=[entity]_id, user_id=current_user.id)

        # Verificar se existe
        existing = await repository.get_by_id([entity]_id)
        if not existing:
            raise HTTPException(status_code=404, detail="[Entity] não encontrada")

        updated_[entity] = await repository.update([entity]_id, [entity]_data)

        logger.info(f"[Entity] updated successfully", [entity]_id=[entity]_id)
        return updated_[entity]

    except HTTPException:
        raise
    except ValidationException as e:
        logger.error(f"Validation error updating [entity]", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating [entity]", [entity]_id=[entity]_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
```

#### 5. **DELETE** - DELETE /{id}
```python
@router.delete(
    "/{[entity]_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir [Entity]",
    tags=["[Entities]"],
)
async def delete_[entity](
    [entity]_id: int,
    repository: [Entity]Repository = Depends(get_[entity]_repository),
    current_user: User = Depends(get_current_user),
):
    try:
        logger.info(f"Deleting [entity]", [entity]_id=[entity]_id, user_id=current_user.id)

        # Verificar se existe
        existing = await repository.get_by_id([entity]_id)
        if not existing:
            raise HTTPException(status_code=404, detail="[Entity] não encontrada")

        await repository.delete([entity]_id)

        logger.info(f"[Entity] deleted successfully", [entity]_id=[entity]_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting [entity]", [entity]_id=[entity]_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
```

---

## 📄 Schemas e Validações

### Schema Base

```python
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, validator

class [Entity]Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"

class [Entity]Base(BaseModel):
    """Schema base para [Entity]"""
    name: str = Field(..., min_length=1, max_length=255, description="Nome da [entity]")
    description: Optional[str] = Field(None, max_length=1000, description="Descrição")
    status: [Entity]Status = Field(default=[Entity]Status.ACTIVE, description="Status")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Nome é obrigatório')
        return v.strip()

class [Entity]Create([Entity]Base):
    """Schema para criação de [entity]"""
    # Adicionar campos específicos para criação
    pass

class [Entity]Update([Entity]Base):
    """Schema para atualização de [entity]"""
    # Todos os campos opcionais na atualização
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[[Entity]Status] = None

class [Entity]List(BaseModel):
    """Schema para listagem de [entities]"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: [Entity]Status
    created_at: datetime
    updated_at: Optional[datetime] = None

class [Entity]Detailed([Entity]List):
    """Schema detalhado para [entity]"""
    description: Optional[str] = None
    # Adicionar relacionamentos e campos extras

    # Relacionamentos
    phones: List[PhoneResponse] = []
    emails: List[EmailResponse] = []
    addresses: List[AddressResponse] = []
```

### Schemas de Relacionamentos

```python
class PhoneBase(BaseModel):
    country_code: str = Field(default="55", regex="^[0-9]{1,3}$")
    area_code: str = Field(..., regex="^[0-9]{2,3}$")
    number: str = Field(..., regex="^[0-9]{8,9}$")
    extension: Optional[str] = Field(None, max_length=10)
    type: PhoneType = Field(default=PhoneType.MOBILE)
    is_principal: bool = Field(default=False)
    is_whatsapp: bool = Field(default=False)

class EmailBase(BaseModel):
    email_address: EmailStr = Field(..., description="Endereço de email")
    type: EmailType = Field(default=EmailType.PERSONAL)
    is_principal: bool = Field(default=False)
    is_verified: bool = Field(default=False)

class AddressBase(BaseModel):
    street: str = Field(..., min_length=1, max_length=255)
    number: Optional[str] = Field(None, max_length=20)
    complement: Optional[str] = Field(None, max_length=100)
    neighborhood: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., regex="^[0-9]{8}$")
    country: str = Field(default="BR", max_length=2)
```

---

## 🗄️ Repositories e Use Cases

### Repository Pattern

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session

class [Entity]RepositoryInterface(ABC):
    @abstractmethod
    async def create(self, [entity]_data: [Entity]Create) -> [Entity]Detailed:
        pass

    @abstractmethod
    async def get_by_id(self, [entity]_id: int) -> Optional[[Entity]Detailed]:
        pass

    @abstractmethod
    async def get_list(self, skip: int, limit: int, **filters) -> List[[Entity]List]:
        pass

    @abstractmethod
    async def update(self, [entity]_id: int, [entity]_data: [Entity]Update) -> [Entity]Detailed:
        pass

    @abstractmethod
    async def delete(self, [entity]_id: int) -> bool:
        pass

class [Entity]Repository([Entity]RepositoryInterface):
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger()

    async def create(self, [entity]_data: [Entity]Create) -> [Entity]Detailed:
        """Criar nova [entity] com relacionamentos"""
        try:
            # Validações de negócio
            await self._validate_business_rules([entity]_data)

            # Criar entidade principal
            db_[entity] = [Entity]Model(**[entity]_data.model_dump(exclude={"phones", "emails", "addresses"}))
            self.db.add(db_[entity])
            await self.db.flush()  # Para obter o ID

            # Criar relacionamentos
            if [entity]_data.phones:
                await self._create_phones(db_[entity].id, [entity]_data.phones)

            if [entity]_data.emails:
                await self._create_emails(db_[entity].id, [entity]_data.emails)

            if [entity]_data.addresses:
                await self._create_addresses(db_[entity].id, [entity]_data.addresses)

            await self.db.commit()
            await self.db.refresh(db_[entity])

            return await self._to_detailed_schema(db_[entity])

        except Exception as e:
            await self.db.rollback()
            raise

    async def _validate_business_rules(self, [entity]_data: [Entity]Create):
        """Validações específicas de negócio"""
        # Implementar validações específicas
        pass

    async def _to_detailed_schema(self, db_[entity]) -> [Entity]Detailed:
        """Converter model para schema detalhado"""
        return [Entity]Detailed.model_validate(db_[entity])
```

### Use Cases

```python
from app.application.interfaces.repositories import [Entity]RepositoryInterface
from app.application.dto.[entity]_dto import [Entity]CreateDTO, [Entity]DetailedDTO

class Create[Entity]UseCase:
    def __init__(self, [entity]_repository: [Entity]RepositoryInterface):
        self.[entity]_repository = [entity]_repository
        self.logger = get_logger()

    async def execute(self, [entity]_data: [Entity]CreateDTO) -> [Entity]DetailedDTO:
        """Caso de uso para criar [entity]"""
        try:
            self.logger.info("Starting create [entity] use case")

            # Validações de negócio
            self._validate_business_rules([entity]_data)

            # Criar [entity]
            new_[entity] = await self.[entity]_repository.create([entity]_data)

            # Log de auditoria
            self.logger.info(f"[Entity] created successfully", [entity]_id=new_[entity].id)

            return new_[entity]

        except Exception as e:
            self.logger.error(f"Error in create [entity] use case", error=str(e))
            raise

    def _validate_business_rules(self, [entity]_data: [Entity]CreateDTO):
        """Validações específicas do caso de uso"""
        # Implementar regras de negócio
        pass
```

---

## 📊 Padrões de Response

### Response Wrappers

```python
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Any] = None

class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    pagination: dict
    total: int

# Uso nos endpoints
@router.get("/", response_model=PaginatedResponse[[Entity]List])
async def list_[entities](...):
    [entities] = await repository.get_list(...)
    total = await repository.count(...)

    return PaginatedResponse(
        data=[entities],
        pagination={
            "skip": skip,
            "limit": limit,
            "has_next": (skip + limit) < total,
            "has_prev": skip > 0,
        },
        total=total
    )
```

### Error Handling

```python
from fastapi import HTTPException
from app.infrastructure.exceptions import ValidationException, BusinessRuleException

class ErrorHandler:
    @staticmethod
    def handle_validation_error(e: ValidationException):
        return HTTPException(
            status_code=400,
            detail={
                "error": "Erro de validação",
                "details": str(e),
                "type": "validation_error"
            }
        )

    @staticmethod
    def handle_business_rule_error(e: BusinessRuleException):
        return HTTPException(
            status_code=422,
            detail={
                "error": "Regra de negócio violada",
                "details": str(e),
                "type": "business_rule_error"
            }
        )

    @staticmethod
    def handle_not_found_error(entity_name: str, entity_id: int):
        return HTTPException(
            status_code=404,
            detail={
                "error": f"{entity_name} não encontrada",
                "details": f"ID {entity_id} não existe",
                "type": "not_found_error"
            }
        )
```

---

**Versão**: 2.0
**Última atualização**: 2025-01-15
**Autor**: Equipe Pro Team Care
