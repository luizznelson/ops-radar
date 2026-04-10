# CLAUDE.md

Contexto do projeto para uso com Claude Code.
Leia este arquivo antes de qualquer tarefa neste repositório.

---

## O que é este projeto

Pipeline de inteligência operacional sobre o dataset público da Olist
(e-commerce brasileiro, 100k pedidos reais, Kaggle).

Não é um projeto de ciência de dados ou ML. É automação de processos com dados e GenAI aplicada.

Quatro pipelines sequenciais:
1. `00_etl.py` — consolida 9 tabelas brutas em parquet
2. `01_diagnostico.py` — identifica gargalos operacionais automaticamente
3. `02_genai_reviews.py` — sumariza reclamações por categoria via LLM
4. `03_relatorio.py` — gera relatório executivo em Markdown via LLM

Entrega final: dashboard Streamlit com link público permanente.

---

## Estrutura de pastas

```
olist-ops-intelligence/
├── data/
│   ├── raw/                        # CSVs do Kaggle — NÃO versionar
│   └── processed/
│       └── olist_master.parquet    # Gerado por 00_etl.py
├── pipelines/
│   ├── 00_etl.py
│   ├── 01_diagnostico.py
│   ├── 02_genai_reviews.py
│   └── 03_relatorio.py
├── app/
│   └── dashboard.py
├── outputs/                        # Gerado pelos pipelines — NÃO versionar
│   ├── diagnostico.json
│   ├── resumo_reclamacoes.json
│   └── relatorio_executivo.md
├── notebooks/
│   └── exploracao.ipynb            # Rascunho — não é entrega
├── .env                            # NÃO versionar
├── .env.example
├── requirements.txt
├── CLAUDE.md
└── README.md
```

---

## Variáveis de ambiente

```bash
GROQ_API_KEY=...   # console.groq.com — gratuito
```

Carregue sempre com `load_dotenv()` + `os.getenv()`. Nunca hardcode. Nunca commite `.env`.

---

## Dados

### Fonte
`olistbr/brazilian-ecommerce` no Kaggle. Extrair CSVs em `data/raw/` manualmente.

### Tabelas originais relevantes

| Arquivo | Uso |
|---------|-----|
| `olist_orders_dataset.csv` | Base principal — status, datas |
| `olist_order_items_dataset.csv` | Valor, produto, vendedor por pedido |
| `olist_order_payments_dataset.csv` | Forma de pagamento |
| `olist_order_reviews_dataset.csv` | Nota + texto da avaliação |
| `olist_customers_dataset.csv` | Estado, cidade |
| `olist_products_dataset.csv` | Categoria do produto |
| `olist_sellers_dataset.csv` | Estado do vendedor |
| `product_category_name_translation.csv` | Tradução PT→EN das categorias |

### Colunas derivadas em olist_master.parquet

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `dias_entrega_real` | int | Dias entre compra e entrega real |
| `dias_entrega_estimado` | int | Dias entre compra e prazo estimado |
| `atraso_dias` | int | Diferença (positivo = atrasado) |
| `atrasado` | bool | True se entregue após o prazo |
| `mes_ano` | str | Período no formato YYYY-MM |
| `faixa_nota` | category | insatisfeito / neutro / satisfeito |
| `processed_at` | str | Timestamp ISO de geração |

Sempre carregar apenas as colunas necessárias:
```python
df = pd.read_parquet("data/processed/olist_master.parquet", columns=["col_a", "col_b"])
```

---

## Pipelines — regras e contexto

### 00_etl.py
- Todos os merges com `validate="m:1"` para detectar duplicatas silenciosas
- Salvar em `.parquet` — nunca em `.csv`
- Adicionar coluna `processed_at` com `datetime.now().isoformat()`

### 01_diagnostico.py
- Filtrar apenas `order_status == "delivered"` antes de qualquer cálculo
- Saída: `outputs/diagnostico.json` com estrutura fixa (não alterar as chaves)
- Colunas `estados_criticos` e `categorias_pior_avaliacao` exigem volume mínimo (100 e 50 pedidos respectivamente) para evitar distorções

### 02_genai_reviews.py
- Usar apenas avaliações com `review_score <= 2` e `review_comment_message` não nulo
- Limitar a 30 reviews por categoria por chamada (controle de tokens)
- `temperature=0.2` — o objetivo é análise factual, não criatividade
- O prompt exige resposta em JSON puro — validar com `json.loads()` e tratar `JSONDecodeError`
- Categorias com menos de 20 reclamações são ignoradas

### 03_relatorio.py
- Depende das saídas de `01_diagnostico.py` e `02_genai_reviews.py`
- `temperature=0.3` — ligeiramente mais fluido para o texto do relatório
- Saída: `outputs/relatorio_executivo.md`

---

## app/dashboard.py — regras

- `@st.cache_data` para DataFrames
- `@st.cache_resource` para qualquer objeto que carregue modelo ou conexão
- Carregar apenas colunas necessárias do parquet — limite de memória no Streamlit Cloud
- Três abas: `KPIs Operacionais`, `Reclamações por Categoria`, `Relatório Executivo`
- Cada aba verifica se o arquivo de saída existe antes de renderizar — nunca assumir que os pipelines já rodaram

---

## Convenções de código

**Commits:**
```
pipeline(N): descrição curta no imperativo
```
Exemplos:
- `pipeline(0): ETL das 9 tabelas e geração do parquet`
- `pipeline(2): sumarização GenAI das top 10 categorias com reclamações`
- `app: dashboard com 3 abas e cache configurado`

**Funções:** funções com mais de 15 linhas saem do pipeline e viram funções nomeadas no mesmo arquivo. Sem lógica inline em blocos `if __name__ == "__main__"`.

**Outputs:** todos os arquivos gerados vão para `outputs/`. Nunca salvar resultados intermediários em `data/processed/` — esse diretório é exclusivo do ETL.

---

## O que NÃO fazer

- Não salvar dados em CSV — sempre parquet para dados tabulares
- Não commitar `data/raw/`, `data/processed/`, `outputs/`, `.env`
- Não usar `temperature` acima de 0.3 nos pipelines — factualidade é prioridade
- Não carregar `olist_master.parquet` completo no dashboard — sempre filtrar colunas
- Não criar novos pipelines fora da sequência `00_`–`03_` sem atualizar este arquivo
- Não remover o `validate="m:1"` dos merges no ETL

---

## Ordem de execução obrigatória

```
1. Extrair CSVs do Kaggle → data/raw/
2. python pipelines/00_etl.py
3. python pipelines/01_diagnostico.py
4. python pipelines/02_genai_reviews.py
5. python pipelines/03_relatorio.py
6. streamlit run app/dashboard.py
```

Os passos 3, 4 e 5 dependem da saída do passo anterior. Não pular etapas.

---

## LLM — modelo e limites

| Parâmetro | Valor |
|-----------|-------|
| Provedor | Groq (gratuito) |
| Modelo | `llama-3.1-8b-instant` |
| Context window | 8.192 tokens |
| Limite gratuito | 14.400 req/dia |
| temperature (análise) | 0.2 |
| temperature (relatório) | 0.3 |

Se o limite diário for atingido durante desenvolvimento, aguardar reset (meia-noite UTC) ou reduzir o número de categorias processadas em `02_genai_reviews.py`.
