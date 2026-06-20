import asyncio
import json
import os
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..config import settings

if settings.ai_mode == "real":
    from .litellm_client import analyze_ticket as _analyze
    from .litellm_client import ask_question as _ask
else:
    from .mock_client import analyze_ticket as _analyze
    from .mock_client import ask_question as _ask

_processing = False
_processing_lock = threading.Lock()


def launch_batch() -> None:
    """Lanza el procesamiento IA. Funciona desde contexto async o sync (thread)."""
    try:
        loop = asyncio.get_running_loop()
        # Contexto async — crear task en el loop actual
        loop.create_task(_batch_async())
    except RuntimeError:
        # Contexto sync (thread) — correr en thread separado con su propio loop
        threading.Thread(target=_batch_in_new_loop, daemon=True).start()


def _batch_in_new_loop() -> None:
    """Corre el batch en un thread con su propio event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_batch_async())
    finally:
        loop.close()


async def _batch_async() -> None:
    """Lógica async del batch. El semáforo limita 3 llamadas IA concurrentes."""
    global _processing
    with _processing_lock:
        if _processing:
            return
        _processing = True

    semaphore = asyncio.Semaphore(3)

    try:
        ticket_ids = await asyncio.to_thread(_fetch_unprocessed_ids)
        tasks = [_process_single(tid, semaphore) for tid in ticket_ids]
        await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        with _processing_lock:
            _processing = False


# Alias para compatibilidad con routers existentes
process_tickets_batch = _batch_async


def _fetch_unprocessed_ids() -> list[int]:
    """Síncrono — corre en thread pool."""
    from ..database import SessionLocal
    from ..models import Ticket

    db = SessionLocal()
    try:
        rows = db.query(Ticket.id).filter(Ticket.ai_processed == False).all()
        return [r.id for r in rows]
    finally:
        db.close()


async def _process_single(ticket_db_id: int, semaphore: asyncio.Semaphore) -> None:
    # Leer ticket en thread para no bloquear el event loop
    ticket_data = await asyncio.to_thread(_read_ticket, ticket_db_id)
    if ticket_data is None:
        return

    try:
        async with semaphore:
            result = await _call_ai_with_retry(ticket_data)
        await asyncio.to_thread(_write_result, ticket_db_id, result)
    except Exception as exc:
        await asyncio.to_thread(_write_error, ticket_db_id, str(exc))


def _read_ticket(ticket_db_id: int) -> dict | None:
    """Síncrono — corre en thread pool."""
    from ..database import SessionLocal
    from ..models import Ticket

    db = SessionLocal()
    try:
        t = db.query(Ticket).filter(Ticket.id == ticket_db_id).first()
        if not t:
            return None
        return {
            "ticket_type": t.ticket_type or "",
            "ticket_subject": t.ticket_subject or "",
            "ticket_description": t.ticket_description or "",
            "product_purchased": t.product_purchased or "",
            "ticket_status": t.ticket_status or "",
            "ticket_priority": t.ticket_priority or "",
        }
    finally:
        db.close()


def _write_result(ticket_db_id: int, result: dict) -> None:
    """Síncrono — corre en thread pool."""
    from ..database import SessionLocal
    from ..models import Ticket

    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_db_id).first()
        if ticket:
            ticket.ai_category = result.get("category")
            ticket.ai_priority = result.get("priority")
            ticket.ai_summary = result.get("summary")
            ticket.ai_sentiment = result.get("sentiment")
            ticket.ai_responsible_team = result.get("responsible_team")
            ticket.ai_processed = True
            ticket.ai_processed_at = datetime.utcnow()
            ticket.ai_error = None
            db.commit()
    finally:
        db.close()


def _write_error(ticket_db_id: int, error_msg: str) -> None:
    """Síncrono — corre en thread pool."""
    from ..database import SessionLocal
    from ..models import Ticket

    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_db_id).first()
        if ticket:
            ticket.ai_error = error_msg
            ticket.ai_processed = False
            ticket.ai_processed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


_TRANSIENT_ERRORS = (TimeoutError, ConnectionError, OSError)


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(_TRANSIENT_ERRORS),
    reraise=True,
)
async def _call_ai_with_retry(ticket_data: dict) -> dict:
    return await _analyze(ticket_data)


async def answer_question(question: str) -> str:
    from ..database import SessionLocal
    from ..models import Ticket

    kb_dir = os.path.join(os.path.dirname(__file__), "../knowledge_base")

    with open(os.path.join(kb_dir, "policies.json"), encoding="utf-8") as f:
        policies = json.load(f)
    with open(os.path.join(kb_dir, "team_routing.json"), encoding="utf-8") as f:
        routing = json.load(f)
    with open(os.path.join(kb_dir, "data_schema.md"), encoding="utf-8") as f:
        schema = f.read()

    knowledge_base = (
        f"### Políticas SLA:\n{json.dumps(policies, ensure_ascii=False, indent=2)}\n\n"
        f"### Enrutamiento de equipos:\n{json.dumps(routing, ensure_ascii=False, indent=2)}\n\n"
        f"### Esquema de datos:\n{schema}"
    )

    db = SessionLocal()
    try:
        from sqlalchemy import func as sqlfunc

        total = db.query(Ticket).count()
        processed = db.query(Ticket).filter(Ticket.ai_processed == True).count()

        top_products = (
            db.query(Ticket.product_purchased, sqlfunc.count().label("cnt"))
            .filter(Ticket.product_purchased != None)
            .group_by(Ticket.product_purchased)
            .order_by(sqlfunc.count().desc())
            .limit(10)
            .all()
        )
        by_priority = (
            db.query(Ticket.ticket_priority, sqlfunc.count())
            .group_by(Ticket.ticket_priority)
            .all()
        )
        by_category = (
            db.query(Ticket.ai_category, sqlfunc.count())
            .filter(Ticket.ai_category != None)
            .group_by(Ticket.ai_category)
            .order_by(sqlfunc.count().desc())
            .all()
        )
        by_sentiment = (
            db.query(Ticket.ai_sentiment, sqlfunc.count())
            .filter(Ticket.ai_sentiment != None)
            .group_by(Ticket.ai_sentiment)
            .all()
        )
        avg_rating = (
            db.query(sqlfunc.avg(Ticket.satisfaction_rating))
            .filter(Ticket.satisfaction_rating != None)
            .scalar()
        )
        critical_open = (
            db.query(Ticket)
            .filter(Ticket.ticket_priority.in_(["Critical", "High"]), Ticket.ticket_status != "Closed")
            .count()
        )
        top_critical_products = (
            db.query(Ticket.product_purchased, sqlfunc.count().label("cnt"))
            .filter(Ticket.ticket_priority.in_(["Critical", "High"]), Ticket.product_purchased != None)
            .group_by(Ticket.product_purchased)
            .order_by(sqlfunc.count().desc())
            .limit(5)
            .all()
        )
        by_gender = (
            db.query(Ticket.customer_gender, sqlfunc.count())
            .filter(Ticket.customer_gender != None)
            .group_by(Ticket.customer_gender).all()
        )
        by_channel = (
            db.query(Ticket.ticket_channel, sqlfunc.count())
            .filter(Ticket.ticket_channel != None)
            .group_by(Ticket.ticket_channel).all()
        )
        by_ticket_type = (
            db.query(Ticket.ticket_type, sqlfunc.count())
            .filter(Ticket.ticket_type != None)
            .group_by(Ticket.ticket_type).all()
        )
        avg_age = db.query(sqlfunc.avg(Ticket.customer_age)).filter(Ticket.customer_age != None).scalar()

        # Enrutamiento real: ticket_type × equipo (para preguntas de validación)
        routing_real = (
            db.query(Ticket.ticket_type, Ticket.ai_responsible_team, sqlfunc.count().label("cnt"))
            .filter(Ticket.ticket_type != None, Ticket.ai_responsible_team != None)
            .group_by(Ticket.ticket_type, Ticket.ai_responsible_team)
            .order_by(Ticket.ticket_type, sqlfunc.count().desc())
            .all()
        )

        # Enrutamiento real: categoría IA × equipo (confirma que el routing por contenido es correcto)
        routing_por_categoria = (
            db.query(Ticket.ai_category, Ticket.ai_responsible_team, sqlfunc.count().label("cnt"))
            .filter(Ticket.ai_category != None, Ticket.ai_responsible_team != None)
            .group_by(Ticket.ai_category, Ticket.ai_responsible_team)
            .order_by(Ticket.ai_category, sqlfunc.count().desc())
            .all()
        )

        # Cobertura de campos opcionales
        sin_edad = db.query(Ticket).filter(Ticket.customer_age.is_(None)).count()
        sin_email = db.query(Ticket).filter(Ticket.customer_email.is_(None)).count()
        sin_rating = db.query(Ticket).filter(Ticket.satisfaction_rating.is_(None)).count()
        sin_genero = db.query(Ticket).filter(Ticket.customer_gender.is_(None)).count()

        # Estado × prioridad (para preguntas de tickets críticos abiertos)
        estado_por_prioridad = (
            db.query(Ticket.ticket_status, Ticket.ticket_priority, sqlfunc.count().label("cnt"))
            .filter(Ticket.ticket_status != None, Ticket.ticket_priority != None)
            .group_by(Ticket.ticket_status, Ticket.ticket_priority)
            .order_by(Ticket.ticket_priority, Ticket.ticket_status)
            .all()
        )

        # Sentimiento × canal (evita que la IA invente sentimientos no válidos)
        sentiment_por_canal = (
            db.query(Ticket.ticket_channel, Ticket.ai_sentiment, sqlfunc.count().label("cnt"))
            .filter(Ticket.ticket_channel != None, Ticket.ai_sentiment != None)
            .group_by(Ticket.ticket_channel, Ticket.ai_sentiment)
            .order_by(Ticket.ticket_channel, sqlfunc.count().desc())
            .all()
        )

        # Sentimiento × estado (tickets frustrados abiertos, etc.)
        sentiment_por_estado = (
            db.query(Ticket.ai_sentiment, Ticket.ticket_status, sqlfunc.count().label("cnt"))
            .filter(Ticket.ai_sentiment != None, Ticket.ticket_status != None)
            .group_by(Ticket.ai_sentiment, Ticket.ticket_status)
            .order_by(Ticket.ai_sentiment, sqlfunc.count().desc())
            .all()
        )

        # Distribución de ratings por valor (1-5)
        rating_distribution = (
            db.query(Ticket.satisfaction_rating, sqlfunc.count().label("cnt"))
            .filter(Ticket.satisfaction_rating != None)
            .group_by(Ticket.satisfaction_rating)
            .order_by(Ticket.satisfaction_rating)
            .all()
        )

        # Rating promedio por producto (solo productos con al menos 3 ratings)
        rating_por_producto = (
            db.query(Ticket.product_purchased, sqlfunc.avg(Ticket.satisfaction_rating).label("avg_r"), sqlfunc.count().label("cnt"))
            .filter(Ticket.product_purchased != None, Ticket.satisfaction_rating != None)
            .group_by(Ticket.product_purchased)
            .having(sqlfunc.count() >= 3)
            .order_by(sqlfunc.avg(Ticket.satisfaction_rating))
            .limit(10)
            .all()
        )

        # Tickets más recientes por first_response_time (último soporte atendido)
        ultimos_tickets = (
            db.query(Ticket)
            .filter(Ticket.first_response_time != None)
            .order_by(Ticket.first_response_time.desc())
            .limit(5)
            .all()
        )

        # Compras por mes (para preguntas sobre fechas)
        purchases_by_month = (
            db.query(
                sqlfunc.strftime("%Y-%m", Ticket.date_of_purchase).label("month"),
                sqlfunc.count().label("cnt"),
            )
            .filter(Ticket.date_of_purchase != None)
            .group_by(sqlfunc.strftime("%Y-%m", Ticket.date_of_purchase))
            .order_by(sqlfunc.strftime("%Y-%m", Ticket.date_of_purchase))
            .all()
        )

        ahora_colombia = datetime.now(ZoneInfo("America/Bogota"))
        fecha_actual = ahora_colombia.strftime("%A %d de %B de %Y, %H:%M (hora Colombia)")

        aggregate_context = f"""### Fecha y hora actual (Colombia): {fecha_actual}
Nota: el dataset contiene tickets del período 2020-2023. Preguntas sobre "hoy" o "esta semana" se refieren a esa ventana de datos, no a la fecha actual.

### Estadísticas agregadas del dataset ({total} tickets totales, {processed} analizados por IA):

**Top productos por volumen de tickets:**
{chr(10).join(f"  - {p}: {c} tickets" for p, c in top_products)}

**Top productos con tickets Critical/High:**
{chr(10).join(f"  - {p}: {c} tickets críticos/altos" for p, c in top_critical_products)}

**Distribución por prioridad (incluye None para tickets sin prioridad asignada):**
{chr(10).join(f"  - {p if p else 'Sin prioridad'}: {c}" for p, c in by_priority)}

**Distribución de ratings de satisfacción (1-5, solo tickets con rating):**
{chr(10).join(f"  - Rating {int(r)}: {c} tickets" for r, c in rating_distribution)}

**Distribución por categoría (IA):**
{chr(10).join(f"  - {c}: {n}" for c, n in by_category)}

**Distribución por sentimiento (IA):**
{chr(10).join(f"  - {s}: {n}" for s, n in by_sentiment)}

**Rating promedio de satisfacción:** {round(avg_rating, 2) if avg_rating else 'N/A'} / 5
**Edad promedio de clientes:** {round(avg_age, 1) if avg_age else 'N/A'} años
**Tickets Critical/High sin resolver:** {critical_open}

**Cobertura de campos (datos faltantes en el dataset completo):**
  - Sin edad registrada: {sin_edad} de {total} tickets
  - Sin email registrado: {sin_email} de {total} tickets
  - Sin rating registrado: {sin_rating} de {total} tickets
  - Sin género registrado: {sin_genero} de {total} tickets

**Enrutamiento real por tipo de ticket (dataset completo):**
{chr(10).join(f"  - {tt} → {eq}: {c}" for tt, eq, c in routing_real)}

**Enrutamiento real por categoría IA (confirma routing por contenido):**
{chr(10).join(f"  - {cat} → {eq}: {c}" for cat, eq, c in routing_por_categoria)}

**Estado × prioridad (tickets abiertos/pendientes por nivel de urgencia):**
{chr(10).join(f"  - {st} | {pr}: {c}" for st, pr, c in estado_por_prioridad)}

**Sentimiento por canal (sentimientos válidos: Neutral, Frustrated, Urgent, Satisfied, Confused):**
{chr(10).join(f"  - {ch} | {s}: {c}" for ch, s, c in sentiment_por_canal)}

**Sentimiento por estado del ticket:**
{chr(10).join(f"  - {s} | {st}: {c}" for s, st, c in sentiment_por_estado)}

**Rating promedio por producto (productos con ≥3 ratings, orden ascendente = peor primero):**
{chr(10).join(f"  - {p}: {round(r,2)}/5 ({c} ratings)" for p, r, c in rating_por_producto)}

**Distribución por género:**
{chr(10).join(f"  - {g}: {c}" for g, c in by_gender)}

**Distribución por canal:**
{chr(10).join(f"  - {ch}: {c}" for ch, c in by_channel)}

**Distribución por tipo de ticket:**
{chr(10).join(f"  - {tt}: {c}" for tt, c in by_ticket_type)}

**Compras por mes (YYYY-MM: cantidad):**
{chr(10).join(f"  - {m}: {c} compras" for m, c in purchases_by_month)}

**Últimos 5 tickets atendidos (por fecha de primera respuesta):**
{chr(10).join(f"  - [ID {t.ticket_id}] {t.first_response_time} | {t.product_purchased} | {t.ticket_status} | {t.ticket_priority} | {t.ai_category or 'sin categoría'}" for t in ultimos_tickets)}
"""

        words = [w.lower() for w in question.split() if len(w) > 2]
        all_tickets = db.query(Ticket).order_by(Ticket.ticket_id).limit(400).all()

        # Buscar IDs de tickets mencionados explícitamente en la pregunta
        import re as _re
        mentioned_ids = [int(n) for n in _re.findall(r'\b\d{1,6}\b', question)]
        if mentioned_ids:
            id_tickets = db.query(Ticket).filter(Ticket.ticket_id.in_(mentioned_ids)).all()
        else:
            id_tickets = []

        relevant = list(id_tickets)
        for t in all_tickets:
            if t.ticket_id in mentioned_ids:
                continue
            combined = " ".join(filter(None, [
                t.ticket_description, t.ticket_subject,
                t.product_purchased, t.ai_category, t.ai_summary,
                str(t.date_of_purchase) if t.date_of_purchase else None,
                str(t.ticket_id),
            ])).lower()
            if any(w in combined for w in words):
                relevant.append(t)
            if len(relevant) >= 20:
                break

        if not relevant:
            relevant = all_tickets[:20]

        tickets_context = "\n".join(
            f"- [ID {t.ticket_id}] {t.ticket_subject or 'Sin asunto'} | "
            f"Cliente: {t.customer_name or 'N/A'} | "
            f"Edad: {t.customer_age or 'N/A'} | "
            f"Género: {t.customer_gender or 'N/A'} | "
            f"Email: {t.customer_email or 'N/A'} | "
            f"Producto: {t.product_purchased or 'N/A'} | "
            f"Fecha compra: {t.date_of_purchase or 'N/A'} | "
            f"Canal: {t.ticket_channel or 'N/A'} | "
            f"Tipo: {t.ticket_type or 'N/A'} | "
            f"Estado: {t.ticket_status or 'N/A'} | "
            f"Prioridad: {t.ticket_priority or 'N/A'} | "
            f"Rating: {t.satisfaction_rating or 'N/A'} | "
            f"Prioridad IA: {t.ai_priority or 'N/A'} | "
            f"Categoría IA: {t.ai_category or 'N/A'} | "
            f"Sentimiento: {t.ai_sentiment or 'N/A'} | "
            f"Equipo: {t.ai_responsible_team or 'N/A'} | "
            f"Resumen: {t.ai_summary or 'N/A'}"
            for t in relevant
        )

        full_context = f"{aggregate_context}\n### Tickets de muestra:\n{tickets_context}"

    finally:
        db.close()

    from .safe_sql import SCHEMA, extract_sql_tags, format_results, run_safe_query

    # Primer intento: responder desde el contexto precalculado
    response = await _ask(question, knowledge_base, full_context, SCHEMA)

    # Si el LLM no tenía los datos emite uno o varios <sql>...</sql>
    sqls = extract_sql_tags(response)
    if sqls:
        parts: list[str] = []
        for i, sql in enumerate(sqls, 1):
            try:
                rows = run_safe_query(sql, settings.database_url)
                parts.append(
                    f"Consulta {i}:\n```sql\n{sql}\n```\n"
                    f"Resultado ({len(rows)} filas):\n{format_results(rows)}"
                )
            except ValueError as exc:
                parts.append(f"Consulta {i}: rechazada por seguridad — {exc}")
            except Exception as exc:
                parts.append(f"Consulta {i}: error al ejecutar — {exc}")

        followup = (
            "Datos obtenidos de la base de datos:\n\n"
            + "\n\n".join(parts)
            + f"\n\nResponde la pregunta de forma concisa usando estos datos. No menciones consultas SQL ni mecanismos internos.\nPregunta: {question}"
        )
        response = await _ask(followup, knowledge_base, "", "")

    return response
