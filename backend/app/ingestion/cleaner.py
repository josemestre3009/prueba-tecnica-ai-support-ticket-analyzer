import re
from datetime import date, timedelta
from typing import Optional

from dateutil import parser as dateparser

VALID_STATUSES = {"Open", "Pending Customer Response", "Closed"}
VALID_CHANNELS = {"Email", "Phone", "Chat", "Social media"}
VALID_GENDERS = {"Male", "Female", "Other"}
TEMPLATE_REGEX = re.compile(r"\{[^}]+\}")

# Títulos y sufijos a eliminar de nombres
_NAME_TITLES = re.compile(
    r"^(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s*|"
    r"\s*(MD|PhD|Jr\.|Sr\.|II|III|IV)$",
    re.IGNORECASE,
)


def _fix_mojibake(text: str) -> str:
    """Corrige texto Latin-1 leído erróneamente como UTF-8 (ej: 'Ã¡' → 'á')."""
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def _normalize_name(value: str) -> Optional[str]:
    if not value:
        return None
    name = _fix_mojibake(value.strip())
    name = _NAME_TITLES.sub("", name).strip()
    if not name:
        return None
    # Si está todo en mayúsculas, convertir a Title Case
    if name == name.upper():
        name = name.title()
    return name or None


_PRODUCT_ALIASES = {
    "playstation": "Sony PlayStation",
    "xbox": "Microsoft Xbox Controller",
    "iphone": "Apple iPhone",
    "macbook": "Apple MacBook Pro",
    "macbook pro": "Apple MacBook Pro",
    "nikon d": "Nikon D",
    "canon eos": "Canon EOS",
    "gopro": "GoPro Hero",
}


def _normalize_product(value: str) -> Optional[str]:
    if not value:
        return None
    product = _fix_mojibake(value.strip())
    # Si está todo en mayúsculas, convertir a Title Case
    if product == product.upper():
        product = product.title()
    # Resolver aliases de productos conocidos
    key = product.lower().strip()
    if key in _PRODUCT_ALIASES:
        return _PRODUCT_ALIASES[key]
    return product or None


def _normalize_priority(value: str) -> Optional[str]:
    v = value.strip().lower()
    mapping = {
        # Valores canónicos (insensible a mayúsculas)
        "critical": "Critical",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        # Variantes en inglés
        "urgent": "Critical",
        "med": "Medium",
        # Variantes en español
        "crítica": "Critical",
        "critica": "Critical",
        "alta": "High",
        "media": "Medium",
        "baja": "Low",
        # Códigos P1-P4
        "p1": "Critical",
        "p2": "High",
        "p3": "Medium",
        "p4": "Low",
        # Números 1-4
        "1": "Critical",
        "2": "High",
        "3": "Medium",
        "4": "Low",
    }
    return mapping.get(v)


def _normalize_ticket_type(value: str) -> Optional[str]:
    v = value.strip().lower().replace("_", " ").replace("-", " ")
    if not v:
        return None
    # Normalizar a los 5 tipos canónicos
    if "billing" in v:
        return "Billing Inquiry"
    if "refund" in v:
        return "Refund Request"
    if "cancel" in v:
        return "Cancellation Request"
    if "product" in v and ("inquiry" in v or "question" in v or "info" in v):
        return "Product Inquiry"
    if "product" in v:
        return "Product Inquiry"
    if "technical" in v or "tech" in v:
        return "Technical Issue"
    # Intento por title-case exacto después del mapeo fallido
    titled = value.strip().title()
    canonical = {
        "Technical Issue", "Billing Inquiry", "Refund Request",
        "Cancellation Request", "Product Inquiry",
    }
    return titled if titled in canonical else titled or None


def _normalize_status(value: str) -> Optional[str]:
    cleaned = value.strip()
    if "pending" in cleaned.lower():
        return "Pending Customer Response"
    titled = cleaned.title()
    return titled if titled in VALID_STATUSES else None


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


def clean_ticket(raw: dict) -> dict:
    ticket: dict = {}

    # ID
    try:
        ticket["ticket_id"] = int(float(str(raw.get("Ticket ID", 0)).strip()))
    except (ValueError, TypeError):
        ticket["ticket_id"] = 0

    # Nombre — normalización de casing, títulos y encoding
    ticket["customer_name"] = _normalize_name(raw.get("Customer Name") or "")

    # Asunto y descripción — solo limpieza de espacios
    ticket["ticket_subject"] = (raw.get("Ticket Subject") or "").strip() or None
    ticket["ticket_description"] = (raw.get("Ticket Description") or "").strip() or None

    # Producto — normalización de casing y encoding
    ticket["product_purchased"] = _normalize_product(raw.get("Product Purchased") or "")

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

    # Tipo de ticket — normalización a 5 valores canónicos
    ticket["ticket_type"] = _normalize_ticket_type(raw.get("Ticket Type") or "")

    # Prioridad — normalización de múltiples formatos (P1-P4, baja, urgent…)
    ticket["ticket_priority"] = _normalize_priority(raw.get("Ticket Priority") or "")

    # Estado
    ticket["ticket_status"] = _normalize_status(raw.get("Ticket Status") or "")

    # Canal
    channel_raw = (raw.get("Ticket Channel") or "").strip()
    channel = channel_raw.title()
    if "social" in channel.lower():
        channel = "Social media"
    ticket["ticket_channel"] = channel if channel in VALID_CHANNELS else channel_raw or None

    # Timestamps — corrige casos donde resolution < first_response (error del CSV)
    # sumando 1 día a time_to_resolution (el ticket se resolvió al día siguiente)
    first_response = _parse_datetime(raw.get("First Response Time", ""))
    time_to_resolution = _parse_datetime(raw.get("Time to Resolution", ""))
    if first_response and time_to_resolution and time_to_resolution < first_response:
        time_to_resolution = time_to_resolution + timedelta(days=1)
    ticket["first_response_time"] = first_response
    ticket["time_to_resolution"] = time_to_resolution

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
