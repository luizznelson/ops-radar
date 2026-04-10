"""
Dashboard Streamlit — Olist Ops Intelligence
Quatro abas: KPIs Operacionais | Reclamações por Categoria | Relatório Executivo | Assistente
"""
import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from chat import build_system_prompt, get_response, load_context

load_dotenv()

PROCESSED = Path("data/processed")
OUTPUTS = Path("outputs")

COLS = [
    "order_status",
    "customer_state",
    "product_category_name_english",
    "review_score",
    "atrasado",
    "atraso_dias",
    "valor_total",
    "mes_ano",
]

st.set_page_config(page_title="Olist Ops Intelligence", layout="wide")
st.title("Olist Ops Intelligence")

# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_resource
def get_groq_client() -> Groq | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


@st.cache_data
def cached_system_prompt() -> str:
    return build_system_prompt(load_context())


@st.cache_data
def load_master() -> pd.DataFrame:
    path = PROCESSED / "olist_master.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path, columns=COLS)


@st.cache_data
def load_json(filename: str) -> dict:
    path = OUTPUTS / filename
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


df = load_master()

if df.empty:
    st.error("olist_master.parquet não encontrado. Execute `python pipelines/00_etl.py` primeiro.")
    st.stop()

entregues = df[df["order_status"] == "delivered"]

# ── Tabs ──────────────────────────────────────────────────────────────────────

aba1, aba2, aba3, aba4 = st.tabs(
    ["KPIs Operacionais", "Reclamações por Categoria", "Relatório Executivo", "Assistente"]
)

# ── Tab 1: KPIs Operacionais ──────────────────────────────────────────────────

with aba1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pedidos entregues", f"{len(entregues):,}")
    c2.metric("Taxa de atraso", f"{entregues['atrasado'].mean():.1%}")
    c3.metric("Nota média geral", f"{entregues['review_score'].mean():.2f}")
    c4.metric(
        "Nota média (atrasados)",
        f"{entregues.loc[entregues['atrasado'], 'review_score'].mean():.2f}",
    )

    st.divider()

    # Delay rate trend
    tendencia = (
        entregues.groupby("mes_ano")["atrasado"]
        .mean()
        .reset_index()
        .sort_values("mes_ano")
    )
    fig_trend = px.line(
        tendencia,
        x="mes_ano",
        y="atrasado",
        title="Taxa de atraso mensal",
        labels={"atrasado": "Taxa de atraso", "mes_ano": "Período"},
        markers=True,
    )
    fig_trend.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig_trend, use_container_width=True)

    # Delay rate by state (top 10, min 100 orders)
    estados = (
        entregues.groupby("customer_state")["atrasado"]
        .agg(taxa="mean", volume="count")
        .query("volume >= 100")
        .sort_values("taxa", ascending=False)
        .head(10)
        .reset_index()
    )
    fig_estados = px.bar(
        estados,
        x="customer_state",
        y="taxa",
        title="Top 10 estados por taxa de atraso (mín. 100 pedidos)",
        labels={"taxa": "Taxa de atraso", "customer_state": "Estado"},
        text_auto=".1%",
    )
    fig_estados.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig_estados, use_container_width=True)

# ── Tab 2: Reclamações por Categoria ─────────────────────────────────────────

with aba2:
    resumo_path = OUTPUTS / "resumo_reclamacoes.json"
    if not resumo_path.exists():
        st.warning("Execute `python pipelines/02_genai_reviews.py` primeiro.")
    else:
        resumo = load_json("resumo_reclamacoes.json")
        if not resumo:
            st.info("Nenhuma categoria processada ainda. Execute `python pipelines/02_genai_reviews.py`.")
        else:
            categoria = st.selectbox("Categoria", list(resumo.keys()))
            dados = resumo[categoria]

            if not dados:
                st.info("Sem dados para esta categoria.")
            elif "erro" in dados:
                st.error(f"Erro ao processar categoria: {dados.get('raw', '')}")
            else:
                col_a, col_b = st.columns([1, 1])

                with col_a:
                    st.subheader("Principais reclamações")
                    for rec in dados.get("principais_reclamacoes", []):
                        st.write(f"• {rec}")

                    tom = dados.get("tom_predominante", "—")
                    st.caption(f"Tom predominante: **{tom}**")

                with col_b:
                    causa = dados.get("causa_raiz_provavel", "—")
                    acao = dados.get("recomendacao_acao", "—")
                    st.info(f"**Causa-raiz:** {causa}")
                    st.success(f"**Recomendação:** {acao}")

# ── Tab 3: Relatório Executivo ────────────────────────────────────────────────

with aba3:
    relatorio_path = OUTPUTS / "relatorio_executivo.md"
    if not relatorio_path.exists():
        st.warning("Execute `python pipelines/03_relatorio.py` primeiro.")
    else:
        st.markdown(relatorio_path.read_text(encoding="utf-8"))

# ── Tab 4: Assistente ─────────────────────────────────────────────────────────

with aba4:
    groq_client = get_groq_client()

    if groq_client is None:
        st.error("GROQ_API_KEY não encontrada. Adicione a chave ao arquivo `.env`.")
    else:
        system_prompt = cached_system_prompt()

        if not load_context():
            st.warning(
                "Nenhum output encontrado. Execute os pipelines 01, 02 e 03 primeiro."
            )
        else:
            st.caption("Assistente com contexto dos dados Olist. Responde apenas com base nos outputs gerados.")

            # Initialise conversation history in session state
            if "chat_messages" not in st.session_state:
                st.session_state.chat_messages = []

            # Render existing messages
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # Handle new user input
            if prompt := st.chat_input("Faça uma pergunta sobre os dados operacionais..."):
                st.session_state.chat_messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Consultando os dados..."):
                        reply = get_response(
                            groq_client,
                            system_prompt,
                            st.session_state.chat_messages,
                        )
                    st.markdown(reply)

                st.session_state.chat_messages.append({"role": "assistant", "content": reply})
