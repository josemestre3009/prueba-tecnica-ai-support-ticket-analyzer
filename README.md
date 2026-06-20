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

Al arrancar, el backend ingesta automáticamente `tickets.csv`, normaliza los datos y lanza el análisis IA en background.

### Cambiar el dataset

```bash
# 1. Reemplazar el archivo
cp tu-nuevo-dataset.csv backend/dataset/tickets.csv

# 2. Bajar los contenedores y borrar la BD anterior
docker compose down -v

# 3. Volver a levantar
docker compose up --build
```

---

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servicio |
| `POST` | `/ingest` | Carga el CSV y guarda en DB |
| `POST` | `/process` | Lanza el análisis IA en background |

| `POST` | `/reprocess` | Fuerza re-análisis de todos los tickets |
| `GET` | `/status` | Progreso del análisis (procesados, pendientes, errores) |
| `GET` | `/tickets` | Lista tickets con filtros y paginación |
| `GET` | `/tickets/{id}` | Detalle de un ticket |
| `GET` | `/summary` | KPIs agregados (prioridad, categoría, sentimiento, top productos) |
| `POST` | `/ask` | Pregunta en lenguaje natural sobre los tickets |

### Filtros disponibles en `/tickets`

```
status, priority, ai_category, ai_sentiment, ai_priority,
product, channel, search, only_processed, page, page_size
```

### Ejemplos con curl

```bash
# Ver progreso del análisis
curl http://localhost:8000/status

# Listar tickets críticos abiertos
curl "http://localhost:8000/tickets?priority=Critical&status=Open&page=1&page_size=20"

# Métricas agregadas
curl http://localhost:8000/summary

# Pregunta en lenguaje natural
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuáles son los productos con peor satisfacción?"}'

# Re-analizar todos los tickets
curl -X POST http://localhost:8000/reprocess
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
| `DATABASE_URL` | URL de SQLite | `sqlite:///./data/tickets.db` |
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
POST /ingest → cleaner.py (normalización de datos)
    ↓
SQLite /data/tickets.db (tickets limpios)
    ↓
POST /process → asyncio.Semaphore(3) + tenacity retry
    ↓
Cliente IA multi-proveedor (Anthropic / Groq / Gemini / OpenAI)
    ↓
SQLite (tickets enriquecidos: categoría IA, prioridad IA, resumen, sentimiento, equipo)
    ↓
FastAPI REST API ←→ Base de conocimiento (JSON + Markdown)
    ↓
Dashboard React (KPIs, gráficos, tabla filtrable, chat /ask)
```

### Stack

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy + SQLite
- **IA:** Cliente propio multi-proveedor + Tenacity (retry con backoff exponencial)
- **Frontend:** React 18 + Vite + TypeScript + TailwindCSS + Recharts + React Query

---

## Decisiones técnicas

**FastAPI sobre Django/Flask:** Async nativo, Swagger automático, Pydantic integrado. Django es excesivo para este scope; Flask requiere más boilerplate para async.

**SQLite sobre PostgreSQL:** Dataset local y pequeño. SQLite no requiere servidor y es portable en un archivo. Migrar a PostgreSQL es cambiar `DATABASE_URL` en el `.env`.

**Cliente multi-proveedor propio:** En lugar de depender de la librería LiteLLM (que añade complejidad de instalación y dependencias), se construyó un router liviano que detecta el prefijo del modelo (`claude-*`, `groq/*`, `gemini/*`) y llama al SDK correcto. Cambiar de proveedor es solo cambiar `AI_MODEL` en el `.env`.

**Routing por categoría IA (Opción B):** El equipo responsable se asigna según la categoría detectada en el contenido del ticket, no según el tipo declarado por el cliente. Esto corrige casos donde el cliente etiqueta mal su ticket (ej: un problema de hardware etiquetado como "Billing Inquiry" se enruta correctamente a Soporte Técnico). La regla está documentada en `backend/app/knowledge_base/team_routing.json`.

**Normalización de datos en ingesta:** El cleaner corrige mojibake (caracteres corruptos), normaliza prioridades con variantes en español (baja→Low, alta→High) y numéricos (p1→Critical), limpia nombres de títulos (Mr./Mrs./PhD), unifica tipos de ticket a 5 valores canónicos y pone emails en minúsculas. Esto garantiza que la IA trabaje con datos consistentes.

**`asyncio.Semaphore(3)` + Tenacity:** El semáforo limita la concurrencia a 3 llamadas simultáneas al LLM para respetar rate limits. Tenacity reintenta solo errores transitorios (`TimeoutError`, `ConnectionError`, `OSError`), no errores de parsing de JSON. Separar `/ingest` de `/process` permite cargar datos instantáneamente y controlar cuándo corre la IA.

**Modo mock:** Permite demostrar toda la arquitectura sin gastar en una API de pago. La interfaz es idéntica al modo real: cambiar `AI_MODE=real` y añadir una key es suficiente.

**Base de conocimiento en JSON/Markdown:** Para este scope, inyectar el texto directamente en el prompt es más simple que montar una vector DB. Con más volumen de conocimiento, migraría a ChromaDB o pgvector.

**Contexto agregado para `/ask`:** En lugar de pasar tickets individuales al LLM, se construye un contexto con estadísticas precalculadas (distribuciones, cruces de dimensiones, últimos tickets atendidos, cobertura de campos). Esto evita alucinaciones por datos faltantes y permite responder preguntas estadísticas con precisión.

---

## Limitaciones conocidas

- El análisis IA corre en background — si el proceso se reinicia durante el procesamiento, los tickets pendientes quedan sin analizar hasta el próximo `POST /process` o usando el botón "Reanalizar todo".
- El dataset es estático (2020-2023); preguntas sobre "esta semana" o "hoy" no tienen datos reales.
- No hay campo de fecha de creación del ticket en el CSV, solo `First Response Time` y `Time to Resolution`. El "último ticket atendido" se determina por la fecha de primera respuesta.
- No hay autenticación en la API.
- SQLite tiene limitaciones de concurrencia en escrituras bajo carga muy alta. Cada operación abre su propia sesión para mitigarlo.
- El modo mock genera resúmenes genéricos; no analiza el texto real del ticket.

## Con más tiempo implementaría

- Cola de procesamiento persistente con Celery + Redis (sobrevive reinicios)
- Búsqueda semántica con embeddings para `/ask` (actualmente es por keywords)
- Text-to-SQL para que `/ask` genere queries dinámicas en lugar de usar agregados precalculados
- Autenticación básica con API keys
- Tests unitarios del cleaner y de los routers
- Alertas para tickets Critical sin respuesta pasado el SLA
- Exportación de la tabla a CSV

---

## Uso de IA durante el desarrollo

Este proyecto fue desarrollado usando **Claude Code** (Anthropic) como asistente principal a lo largo de toda la sesión de trabajo.

### Herramientas usadas

- **Claude Code (claude-sonnet-4-6):** Asistente principal para diseño, generación de código, debugging y validación.

### Para qué lo usé

**Diseño de arquitectura:**
Claude razonó el stack inicial, identificó el problema del `auto_ingest_on_start` llamándose por HTTP a sí mismo, y propuso la solución con `asyncio.create_task` + semáforo. También propuso la Opción B (routing por categoría IA) y explicó sus ventajas frente al routing por tipo declarado por el cliente.

**Generación y corrección de código:**
- Reescritura completa del `cleaner.py` para normalizar prioridades en español, nombres con títulos, mojibake y tipos de ticket con variantes.
- Cliente multi-proveedor sin LiteLLM que detecta el proveedor por prefijo del modelo.
- `ProcessingBanner.tsx` con botón "Reanalizar todo" de doble confirmación y auto-refresh con `useQueryClient.invalidateQueries`.
- Corrección del path de SQLite (`./tickets.db` → `./data/tickets.db`) y creación del `.dockerignore` para evitar que el archivo local se copiara al contenedor.
- Prompts de análisis con reglas explícitas de categorización y routing, y prompt de `/ask` con instrucciones anti-alucinación.

**Debugging:**
- Identificó que había dos archivos de BD (`/app/tickets.db` y `/app/data/tickets.db`) causando que la IA respondiera con datos incorrectos.
- Detectó que el retry con tenacity se aplicaba también a errores de JSON (no transitorios), causando reintentos innecesarios.
- Confirmó que las respuestas cortadas de `/ask` eran por `max_tokens=800` insuficiente.

**Validación de datos:**
Claude ejecutó queries directas contra la BD para verificar que los números que respondía el bot coincidieran con los datos reales (routing 400/400 correcto, distribución de prioridades, totales por equipo).

### Qué validé manualmente

- Lógica del cleaner contra los datos reales del CSV (casos edge de prioridades numéricas, nombres con caracteres especiales).
- Estructura de prompts para obtener JSON válido sin bloques markdown.
- Configuración de Docker Compose (healthcheck, volumen nombrado, dependencias entre servicios).
- Que las respuestas del bot en `/ask` cuadraran con los datos reales de la BD antes de aceptarlas como correctas.
- Decisión de usar Opción B (routing por contenido) vs Opción A (routing por tipo declarado).
