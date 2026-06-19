# AI Support Ticket Analyzer

Analizador de tickets de soporte con IA. Procesa automáticamente tickets desde un CSV, los enriquece con categoría, prioridad, resumen y sentimiento usando un LLM, y los expone a través de una API REST y un dashboard visual con búsqueda en lenguaje natural.

---

## Quick Start (Docker)

```bash
# 1. Clonar y entrar al proyecto
git clone <repo-url>
cd ai-support-ticket-analyzer

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env si quieres usar un LLM real (ver sección Variables de entorno)

# 3. Levantar
docker compose up --build
```

- **Dashboard:** http://localhost:3000
- **API + Swagger:** http://localhost:8000/docs

Al arrancar, el backend ingesta automáticamente `tickets.csv` y lanza el análisis IA en background.

---

## Quick Start (sin Docker)

### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar entorno
cp ../.env.example .env
# Editar .env si es necesario

# Levantar
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- **Dashboard:** http://localhost:5173
- **API:** http://localhost:8000/docs

---

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servicio |
| `POST` | `/ingest` | Carga el CSV y guarda en DB |
| `POST` | `/process` | Lanza el análisis IA en background |
| `GET` | `/status` | Progreso del análisis (procesados, pendientes, errores) |
| `GET` | `/tickets` | Lista tickets con filtros y paginación |
| `GET` | `/tickets/{id}` | Detalle de un ticket |
| `GET` | `/summary` | KPIs agregados (prioridad, categoría, sentimiento, top productos) |
| `POST` | `/ask` | Pregunta en lenguaje natural sobre los tickets |

### Ejemplos con curl

```bash
# Cargar tickets
curl -X POST http://localhost:8000/ingest

# Lanzar análisis IA
curl -X POST http://localhost:8000/process

# Ver progreso
curl http://localhost:8000/status

# Listar tickets con filtros
curl "http://localhost:8000/tickets?priority=Critical&status=Open&page=1&page_size=20"

# Métricas
curl http://localhost:8000/summary

# Pregunta en lenguaje natural
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuáles son los problemas más críticos esta semana?"}'
```

---

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `AI_MODE` | `mock` (sin costo) o `real` (llama a la API) | `mock` |
| `AI_MODEL` | Modelo a usar (ver proveedores abajo) | `mock` |
| `ANTHROPIC_API_KEY` | API key de Anthropic | — |
| `GROQ_API_KEY` | API key de Groq | — |
| `GEMINI_API_KEY` | API key de Google Gemini | — |
| `OPENAI_API_KEY` | API key de OpenAI | — |
| `DATABASE_URL` | URL de SQLite | `sqlite:///./tickets.db` |
| `DATASET_PATH` | Ruta al CSV | `./dataset/tickets.csv` |
| `AUTO_INGEST_ON_START` | Ingesta automática al arrancar | `true` |

### Proveedores compatibles (sin cambiar código)

```env
# Anthropic Claude
AI_MODE=real
AI_MODEL=claude-haiku-4-5-20251001
ANTHROPIC_API_KEY=sk-ant-...

# Groq (rápido, tier gratuito disponible)
AI_MODE=real
AI_MODEL=groq/llama-3.3-70b-versatile
GROQ_API_KEY=gsk_...

# Google Gemini
AI_MODE=real
AI_MODEL=gemini/gemini-2.0-flash
GEMINI_API_KEY=...

# OpenAI
AI_MODE=real
AI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

---

## Arquitectura

```
tickets.csv
    ↓
POST /ingest (limpieza de datos)
    ↓
SQLite (tickets limpios)
    ↓
POST /process → asyncio.Semaphore(3) + tenacity retry
    ↓
LiteLLM → cualquier proveedor de LLM
    ↓
SQLite (tickets enriquecidos: categoría, prioridad, resumen, sentimiento, equipo)
    ↓
FastAPI REST API ←→ Base de conocimiento (JSON + Markdown)
    ↓
Dashboard React (KPIs, gráficos, tabla, /ask)
```

### Stack

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy + SQLite
- **IA:** LiteLLM (interfaz unificada para cualquier proveedor) + Tenacity (retry)
- **Frontend:** React 18 + Vite + TypeScript + TailwindCSS + Recharts + React Query

---

## Decisiones técnicas

**FastAPI sobre Django/Flask:** Async nativo, Swagger automático, Pydantic integrado. Django es excesivo para este scope; Flask requiere más boilerplate para async.

**SQLite sobre PostgreSQL:** Dataset local y pequeño. SQLite no requiere servidor y es portable en un archivo. Migrar a PostgreSQL es cambiar `DATABASE_URL` en el `.env`.

**LiteLLM:** Una interfaz única sobre todos los proveedores. Sin LiteLLM, cambiar de Claude a Groq requeriría reescribir el cliente. El costo es una dependencia extra liviana.

**`asyncio.Semaphore(3)` + Tenacity:** El procesamiento batch original con sleep fijo es frágil ante rate limits. El semáforo limita la concurrencia; tenacity reintenta con backoff exponencial ante errores 429. Separar `/ingest` de `/process` permite cargar datos instantáneamente y controlar cuándo corre la IA.

**Modo mock:** Permite demostrar toda la arquitectura sin gastar en una API de pago. La interfaz es idéntica al modo real: cambiar `AI_MODE=real` y añadir una key es suficiente.

**Base de conocimiento en JSON/Markdown:** Para este scope, inyectar el texto directamente en el prompt es más simple que montar una vector DB. Con más volumen de conocimiento, migraría a ChromaDB o pgvector.

---

## Limitaciones conocidas

- El análisis IA usa `asyncio.create_task()` — si el proceso del servidor se reinicia durante el procesamiento, los tickets pendientes quedan sin analizar hasta el próximo `POST /process`.
- La búsqueda en `/ask` es por keywords simples, no semántica. Muchas preguntas complejas se responden bien, pero preguntas muy específicas sobre fechas o rangos numéricos pueden ser imprecisas.
- No hay autenticación en la API.
- SQLite tiene limitaciones de concurrencia en escrituras; bajo carga muy alta habría contención. Cada `_process_single` abre su propia sesión para mitigarlo.
- El modo mock genera resúmenes genéricos, no analiza el texto real del ticket.

## Con más tiempo implementaría

- Cola de procesamiento persistente con Celery + Redis (sobrevive reinicios)
- Búsqueda semántica con embeddings para `/ask`
- Autenticación básica con API keys
- Tests unitarios del cleaner y de los routers
- Alertas para tickets Critical sin respuesta pasado el SLA
- Exportación de la tabla a CSV

---

## Uso de IA durante el desarrollo

Este proyecto fue desarrollado usando **Claude Code** (Anthropic) como asistente principal:

- **Diseño de arquitectura:** Claude ayudó a razonar el stack, identificar el problema del `auto_ingest_on_start` llamándose por HTTP a sí mismo, y proponer la solución con `asyncio.create_task` + semáforo.
- **Generación de código:** Los archivos base fueron generados con Claude y revisados manualmente para verificar correctitud, especialmente la lógica de limpieza del CSV (los casos edge de fechas en español, prioridades con espacios extra, placeholders sin resolver).
- **Revisión del plan:** Claude identificó proactivamente el cuello de botella del procesamiento IA en batch y propuso `tenacity` para retry con backoff exponencial en lugar del sleep fijo original.
- **Lo que validé manualmente:** Lógica del cleaner contra los datos reales del CSV, estructura de prompts para obtener JSON válido, configuración de Docker Compose (healthcheck y dependencias entre servicios).
