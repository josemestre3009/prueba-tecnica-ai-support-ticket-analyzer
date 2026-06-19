import re
from datetime import date
from typing import Optional

from dateutil import parser as dateparser

VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}
VALID_STATUSES = {"Open", "Pending Customer Response", "Closed"}
VALID_CHANNELS = {"Email", "Phone", "Chat", "Social media"}
VALID_GENDERS = {"Male", "Female", "Other"}
TEMPLATE_REGEX = re.compile(r"\{[^}]+\}")


def _parse_date(value: str) -> Optional[date]:
    if not value or not value.strip():
        return None
    try:
        return dateparser.parse(str(value).strip(), dayfirst=False).date()
    except Exception:
        return None


def _parse_datetime(value: str):
    if not value or not value.strip():
        return None
    try:
        return dateparser.parse(str(value).strip())
    except Exception:
        return None


def _normalize_priority(value: str) -> Optional[str]:
    cleaned = value.strip().title()
    return cleaned if cleaned in VALID_PRIORITIES else None


def _normalize_status(value: str) -> Optional[str]:
    cleaned = value.strip()
    # Variantes de "Pending Customer Response"
    if "pending" in cleaned.lower():
        return "Pending Customer Response"
    titled = cleaned.title()
    return titled if titled in VALID_STATUSES else None


def clean_ticket(raw: dict) -> dict:
    ticket: dict = {}

    # ID
    try:
        ticket["ticket_id"] = int(float(str(raw.get("Ticket ID", 0)).strip()))
    except (ValueError, TypeError):
        ticket["ticket_id"] = 0

    # Campos de texto libre
    ticket["customer_name"] = (raw.get("Customer Name") or "").strip() or None
    ticket["ticket_subject"] = (raw.get("Ticket Subject") or "").strip() or None
    ticket["ticket_description"] = (raw.get("Ticket Description") or "").strip() or None
    ticket["product_purchased"] = (raw.get("Product Purchased") or "").strip() or None

    # Email → minúsculas y validación básica
    email = (raw.get("Customer Email") or "").strip().lower()
    ticket["customer_email"] = email if "@" in email and "." in email else None

    # Edad → rango razonable 18-90
    try:
        age = int(float(str(raw.get("Customer Age", "")).strip()))
        ticket["customer_age"] = age if 18 <= age <= 90 else None
    except (ValueError, TypeError):
        ticket["customer_age"] = None

    # Género
    gender = (raw.get("Customer Gender") or "").strip().title()
    ticket["customer_gender"] = gender if gender in VALID_GENDERS else None

    # Fecha de compra
    ticket["date_of_purchase"] = _parse_date(raw.get("Date of Purchase", ""))

    # Tipo de ticket → strip + title
    ticket_type = (raw.get("Ticket Type") or "").strip().title()
    ticket["ticket_type"] = ticket_type or None

    # Prioridad y estado normalizados
    ticket["ticket_priority"] = _normalize_priority(raw.get("Ticket Priority") or "")
    ticket["ticket_status"] = _normalize_status(raw.get("Ticket Status") or "")

    # Canal
    channel_raw = (raw.get("Ticket Channel") or "").strip()
    channel = channel_raw.title()
    # "Social media" se rompe con title() → "Social Media"
    if "social" in channel.lower():
        channel = "Social media"
    ticket["ticket_channel"] = channel if channel in VALID_CHANNELS else channel_raw or None

    # Timestamps
    ticket["first_response_time"] = _parse_datetime(raw.get("First Response Time", ""))
    ticket["time_to_resolution"] = _parse_datetime(raw.get("Time to Resolution", ""))

    # Rating de satisfacción — solo válido 1-5
    try:
        rating = float(str(raw.get("Customer Satisfaction Rating", "")).strip())
        ticket["satisfaction_rating"] = rating if 1 <= rating <= 5 else None
    except (ValueError, TypeError):
        ticket["satisfaction_rating"] = None

    # Flag para descripciones con placeholders sin resolver
    desc = ticket.get("ticket_description") or ""
    ticket["has_template_placeholders"] = bool(TEMPLATE_REGEX.search(desc))

    return ticket
