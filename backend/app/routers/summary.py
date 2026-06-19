from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Ticket
from ..schemas import SummaryOut

router = APIRouter()


@router.get("/summary", response_model=SummaryOut, summary="KPIs y métricas agregadas")
def get_summary(db: Session = Depends(get_db)):
    total = db.query(Ticket).count()
    processed = (
        db.query(Ticket)
        .filter(Ticket.ai_processed == True, Ticket.ai_error == None)
        .count()
    )

    by_priority = dict(
        db.query(Ticket.ticket_priority, func.count())
        .filter(Ticket.ticket_priority != None)
        .group_by(Ticket.ticket_priority)
        .all()
    )

    by_ai_category = dict(
        db.query(Ticket.ai_category, func.count())
        .filter(Ticket.ai_category != None)
        .group_by(Ticket.ai_category)
        .all()
    )

    by_sentiment = dict(
        db.query(Ticket.ai_sentiment, func.count())
        .filter(Ticket.ai_sentiment != None)
        .group_by(Ticket.ai_sentiment)
        .all()
    )

    top_products = (
        db.query(Ticket.product_purchased, func.count().label("count"))
        .filter(Ticket.product_purchased != None)
        .group_by(Ticket.product_purchased)
        .order_by(func.count().desc())
        .limit(5)
        .all()
    )

    avg_rating = (
        db.query(func.avg(Ticket.satisfaction_rating))
        .filter(Ticket.satisfaction_rating != None)
        .scalar()
    )

    critical_open = (
        db.query(Ticket)
        .filter(
            Ticket.ticket_priority.in_(["Critical", "High"]),
            Ticket.ticket_status != "Closed",
        )
        .count()
    )

    return SummaryOut(
        total_tickets=total,
        tickets_analizados=processed,
        tickets_criticos_abiertos=critical_open,
        rating_promedio=round(avg_rating, 2) if avg_rating else None,
        por_prioridad=by_priority,
        por_categoria_ia=by_ai_category,
        por_sentimiento_ia=by_sentiment,
        top_productos=[{"producto": p, "count": c} for p, c in top_products],
    )
