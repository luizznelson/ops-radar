"""
Pipeline 02 — Sumarização GenAI de Reclamações
Resume avaliações negativas por categoria usando Groq (llama-3.1-8b-instant).
"""
import json
import os
import re
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

PROCESSED = Path("data/processed")
OUTPUTS = Path("outputs")

MODEL = "llama-3.1-8b-instant"
TEMPERATURE = 0.2
MAX_REVIEWS_PER_CATEGORY = 30
MIN_RECLAMACOES = 20

COLS = [
    "review_score",
    "review_comment_message",
    "product_category_name_english",
]

PROMPT_TEMPLATE = """\
Você é um analista de operações de e-commerce.
Abaixo estão avaliações negativas (nota 1 ou 2) sobre a categoria "{categoria}".

Avaliações:
{avaliacoes}

Responda SOMENTE com um objeto JSON válido, sem texto antes ou depois. \
Use exatamente este formato:
{{
  "principais_reclamacoes": ["reclamação 1", "reclamação 2", "reclamação 3"],
  "causa_raiz_provavel": "uma frase descrevendo o padrão central",
  "recomendacao_acao": "uma ação concreta e específica",
  "tom_predominante": "frustrado | revoltado | decepcionado | indiferente"
}}"""


def _extract_json(text: str) -> dict:
    """Try to parse JSON from LLM response, with regex fallback."""
    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Regex: grab first {...} block (handles prose before/after JSON)
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {"erro": "resposta_invalida", "raw": text}


def load_reviews() -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED / "olist_master.parquet", columns=COLS)
    return df[
        (df["review_score"] <= 2)
        & df["review_comment_message"].notna()
        & df["product_category_name_english"].notna()
    ]


def resumir_categoria(client: Groq, categoria: str, reviews: list[str]) -> dict | None:
    amostra = [r for r in reviews[:MAX_REVIEWS_PER_CATEGORY]
               if isinstance(r, str) and len(r.strip()) > 10]
    if not amostra:
        return None

    prompt = PROMPT_TEMPLATE.format(
        categoria=categoria,
        avaliacoes="\n".join(f"- {r}" for r in amostra),
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=TEMPERATURE,
    )
    content = response.choices[0].message.content
    return _extract_json(content)


def run(max_categorias: int | None = None) -> None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERRO: GROQ_API_KEY não encontrada. Crie um arquivo .env com a chave.")
        sys.exit(1)

    print(f"GROQ_API_KEY carregada: {'*' * 8}{api_key[-4:]}")

    client = Groq(api_key=api_key)

    print("Carregando avaliações negativas...")
    negativos = load_reviews()
    print(f"  {len(negativos):,} avaliações negativas com comentário")

    contagem = negativos["product_category_name_english"].value_counts()
    categorias = (
        contagem[contagem >= MIN_RECLAMACOES].index.tolist()
    )
    if max_categorias is not None:
        categorias = categorias[:max_categorias]

    print(f"  {len(categorias)} categorias a processar (mín. {MIN_RECLAMACOES} reclamações)\n")

    resultados = {}
    for i, cat in enumerate(categorias, 1):
        reviews = (
            negativos[negativos["product_category_name_english"] == cat]
            ["review_comment_message"]
            .tolist()
        )
        print(f"[{i}/{len(categorias)}] {cat} — {len(reviews)} reclamações...")
        resultado = resumir_categoria(client, cat, reviews)
        resultados[cat] = resultado

        if resultado and "erro" not in resultado:
            print(f"  OK — tom: {resultado.get('tom_predominante', '?')}")
        else:
            print(f"  AVISO — JSON inválido, raw salvo para debug")

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUTS / "resumo_reclamacoes.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"\nSalvo em {out_path}")


if __name__ == "__main__":
    run(max_categorias=3)
