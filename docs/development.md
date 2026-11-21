# Development Guide

## Setup

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
bun install
```

## Running

```bash
# Backend (development)
cd backend
python app.py

# Frontend (development)
cd frontend
bun run dev
```

The Vite dev server proxies `/api` requests to `http://localhost:5000`.

## Testing

```bash
# Backend
cd backend
pip install pytest
python -m pytest tests/ -v

# Frontend
cd frontend
bun run test
```

Run specific backend test files:
```bash
python -m pytest tests/test_simulation.py -v
python -m pytest tests/validation/test_repressilator.py -v
```

## Build

```bash
cd frontend
bun run build
```

## Lint & Type check

```bash
cd frontend
bun run lint     # ESLint
bun run typecheck  # TypeScript
```

## Docker

```bash
# Build
docker build -t cyto-logic-backend .

# Run
docker run -p 5000:5000 cyto-logic-backend
```

## Adding a Backend

1. Create `compiler/backends/my_backend.py` subclassing `Backend`
2. Implement `generate(self, cir, **kwargs)` and `name` property
3. Register in `compiler/backends/registry.py`
4. Add API route in `app.py` if needed

## Adding a Plugin

1. Subclass `PluginBase` from `compiler.plugin.base`
2. Override any hook methods (`before_compile`, `after_simulate`, etc.)
3. Register via `PluginManager.register()` or set `CYTOLOGIC_PLUGINS=myplugin`

## Code Style

- No inline comments in production code
- Tests use pytest (no unittest)
- 4-space indentation
- Type hints preferred for public APIs
