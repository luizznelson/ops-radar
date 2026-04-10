"""
Pipeline 01 — Diagnóstico Operacional
Identifica gargalos a partir do olist_master.parquet e salva diagnostico.json.
"""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

PROCESSED = Path("data/processed")
OUTPUTS = Path("outputs")

COLS = [
    "order_status",
    "atrasado",
    "atraso_dias",
    "customer_state",
    "review_score",
    "product_category_name_english",
    "mes_ano",
]


def load_master() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "olist_master.parquet", columns=COLS)


def calcular_diagnostico(df: pd.DataFrame) -> dict:
    entregues = df[df["order_status"] == "delivered"].copy()

    taxa_atraso = entregues["atrasado"].mean()

    estados_criticos = (
        entregues.groupby("customer_state")["atrasado"]
        .agg(taxa="mean", volume="count")
        .query("volume >= 100")
        .sort_values("taxa", ascending=False)
        .head(5)
        .reset_index()
        .to_dict(orient="records")
    )

    categorias_pior_avaliacao = (
        entregues.groupby("product_category_name_english")["review_score"]
        .agg(nota_media="mean", volume="count")
        .query("volume >= 50")
        .sort_values("nota_media")
        .head(5)
        .reset_index()
        .to_dict(orient="records")
    )

    nota_atrasado = entregues.loc[entregues["atrasado"], "review_score"].mean()
    nota_no_prazo = entregues.loc[~entregues["atrasado"], "review_score"].mean()

    tendencia_mensal_atraso = (
        entregues.groupby("mes_ano")["atrasado"]
        .mean()
        .tail(12)
        .round(3)
        .to_dict()
    )

    return {
        "gerado_em": datetime.now().isoformat(),
        "total_pedidos_analisados": len(entregues),
        "taxa_atraso_geral": round(taxa_atraso, 3),
        "impacto_atraso_na_nota": round(nota_atrasado - nota_no_prazo, 2),
        "estados_criticos": estados_criticos,
        "categorias_pior_avaliacao": categorias_pior_avaliacao,
        "tendencia_mensal_atraso": tendencia_mensal_atraso,
    }


def save_diagnostico(result: dict) -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    with open(OUTPUTS / "diagnostico.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print("Carregando olist_master.parquet...")
    df = load_master()
    print(f"  {len(df):,} pedidos no total")

    print("Calculando diagnóstico...")
    result = calcular_diagnostico(df)

    save_diagnostico(result)

    # Summary print
    print("\n--- Diagnóstico Operacional ---")
    print(f"Pedidos entregues analisados : {result['total_pedidos_analisados']:,}")
    print(f"Taxa de atraso geral         : {result['taxa_atraso_geral']:.1%}")
    print(f"Impacto do atraso na nota    : {result['impacto_atraso_na_nota']:+.2f} estrelas")
    print("\nTop 3 estados críticos (maior taxa de atraso):")
    for i, e in enumerate(result["estados_criticos"][:3], 1):
        print(f"  {i}. {e['customer_state']}  {e['taxa']:.1%}  ({e['volume']:,} pedidos)")
    print("\nSalvo em outputs/diagnostico.json")
