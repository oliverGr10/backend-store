# BodegaApp — Backend

API REST con FastAPI para digitalizar bodegas de barrio en Perú.

## 🚀 Setup rápido

```bash
# 1. Crear entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate     # Mac/Linux
# .venv\Scripts\activate      # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Edita .env con tus credenciales de Supabase y Anthropic

# 4. Correr la API en modo desarrollo
uvicorn app.main:app --reload --port 8000
```

La API estará disponible en:
- **Docs interactivos:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health check:** http://localhost:8000/health

## 📁 Estructura

```
backend/
├── app/
│   ├── main.py          ← FastAPI app, middlewares, routers
│   ├── config.py        ← Variables de entorno (pydantic-settings)
│   ├── database.py      ← SQLAlchemy async + cliente Supabase
│   ├── modules/
│   │   └── products/    ← ✅ Implementado
│   │       ├── models.py
│   │       ├── schemas.py
│   │       ├── repository.py
│   │       ├── service.py
│   │       └── router.py
│   └── shared/
│       ├── exceptions.py
│       ├── responses.py
│       └── utils.py
├── tests/
├── .env.example
└── requirements.txt
```

## 🧪 Tests

```bash
pytest tests/ -v
```

## 📡 Endpoints disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/products/` | Listar productos |
| POST | `/api/v1/products/` | Crear producto |
| GET | `/api/v1/products/low-stock` | Productos con stock bajo |
| GET | `/api/v1/products/{id}` | Detalle de producto |
| PUT | `/api/v1/products/{id}` | Actualizar producto |
| DELETE | `/api/v1/products/{id}` | Desactivar producto |
| PATCH | `/api/v1/products/{id}/stock` | Ajustar stock |

## 🔧 Módulos por implementar (Semana 2)

- `sales/` — Ventas con descuento automático de stock
- `debts/` — Fiados (créditos a clientes)
- `auth/` — Autenticación con Supabase JWT
- `ai/` — Recomendaciones con Claude API
