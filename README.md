# Olist Ops Intelligence

[![Demo ao vivo](https://img.shields.io/badge/Demo-Streamlit%20Cloud-FF4B4B?logo=streamlit)](https://ops-radar-b2kguj4mcnpgq78ybvsdxk.streamlit.app/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Luiz%20Nelson-0A66C2?logo=linkedin)](https://www.linkedin.com/in/luiznelson)
[![GitHub](https://img.shields.io/badge/GitHub-luizznelson-181717?logo=github)](https://github.com/luizznelson)

---

## O que este projeto faz

Empresas de e-commerce produzem milhares de pedidos por dia, mas raramente conseguem transformar esse volume de dados em decisões rápidas. Este projeto constrói um pipeline completo de inteligência operacional sobre o dataset público da Olist — com 99 mil pedidos reais do e-commerce brasileiro — que identifica automaticamente gargalos de entrega por estado e categoria de produto, usa inteligência artificial para resumir as principais reclamações dos clientes, e gera um relatório executivo em linguagem de negócio sem nenhuma intervenção humana. O resultado é um painel interativo acessível pelo navegador, com um assistente de dados integrado que responde perguntas em linguagem natural sobre os números do negócio.

---

## Resultados concretos

| Resultado | Detalhe |
|-----------|---------|
| **Diagnóstico automático de atrasos** | 7,6% dos pedidos entregues chegam fora do prazo — pedidos atrasados têm nota média 1,83 estrelas menor que os pontuais |
| **Mapa de risco por estado** | AL (22,9%), MA (18,8%) e SE (15,2%) lideram a taxa de atraso entre os estados com volume relevante |
| **Resumo de reclamações por IA** | Reclamações negativas agrupadas por categoria de produto, com causa-raiz e recomendação de ação geradas automaticamente |
| **Relatório executivo sem intervenção humana** | Documento em Markdown gerado por LLM, pronto para enviar a um gestor, combinando dados quantitativos e qualitativos |

---

## Como funciona

O projeto é composto por quatro etapas sequenciais e um painel de visualização.

### Etapa 1 — Consolidação dos dados
Nove tabelas brutas do Kaggle (pedidos, itens, pagamentos, avaliações, clientes, produtos, vendedores e traduções) são unificadas em uma única base analítica confiável. O processo valida a integridade de cada junção e calcula colunas derivadas como dias de atraso, nota por faixa e período do pedido.

### Etapa 2 — Diagnóstico operacional automático
A base consolidada é analisada automaticamente para identificar: taxa de atraso geral, estados com maior concentração de atrasos, categorias de produto com pior avaliação e a tendência mensal dos últimos 12 meses. Tudo salvo em um arquivo estruturado, sem intervenção manual.

### Etapa 3 — Sumarização de reclamações com IA
As avaliações negativas (nota 1 ou 2) são agrupadas por categoria de produto e enviadas a um modelo de linguagem (Llama 3 via Groq). Para cada categoria, a IA retorna as principais reclamações, a causa-raiz provável, uma recomendação de ação e o tom emocional predominante dos clientes.

### Etapa 4 — Relatório executivo gerado por IA
Os resultados das etapas 2 e 3 são combinados e enviados ao modelo, que escreve um relatório executivo completo em Markdown — estruturado em Resumo Executivo, Principais Problemas e Recomendações Prioritárias — em linguagem direta, sem jargão técnico.

### Painel interativo
Um dashboard Streamlit com quatro abas reúne tudo em um só lugar:
- **KPIs Operacionais** — métricas e gráficos de atraso por período e por estado
- **Reclamações por Categoria** — resumos da IA por categoria de produto
- **Relatório Executivo** — o documento gerado automaticamente
- **Assistente** — chat em linguagem natural que responde perguntas sobre os dados

---

## Stack

Python · Pandas · PyArrow · Plotly · Streamlit · Groq API (Llama 3.1) · python-dotenv

---

## Estrutura do projeto

```
olist-analytics/
├── data/
│   ├── raw/                  # CSVs originais do Kaggle (não versionados)
│   └── processed/            # Base analítica consolidada (gerada pelo ETL)
├── pipelines/
│   ├── 00_etl.py             # Unifica as 9 tabelas e calcula colunas derivadas
│   ├── 01_diagnostico.py     # Diagnóstico automático de gargalos operacionais
│   ├── 02_genai_reviews.py   # Sumarização de reclamações com IA por categoria
│   └── 03_relatorio.py       # Geração automática do relatório executivo
├── app/
│   ├── dashboard.py          # Painel Streamlit com 4 abas
│   └── chat.py               # Lógica do assistente de dados
├── outputs/                  # JSONs e Markdown gerados pelos pipelines
├── .env.example              # Modelo de variáveis de ambiente
├── requirements.txt          # Dependências do projeto
└── CLAUDE.md                 # Contexto do projeto para desenvolvimento com IA
```

---

## Como rodar localmente

**Pré-requisitos:** Python 3.11+, conta gratuita no [Groq](https://console.groq.com) para obter a API key.

```bash
# 1. Clone o repositório e instale as dependências
git clone https://github.com/luizznelson/olist-ops-intelligence.git
cd olist-ops-intelligence
pip install -r requirements.txt

# 2. Configure a API key
cp .env.example .env
# Edite o .env e adicione sua GROQ_API_KEY

# 3. Baixe os dados
# Acesse kaggle.com/datasets/olistbr/brazilian-ecommerce
# Extraia os CSVs em data/raw/

# 4. Execute os pipelines em ordem
python pipelines/00_etl.py
python pipelines/01_diagnostico.py
python pipelines/02_genai_reviews.py
python pipelines/03_relatorio.py

# 5. Abra o painel
streamlit run app/dashboard.py
```

---

## Sobre o autor

Analista com foco em automação de processos, dados e GenAI aplicada. Este projeto foi desenvolvido como demonstração prática de como transformar dados brutos em inteligência operacional de forma autônoma — da ingestão ao relatório executivo.

- [LinkedIn](https://www.linkedin.com/in/luiznelson)
- [GitHub](https://github.com/luizznelson)
