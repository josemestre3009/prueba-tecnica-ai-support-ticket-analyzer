import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine, SessionLocal
from .routers import ask, ingest, process, summary, tickets

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Support Ticket Analyzer",
    version="1.0.0",
    description="Analiza tickets de soporte con IA — categoriza, prioriza y responde preguntas en lenguaje natural.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://frontend:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, tags=["Ingesta"])
app.include_router(process.router, tags=["Procesamiento IA"])
app.include_router(tickets.router, tags=["Tickets"])
app.include_router(summary.router, tags=["Resumen"])
app.include_router(ask.router, tags=["Ask"])


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok", "ai_mode": settings.ai_mode, "ai_model": settings.ai_model}


@app.on_event("startup")
async def startup():
    if not settings.auto_ingest_on_start:
        return
    # La ingesta y el procesamiento corren en un thread separado para no
    # bloquear el event loop de uvicorn durante el arranque.
    threading.Thread(target=_startup_worker, daemon=True).start()


def _startup_worker() -> None:
    """Ingesta el CSV y lanza el análisis IA en background (thread separado)."""
    import time
    # Pausa breve para que uvicorn termine de abrir el puerto antes de cargar datos
    time.sleep(2)

    from .models import Ticket
    from .ingestion.reader import read_csv
    from .ai import service as ai_service

    db = SessionLocal()
    try:
        count = db.query(Ticket).count()
        if count == 0:
            print("[startup] Ingesting CSV dataset...")
            tickets_data = read_csv(settings.dataset_path)
            db.bulk_insert_mappings(Ticket, tickets_data)
            db.commit()
            print(f"[startup] Ingested {len(tickets_data)} tickets.")

        pending = db.query(Ticket).filter(Ticket.ai_processed == False).count()
        if pending > 0:
            print(f"[startup] Launching AI analysis for {pending} tickets...")
            ai_service.launch_batch()
    except Exception as exc:
        print(f"[startup] Error: {exc}")
    finally:
        db.close()
