# AGENTS.md - Pro Team Care Development Guide

## Build/Lint/Test Commands

### Backend (Python/FastAPI)
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run single test file
pytest tests/test_auth.py

# Run single test method
pytest tests/test_auth.py::TestAuth::test_login_success

# Run tests by marker
pytest -m "auth"  # unit, integration, slow, cache, auth, db

# Format code
black .

# Lint code
flake8

# Sort imports
isort .

# Run all pre-commit hooks
pre-commit run --all-files

# Type check (if mypy configured)
mypy app/
```

### Frontend (React/TypeScript)
```bash
# Install dependencies
cd frontend && npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Lint code
npm run lint

# Format code
npm run format
```

## Code Style Guidelines

### Python Backend
- **Formatting**: Black with 88 character line length
- **Imports**: isort with `--profile=black` (imports sorted alphabetically, stdlib → third-party → local)
- **Linting**: flake8 with `--extend-ignore=E203,W503` (compatible with Black)
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Types**: Use type hints, Pydantic models with `ConfigDict(from_attributes=True)`
- **Docstrings**: Google/NumPy style for functions/classes
- **Error Handling**: Custom exceptions (`BusinessException`, `ValidationException`, `NotFoundException`)
- **Logging**: Structured logging with structlog (JSON format)

### Frontend (React/TypeScript)
- **Formatting**: Prettier (auto-formatting)
- **Linting**: ESLint with React/TypeScript rules
- **Naming**: camelCase for variables/functions, PascalCase for components
- **Components**: Functional components with hooks, named exports
- **Styling**: Tailwind CSS with custom color system via CSS variables
- **State Management**: React Query for server state, Context for global state

### Architecture Patterns
- **Clean Architecture**: Domain → Application → Infrastructure → Presentation layers
- **Async/Await**: All database operations use async/await
- **Dependency Injection**: Repository pattern for data access
- **Security**: Basic JWT authentication, minimal rate limiting (login only), open CORS for development
- **Testing**: pytest-asyncio for async tests, TestClient for API tests

**Note**: Architecture simplified for better performance and development freedom. Removed complex security headers (CSP, HSTS, Permissions Policy), dynamic rate limiting, restrictive CORS validation, and heavy middlewares. Maintains essential security while reducing complexity by ~60%.

### File Structure
```
app/
├── domain/          # Business entities (Pydantic models)
├── application/     # Use cases (business logic)
├── infrastructure/  # External concerns (DB, auth, cache)
└── presentation/    # API routes (FastAPI routers)

frontend/src/
├── components/      # Reusable UI components
├── pages/          # Page components
├── services/       # API client functions
├── contexts/       # React contexts
├── utils/          # Utility functions
└── styles/         # Global styles
```

### Commit Messages
- Use conventional commits: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`
- Include scope when relevant: `feat(auth): add password reset`
- Keep first line under 50 characters, body under 72 characters per line

### Environment Setup
- Use `.env` files for configuration (never commit secrets)
- Database: PostgreSQL with asyncpg driver
- Cache: Redis for session storage and rate limiting
- CORS: Restrictive origins, no wildcards allowed
