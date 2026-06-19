from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class TicketOut(BaseModel):
    id: int
    ticket_id: int
    customer_name: Optional[str]
    customer_email: Optional[str]
    customer_age: Optional[int]
    customer_gender: Optional[str]
    product_purchased: Optional[str]
    date_of_purchase: Optional[date]
    ticket_type: Optional[str]
    ticket_subject: Optional[str]
    ticket_description: Optional[str]
    ticket_status: Optional[str]
    ticket_priority: Optional[str]
    ticket_channel: Optional[str]
    first_response_time: Optional[datetime]
    time_to_resolution: Optional[datetime]
    satisfaction_rating: Optional[float]
    has_template_placeholders: bool

    ai_category: Optional[str]
    ai_priority: Optional[str]
    ai_summary: Optional[str]
    ai_sentiment: Optional[str]
    ai_responsible_team: Optional[str]
    ai_processed: bool
    ai_processed_at: Optional[datetime]
    ai_error: Optional[str]

    class Config:
        from_attributes = True


class TicketListOut(BaseModel):
    total: int
    page: int
    page_size: int
    data: list[TicketOut]


class SummaryOut(BaseModel):
    total_tickets: int
    tickets_analizados: int
    tickets_criticos_abiertos: int
    rating_promedio: Optional[float]
    por_prioridad: dict
    por_categoria_ia: dict
    por_sentimiento_ia: dict
    top_productos: list[dict]


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    question: str
    answer: str


class StatusOut(BaseModel):
    total: int
    procesados_ok: int
    con_error: int
    pendientes: int
    en_curso: bool
    progreso_pct: float
