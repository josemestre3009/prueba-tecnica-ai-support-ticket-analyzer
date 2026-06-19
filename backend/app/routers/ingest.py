from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..ingestion.reader import read_csv
from ..models import Ticket
from ..config import settings

router = APIRouter()


@router.post("/ingest", summary="Cargar tickets desde el CSV")
def ingest_tickets(db: Session = Depends(get_db)):
    tickets_data = read_csv(settings.dataset_path)

    inserted = 0
    updated = 0
    for data in tickets_data:
        existing = db.query(Ticket).filter(Ticket.ticket_id == data["ticket_id"]).first()
        if not existing:
            db.add(Ticket(**data))
            inserted += 1
        # No sobreescribir si ya fue procesado por IA
    db.commit()

    total = db.query(Ticket).count()
    pending = db.query(Ticket).filter(Ticket.ai_processed == False).count()

    return {
        "message": "Ingesta completada. Llama a POST /process para iniciar el análisis IA.",
        "tickets_insertados": inserted,
        "total_en_db": total,
        "pendientes_de_ia": pending,
    }
