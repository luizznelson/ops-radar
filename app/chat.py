"""
Chat assistant context and response logic for the Olist Ops Intelligence dashboard.
Loads pipeline outputs as a single context string and calls the Groq API.
"""
import json
import os
from pathlib import Path

from groq import Groq

OUTPUTS = Path("outputs")

# llama3-8b-8192 was decommissioned — llama-3.1-8b-instant is the direct replacement
MODEL = "llama-3.1-8b-instant"
TEMPERATURE = 0.1

_SYSTEM_TEMPLATE = """\
Você é um assistente especialista em operações de e-commerce da Olist.
Responda APENAS com base nas informações do contexto abaixo.
Se a pergunta não puder ser respondida com o contexto disponível, \
diga claramente que não tem essa informação — nunca invente dados.
Seja direto e objetivo. Use números do contexto sempre que relevante.

=== CONTEXTO DISPONÍVEL ===

{context}"""


def load_context() -> str:
    """Load and format all pipeline outputs into a single context string."""
    parts = []

    diag_path = OUTPUTS / "diagnostico.json"
    if diag_path.exists():
        diag = json.loads(diag_path.read_text(encoding="utf-8"))
        parts.append(
            "--- DIAGNÓSTICO OPERACIONAL ---\n"
            + json.dumps(diag, ensure_ascii=False, indent=2)
        )

    resumo_path = OUTPUTS / "resumo_reclamacoes.json"
    if resumo_path.exists():
        resumo = json.loads(resumo_path.read_text(encoding="utf-8"))
        parts.append(
            "--- RESUMO DE RECLAMAÇÕES POR CATEGORIA ---\n"
            + json.dumps(resumo, ensure_ascii=False, indent=2)
        )

    relatorio_path = OUTPUTS / "relatorio_executivo.md"
    if relatorio_path.exists():
        parts.append(
            "--- RELATÓRIO EXECUTIVO ---\n"
            + relatorio_path.read_text(encoding="utf-8")
        )

    return "\n\n".join(parts)


def build_system_prompt(context: str) -> str:
    return _SYSTEM_TEMPLATE.format(context=context)


def get_response(client: Groq, system_prompt: str, history: list[dict]) -> str:
    """
    Call the Groq API with the full conversation history.

    Args:
        client:        Groq client instance.
        system_prompt: System message containing the full context.
        history:       List of {"role": ..., "content": ...} dicts (user + assistant turns).

    Returns:
        The assistant reply as a plain string.
    """
    messages = [{"role": "system", "content": system_prompt}] + history
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
    )
    return response.choices[0].message.content
