# Testes E2E com Playwright 🎭

Este diretório contém testes End-to-End (E2E) para o sistema de menus dinâmicos do Pro Team Care, implementados usando Playwright.

## 📁 Estrutura

```
e2e/
├── README.md                    # Este arquivo
├── global-setup.ts             # Setup global dos testes
├── pages/                      # Page Object Models
│   └── AdminPage.ts            # POM para área administrativa
├── fixtures/                   # Fixtures e dados de teste
│   └── auth-state.json         # Estado de autenticação
├── utils/                      # Utilitários para testes
├── dynamic-menus.spec.ts       # Testes específicos de menus dinâmicos
├── complete-flow.spec.ts       # Testes de fluxo completo
└── performance.spec.ts         # Testes de performance
```

## 🚀 Como Executar

### Comandos Disponíveis

```bash
# Executar todos os testes E2E
npm run test:e2e

# Executar com interface gráfica
npm run test:e2e:ui

# Executar em modo debug
npm run test:e2e:debug

# Executar com browsers visíveis
npm run test:e2e:headed

# Executar apenas no Chromium
npm run test:e2e:chromium

# Executar apenas no Firefox
npm run test:e2e:firefox

# Executar apenas no Safari
npm run test:e2e:webkit

# Executar apenas no mobile
npm run test:e2e:mobile

# Ver relatório de testes
npm run test:e2e:report

# Executar todos os testes (unit + E2E)
npm run test:all
```

### Pré-requisitos

1. **Backend rodando**: Os testes precisam que o backend esteja disponível em `http://192.168.11.83:8000`
2. **Frontend rodando**: O Playwright irá iniciar automaticamente o frontend na porta 3001

## 📋 Suítes de Teste

### 1. Testes de Menus Dinâmicos (`dynamic-menus.spec.ts`)

Testa especificamente o sistema de menus dinâmicos:

- ✅ Carregamento de menus para usuário normal (6 menus)
- ✅ Alternância entre usuário normal e ROOT (11 menus para ROOT)
- ✅ Alternância entre menus dinâmicos e estáticos
- ✅ Expansão e colapso de submenus
- ✅ Exibição de badges nos menus
- ✅ Navegação correta ao clicar em menus
- ✅ Tratamento gracioso de erros de API
- ✅ Atualização de menus via refresh
- ✅ Persistência de estado após navegação
- ✅ Responsividade em diferentes tamanhos de tela

### 2. Fluxo Completo (`complete-flow.spec.ts`)

Testa o fluxo E2E completo do usuário:

**Fluxo Principal:**

1. 🔍 Verificação de conectividade (backend + frontend)
2. 🔐 Simulação de processo de login
3. 🏠 Navegação para área administrativa
4. 📋 Validação de menus dinâmicos (usuário normal)
5. 🧭 Navegação e interação com menus
6. 👑 Alternância para usuário ROOT
7. 🔧 Teste de alternância de modo de menu
8. 📱 Teste de responsividade
9. ⚡ Verificação de performance
10. 🎯 Validação final do sistema

**Fluxo de Recuperação:**

- 🚨 Teste de recuperação graciosamente de erros de API

### 3. Testes de Performance (`performance.spec.ts`)

Valida aspectos de performance do sistema:

- ⚡ Tempo de carregamento de menus (< 3s)
- 🔄 Performance ao alternar entre usuários múltiplas vezes
- 🧭 Eficiência em múltiplas navegações
- 📱 Performance em diferentes resoluções
- 💾 Eficiência do sistema de cache

## 🎯 Critérios de Sucesso

### Performance

- **Carregamento inicial**: < 3 segundos
- **Alternância de usuário**: < 5 segundos
- **Navegação entre páginas**: < 2 segundos
- **Responsividade**: Funcional em 4 resoluções diferentes

### Funcionalidade

- **Usuário Normal**: 6 menus básicos carregados
- **Usuário ROOT**: 11 menus (básicos + admin + dev)
- **Menus Hierárquicos**: Expansão/colapso funcionando
- **Navegação**: URLs corretas após cliques
- **Error Recovery**: Fallback funcional para erros de API

### Compatibilidade

- **Browsers**: Chrome, Firefox, Safari
- **Dispositivos**: Desktop, Tablet, Mobile
- **Resoluções**: 1920x1080, 1280x720, 768x1024, 375x667

## 🐛 Debug e Troubleshooting

### Problemas Comuns

1. **Backend não está rodando**

   ```bash
   # Verificar se backend está ativo
   curl http://192.168.11.83:8000/api/v1/health
   ```

2. **Frontend não inicia automaticamente**

   ```bash
   # Iniciar manualmente
   npm run dev
   ```

3. **Testes falham por timeout**

   - Verificar se o sistema está sobrecarregado
   - Aumentar timeouts no `playwright.config.ts`

4. **Problemas de autenticação**
   - Verificar se o token mock está sendo aceito
   - Verificar configuração no `global-setup.ts`

### Modo Debug

Para debugar testes específicos:

```bash
# Debug com Playwright UI
npm run test:e2e:ui

# Debug linha por linha
npm run test:e2e:debug

# Executar apenas um arquivo
npx playwright test dynamic-menus.spec.ts --debug
```

### Visualizar Resultados

Após executar os testes:

```bash
# Ver relatório HTML
npm run test:e2e:report

# Ver screenshots de falhas
ls test-results/
```

## 📊 Métricas e Relatórios

Os testes geram automaticamente:

- **Screenshots** de falhas
- **Vídeos** de testes que falharam
- **Traces** para debug detalhado
- **Relatórios HTML** com resultados completos
- **Métricas de performance** no console

## 🔧 Configuração Avançada

### Customizar Timeouts

Editar `playwright.config.ts`:

```typescript
use: {
  actionTimeout: 10000,      // Timeout para ações
  navigationTimeout: 30000,  // Timeout para navegação
}
```

### Adicionar Novos Browsers

```typescript
projects: [
  {
    name: "Microsoft Edge",
    use: { ...devices["Desktop Edge"], channel: "msedge" },
  },
];
```

### Configurar CI/CD

Para execução em pipeline:

```bash
# Instalar dependências do sistema (apenas uma vez)
npx playwright install-deps

# Executar testes headless
npm run test:e2e
```

## 🎯 Próximos Passos

Potenciais melhorias para os testes E2E:

1. **Testes de Acessibilidade**: Usando `axe-core`
2. **Testes Visuais**: Screenshot comparison
3. **Testes de Carga**: Múltiplos usuários simultâneos
4. **Integration com CI/CD**: GitHub Actions
5. **Testes de Segurança**: Validação de XSS/CSRF
6. **Testes de API**: Validação direta das APIs

## 📚 Referências

- [Playwright Documentation](https://playwright.dev/)
- [Page Object Model](https://playwright.dev/docs/pom)
- [Test Configuration](https://playwright.dev/docs/test-configuration)
- [Debugging Tests](https://playwright.dev/docs/debug)
