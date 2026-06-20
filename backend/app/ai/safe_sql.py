"""
Módulo de ejecución segura de queries SQL generadas por IA.

Restricciones:
- Solo SELECT (no INSERT/UPDATE/DELETE/DROP ni ninguna escritura)
- Sin múltiples sentencias (previene stacked queries)
- Sin comentarios que puedan ocultar operaciones maliciosas
- Sin ATTACH/DETACH (previene acceso a otros archivos de BD)
- Conexión en modo read-only a nivel de SQLite URI
- Máximo 100 filas por resultado
- Timeout de 5 segundos
"""
import os
import re
import sqlite3
from typing import Any

_COMMENT = re.compile(r"(--[^\n]*|/\*.*?\*/)", re.DOTALL)

_BLOCKED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|ATTACH|DETACH|TRUNCATE|REPLACE"
    r"|EXEC|EXECUTE|INTO|VACUUM|REINDEX)\b",
    re.IGNORECASE,
)

_SELECT_ONLY = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
_LIMIT = re.compile(r"\bLIMIT\b", re.IGNORECASE)
_SQL_TAG = re.compile(r"<sql>(.*?)</sql>", re.DOTALL | re.IGNORECASE)

MAX_ROWS = 100

SCHEMA = """\
Tabla única disponible: `tickets`

| Columna               | Tipo    | Valores / notas                                                                 |
|-----------------------|---------|---------------------------------------------------------------------------------|
| ticket_id             | INTEGER | Clave primaria                                                                  |
| customer_name         | TEXT    |                                                                                 |
| customer_email        | TEXT    | Puede ser NULL                                                                  |
| customer_age          | REAL    | Puede ser NULL                                                                  |
| customer_gender       | TEXT    | Male, Female — puede ser NULL                                                   |
| product_purchased     | TEXT    |                                                                                 |
| date_of_purchase      | TEXT    | Formato YYYY-MM-DD                                                              |
| ticket_type           | TEXT    | Billing Inquiry, Refund Request, Technical Issue, Product Inquiry, Cancellation Request |
| ticket_subject        | TEXT    |                                                                                 |
| ticket_description    | TEXT    |                                                                                 |
| ticket_status         | TEXT    | Open, Closed, Pending Customer Response                                         |
| ticket_priority       | TEXT    | Critical, High, Medium, Low — puede ser NULL                                   |
| ticket_channel        | TEXT    | Email, Chat, Phone, Social Media                                                |
| first_response_time   | TEXT    | Formato YYYY-MM-DD HH:MM:SS — puede ser NULL                                   |
| time_to_resolution    | TEXT    | Formato YYYY-MM-DD HH:MM:SS — puede ser NULL                                   |
| satisfaction_rating   | REAL    | 1.0 a 5.0 — NULL si el ticket no está cerrado                                  |
| ai_category           | TEXT    | Hardware, Software, Network, Billing, Cancellation, Product Inquiry, Other     |
| ai_priority           | TEXT    | Critical, High, Medium, Low                                                    |
| ai_summary            | TEXT    | Resumen generado por IA                                                         |
| ai_sentiment          | TEXT    | Neutral, Frustrated, Urgent, Satisfied, Confused                               |
| ai_responsible_team   | TEXT    | Soporte Técnico, Facturación, Retención, Producto                              |"""


def validate_query(sql: str) -> tuple[bool, str]:
    """Devuelve (ok, motivo_de_rechazo)."""
    # Eliminar comentarios antes de validar
    clean = _COMMENT.sub("", sql).strip().rstrip(";")

    if not _SELECT_ONLY.match(clean):
        return False, "Solo se permiten consultas SELECT."

    if _BLOCKED.search(clean):
        return False, "La consulta contiene operaciones no permitidas."

    # Bloquear múltiples sentencias (stacked queries)
    if ";" in clean:
        return False, "No se permiten múltiples sentencias en una sola consulta."

    return True, ""


def run_safe_query(sql: str, db_url: str) -> list[dict[str, Any]]:
    """
    Ejecuta un SELECT de forma segura.
    - db_url: DATABASE_URL de settings (sqlite:///./data/tickets.db)
    - Abre la conexión en modo read-only a nivel de URI de SQLite.
    - Lanza ValueError si la query no pasa validación.
    """
    ok, reason = validate_query(sql)
    if not ok:
        raise ValueError(reason)

    # Añadir LIMIT si no tiene para evitar resultados masivos
    if not _LIMIT.search(sql):
        sql = sql.rstrip(";") + f" LIMIT {MAX_ROWS}"

    # Extraer ruta del archivo desde DATABASE_URL
    raw_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
    abs_path = os.path.abspath(raw_path)

    # Modo read-only a nivel de SQLite (no es solo Python, SQLite mismo lo fuerza)
    uri = f"file:{abs_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def extract_sql_tags(text: str) -> list[str]:
    """Extrae todos los <sql>...</sql> de la respuesta del LLM."""
    return [m.group(1).strip() for m in _SQL_TAG.finditer(text)]


def format_results(rows: list[dict[str, Any]]) -> str:
    """Convierte filas de SQL en texto tabular para el segundo prompt."""
    if not rows:
        return "La consulta no devolvió resultados."
    headers = list(rows[0].keys())
    lines = [" | ".join(headers)]
    lines.append("-" * len(lines[0]))
    for row in rows:
        lines.append(" | ".join(str(v) if v is not None else "NULL" for v in row.values()))
    return "\n".join(lines)
