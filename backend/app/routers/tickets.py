from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import Ticket
from ..schemas import TicketListOut, TicketOut

router = APIRouter()


@router.get("/tickets", response_model=TicketListOut, summary="Listar tickets con filtros")
def list_tickets(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    ai_category: Optional[str] = None,
    ai_sentiment: Optional[str] = None,
    ai_priority: Optional[str] = None,
    product: Optional[str] = None,
    channel: Optional[str] = None,
    search: Optional[str] = None,
    only_processed: Optional[bool] = None,
):
    query = db.query(Ticket)

    if status:
        query = query.filter(Ticket.ticket_status == status)
    if priority:
        query = query.filter(Ticket.ticket_priority == priority)
    if ai_category:
        query = query.filter(Ticket.ai_category == ai_category)
    if ai_sentiment:
        query = query.filter(Ticket.ai_sentiment == ai_sentiment)
    if ai_priority:
        query = query.filter(Ticket.ai_priority == ai_priority)
    if product:
        query = query.filter(Ticket.product_purchased.ilike(f"%{product}%"))
    if channel:
        query = query.filter(Ticket.ticket_channel == channel)
    if search:
        query = query.filter(
            Ticket.ticket_description.ilike(f"%{search}%")
            | Ticket.ticket_subject.ilike(f"%{search}%")
        )
    if only_processed is not None:
        query = query.filter(Ticket.ai_processed == only_processed)

    total = query.count()
    tickets = query.order_by(Ticket.ticket_id).offset((page - 1) * page_size).limit(page_size).all()

    return TicketListOut(total=total, page=page, page_size=page_size, data=tickets)


@router.get("/tickets/{ticket_id}", response_model=TicketOut, summary="Detalle de un ticket")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} no encontrado")
    return ticket
