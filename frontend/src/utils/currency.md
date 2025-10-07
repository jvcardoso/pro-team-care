# 💰 Sistema de Formatação de Moeda Centralizado

## 📋 Visão Geral

Este sistema fornece formatação e validação unificada de valores monetários para toda a aplicação Pro Team Care, garantindo consistência, precisão e uma experiência de usuário otimizada.

## 🛠️ Componentes Principais

### 1. **Utilitários de Formatação** (`utils/formatters.js`)

#### **formatCurrencyDisplay(value, options)**

Formata valores numéricos como moeda brasileira para exibição

```javascript
import { formatCurrencyDisplay } from "../utils/formatters";

// Exemplos
formatCurrencyDisplay(1234.56); // → "R$ 1.234,56"
formatCurrencyDisplay(0); // → "R$ 0,00"
formatCurrencyDisplay(null); // → "R$ 0,00"
formatCurrencyDisplay(1000, { currency: "USD" }); // → "$1,000.00"
```

#### **formatCurrencyValue(value)**

Formata sem símbolo de moeda (apenas separadores)

```javascript
formatCurrencyValue(1234.56); // → "1.234,56"
formatCurrencyValue(0); // → "0,00"
```

#### **parseCurrencyRobust(formattedValue)**

Converte strings formatadas em valores numéricos

```javascript
parseCurrencyRobust("R$ 1.234,56"); // → 1234.56
parseCurrencyRobust("1234,56"); // → 1234.56
parseCurrencyRobust("1,234.56"); // → 1234.56
```

#### **validateCurrency(value, options)**

Validação completa de valores monetários

```javascript
validateCurrency("1234,56", {
  min: 100,
  max: 10000,
  required: true,
});
// → { isValid: true, error: "", numericValue: 1234.56 }
```

### 2. **Componente CurrencyInput** (`components/ui/CurrencyInput.tsx`)

Componente React avançado para entrada de valores monetários:

```tsx
import CurrencyInput from '../ui/CurrencyInput';

// Uso básico
<CurrencyInput
  label="Valor Mensal"
  value={monthlyValue}
  onChange={(event) => setMonthlyValue(event.numericValue)}
  required
/>

// Uso avançado com validação
<CurrencyInput
  label="Valor do Contrato"
  value={contractValue}
  onChange={(event) => {
    setValue("monthly_value", event.numericValue);
  }}
  required
  min={100}
  max={999999}
  showValidation
  error={errors.monthly_value?.message}
  placeholder="R$ 0,00"
/>
```

## 🎯 Recursos Avançados

### **Auto-formatação Inteligente**

- ✅ Detecta formatos: `1234,56`, `R$ 1.234,56`, `1,234.56`
- ✅ Converte automaticamente para formato brasileiro
- ✅ Mantém precisão decimal (2 casas)

### **Validação Robusta**

- ✅ Valores mínimo e máximo configuráveis
- ✅ Suporte a valores negativos (configurável)
- ✅ Validação em tempo real
- ✅ Mensagens de erro contextuais

### **UX Otimizada**

- ✅ Feedback visual (ícones de validação)
- ✅ Dicas contextuais durante digitação
- ✅ Formatação automática enquanto digita
- ✅ Suporte a teclado numérico móvel

### **Acessibilidade**

- ✅ Labels semânticos
- ✅ ARIA attributes
- ✅ Navegação por teclado
- ✅ Alto contraste para validação

## 📊 Integração com Backend

### **Persistência no Banco**

```sql
-- Tabela contracts
monthly_value NUMERIC(10, 2) NOT NULL
```

### **Schema Pydantic**

```python
from decimal import Decimal
from pydantic import BaseModel

class ContractBase(BaseModel):
    monthly_value: Optional[Decimal] = None
```

### **Fluxo Completo**

1. **Frontend**: `CurrencyInput` → `event.numericValue` (number)
2. **API**: Decimal com 2 casas decimais
3. **Database**: `NUMERIC(10, 2)`
4. **Exibição**: `formatCurrencyDisplay()` → `"R$ 1.234,56"`

## 🔧 Casos de Uso Comuns

### **1. Formulários de Contrato**

```tsx
// ContractForm.tsx
<CurrencyInput
  label="Valor Mensal (R$)"
  value={watch("monthly_value") || 0}
  onChange={(event) => setValue("monthly_value", event.numericValue)}
  required
  min={0}
  max={999999999}
  showValidation
  error={errors.monthly_value?.message}
/>
```

### **2. Exibição em Tabelas**

```tsx
// DataTable column
{
  header: "Valor",
  cell: ({ row }) => formatCurrencyDisplay(row.monthly_value)
}
```

### **3. Dashboard de Métricas**

```tsx
// ContractDetails.tsx
const metrics = [
  {
    icon: <DollarSign className="h-5 w-5" />,
    label: "Valor Mensal",
    value: formatCurrencyDisplay(contract.monthly_value),
  },
];
```

### **4. Validação de Formulários**

```tsx
// Com React Hook Form + Zod
const contractSchema = z.object({
  monthly_value: z.number().min(0, "Valor deve ser positivo"),
});

// Integração automática
const {
  formState: { errors },
} = useForm({
  resolver: zodResolver(contractSchema),
});
```

## ⚡ Performance e Otimização

### **Memoização**

```tsx
const formattedValue = useMemo(() => formatCurrencyDisplay(value), [value]);
```

### **Debounce em Validação**

```tsx
const [debouncedValue] = useDebounce(value, 300);
useEffect(() => {
  if (debouncedValue) {
    validateCurrency(debouncedValue, validationOptions);
  }
}, [debouncedValue]);
```

## 🔍 Debugging e Logs

```javascript
// Logs estruturados para debugging
console.log("Currency Debug:", {
  input: userInput,
  parsed: parseCurrencyRobust(userInput),
  formatted: formatCurrencyDisplay(parsedValue),
  isValid: validateCurrency(userInput).isValid,
});
```

## 📈 Extensibilidade

### **Múltiplas Moedas**

```javascript
formatCurrencyDisplay(value, {
  currency: "USD",
  locale: "en-US",
}); // → "$1,234.56"
```

### **Formatação Customizada**

```javascript
formatCurrencyDisplay(value, {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
}); // → "R$ 1.234,560"
```

---

**✨ Este sistema garante formatação consistente e precisão monetária em toda a aplicação Pro Team Care!**
