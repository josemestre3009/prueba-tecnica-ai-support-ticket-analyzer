"""
Cliente de IA agnóstico de proveedor — sin LiteLLM.

Rutea al SDK correcto según el prefijo de AI_MODEL:
  claude-*          → anthropic SDK
  groq/<model>      → openai SDK con base_url de Groq
  gemini/<model>    → openai SDK con base_url de Gemini
  gpt-* / cualquier → openai SDK estándar
"""
import json
import os

from ..config import settings
from .prompts import ANALYZE_TICKET_PROMPT, ASK_PROMPT


# ── Helpers por proveedor ────────────────────────────────────────────────────

async def _call_anthropic(model: str, messages: list, max_tokens: int, temperature: float) -> str:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic()
    resp = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=messages,
    )
    return resp.content[0].text


async def _call_openai_compatible(
    model: str,
    messages: list,
    max_tokens: int,
    temperature: float,
    base_url: str | None = None,
    api_key: str | None = None,
) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=api_key or os.environ.get("OPENAI_API_KEY"),
        base_url=base_url,
    )
    resp = await client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content


# ── Router principal ─────────────────────────────────────────────────────────

async def _complete(messages: list, max_tokens: int = 300, temperature: float = 0.1) -> str:
    model = settings.ai_model

    if model.startswith("claude"):
        return await _call_anthropic(model, messages, max_tokens, temperature)

    if model.startswith("groq/"):
        return await _call_openai_compatible(
            model=model.removeprefix("groq/"),
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY"),
        )

    if model.startswith("gemini/"):
        return await _call_openai_compatible(
            model=model.removeprefix("gemini/"),
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=os.environ.get("GEMINI_API_KEY"),
        )

    # OpenAI por defecto (gpt-4o, gpt-4o-mini, etc.)
    return await _call_openai_compatible(model, messages, max_tokens, temperature)


# ── Funciones públicas (misma interfaz que antes) ────────────────────────────

async def analyze_ticket(ticket_data: dict) -> dict:
    prompt = ANALYZE_TICKET_PROMPT.format(
        ticket_type=ticket_data.get("ticket_type", ""),
        ticket_subject=ticket_data.get("ticket_subject", ""),
        product_purchased=ticket_data.get("product_purchased", ""),
        ticket_description=ticket_data.get("ticket_description", "")[:1500],
        ticket_status=ticket_data.get("ticket_status", ""),
        ticket_priority=ticket_data.get("ticket_priority", ""),
    )

    raw = await _complete([{"role": "user", "content": prompt}], max_tokens=300, temperature=0.1)
    raw = raw.strip()

    # Limpiar posibles bloques de código markdown
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)


async def ask_question(question: str, knowledge_base: str, tickets_context: str, schema: str = "") -> str:
    prompt = ASK_PROMPT.format(
        knowledge_base=knowledge_base,
        tickets_context=tickets_context,
        question=question,
        schema=schema,
    )
    return await _complete([{"role": "user", "content": prompt}], max_tokens=2000, temperature=0.3)
