# Plan de Desarrollo — AI Support Ticket Analyzer

## Índice
1. [Visión general](#1-visión-general)
2. [Stack tecnológico](#2-stack-tecnológico)
3. [Estructura del proyecto](#3-estructura-del-proyecto)
4. [Variables de entorno](#4-variables-de-entorno)
5. [Paso 1 — Análisis y limpieza de datos](#5-paso-1--análisis-y-limpieza-de-datos)
6. [Paso 2 — Base de datos](#6-paso-2--base-de-datos)
7. [Paso 3 — Servicio de IA (agnóstico de proveedor)](#7-paso-3--servicio-de-ia-agnóstico-de-proveedor)
8. [Paso 4 — Base de conocimiento](#8-paso-4--base-de-conocimiento)
9. [Paso 5 — API REST con FastAPI](#9-paso-5--api-rest-con-fastapi)
10. [Paso 6 — Dashboard con React](#10-paso-6--dashboard-con-react)
11. [Paso 7 — Docker Compose](#11-paso-7--docker-compose)
12. [Paso 8 — README y entregables](#12-paso-8--readme-y-entregables)
13. [Orden de trabajo en 1 día](#13-orden-de-trabajo-en-1-día)
14. [Decisiones técnicas y trade-offs](#14-decisiones-técnicas-y-trade-offs)

---

## 1. Visión general

El objetivo es construir un sistema que tome el archivo `tickets.csv`, lo limpie, lo procese con IA para enriquecer cada ticket con categoría, prioridad, resumen, sentimiento y equipo responsable, y exponga esos resultados a través de una API REST y un dashboard visual.

El sistema debe poder responder preguntas en lenguaje natural sobre los tickets, apoyándose en el contenido del CSV y en una base de conocimiento con políticas, SLAs y reglas de enrutamiento.

**Flujo principal:**

```
tickets.csv
    ↓
Ingesta + Limpieza
    ↓
SQLite (tickets limpios)
    ↓
Análisis IA por ticket
    ↓
SQLite (tickets enriquecidos)
    ↓
API FastAPI  ←→  Base de conocimiento
    ↓
Dashboard React
```

---

## 2. Stack tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| **Backend / API** | Python 3.12 + FastAPI | Rápido de escribir, async nativo, documentación automática con Swagger, ideal para pipelines de IA |
| **Base de datos** | SQLite + SQLAlchemy | Sin servidor, cero configuración, más que suficiente para este volumen de datos, portable en un solo archivo |
| **IA — interfaz unificada** | LiteLLM | Una sola interfaz para Claude, Groq, Gemini, OpenAI o cualquier proveedor; cambiar de LLM es solo cambiar una variable de entorno |
| **IA — proveedor por defecto** | Anthropic Claude (`claude-haiku-4-5`) | Rápido y barato para análisis en batch; fácil de cambiar por Groq o Gemini sin tocar código |
| **Base de conocimiento** | JSON + Markdown | Simple, legible, sin dependencias extra; los archivos se inyectan como contexto en los prompts |
| **Frontend** | React 18 + Vite + TypeScript | Setup rápido, ecosistema maduro, DX excelente |
| **Gráficos** | Recharts | Declarativo, integra bien con React, suficiente para los KPIs requeridos |
| **Estilos** | TailwindCSS | Clases utilitarias = UI decente sin escribir CSS custom |
| **HTTP Client (frontend)** | Axios + React Query | Cache de peticiones, estados de carga/error automáticos |
| **Containerización** | Docker + Docker Compose | Un comando para levantar todo el proyecto |
| **Variables de entorno** | python-dotenv (backend) / Vite env (frontend) | Separación segura de configuración y secretos |

### Proveedores de IA compatibles (sin cambiar código)

```env
# Anthropic
AI_MODEL=claude-haiku-4-5-20251001
ANTHROPIC_API_KEY=sk-ant-...

# Groq (muy rápido, tier gratuito generoso)
AI_MODEL=groq/llama-3.3-70b-versatile
GROQ_API_KEY=gsk_...

# Google Gemini
AI_MODEL=gemini/gemini-2.0-flash
GEMINI_API_KEY=...

# OpenAI
AI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...

# Sin costo (modo demo)
AI_MODEL=mock
```

---

## 3. Estructura del proyecto

```
ai-support-ticket-analyzer/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Entrada FastAPI, registro de routers
│   │   ├── config.py            # Settings desde .env con pydantic-settings
│   │   ├── database.py          # Conexión SQLite, sesión SQLAlchemy
│   │   ├── models.py            # Tabla tickets (ORM)
│   │   ├── schemas.py           # Schemas Pydantic para request/response
│   │   │
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── reader.py        # Leer y parsear el CSV
│   │   │   └── cleaner.py       # Normalizar y validar los datos
│   │   │
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── service.py       # Orquestador: procesa tickets en batch
│   │   │   ├── prompts.py       # Templates de prompts para el LLM
│   │   │   ├── litellm_client.py# Wrapper de LiteLLM (modo real)
│   │   │   └── mock_client.py   # Respuestas simuladas (modo mock)
│   │   │
│   │   ├── knowledge_base/
│   │   │   ├── policies.json    # SLAs y políticas de soporte
│   │   │   ├── team_routing.json# Reglas de enrutamiento por tipo de ticket
│   │   │   └── data_schema.md   # Copia del diccionario-de-datos.md
│   │   │
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── ingest.py        # POST /ingest (solo lectura y guardado del CSV)
│   │       ├── process.py       # POST /process, GET /status (análisis IA con control de flujo)
│   │       ├── tickets.py       # GET /tickets, GET /tickets/{id}
│   │       ├── summary.py       # GET /summary
│   │       └── ask.py           # POST /ask
│   │
│   ├── dataset/
│   │   ├── tickets.csv
│   │   └── diccionario-de-datos.md
│   │
│   ├── tickets.db               # Generado en runtime (gitignored)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env                     # Gitignored
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   └── client.ts        # Axios instance + funciones de cada endpoint
│   │   ├── components/
│   │   │   ├── KPICards.tsx     # Tarjetas de métricas principales
│   │   │   ├── TicketsTable.tsx # Tabla con filtros
│   │   │   ├── Charts.tsx       # Barras y dona con Recharts
│   │   │   └── AskBar.tsx       # Input de preguntas en lenguaje natural
│   │   ├── hooks/
│   │   │   └── useTickets.ts    # React Query hooks
│   │   └── types/
│   │       └── ticket.ts        # Tipos TypeScript
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
│
├── .env                         # Gitignored — variables reales
├── .env.example                 # Commiteado — plantilla sin valores
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

## 4. Variables de entorno

### `.env.example` (commiteado al repo)

```env
# ── IA ──────────────────────────────────────────────────────────────────────
# Proveedor por defecto: "mock" no requiere API key
# Cambia el modelo y agrega la key del proveedor que quieras usar
AI_MODE=mock
AI_MODEL=claude-haiku-4-5-20251001

# Descomenta según el proveedor que uses:
# ANTHROPIC_API_KEY=your_key_here
# GROQ_API_KEY=your_key_here
# GEMINI_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here

# ── Backend ──────────────────────────────────────────────────────────────────
DATABASE_URL=sqlite:///./tickets.db
DATASET_PATH=./dataset/tickets.csv
AUTO_INGEST_ON_START=true   # Ingesta automática si la DB está vacía

# ── Frontend ─────────────────────────────────────────────────────────────────
VITE_API_URL=http://localhost:8000
```

### `backend/app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ai_mode: str = "mock"           # "real" | "mock"
    ai_model: str = "mock"
    database_url: str = "sqlite:///./tickets.db"
    dataset_path: str = "./dataset/tickets.csv"
    auto_ingest_on_start: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 5. Paso 1 — Análisis y limpieza de datos

### Problemas conocidos en `tickets.csv`

Observados en el dataset real:

| Problema | Ejemplo | Solución |
|---|---|---|
| Emails en mayúsculas | `MARIE76@EXAMPLE.COM` | `.lower().strip()` |
| Fechas en formato distinto | `19 de diciembre 2020` vs `2021-07-19` | `dateutil.parser.parse()` |
| Prioridades con espacios extra | ` Critical ` | `.strip().title()` |
| Prioridades en minúscula | `medium` | `.strip().title()` → `Medium` |
| Tipos de ticket con espacios | ` product inquiry ` | `.strip().title()` |
| Placeholders sin resolver | `{error_message}`, `{product_for_all}` | Detectar con regex, marcar campo `has_template_placeholders=True` |
| Ticket IDs duplicados | Mismo ID, datos distintos | Conservar el registro más reciente |
| Edad fuera de rango | `-5`, `200` | Guardar como `None` |
| Campos vacíos esperados | `First Response Time` en tickets abiertos | Aceptar `None`, es comportamiento normal según el diccionario |
| `Customer Satisfaction Rating` en abiertos | Rating presente en ticket `Open` | Ignorar y guardar como `None` |

### `backend/app/ingestion/cleaner.py`

```python
import re
from datetime import datetime
from dateutil import parser as dateparser

VALID_PRIORITIES   = {"Low", "Medium", "High", "Critical"}
VALID_STATUSES     = {"Open", "Pending Customer Response", "Closed"}
VALID_CHANNELS     = {"Email", "Phone", "Chat", "Social media"}
TEMPLATE_REGEX     = re.compile(r"\{[^}]+\}")

def clean_ticket(raw: dict) -> dict:
    ticket = {}

    # IDs
    ticket["ticket_id"] = int(raw.get("Ticket ID", 0))

    # Texto libre — solo strip
    ticket["customer_name"]        = (raw.get("Customer Name") or "").strip() or None
    ticket["ticket_subject"]       = (raw.get("Ticket Subject") or "").strip() or None
    ticket["ticket_description"]   = (raw.get("Ticket Description") or "").strip() or None
    ticket["product_purchased"]    = (raw.get("Product Purchased") or "").strip() or None

    # Email → minúsculas
    email = (raw.get("Customer Email") or "").strip().lower()
    ticket["customer_email"] = email if "@" in email else None

    # Edad → validar rango
    try:
        age = int(float(raw.get("Customer Age", 0)))
        ticket["customer_age"] = age if 18 <= age <= 90 else None
    except (ValueError, TypeError):
        ticket["customer_age"] = None

    # Género → normalizar
    gender = (raw.get("Customer Gender") or "").strip().title()
    ticket["customer_gender"] = gender if gender in {"Male", "Female", "Other"} else None

    # Fecha de compra → parsear formatos mixtos
    date_raw = raw.get("Date of Purchase", "")
    try:
        ticket["date_of_purchase"] = dateparser.parse(str(date_raw)).date()
    except Exception:
        ticket["date_of_purchase"] = None

    # Prioridad y estado → strip + title
    priority = (raw.get("Ticket Priority") or "").strip().title()
    ticket["ticket_priority"] = priority if priority in VALID_PRIORITIES else None

    status = (raw.get("Ticket Status") or "").strip().title()
    # Manejar "Pending Customer Response" que puede venir partido
    if "Pending" in status:
        status = "Pending Customer Response"
    ticket["ticket_status"] = status if status in VALID_STATUSES else None

    # Tipo y canal
    ticket_type = (raw.get("Ticket Type") or "").strip().title()
    ticket["ticket_type"] = ticket_type or None

    channel = (raw.get("Ticket Channel") or "").strip().title()
    ticket["ticket_channel"] = channel if channel in VALID_CHANNELS else None

    # Timestamps — solo para tickets con respuesta/cierre
    for field, key in [
        ("First Response Time",  "first_response_time"),
        ("Time to Resolution",   "time_to_resolution"),
    ]:
        raw_val = raw.get(field, "")
        try:
            ticket[key] = dateparser.parse(str(raw_val)) if raw_val else None
        except Exception:
            ticket[key] = None

    # Rating — solo válido en tickets cerrados
    try:
        rating = float(raw.get("Customer Satisfaction Rating", ""))
        ticket["satisfaction_rating"] = rating if 1 <= rating <= 5 else None
    except (ValueError, TypeError):
        ticket["satisfaction_rating"] = None

    # Flag para descripciones con placeholders sin resolver
    desc = ticket.get("ticket_description") or ""
    ticket["has_template_placeholders"] = bool(TEMPLATE_REGEX.search(desc))

    return ticket
```

### `backend/app/ingestion/reader.py`

```python
import csv
from .cleaner import clean_ticket

def read_csv(path: str) -> list[dict]:
    tickets = []
    seen_ids = {}

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = clean_ticket(row)
            tid = cleaned["ticket_id"]
            # En caso de duplicados, conservar el último
            seen_ids[tid] = cleaned

    return list(seen_ids.values())
```

---

## 6. Paso 2 — Base de datos

### `backend/app/models.py`

```python
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text
from .database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    # ── Campos originales (limpios) ──────────────────────────────────────────
    id                       = Column(Integer, primary_key=True, index=True)
    ticket_id                = Column(Integer, unique=True, index=True)
    customer_name            = Column(String)
    customer_email           = Column(String)
    customer_age             = Column(Integer, nullable=True)
    customer_gender          = Column(String, nullable=True)
    product_purchased        = Column(String, nullable=True)
    date_of_purchase         = Column(Date, nullable=True)
    ticket_type              = Column(String, nullable=True)
    ticket_subject           = Column(String, nullable=True)
    ticket_description       = Column(Text, nullable=True)
    ticket_status            = Column(String, nullable=True)
    ticket_priority          = Column(String, nullable=True)
    ticket_channel           = Column(String, nullable=True)
    first_response_time      = Column(DateTime, nullable=True)
    time_to_resolution       = Column(DateTime, nullable=True)
    satisfaction_rating      = Column(Float, nullable=True)
    has_template_placeholders = Column(Boolean, default=False)

    # ── Campos enriquecidos por IA ───────────────────────────────────────────
    ai_category              = Column(String, nullable=True)
    ai_priority              = Column(String, nullable=True)
    ai_summary               = Column(Text, nullable=True)
    ai_sentiment             = Column(String, nullable=True)
    ai_responsible_team      = Column(String, nullable=True)
    ai_processed             = Column(Boolean, default=False)
    ai_processed_at          = Column(DateTime, nullable=True)
    ai_error                 = Column(Text, nullable=True)  # Log de error si el análisis falló
```

### `backend/app/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # Necesario para SQLite en FastAPI async
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 7. Paso 3 — Servicio de IA (agnóstico de proveedor)

### Arquitectura del servicio de IA

```
ai/service.py
    ├── Si AI_MODE=mock → mock_client.py  (reglas basadas en keywords)
    └── Si AI_MODE=real → litellm_client.py → cualquier proveedor via LiteLLM
```

### `backend/app/ai/prompts.py`

```python
ANALYZE_TICKET_PROMPT = """
Eres un asistente especializado en análisis de tickets de soporte técnico.

Analiza el siguiente ticket y responde ÚNICAMENTE con un objeto JSON válido, 
sin texto adicional ni bloques de código markdown.

### Ticket a analizar:
- Tipo: {ticket_type}
- Asunto: {ticket_subject}
- Producto: {product_purchased}
- Descripción: {ticket_description}
- Estado actual: {ticket_status}
- Prioridad asignada: {ticket_priority}

### Responde con exactamente este JSON:
{{
  "category": "<categoría concisa, ej: Hardware, Software, Facturación, Cancelación, Consulta>",
  "priority": "<Low | Medium | High | Critical>",
  "summary": "<resumen del problema en máximo 2 oraciones>",
  "sentiment": "<Neutral | Frustrated | Urgent | Satisfied | Confused>",
  "responsible_team": "<Soporte Técnico | Facturación | Retención | Producto | Otro>"
}}
"""

ASK_PROMPT = """
Eres un asistente de análisis de tickets de soporte. 
Responde la pregunta del usuario basándote en los tickets y políticas proporcionados.

### Base de conocimiento (políticas y SLAs):
{knowledge_base}

### Tickets relevantes (muestra):
{tickets_context}

### Pregunta del usuario:
{question}

Responde de forma clara y concisa. Si necesitas hacer referencia a tickets específicos, 
menciona su ID. Si la información no está disponible en el contexto, dilo explícitamente.
"""
```

### `backend/app/ai/litellm_client.py`

```python
import json
from litellm import acompletion
from ..config import settings
from .prompts import ANALYZE_TICKET_PROMPT, ASK_PROMPT

async def analyze_ticket(ticket_data: dict) -> dict:
    prompt = ANALYZE_TICKET_PROMPT.format(**ticket_data)
    
    response = await acompletion(
        model=settings.ai_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,  # Baja temperatura para respuestas consistentes
        max_tokens=300,
    )
    
    return json.loads(response.choices[0].message.content)

async def ask_question(question: str, knowledge_base: str, tickets_context: str) -> str:
    prompt = ASK_PROMPT.format(
        knowledge_base=knowledge_base,
        tickets_context=tickets_context,
        question=question,
    )
    
    response = await acompletion(
        model=settings.ai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800,
    )
    
    return response.choices[0].message.content
```

### `backend/app/ai/mock_client.py`

Implementa las mismas funciones que `litellm_client.py` pero con lógica basada en reglas, sin llamadas externas.

```python
import re

KEYWORD_CATEGORIES = {
    "Hardware":     ["hardware", "device", "screen", "keyboard", "battery", "physical"],
    "Software":     ["software", "bug", "error", "crash", "app", "install", "update"],
    "Facturación":  ["billing", "charge", "invoice", "payment", "refund"],
    "Cancelación":  ["cancel", "cancellation", "unsubscribe", "terminate"],
    "Consulta":     ["inquiry", "question", "how to", "guide", "information"],
}

SENTIMENT_KEYWORDS = {
    "Urgent":      ["urgent", "asap", "immediately", "critical", "emergency"],
    "Frustrated":  ["frustrated", "disappointed", "terrible", "worst", "angry", "unacceptable"],
    "Satisfied":   ["thank", "great", "excellent", "love", "amazing"],
}

TEAM_BY_TYPE = {
    "Technical issue":     "Soporte Técnico",
    "Billing inquiry":     "Facturación",
    "Refund request":      "Facturación",
    "Cancellation request":"Retención",
    "Product inquiry":     "Producto",
}

def _detect_category(text: str) -> str:
    text_lower = text.lower()
    for category, keywords in KEYWORD_CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return "General"

def _detect_sentiment(text: str) -> str:
    text_lower = text.lower()
    for sentiment, keywords in SENTIMENT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return sentiment
    return "Neutral"

async def analyze_ticket(ticket_data: dict) -> dict:
    desc    = ticket_data.get("ticket_description", "")
    t_type  = ticket_data.get("ticket_type", "")
    priority = ticket_data.get("ticket_priority") or "Medium"

    return {
        "category":         _detect_category(desc),
        "priority":         priority,
        "summary":          f"[MOCK] Ticket sobre {t_type.lower()} relacionado con {ticket_data.get('product_purchased', 'un producto')}.",
        "sentiment":        _detect_sentiment(desc),
        "responsible_team": TEAM_BY_TYPE.get(t_type, "Soporte Técnico"),
    }

async def ask_question(question: str, knowledge_base: str, tickets_context: str) -> str:
    return (
        f"[MODO MOCK] Respuesta simulada para: '{question}'\n\n"
        "Esta respuesta es generada sin un LLM real. "
        "Configura AI_MODE=real y una API key válida para obtener respuestas reales."
    )
```

### `backend/app/ai/service.py`

```python
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from ..models import Ticket
from ..config import settings

# Selección dinámica del cliente según AI_MODE
if settings.ai_mode == "real":
    from .litellm_client import analyze_ticket as _analyze, ask_question as _ask
else:
    from .mock_client import analyze_ticket as _analyze, ask_question as _ask

# Máximo 3 llamadas concurrentes a la IA — evita saturar el rate limit del proveedor
_semaphore = asyncio.Semaphore(3)

# Flag global para saber si hay un procesamiento en curso (evita ejecuciones paralelas)
_processing = False

async def process_tickets_batch():
    """
    Procesa todos los tickets no analizados.
    Usa un semáforo para limitar la concurrencia y tenacity para reintentos
    con backoff exponencial ante errores de rate limiting (HTTP 429).
    """
    global _processing
    if _processing:
        return  # Ya hay un procesamiento en curso, no lanzar otro

    _processing = True
    try:
        from ..database import SessionLocal
        db = SessionLocal()
        try:
            unprocessed = db.query(Ticket).filter(Ticket.ai_processed == False).all()
            tasks = [_process_single(ticket.id) for ticket in unprocessed]
            await asyncio.gather(*tasks)
        finally:
            db.close()
    finally:
        _processing = False

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def _call_ai_with_retry(ticket_data: dict) -> dict:
    """Llama a la IA con reintentos y backoff exponencial ante fallos o rate limits."""
    async with _semaphore:
        return await _analyze(ticket_data)

async def _process_single(ticket_db_id: int):
    """Procesa un ticket individual. Usa su propio contexto de DB para thread-safety."""
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_db_id).first()
        if not ticket:
            return

        result = await _call_ai_with_retry({
            "ticket_type":        ticket.ticket_type or "",
            "ticket_subject":     ticket.ticket_subject or "",
            "ticket_description": ticket.ticket_description or "",
            "product_purchased":  ticket.product_purchased or "",
            "ticket_status":      ticket.ticket_status or "",
            "ticket_priority":    ticket.ticket_priority or "",
        })

        ticket.ai_category         = result.get("category")
        ticket.ai_priority         = result.get("priority")
        ticket.ai_summary          = result.get("summary")
        ticket.ai_sentiment        = result.get("sentiment")
        ticket.ai_responsible_team = result.get("responsible_team")
        ticket.ai_processed        = True
        ticket.ai_processed_at     = datetime.utcnow()
        ticket.ai_error            = None

    except Exception as e:
        # Después de 3 reintentos fallidos: marcar con error y continuar
        # Se puede reintentar manualmente con POST /process
        ticket.ai_error       = str(e)
        ticket.ai_processed   = False  # Dejar en False para permitir reintento manual
        ticket.ai_processed_at = datetime.utcnow()

    finally:
        db.commit()
        db.close()

    db.commit()

async def answer_question(question: str, db: Session) -> str:
    """Responde una pregunta en lenguaje natural usando tickets + base de conocimiento."""
    import json, os

    # Cargar base de conocimiento
    kb_path = os.path.join(os.path.dirname(__file__), "../knowledge_base")
    with open(f"{kb_path}/policies.json") as f:
        policies = json.load(f)
    with open(f"{kb_path}/team_routing.json") as f:
        routing = json.load(f)
    with open(f"{kb_path}/data_schema.md") as f:
        schema = f.read()

    knowledge_base = (
        f"### Políticas SLA:\n{json.dumps(policies, ensure_ascii=False, indent=2)}\n\n"
        f"### Enrutamiento de equipos:\n{json.dumps(routing, ensure_ascii=False, indent=2)}\n\n"
        f"### Esquema de datos:\n{schema}"
    )

    # Filtrar tickets relevantes con búsqueda por keywords de la pregunta
    words = [w.lower() for w in question.split() if len(w) > 3]
    tickets = db.query(Ticket).filter(Ticket.ai_processed == True).limit(200).all()

    relevant = []
    for t in tickets:
        desc = (t.ticket_description or "").lower()
        if any(w in desc for w in words) or not words:
            relevant.append(t)
        if len(relevant) >= 20:
            break

    tickets_context = "\n".join([
        f"- [ID {t.ticket_id}] {t.ticket_subject} | {t.product_purchased} | "
        f"Prioridad: {t.ai_priority} | Sentimiento: {t.ai_sentiment} | "
        f"Equipo: {t.ai_responsible_team} | Resumen: {t.ai_summary}"
        for t in relevant
    ])

    return await _ask(question, knowledge_base, tickets_context)
```

---

## 8. Paso 4 — Base de conocimiento

### `backend/app/knowledge_base/policies.json`

```json
{
  "slas": {
    "Critical": {
      "primera_respuesta": "1 hora",
      "resolucion": "4 horas",
      "descripcion": "Problemas que impiden completamente el uso del producto o generan pérdida económica"
    },
    "High": {
      "primera_respuesta": "4 horas",
      "resolucion": "24 horas",
      "descripcion": "Funcionalidades importantes afectadas, workaround disponible"
    },
    "Medium": {
      "primera_respuesta": "8 horas",
      "resolucion": "48 horas",
      "descripcion": "Problemas que no bloquean el uso principal del producto"
    },
    "Low": {
      "primera_respuesta": "24 horas",
      "resolucion": "5 días hábiles",
      "descripcion": "Consultas, solicitudes de información, mejoras menores"
    }
  },
  "escalation": {
    "regla": "Tickets Critical sin primera respuesta en 30 minutos → escalar al líder de turno",
    "contacto": "El equipo de guardia recibe alertas automáticas"
  },
  "satisfaccion": {
    "escala": "1 (muy insatisfecho) a 5 (muy satisfecho)",
    "objetivo": "Promedio ≥ 4.0 mensual",
    "nota": "Solo se recopila al cerrar el ticket"
  }
}
```

### `backend/app/knowledge_base/team_routing.json`

```json
{
  "por_tipo": {
    "Technical issue":     "Soporte Técnico",
    "Billing inquiry":     "Facturación",
    "Refund request":      "Facturación",
    "Cancellation request":"Retención",
    "Product inquiry":     "Producto"
  },
  "por_canal": {
    "Social media": "El equipo de Social debe responder en máximo 2h independientemente de la prioridad",
    "Chat":         "Respuesta inmediata esperada durante horario de oficina",
    "Email":        "Aplican SLAs estándar",
    "Phone":        "Aplican SLAs estándar"
  },
  "equipos": {
    "Soporte Técnico": "Bugs, errores, problemas de instalación, fallos de hardware/software",
    "Facturación":     "Cargos incorrectos, facturas, reembolsos, métodos de pago",
    "Retención":       "Cancelaciones, downgrades, clientes en riesgo de churn",
    "Producto":        "Consultas sobre funcionalidades, roadmap, cómo usar el producto"
  }
}
```

### `backend/app/knowledge_base/data_schema.md`

Copiar el contenido de `diccionario-de-datos.md` aquí. El LLM lo usará para entender los campos cuando responda preguntas sobre el dataset.

---

## 9. Paso 5 — API REST con FastAPI

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servicio, modo IA y conteo de tickets |
| `POST` | `/ingest` | Lee el CSV, limpia y guarda en DB — **no** dispara la IA |
| `POST` | `/process` | Lanza el análisis IA con semáforo y retry (control de flujo) |
| `GET` | `/status` | Progreso del análisis: cuántos procesados, pendientes y con error |
| `GET` | `/tickets` | Lista tickets con filtros y paginación |
| `GET` | `/tickets/{id}` | Detalle de un ticket |
| `GET` | `/summary` | KPIs y métricas agregadas |
| `POST` | `/ask` | Pregunta en lenguaje natural |

> **Por qué separar `/ingest` de `/process`:** permite cargar los datos instantáneamente y decidir cuándo lanzar el análisis IA — que puede tardar minutos si hay cientos de tickets. El usuario puede ver el progreso con `/status` sin bloquear la API.

### `backend/app/routers/ingest.py`

Solo lee el CSV y persiste en DB. No toca la IA — eso es responsabilidad de `/process`.

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Ticket
from ..ingestion.reader import read_csv
from ..config import settings

router = APIRouter()

@router.post("/ingest")
def ingest_tickets(db: Session = Depends(get_db)):
    tickets_data = read_csv(settings.dataset_path)

    inserted = 0
    for data in tickets_data:
        existing = db.query(Ticket).filter(Ticket.ticket_id == data["ticket_id"]).first()
        if not existing:
            db.add(Ticket(**data))
            inserted += 1
    db.commit()

    total     = db.query(Ticket).count()
    pending   = db.query(Ticket).filter(Ticket.ai_processed == False).count()
    return {
        "message":             "Ingesta completada. Llama a POST /process para iniciar el análisis IA.",
        "tickets_insertados":  inserted,
        "total_en_db":         total,
        "pendientes_de_ia":    pending,
    }
```

### `backend/app/routers/process.py`

Lanza el análisis IA con control de concurrencia y expone el progreso.

```python
import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Ticket
from ..ai import service as ai_service

router = APIRouter()

@router.post("/process")
async def process_tickets(db: Session = Depends(get_db)):
    pending = db.query(Ticket).filter(Ticket.ai_processed == False).count()
    if pending == 0:
        return {"message": "No hay tickets pendientes de análisis."}

    # Lanzar como tarea asyncio independiente — no bloquea la respuesta HTTP
    asyncio.create_task(ai_service.process_tickets_batch())

    return {
        "message":   f"Análisis IA iniciado para {pending} tickets.",
        "pendientes": pending,
        "tip":        "Consulta GET /status para ver el progreso.",
    }

@router.get("/status")
def processing_status(db: Session = Depends(get_db)):
    total     = db.query(Ticket).count()
    processed = db.query(Ticket).filter(
        Ticket.ai_processed == True, Ticket.ai_error == None
    ).count()
    with_error = db.query(Ticket).filter(Ticket.ai_error != None).count()
    pending   = db.query(Ticket).filter(Ticket.ai_processed == False).count()

    return {
        "total":          total,
        "procesados_ok":  processed,
        "con_error":      with_error,
        "pendientes":     pending,
        "en_curso":       ai_service._processing,
        "progreso_pct":   round((processed / total) * 100, 1) if total else 0,
    }
```

### `backend/app/routers/tickets.py`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Ticket

router = APIRouter()

@router.get("/tickets")
def list_tickets(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str = None,
    priority: str = None,
    ai_category: str = None,
    ai_sentiment: str = None,
    product: str = None,
    search: str = None,
):
    query = db.query(Ticket)

    if status:       query = query.filter(Ticket.ticket_status == status)
    if priority:     query = query.filter(Ticket.ticket_priority == priority)
    if ai_category:  query = query.filter(Ticket.ai_category == ai_category)
    if ai_sentiment: query = query.filter(Ticket.ai_sentiment == ai_sentiment)
    if product:      query = query.filter(Ticket.product_purchased.ilike(f"%{product}%"))
    if search:       query = query.filter(Ticket.ticket_description.ilike(f"%{search}%"))

    total = query.count()
    tickets = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": tickets,
    }

@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket
```

### `backend/app/routers/summary.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Ticket

router = APIRouter()

@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    total = db.query(Ticket).count()
    processed = db.query(Ticket).filter(Ticket.ai_processed == True).count()

    # Distribución por prioridad original
    by_priority = dict(db.query(Ticket.ticket_priority, func.count())
                        .group_by(Ticket.ticket_priority).all())

    # Distribución por categoría IA
    by_ai_category = dict(db.query(Ticket.ai_category, func.count())
                           .filter(Ticket.ai_category != None)
                           .group_by(Ticket.ai_category).all())

    # Distribución por sentimiento IA
    by_sentiment = dict(db.query(Ticket.ai_sentiment, func.count())
                         .filter(Ticket.ai_sentiment != None)
                         .group_by(Ticket.ai_sentiment).all())

    # Productos más afectados (top 5)
    top_products = db.query(Ticket.product_purchased, func.count().label("count")) \
                     .group_by(Ticket.product_purchased) \
                     .order_by(func.count().desc()) \
                     .limit(5).all()

    # Rating promedio (solo tickets cerrados)
    avg_rating = db.query(func.avg(Ticket.satisfaction_rating)) \
                   .filter(Ticket.satisfaction_rating != None).scalar()

    # Tickets críticos o de alta prioridad sin resolver
    critical_open = db.query(Ticket).filter(
        Ticket.ticket_priority.in_(["Critical", "High"]),
        Ticket.ticket_status != "Closed"
    ).count()

    return {
        "total_tickets":        total,
        "tickets_analizados":   processed,
        "tickets_criticos_abiertos": critical_open,
        "rating_promedio":      round(avg_rating, 2) if avg_rating else None,
        "por_prioridad":        by_priority,
        "por_categoria_ia":     by_ai_category,
        "por_sentimiento_ia":   by_sentiment,
        "top_productos":        [{"producto": p, "count": c} for p, c in top_products],
    }
```

### `backend/app/routers/ask.py`

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..ai.service import answer_question

router = APIRouter()

class AskRequest(BaseModel):
    question: str

@router.post("/ask")
async def ask(request: AskRequest, db: Session = Depends(get_db)):
    answer = await answer_question(request.question, db)
    return {"question": request.question, "answer": answer}
```

### `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .config import settings
from .routers import ingest, tickets, summary, ask, process

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Support Ticket Analyzer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(process.router)
app.include_router(tickets.router)
app.include_router(summary.router)
app.include_router(ask.router)

@app.get("/health")
def health():
    from .ai import service as ai_service
    return {
        "status":    "ok",
        "ai_mode":   settings.ai_mode,
        "ai_model":  settings.ai_model,
        "procesando": ai_service._processing,
    }

@app.on_event("startup")
async def startup():
    """
    Si AUTO_INGEST_ON_START=true y la DB está vacía:
    - Lee y guarda el CSV directamente (sin llamada HTTP a sí mismo)
    - Lanza el análisis IA como tarea asyncio independiente
    """
    if not settings.auto_ingest_on_start:
        return

    from .database import SessionLocal
    from .models import Ticket as TicketModel
    from .ingestion.reader import read_csv
    from .ai import service as ai_service
    import asyncio

    db = SessionLocal()
    try:
        if db.query(TicketModel).count() == 0:
            tickets_data = read_csv(settings.dataset_path)
            for data in tickets_data:
                db.add(TicketModel(**data))
            db.commit()
            # Lanzar análisis IA como tarea asyncio — no bloquea el arranque del servidor
            asyncio.create_task(ai_service.process_tickets_batch())
    finally:
        db.close()
```

---

## 10. Paso 6 — Dashboard con React

### Componentes principales

#### `KPICards.tsx`
Muestra 5 tarjetas con métricas clave:
- Total de tickets
- Tickets analizados por IA
- Tickets críticos/altos abiertos (en rojo si > 0)
- Rating promedio de satisfacción
- Categoría IA más frecuente

#### `Charts.tsx`
Dos gráficos con Recharts:
1. **BarChart** — Tickets por categoría IA (horizontal, ordenado desc)
2. **PieChart** — Distribución por prioridad con colores semáforo (rojo=Critical, naranja=High, amarillo=Medium, verde=Low)

#### `TicketsTable.tsx`
Tabla con columnas:
- ID, Cliente, Producto, Tipo, Estado (badge de color), Prioridad original, Prioridad IA, Categoría IA, Sentimiento, Equipo responsable, Resumen IA

Panel lateral de filtros:
- Select: Estado, Prioridad, Categoría IA, Sentimiento
- Input: Buscar por producto o descripción
- Botón "Limpiar filtros"

Paginación: botones Anterior / Siguiente + indicador "Página X de Y".

#### `AskBar.tsx`
Campo de texto con placeholder *"¿Cuáles son los problemas más críticos esta semana?"*

Al enviar:
- Spinner de carga mientras espera respuesta
- Respuesta del LLM renderizada en un bloque con fondo destacado
- Historial de las últimas 3 preguntas/respuestas

### `frontend/src/api/client.ts`

```typescript
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

export const getTickets = (params: object) => api.get("/tickets", { params });
export const getTicket = (id: number) => api.get(`/tickets/${id}`);
export const getSummary = () => api.get("/summary");
export const askQuestion = (question: string) => api.post("/ask", { question });
export const triggerIngest = () => api.post("/ingest");
```

---

## 11. Paso 7 — Docker Compose

### `docker-compose.yml`

```yaml
version: "3.9"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./backend/dataset:/app/dataset
      - db_data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      backend:
        condition: service_healthy

volumes:
  db_data:
```

### `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 3000
```

### `backend/requirements.txt`

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.36
pydantic-settings==2.6.0
python-dotenv==1.0.1
litellm==1.52.0
python-dateutil==2.9.0
tenacity==8.5.0
```

---

## 12. Paso 8 — README y entregables

El `README.md` debe cubrir:

1. **Quick start** (3 comandos):
   ```bash
   cp .env.example .env
   # (editar .env con tu API key si quieres modo real)
   docker compose up
   ```
2. **Sin Docker** (comandos directos pip/npm)
3. **Endpoints** con ejemplos de curl
4. **Variables de entorno** — tabla con nombre, descripción, valores posibles y si es obligatoria
5. **Decisiones técnicas** — por qué este stack, por qué LiteLLM, por qué SQLite
6. **Limitaciones conocidas** — qué mejoraría con más tiempo
7. **Uso de IA durante el desarrollo** — herramientas usadas, para qué, qué validé manualmente

---

## 13. Orden de trabajo en 1 día

```
MAÑANA (4h)
├── [30min] Revisar CSV, diccionario de datos, identificar todos los problemas de calidad
├── [30min] Scaffolding: estructura de carpetas, requirements.txt, .env.example
├── [1h]    Backend: models.py, database.py, config.py, ingestion (reader + cleaner)
├── [1h]    Backend: AI service — mock_client primero, luego litellm_client
└── [1h]    Backend: todos los routers + main.py con CORS

TARDE (3h)
├── [30min] Verificar API con Swagger UI (http://localhost:8000/docs)
├── [30min] Base de conocimiento: policies.json, team_routing.json
├── [1h]    Frontend: scaffolding React + Vite, instalar deps, conectar API
└── [1h]    Frontend: KPICards + Charts + TicketsTable

NOCHE (2h)
├── [45min] Frontend: AskBar + filtros en la tabla
├── [30min] Docker Compose: probar `docker compose up` desde cero
└── [45min] README completo + revisión final + git push
```

---

## 14. Decisiones técnicas y trade-offs

### Por qué FastAPI y no Django/Flask
FastAPI tiene async nativo (crítico para llamadas concurrentes a la IA), documentación Swagger automática, y Pydantic integrado para validación. Django es excesivo para este scope; Flask requiere más boilerplate.

### Por qué SQLite y no PostgreSQL
El dataset es local y pequeño. SQLite no requiere servidor, es un archivo portable y SQLAlchemy abstrae la diferencia — migrar a PostgreSQL sería cambiar una sola línea en el `.env`.

### Por qué LiteLLM y no llamar directamente a la API de Anthropic
LiteLLM permite cambiar de proveedor modificando solo variables de entorno. Sin LiteLLM, cambiar de Claude a Groq requeriría reescribir el cliente. El costo es una dependencia extra liviana.

### Por qué modo mock
Permite demostrar y probar toda la arquitectura sin gastar en una API de pago. La interfaz es idéntica — el revisor puede conectar cualquier LLM real con solo cambiar `.env`.

### Por qué base de conocimiento en JSON/Markdown y no vector DB
Para el scope de esta prueba, la inyección directa de texto en el prompt es más simple, más rápida de implementar y suficientemente efectiva. Con más tiempo y más volumen de conocimiento, migraría a ChromaDB o pgvector.

### Limitaciones conocidas
- El análisis IA usa `asyncio.Semaphore(3)` para controlar concurrencia; con miles de tickets y un proveedor lento, sería mejor una cola persistente (Celery + Redis) que sobreviva reinicios del proceso
- No hay autenticación en la API
- El modo mock no genera resúmenes reales del texto
- La búsqueda en `/ask` es por keywords simples, no semántica
- SQLite no soporta concurrencia alta en escrituras — si dos requests escriben a la vez durante el procesamiento IA, puede haber contención (cada `_process_single` abre su propia sesión para mitigarlo)

### Con más tiempo implementaría
- Autenticación básica con API keys
- Cola de procesamiento async con Celery
- Búsqueda semántica con embeddings para `/ask`
- Tests unitarios para el cleaner y los routers
- Alertas para tickets críticos sin respuesta
- Exportación del dashboard a PDF/CSV
