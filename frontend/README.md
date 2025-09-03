# Pro Team Care - Frontend

Frontend React + Tailwind CSS para o sistema Pro Team Care.

## 🚀 Quick Start

```bash
# Instalar dependências
cd frontend
npm install

# Desenvolvimento
npm run dev

# Build para produção
npm run build

# Preview da build
npm run preview
```

## 🌐 URLs

- **Frontend**: http://192.168.11.62:3000
- **API Backend**: http://192.168.11.62:8000
- **Documentação API**: http://192.168.11.62:8000/docs

## 🏗️ Estrutura

```
frontend/
├── src/
│   ├── components/    # Componentes reutilizáveis
│   ├── pages/         # Páginas da aplicação
│   ├── services/      # Integração com API
│   ├── styles/        # Estilos globais
│   ├── utils/         # Utilitários
│   ├── hooks/         # Custom hooks
│   └── contexts/      # Context providers
├── public/            # Assets estáticos
└── static/           # Arquivos servidos estaticamente
```

## 🎨 Stack Tecnológica

- **React 18** - Biblioteca UI
- **Vite** - Build tool e dev server
- **Tailwind CSS** - Framework CSS
- **Axios** - Cliente HTTP
- **React Router** - Roteamento
- **React Query** - State management para APIs
- **TypeScript** - Tipagem (opcional)

## 🔗 Integração com Backend

O frontend se comunica com a API FastAPI através de:

- **Proxy**: Vite proxy `/api` para `http://192.168.11.62:8000`
- **Autenticação**: JWT tokens via localStorage
- **CORS**: Configurado no backend para aceitar requests

## 📱 Features Preparadas

- ✅ Estrutura modular e escalável
- ✅ Integração completa com API
- ✅ Autenticação JWT
- ✅ Responsive design com Tailwind
- ✅ Build otimizado para produção
- ✅ Acesso via rede local (0.0.0.0:3000)

## 🚀 Deploy

```bash
# Build
npm run build

# Servir estaticamente
npm run serve
```

A aplicação estará disponível para toda a rede local!
