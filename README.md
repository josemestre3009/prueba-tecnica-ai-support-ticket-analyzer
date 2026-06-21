# AI Support Ticket Analyzer

Analizador de tickets de soporte con IA. Ingesta tickets desde un CSV, los enriquece automáticamente con categoría, prioridad, resumen, sentimiento y equipo responsable usando un LLM, y los expone a través de una API REST y un dashboard visual con búsqueda en lenguaje natural.

---

## Índice

1. [Requisitos](#requisitos)
2. [Instalación y arranque](#instalación-y-arranque)
3. [Cómo probarlo](#cómo-probarlo)
4. [Endpoints principales](#endpoints-principales)
5. [Variables de entorno](#variables-de-entorno)
6. [Arquitectura](#arquitectura)
7. [Decisiones técnicas](#decisiones-técnicas)
8. [Normalización de datos](#normalización-de-datos)
9. [Base de conocimiento](#base-de-conocimiento)
10. [Limitaciones conocidas](#limitaciones-conocidas)
11. [Con más tiempo implementaría](#con-más-tiempo-implementaría)
12. [Uso de IA durante el desarrollo](#uso-de-ia-durante-el-desarrollo)

---

## Requisitos

- [Docker](https://www.docker.com/) y Docker Compose v2
- No se requiere Python, Node ni ningún runtime local

---

## Instalación y arranque

```bash
# 1. Clonar el repositorio
git clone https://github.com/josemestre3009/prueba-tecnica-ai-support-ticket-analyzer
cd ai-support-ticket-analyzer

# 2. Configurar variables de entorno
cp .env.example .env
# El modo mock funciona sin ninguna API key — editar .env solo si se quiere IA real

# 3. Levantar
docker compose up --build
```

El backend tarda unos segundos en iniciar. Al arrancar:
- Ingesta automáticamente `backend/dataset/tickets.csv`
- Normaliza los datos (nombres, prioridades, tipos, timestamps)
- Lanza el análisis IA en background para todos los tickets

| Servicio | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API REST + Swagger | http://localhost:8000/docs |

### Cambiar el dataset

```bash
# 1. Reemplazar el CSV
cp mi-nuevo-dataset.csv backend/dataset/tickets.csv

# 2. Bajar los contenedores Y borrar el volumen de BD (obligatorio)
docker compose down -v

# 3. Volver a levantar — ingestará el nuevo CSV automáticamente
docker compose up --build
```

> El paso `down -v` es obligatorio — sin él la BD anterior permanece y el nuevo CSV no se ingesta.

**Columnas requeridas en el CSV** (nombres exactos, el orden no importa):

| Columna | Tipo | Notas |
|---|---|---|
| `Ticket ID` | Entero | Identificador único |
| `Customer Name` | Texto | Se normalizan títulos y encoding |
| `Customer Email` | Texto | Puede estar vacío |
| `Customer Age` | Entero | Rango válido 18–90; fuera de rango se ignora |
| `Customer Gender` | Texto | `Male`, `Female`, `Other` |
| `Product Purchased` | Texto | |
| `Date of Purchase` | Fecha | Formato `YYYY-MM-DD` o similar |
| `Ticket Type` | Texto | Se normaliza a 5 valores canónicos |
| `Ticket Subject` | Texto | |
| `Ticket Description` | Texto | El campo que analiza la IA |
| `Ticket Status` | Texto | `Open`, `Closed`, `Pending Customer Response` |
| `Ticket Priority` | Texto | `Critical/High/Medium/Low` o variantes en español |
| `Ticket Channel` | Texto | `Email`, `Phone`, `Chat`, `Social media` |
| `First Response Time` | Datetime | `YYYY-MM-DD HH:MM:SS` |
| `Time to Resolution` | Datetime | `YYYY-MM-DD HH:MM:SS` — puede estar vacío |
| `Customer Satisfaction Rating` | Número | 1–5; solo tickets cerrados suelen tenerlo |

Si el CSV nuevo tiene columnas con nombres distintos, editar el mapeo en `backend/app/ingestion/cleaner.py`.

### Detener el proyecto

```bash
docker compose down          # detiene, conserva la BD
docker compose down -v       # detiene y borra la BD
```

---

## Cómo probarlo

### Desde el dashboard (http://localhost:3000)

1. **Banner de procesamiento** — al iniciar aparece un banner con el progreso del análisis IA en tiempo real. Al terminar, la tabla se refresca automáticamente.
2. **KPIs** — tarjetas con total de tickets, prioridades críticas/altas, distribución por categoría y sentimiento.
3. **Gráficos** — barras de distribución por categoría, prioridad y sentimiento.
4. **Tabla de tickets** — filtros por estado, prioridad, categoría, sentimiento, canal y búsqueda por texto. Paginación de 50 por página.
5. **Chat `/ask`** — campo de texto libre para hacer preguntas en lenguaje natural sobre los tickets. El bot responde usando estadísticas reales de la BD y puede generar queries SQL de lectura cuando los datos agregados no son suficientes.
6. **Botón "Reanalizar todo"** — fuerza un re-análisis IA de todos los tickets. Requiere doble confirmación (el botón se vuelve rojo).

### Desde la API (curl)

```bash
# Ver estado del análisis IA
curl http://localhost:8000/status

# Listar tickets con filtros
curl "http://localhost:8000/tickets?priority=Critical&status=Open&page=1&page_size=20"

# Solo tickets ya procesados por IA
curl "http://localhost:8000/tickets?only_processed=true"

# KPIs agregados
curl http://localhost:8000/summary

# Pregunta en lenguaje natural
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuál es el producto con más tickets críticos?"}'

# Forzar re-análisis
curl -X POST http://localhost:8000/reprocess
```

### Preguntas de ejemplo para el chat

```
¿Cuántos tickets hay en total?
¿Cuál es el producto con peor rating promedio?
¿Qué canal tiene el tiempo de respuesta más rápido?
¿Cuántos tickets mencionan "battery" en la descripción?
¿Cuál fue el último soporte atendido?
¿Cuántos clientes mayores de 60 años tienen tickets sin resolver?
¿Qué género tiene más tickets con sentimiento Frustrated y prioridad Critical?
¿Cuántos tickets tardaron más de 4 horas en resolverse?
```

---

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servicio |
| `POST` | `/ingest` | Carga el CSV y guarda en BD (normaliza datos) |
| `POST` | `/process` | Lanza análisis IA en background |
| `POST` | `/reprocess` | Resetea flags y relanza análisis IA en todos los tickets |
| `GET` | `/status` | Progreso: procesados, pendientes, errores |
| `GET` | `/tickets` | Lista tickets con filtros y paginación |
| `GET` | `/tickets/{id}` | Detalle completo de un ticket |
| `GET` | `/summary` | KPIs agregados del dataset |
| `POST` | `/ask` | Pregunta en lenguaje natural |

### Parámetros de filtrado en `GET /tickets`

| Parámetro | Tipo | Ejemplo |
|---|---|---|
| `status` | string | `Open`, `Closed`, `Pending Customer Response` |
| `priority` | string | `Critical`, `High`, `Medium`, `Low` |
| `ai_category` | string | `Hardware`, `Software`, `Billing`, `Network`, `Cancellation`, `Product Inquiry`, `Other` |
| `ai_sentiment` | string | `Frustrated`, `Urgent`, `Neutral`, `Satisfied`, `Confused` |
| `ai_priority` | string | Prioridad sugerida por IA |
| `product` | string | Búsqueda parcial por nombre de producto |
| `channel` | string | `Email`, `Chat`, `Phone`, `Social media` |
| `search` | string | Búsqueda en asunto y descripción |
| `only_processed` | bool | `true` para ver solo los analizados por IA |
| `page` | int | Número de página (default: 1) |
| `page_size` | int | Registros por página (default: 50, máx: 200) |

### Campos enriquecidos por IA en cada ticket

| Campo | Descripción |
|---|---|
| `ai_category` | Categoría real del problema detectada en la descripción |
| `ai_priority` | Prioridad sugerida según impacto real |
| `ai_summary` | Resumen en español del problema (máx 2 oraciones) |
| `ai_sentiment` | Sentimiento del cliente |
| `ai_responsible_team` | Equipo al que debe ir el ticket |
| `ai_processed` | Si ya fue analizado por la IA |

---

## Variables de entorno

Copia `.env.example` a `.env` y edita según el proveedor que quieras usar.

| Variable | Descripción | Default |
|---|---|---|
| `AI_MODE` | `mock` (sin costo, sin API key) o `real` (llama al LLM) | `mock` |
| `AI_MODEL` | Modelo a usar — ver proveedores abajo | `mock` |
| `ANTHROPIC_API_KEY` | API key de Anthropic (Claude) | — |
| `GROQ_API_KEY` | API key de Groq | — |
| `GEMINI_API_KEY` | API key de Google Gemini | — |
| `OPENAI_API_KEY` | API key de OpenAI | — |
| `DATABASE_URL` | URL de SQLite | `sqlite:///./data/tickets.db` |
| `DATASET_PATH` | Ruta al CSV dentro del contenedor | `./dataset/tickets.csv` |
| `AUTO_INGEST_ON_START` | Ingesta automática al arrancar | `true` |

### Configuración por proveedor

```env
# Anthropic Claude (recomendado para calidad de análisis)
AI_MODE=real
AI_MODEL=claude-haiku-4-5-20251001
ANTHROPIC_API_KEY=sk-ant-...

# Groq — rápido, tiene tier gratuito
AI_MODE=real
AI_MODEL=groq/llama-3.3-70b-versatile
GROQ_API_KEY=gsk_...

# Google Gemini
AI_MODE=real
AI_MODEL=gemini/gemini-2.0-flash
GEMINI_API_KEY=AIza...

# OpenAI
AI_MODE=real
AI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

> En modo `mock` el sistema funciona completo: ingesta, normalización, dashboard, filtros y chat `/ask`. Solo los resúmenes y categorías son simulados, no se analiza el texto real del ticket.

---

## Arquitectura

```
backend/dataset/tickets.csv
        ↓
POST /ingest
        ↓
cleaner.py — normalización de datos
  · Nombres: elimina títulos (Mr./Mrs./PhD), corrige encoding
  · Prioridades: baja→Low, alta→High, p1→Critical, urgent→Critical
  · Tipos: unifica 24 variantes a 5 valores canónicos
  · Emails: minúsculas + validación básica
  · Timestamps: corrige resolution < first_response sumando 1 día
  · Productos: resuelve aliases (PlayStation → Sony PlayStation)
        ↓
SQLite /data/tickets.db  ← volumen Docker nombrado (persiste entre reinicios)
        ↓
POST /process — asyncio.Semaphore(3) + tenacity retry
        ↓
litellm_client.py — router multi-proveedor
  · claude-*  → Anthropic SDK
  · groq/*    → OpenAI SDK con base_url Groq
  · gemini/*  → OpenAI SDK con base_url Gemini
  · otros     → OpenAI SDK estándar
        ↓
Prompt de análisis → JSON: {category, priority, summary, sentiment, responsible_team}
        ↓
SQLite (tickets enriquecidos)
        ↓
FastAPI REST API
  ↕ knowledge_base/ (JSON + Markdown: SLAs, políticas, enrutamiento)
        ↓
POST /ask
  1. Ejecuta ~15 queries SQL → contexto agregado (distribuciones, cruces, cobertura)
  2. LLM responde desde el contexto
  3. Si emite <sql>...</sql> → safe_sql.py valida y ejecuta en modo read-only
  4. Segundo LLM call con los resultados → respuesta final
        ↓
Dashboard React
  · KPIs + gráficos (Recharts)
  · Tabla filtrable con paginación
  · Chat /ask con streaming de respuesta
  · Auto-refresh al terminar el análisis IA (React Query)
```

### Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, SQLite |
| IA | Cliente multi-proveedor propio, Tenacity (retry exponencial) |
| Frontend | React 18, Vite, TypeScript, TailwindCSS, Recharts, React Query |
| Infra | Docker Compose, volúmenes nombrados |

---

## Decisiones técnicas

### FastAPI sobre Django/Flask
Async nativo sin configuración extra, Swagger automático en `/docs`, Pydantic para validación de schemas. Django es excesivo para este scope; Flask requiere boilerplate adicional para async.

### SQLite sobre PostgreSQL
El dataset es local y pequeño. SQLite no requiere servidor y viaja en un archivo. Cambiar a PostgreSQL es únicamente cambiar `DATABASE_URL` en el `.env` — el resto del código (SQLAlchemy ORM) no cambia.

### Cliente multi-proveedor propio (sin LiteLLM)
En lugar de depender de la librería LiteLLM, se construyó un router de ~80 líneas que detecta el proveedor por el prefijo del modelo (`claude-*`, `groq/*`, `gemini/*`) y llama al SDK nativo correspondiente. Esto elimina una dependencia pesada manteniendo la misma flexibilidad. Cambiar de proveedor es cambiar `AI_MODEL` en `.env`.

### Routing por contenido, no por tipo declarado
El equipo responsable se asigna según la **categoría detectada por IA en el contenido del ticket**, no según el tipo declarado por el cliente. Esto corrige casos donde el cliente etiqueta mal su ticket: un "Billing Inquiry" cuya descripción habla de un fallo de hardware se categoriza como `Hardware` y va a Soporte Técnico — que es el comportamiento correcto. La regla está documentada en `backend/app/knowledge_base/team_routing.json`.

### asyncio.Semaphore(3) + Tenacity
El semáforo limita a 3 llamadas concurrentes al LLM para respetar rate limits sin serializar todo. Tenacity reintenta únicamente errores transitorios (`TimeoutError`, `ConnectionError`, `OSError`) — no reintenta errores de parsing de JSON ni de validación, que son deterministas.

### Contexto agregado para /ask (no RAG)
Para este scope, pre-calcular ~15 estadísticas SQL y pasarlas como texto al LLM es más simple, más rápido y más preciso que montar una vector DB. El LLM lee distribuciones reales y no puede inventar números. Con volumen mayor de datos o base de conocimiento más extensa, migraría a ChromaDB o pgvector.

### Fallback Text-to-SQL seguro
Cuando las estadísticas precalculadas no son suficientes (ej: "¿cuántos clientes mayores de 60 tienen tickets abiertos?"), el LLM emite `<sql>SELECT...</sql>`. El módulo `safe_sql.py` valida que sea solo `SELECT`, sin múltiples sentencias, sin palabras clave de escritura, y ejecuta contra SQLite en modo read-only a nivel de URI (`file:path?mode=ro`). El resultado vuelve al LLM para formatear la respuesta final.

### Modo mock
Permite demostrar toda la arquitectura sin gastar en APIs de pago. La interfaz del cliente IA es idéntica en modo mock y real: `AI_MODE=real` + API key es suficiente para activar el LLM real.

---

## Normalización de datos

El CSV original tiene inconsistencias. El módulo `backend/app/ingestion/cleaner.py` las resuelve en ingesta:

| Campo | Problema original | Corrección |
|---|---|---|
| `Customer Name` | Títulos (`Mr.`, `Mrs.`, `PhD`), CAPS, encoding roto | Elimina títulos, Title Case, fix mojibake |
| `Ticket Priority` | `baja`, `alta`, `p1`, `urgent`, `1`, `HIGH` | Normaliza a `Low/Medium/High/Critical` |
| `Ticket Type` | 24+ variantes distintas | Unifica a 5 valores canónicos |
| `Customer Email` | Mayúsculas, formatos inválidos | Minúsculas, valida presencia de `@` y `.` |
| `Customer Age` | Edades fuera de rango (0, 150) | Acepta solo 18-90 |
| `Product Purchased` | `PlayStation`, `MacBook` sin marca | Resuelve aliases a nombre completo |
| `First/Time to Resolution` | 68 registros con `resolution < first_response` | Suma 1 día a `time_to_resolution` |
| Encoding | Caracteres Latin-1 leídos como UTF-8 (`Ã¡` → `á`) | `encode('latin-1').decode('utf-8')` |

---

## Base de conocimiento

Ubicada en `backend/app/knowledge_base/`. Se inyecta completa en el prompt de `/ask`.

| Archivo | Contenido |
|---|---|
| `policies.json` | SLAs por prioridad (tiempos de respuesta y resolución), reglas de escalación, objetivos de satisfacción |
| `team_routing.json` | Criterio de enrutamiento por categoría IA (no por tipo declarado), tabla de equipos y horarios, reglas especiales (reembolsos >$500, escalación legal) |
| `product_catalog.md` | Categorías de productos y equipos que los soportan |

---

## Limitaciones conocidas

- **Sin fecha de creación del ticket** — el CSV no incluye cuándo se abrió cada ticket, solo cuándo se respondió y resolvió. El "último ticket atendido" se determina por `first_response_time`.
- **Dataset estático (2020-2023)** — preguntas sobre "hoy" o "esta semana" se responden en contexto del dataset histórico, no de datos en tiempo real. El bot conoce la fecha actual de Colombia pero la usa solo para contexto.
- **Procesamiento no persistente** — el análisis IA corre en background con `asyncio`. Si el contenedor se reinicia durante el procesamiento, los tickets pendientes quedan sin analizar hasta el próximo `POST /process` o el botón "Reanalizar todo".
- **Sin autenticación** — la API es pública. No hay API keys ni roles.
- **SQLite bajo carga alta** — SQLite tiene limitaciones de concurrencia en escrituras. Cada operación usa su propia sesión para mitigarlo, pero bajo carga muy alta habría contención. PostgreSQL resuelve esto.
- **Modo mock sin análisis real** — el modo mock detecta keywords básicas pero no entiende el texto del ticket. Las categorías y resúmenes son aproximados.

---

## Con más tiempo implementaría

1. **Cola persistente con Celery + Redis** — el procesamiento IA sobreviviría reinicios del contenedor.
2. **Tests automatizados** — unitarios del cleaner (casos edge de normalización) y de integración de los endpoints.
3. **Autenticación básica** — API keys por equipo para separar accesos.
4. **Alertas de SLA** — notificación cuando un ticket Critical lleva más de 1 hora sin primera respuesta.
5. **Exportación a CSV** — botón en el dashboard para descargar la tabla filtrada.
6. **Streaming en /ask** — respuestas en tiempo real en lugar de esperar el texto completo.
7. **Migración a PostgreSQL** — para entornos de producción con múltiples usuarios concurrentes.

---

## Uso de IA durante el desarrollo

Este proyecto fue desarrollado usando **Claude Code** (claude-opus-4-8, Anthropic) como asistente principal durante toda la sesión de trabajo.

### Herramientas usadas

- **Claude Code** — asistente de terminal integrado en el editor (VSCode). Acceso a todos los archivos del proyecto, ejecución de comandos bash, lectura de logs y salida de Docker.
- **Gemini** — usado para verificar el plan técnico propuesto y obtener un segundo punto de vista sobre las decisiones de arquitectura, lo que permitió refinar el enfoque antes de implementar.

### Para qué lo usé

**Diseño de arquitectura:**
Claude propuso el stack inicial (FastAPI + SQLite + React), la separación `/ingest` / `/process`, el uso de `asyncio.Semaphore` + tenacity para el procesamiento batch, y el modo mock para desarrollar sin gastar en APIs.

**Generación de código base:**
Los archivos iniciales del proyecto fueron generados con Claude: modelos SQLAlchemy, schemas Pydantic, routers FastAPI, componentes React, Docker Compose con healthcheck y volúmenes nombrados.

**Decisiones de producto:**
- Propuso y argumentó el **routing por categoría IA** (en lugar de usar el tipo declarado por el cliente), explicando por qué el tipo declarado es poco fiable y puede estar equivocado.
- Diseñó el sistema de **contexto agregado** para `/ask` (pre-calcular estadísticas SQL en lugar de pasar tickets individuales), y el **fallback Text-to-SQL** con validación de seguridad.

**Normalización de datos:**
Identificó todos los casos edge del CSV (24 variantes de Ticket Type, prioridades en español, mojibake, timestamps negativos) y reescribió `cleaner.py` para cubrirlos.

### Qué validé manualmente

- Que la lógica del cleaner producía los datos esperados (revisé el CSV original vs BD directamente).
- Que los prompts generaban JSON válido sin bloques markdown (probé contra la API real).
- La configuración de Docker Compose (healthcheck, dependencias entre servicios, volúmenes).
- Las decisiones de producto: elegí routing por categoría IA en lugar de routing por tipo declarado, después de entender por qué el tipo declarado por el cliente no es confiable.
- Que los números que respondía el bot cuadraban con la BD real antes de aceptarlos como correctos.

### Archivos de prompts reutilizables

Los prompts del sistema están en `backend/app/ai/prompts.py`:
- `ANALYZE_TICKET_PROMPT` — prompt de análisis individual de tickets (4 reglas explícitas: categoría, equipo, prioridad, resumen)
- `ASK_PROMPT` — prompt del chat con instrucciones de concisión, anti-alucinación, fallback SQL y schema de la BD
