from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..ai import service as ai_service
from ..database import get_db
from ..models import Ticket
from ..schemas import StatusOut

router = APIRouter()


@router.post("/process", summary="Lanzar análisis IA sobre tickets pendientes")
async def process_tickets(db: Session = Depends(get_db)):
    if ai_service._processing:
        pending = db.query(Ticket).filter(Ticket.ai_processed == False).count()
        return {
            "message": "Ya hay un procesamiento en curso.",
            "pendientes": pending,
            "tip": "Consulta GET /status para ver el progreso.",
        }

    pending = db.query(Ticket).filter(Ticket.ai_processed == False).count()
    if pending == 0:
        return {"message": "No hay tickets pendientes de análisis."}

    ai_service.launch_batch()

    return {
        "message": f"Análisis IA iniciado para {pending} tickets.",
        "pendientes": pending,
        "tip": "Consulta GET /status para ver el progreso.",
    }


@router.post("/reprocess", summary="Re-analizar todos los tickets (útil tras cambiar el modo IA)")
async def reprocess_all(db: Session = Depends(get_db)):
    if ai_service._processing:
        return {"message": "Ya hay un procesamiento en curso."}

    db.query(Ticket).update({
        Ticket.ai_processed: False,
        Ticket.ai_category: None,
        Ticket.ai_priority: None,
        Ticket.ai_summary: None,
        Ticket.ai_sentiment: None,
        Ticket.ai_responsible_team: None,
        Ticket.ai_error: None,
    })
    db.commit()

    total = db.query(Ticket).count()
    ai_service.launch_batch()

    return {
        "message": f"Re-análisis iniciado para {total} tickets.",
        "tip": "Consulta GET /status para ver el progreso.",
    }


@router.get("/status", response_model=StatusOut, summary="Progreso del análisis IA")
def processing_status(db: Session = Depends(get_db)):
    total = db.query(Ticket).count()
    processed_ok = (
        db.query(Ticket)
        .filter(Ticket.ai_processed == True, Ticket.ai_error == None)
        .count()
    )
    with_error = db.query(Ticket).filter(Ticket.ai_error != None).count()
    pending = db.query(Ticket).filter(Ticket.ai_processed == False).count()

    return StatusOut(
        total=total,
        procesados_ok=processed_ok,
        con_error=with_error,
        pendientes=pending,
        en_curso=ai_service._processing,
        progreso_pct=round((processed_ok / total) * 100, 1) if total else 0.0,
    )
