# Documentação dos Hooks

Este documento descreve os hooks customizados utilizados no frontend do Pro Team Care.

## Índice

- [usePhone](#usephone)
- [useCEP](#usecep)
- [useForm](#useform)
- [useDataTable](#usedatatable)
- [useCompanyForm](#usecompanyform)
- [useBreadcrumbs](#usebreadcrumbs)

## usePhone

Hook para gerenciamento de entrada de telefone com formatação e validação automática.

### Uso Básico

```javascript
import { usePhone } from '../hooks';

const MyComponent = () => {
  const phoneHook = usePhone('', {
    required: true,
    onChange: (data) => console.log(data),
    showValidation: true
  });

  return (
    <input
      type="text"
      value={phoneHook.formattedValue}
      onChange={(e) => phoneHook.handleChange(e.target.value)}
      onBlur={phoneHook.handleBlur}
    />
    {phoneHook.displayError && (
      <span className="error">{phoneHook.validationMessage}</span>
    )}
  );
};
```

### Propriedades Retornadas

- `formattedValue`: Valor formatado do telefone
- `rawValue`: Valor sem formatação
- `isValid`: Se o telefone é válido
- `validationMessage`: Mensagem de erro de validação
- `isDirty`: Se o campo foi modificado
- `phoneType`: Tipo do telefone ('mobile' ou 'landline')
- `handleChange`: Função para atualizar o valor
- `handleBlur`: Função para validar no blur
- `setValue`: Função para definir valor programaticamente
- `clear`: Função para limpar o campo
- `validate`: Função para validar manualmente

### Opções

- `required`: Campo obrigatório (padrão: false)
- `onChange`: Callback chamado quando o valor muda
- `countryCode`: Código do país (padrão: '55')
- `showValidation`: Mostrar validação (padrão: true)

## useCEP

Hook para gerenciamento de entrada de CEP com integração ViaCEP.

### Uso Básico

```javascript
import { useCEP } from '../hooks';

const MyComponent = () => {
  const cepHook = useCEP('', {
    required: true,
    onAddressFound: (address) => console.log('Endereço encontrado:', address),
    autoConsult: true
  });

  return (
    <div>
      <input
        type="text"
        value={cepHook.formattedValue}
        onChange={(e) => cepHook.handleChange(e.target.value)}
        onBlur={cepHook.handleBlur}
      />
      <button
        onClick={cepHook.handleConsult}
        disabled={!cepHook.canConsult}
      >
        Consultar CEP
      </button>
      {cepHook.addressData && (
        <div>
          <p>{cepHook.addressData.street}</p>
          <p>{cepHook.addressData.city} - {cepHook.addressData.state}</p>
        </div>
      )}
    </div>
  );
};
```

### Propriedades Retornadas

- `formattedValue`: CEP formatado
- `rawValue`: CEP sem formatação
- `isValid`: Se o CEP é válido
- `validationMessage`: Mensagem de erro
- `isLoading`: Se está consultando o ViaCEP
- `isDirty`: Se o campo foi modificado
- `addressData`: Dados do endereço retornados pelo ViaCEP
- `handleChange`: Função para atualizar o valor
- `handleBlur`: Função para validar no blur
- `handleConsult`: Função para consultar CEP manualmente
- `setValue`: Função para definir valor programaticamente
- `clear`: Função para limpar o campo

### Opções

- `required`: Campo obrigatório (padrão: false)
- `onChange`: Callback quando valor muda
- `onAddressFound`: Callback quando endereço é encontrado
- `autoConsult`: Consultar automaticamente quando CEP completo (padrão: false)
- `showValidation`: Mostrar validação (padrão: true)

## useForm

Hook genérico para gerenciamento de formulários complexos.

### Uso Básico

```javascript
import { useForm } from '../hooks';

const MyComponent = () => {
  const form = useForm({
    name: '',
    email: '',
    age: 0
  }, {
    validate: {
      name: (value) => value.length < 2 ? 'Nome muito curto' : null,
      email: (value) => !value.includes('@') ? 'Email inválido' : null,
      age: (value) => value < 18 ? 'Deve ser maior de idade' : null
    },
    onSubmit: async (data) => {
      console.log('Enviando:', data);
      // Lógica de submit
    }
  });

  return (
    <form onSubmit={form.handleSubmit}>
      <input
        {...form.getFieldProps('name')}
        placeholder="Nome"
      />
      {form.errors.name && <span>{form.errors.name}</span>}

      <input
        {...form.getFieldProps('email')}
        type="email"
        placeholder="Email"
      />
      {form.errors.email && <span>{form.errors.email}</span>}

      <input
        {...form.getFieldProps('age')}
        type="number"
        placeholder="Idade"
      />
      {form.errors.age && <span>{form.errors.age}</span>}

      <button type="submit" disabled={form.isSubmitting}>
        {form.isSubmitting ? 'Enviando...' : 'Enviar'}
      </button>

      {form.submitError && <span>{form.submitError}</span>}
    </form>
  );
};
```

### Propriedades Retornadas

- `formData`: Dados atuais do formulário
- `errors`: Objeto com erros de validação
- `touched`: Campos que foram tocados
- `isSubmitting`: Se está enviando
- `submitError`: Erro do submit
- `isValid`: Se o formulário é válido
- `isDirty`: Se o formulário foi modificado
- `hasErrors`: Se há erros
- `setValue`: Definir valor de campo específico
- `setValues`: Definir múltiplos valores
- `setFieldTouched`: Marcar campo como tocado
- `validateForm`: Validar todo formulário
- `handleSubmit`: Handler para submit
- `reset`: Resetar formulário
- `getFieldProps`: Props para input com handlers

## useDataTable

Hook abrangente para gerenciamento de tabelas de dados com paginação, filtros e exportação.

### Uso Básico

```javascript
import { useDataTable } from '../hooks';

const MyComponent = () => {
  const table = useDataTable({
    config: {
      title: 'Minha Tabela',
      searchFields: ['name', 'email'],
      columns: [
        { key: 'id', label: 'ID', type: 'number' },
        { key: 'name', label: 'Nome', type: 'text' },
        { key: 'email', label: 'Email', type: 'text' }
      ],
      metrics: {
        primary: [
          { id: 'total', label: 'Total', value: 0 }
        ]
      },
      actions: [
        { id: 'edit', label: 'Editar', onClick: (item) => console.log('Editar', item) }
      ]
    },
    initialData: myData,
    onDataChange: (data) => console.log('Dados mudaram:', data)
  });

  return (
    <div>
      {/* Métricas */}
      {table.metrics.map(metric => (
        <div key={metric.id}>
          <h3>{metric.label}</h3>
          <p>{metric.value}</p>
        </div>
      ))}

      {/* Barra de busca */}
      <input
        type="text"
        value={table.state.searchTerm}
        onChange={(e) => table.callbacks.onSearch(e.target.value)}
        placeholder="Buscar..."
      />

      {/* Tabela */}
      <table>
        <thead>
          <tr>
            {table.config.columns.map(col => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.state.data.map(item => (
            <tr key={item.id}>
              {table.config.columns.map(col => (
                <td key={col.key}>{item[col.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Paginação */}
      <button
        onClick={() => table.callbacks.onPageChange(table.state.currentPage - 1)}
        disabled={table.state.currentPage === 1}
      >
        Anterior
      </button>
      <span>{table.state.currentPage} de {table.state.totalPages}</span>
      <button
        onClick={() => table.callbacks.onPageChange(table.state.currentPage + 1)}
        disabled={table.state.currentPage === table.state.totalPages}
      >
        Próximo
      </button>
    </div>
  );
};
```

### Propriedades Principais

- `state`: Estado atual da tabela (dados, paginação, filtros, etc.)
- `callbacks`: Funções para interagir com a tabela
- `metrics`: Métricas calculadas
- `detailedMetrics`: Métricas detalhadas

### Configuração

A configuração inclui:
- `title`: Título da tabela
- `searchFields`: Campos para busca
- `columns`: Definição das colunas
- `metrics`: Métricas a calcular
- `actions`: Ações disponíveis
- `bulkActions`: Ações em lote
- `export`: Configuração de exportação

## useCompanyForm

Hook específico para gerenciamento de formulários de empresa com integração com APIs externas.

### Uso Básico

```javascript
import { useCompanyForm } from '../hooks';

const CompanyFormComponent = ({ companyId }) => {
  const form = useCompanyForm({
    companyId,
    onSave: () => console.log('Empresa salva'),
    onRedirectToDetails: (id) => navigate(`/companies/${id}`)
  });

  // O hook gerencia automaticamente:
  // - Carregamento de dados da empresa
  // - Validação de CNPJ
  // - Enriquecimento de endereços
  // - Submissão do formulário
  // - Tratamento de erros

  return (
    <div>
      {form.loading && <p>Carregando...</p>}
      {form.error && <p className="error">{form.error}</p>}

      {/* Formulário de empresa */}
      <form onSubmit={(e) => form.proceedWithSave(form.formData)}>
        {/* Campos do formulário */}
        <button type="submit" disabled={form.loading}>
          Salvar
        </button>
      </form>
    </div>
  );
};
```

### Funcionalidades

- Carregamento automático de dados da empresa
- Validação de CNPJ com consulta à Receita Federal
- Enriquecimento automático de endereços via ViaCEP
- Gerenciamento de telefones, emails e endereços múltiplos
- Validação completa de formulários
- Tratamento de erros detalhado
- Integração com serviço de convites para gestores

## useBreadcrumbs

Hook para geração automática de breadcrumbs baseado na rota atual.

### Uso Básico

```javascript
import { useBreadcrumbs } from '../hooks';

const MyComponent = () => {
  const breadcrumbs = useBreadcrumbs();

  return (
    <nav aria-label="Breadcrumb">
      <ol>
        {breadcrumbs.map((crumb, index) => (
          <li key={index}>
            {crumb.href ? (
              <a href={crumb.href}>{crumb.label}</a>
            ) : (
              <span>{crumb.label}</span>
            )}
            {index < breadcrumbs.length - 1 && <span> / </span>}
          </li>
        ))}
      </ol>
    </nav>
  );
};
```

### Funcionalidades

- Geração automática baseada na URL atual
- Suporte a parâmetros de query (tab, companyId)
- Labels traduzidos para rotas comuns
- Marcação do item atual
- Links para navegação

## Considerações Gerais

### Padrões Comuns

Todos os hooks seguem padrões similares:
- Retornam objetos com estado e funções
- Usam callbacks para comunicação externa
- Incluem validação e tratamento de erros
- São tipados com TypeScript
- Seguem convenções de nomenclatura camelCase

### Validação

Os hooks incluem validação automática:
- Síncrona para formato básico
- Assíncrona para consultas externas (CEP, CNPJ)
- Mensagens de erro localizadas em português
- Estados de loading para operações assíncronas

### Integração

Os hooks são projetados para trabalhar juntos:
- `useForm` pode ser usado com `usePhone` e `useCEP`
- `useDataTable` integra com `useCompanyForm`
- `useBreadcrumbs` funciona com todas as rotas

### Performance

- Uso de `useCallback` e `useMemo` para otimização
- Evitação de re-renders desnecessários
- Cache de resultados de API quando apropriado

## Arquitetura e Design Patterns

### Estrutura de Hooks Customizados

#### Anatomia de um Hook Personalizado

```typescript
interface HookState<T> {
  data: T;
  loading: boolean;
  error: string | null;
  isDirty: boolean;
}

interface HookActions<T> {
  setValue: (value: T) => void;
  reset: () => void;
  validate: () => Promise<boolean>;
}

type CustomHook<T> = HookState<T> & HookActions<T>;
```

#### Padrão de Composição de Hooks

```typescript
// Hook base para estado comum
const useBaseField = <T>(initialValue: T) => {
  const [value, setValue] = useState<T>(initialValue);
  const [isDirty, setIsDirty] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = useCallback((newValue: T) => {
    setValue(newValue);
    setIsDirty(true);
    setError(null);
  }, []);

  return {
    value,
    setValue: handleChange,
    isDirty,
    error,
    setError,
    reset: () => {
      setValue(initialValue);
      setIsDirty(false);
      setError(null);
    }
  };
};

// Hook composto usando o base
const usePhoneField = (initialValue: string, options: PhoneOptions) => {
  const base = useBaseField(initialValue);
  const [phoneType, setPhoneType] = useState<'mobile' | 'landline'>('mobile');

  // Lógica específica de telefone...

  return {
    ...base,
    phoneType,
    formattedValue: formatPhone(base.value),
    // ... outras propriedades específicas
  };
};
```

### Gerenciamento de Estado

#### Estados Síncronos vs Assíncronos

```typescript
// Estado síncrono - validação imediata
const useSyncValidation = <T>(
  value: T,
  validator: (val: T) => string | null
) => {
  const error = useMemo(() => validator(value), [value, validator]);
  return { isValid: !error, error };
};

// Estado assíncrono - consultas externas
const useAsyncValidation = <T>(
  value: T,
  asyncValidator: (val: T) => Promise<string | null>,
  debounceMs = 500
) => {
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const debouncedValue = useDebounce(value, debounceMs);

  useEffect(() => {
    if (!debouncedValue) return;

    setIsValidating(true);
    asyncValidator(debouncedValue)
      .then(setError)
      .finally(() => setIsValidating(false));
  }, [debouncedValue, asyncValidator]);

  return { isValidating, error, isValid: !error };
};
```

### Padrões de Cache e Memoização

#### Cache Inteligente para APIs

```typescript
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiry: number;
}

const useAPICache = <T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl = 5 * 60 * 1000 // 5 minutos
) => {
  const cacheRef = useRef<Map<string, CacheEntry<T>>>(new Map());
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);

  const getCachedData = useCallback(() => {
    const entry = cacheRef.current.get(key);
    if (entry && Date.now() < entry.timestamp + entry.expiry) {
      return entry.data;
    }
    return null;
  }, [key]);

  const fetchData = useCallback(async () => {
    const cached = getCachedData();
    if (cached) {
      setData(cached);
      return cached;
    }

    setLoading(true);
    try {
      const result = await fetcher();
      cacheRef.current.set(key, {
        data: result,
        timestamp: Date.now(),
        expiry: ttl
      });
      setData(result);
      return result;
    } finally {
      setLoading(false);
    }
  }, [key, fetcher, ttl, getCachedData]);

  return { data, loading, fetch: fetchData, invalidate: () => cacheRef.current.delete(key) };
};
```

#### Debounce Otimizado

```typescript
const useDebounce = <T>(value: T, delay: number) => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};

// Hook para cancelar operações anteriores
const useCancelablePromise = () => {
  const pendingPromises = useRef<Set<() => void>>(new Set());

  const appendPendingPromise = useCallback((promise: Promise<any>) => {
    let isCanceled = false;
    const wrappedPromise = new Promise((resolve, reject) => {
      promise.then(
        value => isCanceled ? reject({ isCanceled: true }) : resolve(value),
        error => isCanceled ? reject({ isCanceled: true }) : reject(error)
      );
    });

    const cancel = () => { isCanceled = true; };
    pendingPromises.current.add(cancel);

    return wrappedPromise.finally(() => {
      pendingPromises.current.delete(cancel);
    });
  }, []);

  useEffect(() => {
    return () => {
      pendingPromises.current.forEach(cancel => cancel());
      pendingPromises.current.clear();
    };
  }, []);

  return { appendPendingPromise };
};
```

## Estratégias de Teste

### Testando Hooks Customizados

#### Setup de Teste com React Testing Library

```typescript
import { renderHook, act } from '@testing-library/react';
import { usePhone } from '../usePhone';

describe('usePhone', () => {
  it('should format phone number correctly', () => {
    const { result } = renderHook(() => usePhone(''));

    act(() => {
      result.current.handleChange('11999887766');
    });

    expect(result.current.formattedValue).toBe('(11) 99988-7766');
    expect(result.current.phoneType).toBe('mobile');
    expect(result.current.isValid).toBe(true);
  });

  it('should validate required field', () => {
    const { result } = renderHook(() => usePhone('', { required: true }));

    act(() => {
      result.current.handleBlur();
    });

    expect(result.current.validationMessage).toBe('Campo obrigatório');
    expect(result.current.isValid).toBe(false);
  });
});
```

#### Mocking APIs Externas

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useCEP } from '../useCEP';

// Mock do serviço ViaCEP
jest.mock('../../services/viacep', () => ({
  consultarCEP: jest.fn()
}));

const mockViaCEP = require('../../services/viacep').consultarCEP as jest.Mock;

describe('useCEP', () => {
  beforeEach(() => {
    mockViaCEP.mockClear();
  });

  it('should fetch address data when CEP is valid', async () => {
    const mockAddress = {
      street: 'Rua das Flores',
      city: 'São Paulo',
      state: 'SP'
    };

    mockViaCEP.mockResolvedValue(mockAddress);

    const { result } = renderHook(() => useCEP('', { autoConsult: true }));

    act(() => {
      result.current.handleChange('01310-100');
    });

    await waitFor(() => {
      expect(result.current.addressData).toEqual(mockAddress);
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('should handle API errors gracefully', async () => {
    mockViaCEP.mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useCEP(''));

    act(() => {
      result.current.handleConsult();
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.validationMessage).toContain('Erro ao consultar CEP');
    });
  });
});
```

#### Testando Hooks Complexos com Context

```typescript
import React from 'react';
import { renderHook } from '@testing-library/react';
import { useDataTable } from '../useDataTable';
import { DataTableProvider } from '../../contexts/DataTableContext';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <DataTableProvider>{children}</DataTableProvider>
);

describe('useDataTable', () => {
  it('should manage table state correctly', () => {
    const config = {
      title: 'Test Table',
      columns: [{ key: 'id', label: 'ID' }],
      searchFields: ['name']
    };

    const { result } = renderHook(
      () => useDataTable({ config, initialData: [] }),
      { wrapper }
    );

    expect(result.current.state.currentPage).toBe(1);
    expect(result.current.state.searchTerm).toBe('');
    expect(result.current.config.title).toBe('Test Table');
  });
});
```

## Guidelines de Performance

### Otimizações de Re-render

#### Memoização Inteligente

```typescript
const useOptimizedForm = <T extends Record<string, any>>(
  initialValues: T,
  options: FormOptions<T>
) => {
  // Memoizar validators para evitar re-criação
  const validators = useMemo(() => {
    return Object.entries(options.validate || {}).reduce((acc, [key, validator]) => {
      acc[key] = validator;
      return acc;
    }, {} as Record<string, Function>);
  }, [options.validate]);

  // Callbacks estáveis
  const handleChange = useCallback((field: keyof T, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  // Memoizar propriedades de campo para evitar re-renders
  const getFieldProps = useCallback((field: keyof T) => {
    return {
      value: formData[field],
      onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
        handleChange(field, e.target.value),
      onBlur: () => validateField(field)
    };
  }, [formData, handleChange]);

  return { handleChange, getFieldProps, /* ... */ };
};
```

#### Lazy Loading de Validações

```typescript
const useLazyValidation = <T>(
  value: T,
  validatorFactory: () => Promise<(val: T) => string | null>
) => {
  const [validator, setValidator] = useState<Function | null>(null);
  const [isLoadingValidator, setIsLoadingValidator] = useState(false);

  useEffect(() => {
    if (!validator && !isLoadingValidator) {
      setIsLoadingValidator(true);
      validatorFactory().then(v => {
        setValidator(() => v);
        setIsLoadingValidator(false);
      });
    }
  }, [validator, isLoadingValidator, validatorFactory]);

  const validationResult = useMemo(() => {
    return validator ? validator(value) : null;
  }, [validator, value]);

  return { validationResult, isLoadingValidator };
};
```

### Gerenciamento de Memória

#### Cleanup de Effects

```typescript
const useAPISubscription = (endpoint: string) => {
  const [data, setData] = useState(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    // Cancelar requisição anterior se existir
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    fetch(endpoint, { signal: controller.signal })
      .then(response => response.json())
      .then(setData)
      .catch(error => {
        if (error.name !== 'AbortError') {
          console.error('Fetch error:', error);
        }
      });

    return () => {
      controller.abort();
    };
  }, [endpoint]);

  // Cleanup final
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return { data };
};
```

## Padrões de Implementação

### Hook Factory Pattern

```typescript
interface BaseFieldOptions {
  required?: boolean;
  onChange?: (value: any) => void;
  validator?: (value: any) => string | null;
}

const createFieldHook = <T, O extends BaseFieldOptions>(
  formatter: (value: string) => T,
  validator: (value: T, options: O) => string | null
) => {
  return (initialValue: T, options: O = {} as O) => {
    const [value, setValue] = useState<T>(initialValue);
    const [isDirty, setIsDirty] = useState(false);

    const formattedValue = useMemo(() => formatter(String(value)), [value]);
    const error = useMemo(() => validator(value, options), [value, options]);

    const handleChange = useCallback((newValue: string) => {
      setValue(formatter(newValue));
      setIsDirty(true);
      options.onChange?.(formatter(newValue));
    }, [options]);

    return {
      value,
      formattedValue,
      error,
      isDirty,
      isValid: !error,
      handleChange,
      reset: () => {
        setValue(initialValue);
        setIsDirty(false);
      }
    };
  };
};

// Implementações específicas
export const usePhone = createFieldHook(
  (value: string) => formatPhone(value),
  (value: string, options: PhoneOptions) => validatePhone(value, options)
);

export const useCPF = createFieldHook(
  (value: string) => formatCPF(value),
  (value: string, options: CPFOptions) => validateCPF(value, options)
);
```

### Composição de Hooks para Formulários Complexos

```typescript
interface AddressFormData {
  zipCode: string;
  street: string;
  number: string;
  city: string;
  state: string;
}

const useAddressForm = (initialData: Partial<AddressFormData> = {}) => {
  const zipCode = useCEP(initialData.zipCode || '', {
    onAddressFound: (address) => {
      street.setValue(address.street);
      city.setValue(address.city);
      state.setValue(address.state);
    },
    autoConsult: true
  });

  const street = useBaseField(initialData.street || '');
  const number = useBaseField(initialData.number || '');
  const city = useBaseField(initialData.city || '');
  const state = useBaseField(initialData.state || '');

  const isValid = useMemo(() => {
    return zipCode.isValid &&
           street.value.length > 0 &&
           city.value.length > 0 &&
           state.value.length > 0;
  }, [zipCode.isValid, street.value, city.value, state.value]);

  const getFormData = useCallback((): AddressFormData => ({
    zipCode: zipCode.rawValue,
    street: street.value,
    number: number.value,
    city: city.value,
    state: state.value
  }), [zipCode.rawValue, street.value, number.value, city.value, state.value]);

  const reset = useCallback(() => {
    zipCode.clear();
    street.reset();
    number.reset();
    city.reset();
    state.reset();
  }, [zipCode, street, number, city, state]);

  return {
    fields: { zipCode, street, number, city, state },
    isValid,
    getFormData,
    reset
  };
};
```

### Error Boundary para Hooks

```typescript
interface HookErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export const useErrorBoundary = () => {
  const [state, setState] = useState<HookErrorBoundaryState>({
    hasError: false,
    error: null
  });

  const resetError = useCallback(() => {
    setState({ hasError: false, error: null });
  }, []);

  const captureError = useCallback((error: Error) => {
    setState({ hasError: true, error });
  }, []);

  return { ...state, resetError, captureError };
};

// Hook wrapper para capturar erros
export const withErrorBoundary = <T extends any[], R>(
  hook: (...args: T) => R
) => {
  return (...args: T): R & { error: Error | null; resetError: () => void } => {
    const errorBoundary = useErrorBoundary();

    let result: R;
    try {
      result = hook(...args);
    } catch (error) {
      errorBoundary.captureError(error as Error);
      result = {} as R; // Fallback
    }

    return {
      ...result,
      error: errorBoundary.error,
      resetError: errorBoundary.resetError
    };
  };
};
```

## Arquitetura de Dependências

### Hierarquia de Hooks

```
useBaseField (primitivo)
    ├── usePhone
    ├── useCEP
    ├── useCPF
    └── useEmail

useForm (composição)
    ├── useCompanyForm
    ├── useClientForm
    └── useUserForm

useDataTable (complexo)
    ├── useTableState
    ├── useTableFilters
    ├── useTablePagination
    └── useTableExport
```

### Injeção de Dependências

```typescript
interface HookDependencies {
  apiClient: ApiClient;
  validator: ValidatorService;
  formatter: FormatterService;
}

const HookDependenciesContext = createContext<HookDependencies | null>(null);

export const useHookDependencies = () => {
  const context = useContext(HookDependenciesContext);
  if (!context) {
    throw new Error('useHookDependencies must be used within HookDependenciesProvider');
  }
  return context;
};

// Hook que usa dependências injetadas
export const useValidatedField = <T>(initialValue: T, validationRules: ValidationRule[]) => {
  const { validator } = useHookDependencies();

  const [value, setValue] = useState<T>(initialValue);
  const [error, setError] = useState<string | null>(null);

  const validate = useCallback(async () => {
    try {
      await validator.validate(value, validationRules);
      setError(null);
      return true;
    } catch (validationError) {
      setError(validationError.message);
      return false;
    }
  }, [value, validationRules, validator]);

  return { value, setValue, error, validate };
};
```

Este documento agora fornece uma visão completa da arquitetura de hooks, incluindo padrões de implementação, estratégias de teste, otimizações de performance e diretrizes para desenvolvimento escalável.