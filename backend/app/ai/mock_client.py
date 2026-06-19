KEYWORD_CATEGORIES = {
    "Hardware": ["hardware", "device", "screen", "keyboard", "battery", "physical", "printer", "cable"],
    "Software": ["software", "bug", "error", "crash", "app", "install", "update", "freeze", "slow"],
    "Billing": ["billing", "charge", "invoice", "payment", "refund", "price", "fee", "subscription"],
    "Cancellation": ["cancel", "cancellation", "unsubscribe", "terminate", "close account"],
    "Network": ["network", "internet", "connection", "wifi", "disconnect", "offline", "latency"],
    "Product Inquiry": ["inquiry", "question", "how to", "guide", "information", "feature", "option"],
}

SENTIMENT_KEYWORDS = {
    "Urgent": ["urgent", "asap", "immediately", "critical", "emergency", "now", "right away"],
    "Frustrated": ["frustrated", "disappointed", "terrible", "worst", "angry", "unacceptable", "awful"],
    "Satisfied": ["thank", "great", "excellent", "love", "amazing", "perfect", "happy"],
    "Confused": ["confused", "don't understand", "unclear", "not sure", "what does", "how do"],
}

TEAM_BY_TYPE = {
    "Technical Issue": "Soporte Técnico",
    "Billing Inquiry": "Facturación",
    "Refund Request": "Facturación",
    "Cancellation Request": "Retención",
    "Product Inquiry": "Producto",
}


def _detect_category(text: str) -> str:
    text_lower = text.lower()
    for category, keywords in KEYWORD_CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return "Other"


def _detect_sentiment(text: str) -> str:
    text_lower = text.lower()
    for sentiment, keywords in SENTIMENT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return sentiment
    return "Neutral"


def _extract_summary(desc: str, subject: str, product: str) -> str:
    """Extrae las primeras 2 oraciones útiles de la descripción, filtrando ruido."""
    import re

    # Quitar placeholders sin resolver
    cleaned = re.sub(r"\{[^}]+\}", "", desc).strip()

    # Separar en oraciones
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)

    # Filtrar oraciones genéricas de relleno
    noise = {
        "please assist", "thank you", "please contact", "please,",
        "i'm having an issue with", "i am having an issue",
        "if possible", "greetings", "we've got", "we have",
    }
    useful = [
        s.strip() for s in sentences
        if len(s.strip()) > 20
        and not any(n in s.lower() for n in noise)
    ]

    if useful:
        # Tomar las primeras 2 oraciones útiles, máximo 180 caracteres
        summary = " ".join(useful[:2])
        if len(summary) > 180:
            summary = summary[:177] + "..."
        return summary

    # Fallback si no hay texto útil
    return f"Cliente reporta un problema con {product or 'el producto'} relacionado con {subject or 'soporte'}."


async def analyze_ticket(ticket_data: dict) -> dict:
    desc = ticket_data.get("ticket_description", "")
    subject = ticket_data.get("ticket_subject", "")
    t_type = ticket_data.get("ticket_type", "")
    product = ticket_data.get("product_purchased", "")
    priority = ticket_data.get("ticket_priority") or "Medium"

    category = _detect_category(desc)
    sentiment = _detect_sentiment(desc)
    summary = _extract_summary(desc, subject, product)

    return {
        "category": category,
        "priority": priority,
        "summary": summary,
        "sentiment": sentiment,
        "responsible_team": TEAM_BY_TYPE.get(t_type, "Soporte Técnico"),
    }


async def ask_question(question: str, knowledge_base: str, tickets_context: str) -> str:
    return (
        f"**[MODO MOCK]** Respuesta simulada para: *{question}*\n\n"
        "Esta respuesta es generada sin un LLM real. "
        "Para obtener respuestas reales, configura `AI_MODE=real` y añade una API key válida en el archivo `.env`.\n\n"
        f"Tickets en contexto cargados: {len(tickets_context.splitlines())} líneas.\n"
        "Base de conocimiento disponible: SLAs, enrutamiento de equipos y esquema de datos."
    )
