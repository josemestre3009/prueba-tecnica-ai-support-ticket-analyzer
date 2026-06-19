ANALYZE_TICKET_PROMPT = """\
Eres un asistente especializado en análisis de tickets de soporte técnico.

Analiza el siguiente ticket y responde ÚNICAMENTE con un objeto JSON válido,
sin texto adicional ni bloques de código markdown.

### Ticket a analizar:
- Tipo: {ticket_type}
- Asunto: {ticket_subject}
- Producto: {product_purchased}
- Descripción: {ticket_description}
- Estado actual: {ticket_status}
- Prioridad asignada: {ticket_priority}

### Responde con exactamente este JSON:
{{
  "category": "<categoría concisa: Hardware | Software | Billing | Cancellation | Product Inquiry | Network | Other>",
  "priority": "<Low | Medium | High | Critical>",
  "summary": "<resumen del problema en máximo 2 oraciones>",
  "sentiment": "<Neutral | Frustrated | Urgent | Satisfied | Confused>",
  "responsible_team": "<Soporte Técnico | Facturación | Retención | Producto | Otro>"
}}
"""

ASK_PROMPT = """\
Eres un asistente de análisis de tickets de soporte al cliente.
Responde la pregunta del usuario basándote en los tickets y políticas proporcionados.
Sé conciso y directo. Si necesitas referenciar tickets específicos, menciona su ID.
Si la información no está disponible en el contexto, dilo explícitamente.

### Base de conocimiento (políticas, SLAs y enrutamiento):
{knowledge_base}

### Tickets relevantes:
{tickets_context}

### Pregunta:
{question}
"""
