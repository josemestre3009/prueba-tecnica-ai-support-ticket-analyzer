from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, Text
from .database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, unique=True, index=True)

    # Campos originales limpios
    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    customer_age = Column(Integer, nullable=True)
    customer_gender = Column(String, nullable=True)
    product_purchased = Column(String, nullable=True)
    date_of_purchase = Column(Date, nullable=True)
    ticket_type = Column(String, nullable=True)
    ticket_subject = Column(String, nullable=True)
    ticket_description = Column(Text, nullable=True)
    ticket_status = Column(String, nullable=True)
    ticket_priority = Column(String, nullable=True)
    ticket_channel = Column(String, nullable=True)
    first_response_time = Column(DateTime, nullable=True)
    time_to_resolution = Column(DateTime, nullable=True)
    satisfaction_rating = Column(Float, nullable=True)
    has_template_placeholders = Column(Boolean, default=False)

    # Campos enriquecidos por IA
    ai_category = Column(String, nullable=True)
    ai_priority = Column(String, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_sentiment = Column(String, nullable=True)
    ai_responsible_team = Column(String, nullable=True)
    ai_processed = Column(Boolean, default=False)
    ai_processed_at = Column(DateTime, nullable=True)
    ai_error = Column(Text, nullable=True)
