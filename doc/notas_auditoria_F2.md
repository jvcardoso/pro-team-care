### **Qualidade de Código:**
1. "Identifique redundâncias de código que podem ser refatoradas"
2. "Há anti-patterns que devem ser corrigidos?"
3. "O error handling é consistente em toda aplicação?"

## 🎨 **FASE 2: Auditoria Visual e UI/UX**

### **B1. Consistência do Design System**
```bash
# Análise dos componentes UI
claude-code review --directory frontend/src/components --focus design

# Validar:
- Todos os componentes seguem o mesmo padrão visual?
- Sistema de cores consistente (CSS Variables)?
- Tipografia uniforme (tamanhos, pesos, families)?
- Espaçamentos seguem escala consistente?
- Estados hover/focus/active padronizados?
```

### **B2. Sistema de Tema Dark/Light**
```bash
# Verificar implementação do tema
claude-code analyze --files "frontend/src/contexts/ThemeContext.jsx,tailwind.config.js,frontend/styles/index.css"

# Questões:
- Todas as cores usam CSS Variables?
- Transições suaves funcionando em todos componentes?
- Persistência do tema funciona corretamente?
- Não há cores hardcodadas que quebram o tema?
```

### **B3. Responsividade e Layout**
```bash
# Análise de responsividade
claude-code review --directory frontend/src/components/layout --focus responsive

# Verificar:
- Breakpoints Tailwind usados consistentemente?
- Sidebar funciona em mobile e desktop?
- Cards e componentes adaptam bem em diferentes telas?
- Não há scroll horizontal indesejado?
```