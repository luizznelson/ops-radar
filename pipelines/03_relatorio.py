"""
Pipeline 03 — Relatório Executivo
Gera relatorio_executivo.md a partir dos outputs dos pipelines 01 e 02.
Depende de: outputs/diagnostico.json e outputs/resumo_reclamacoes.json
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

OUTPUTS = Path("outputs")
MODEL = "llama-3.1-8b-instant"
TEMPERATURE = 0.3

PROMPT_TEMPLATE = """\
Você é um analista sênior de operações de e-commerce.
Escreva um relatório executivo em Markdown com base nos dados abaixo.

Regras:
- Linguagem direta, sem jargão técnico
- Foque em impacto de negócio
- Estrutura obrigatória: Resumo Executivo · Principais Problemas · Recomendações Prioritárias
- Máximo 400 palavras

Diagnóstico operacional:
{diagnostico}

Resumo das reclamações por categoria:
{reclamacoes}

Data: {data}"""


def load_diagnostico() -> dict:
    path = OUTPUTS / "diagnostico.json"
    if not path.exists():
        print("ERRO: outputs/diagnostico.json não encontrado. Execute 01_diagnostico.py primeiro.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_resumo_reclamacoes() -> dict:
    path = OUTPUTS / "resumo_reclamacoes.json"
    if not path.exists():
        print("ERRO: outputs/resumo_reclamacoes.json não encontrado. Execute 02_genai_reviews.py primeiro.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def gerar_relatorio(client: Groq, diagnostico: dict, resumo: dict) -> str:
    prompt = PROMPT_TEMPLATE.format(
        diagnostico=json.dumps(diagnostico, ensure_ascii=False, indent=2),
        reclamacoes=json.dumps(resumo, ensure_ascii=False, indent=2),
        data=datetime.now().strftime("%d/%m/%Y"),
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=TEMPERATURE,
    )
    return response.choices[0].message.content


def save_relatorio(texto: str) -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    with open(OUTPUTS / "relatorio_executivo.md", "w", encoding="utf-8") as f:
        f.write(texto)


if __name__ == "__main__":
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERRO: GROQ_API_KEY não encontrada. Crie um arquivo .env com a chave.")
        sys.exit(1)

    client = Groq(api_key=api_key)

    print("Carregando diagnóstico e resumo de reclamações...")
    diagnostico = load_diagnostico()
    resumo = load_resumo_reclamacoes()
    print(f"  {len(resumo)} categorias no resumo de reclamações")

    print("Gerando relatório executivo via LLM...")
    relatorio = gerar_relatorio(client, diagnostico, resumo)

    save_relatorio(relatorio)
    print("Salvo em outputs/relatorio_executivo.md\n")

    print("--- Primeiras 20 linhas ---")
    for line in relatorio.splitlines()[:20]:
        print(line)
