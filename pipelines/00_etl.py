"""
Pipeline 00 — ETL
Consolida as 8 tabelas brutas do Kaggle em olist_master.parquet.
"""
from datetime import datetime
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
PROCESSED = Path("data/processed")


def load_raw_tables() -> dict[str, pd.DataFrame]:
    return {
        "orders": pd.read_csv(
            RAW / "olist_orders_dataset.csv",
            parse_dates=[
                "order_purchase_timestamp",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ],
        ),
        "items": pd.read_csv(RAW / "olist_order_items_dataset.csv"),
        "payments": pd.read_csv(RAW / "olist_order_payments_dataset.csv"),
        "reviews": pd.read_csv(RAW / "olist_order_reviews_dataset.csv"),
        "customers": pd.read_csv(RAW / "olist_customers_dataset.csv"),
        "products": pd.read_csv(RAW / "olist_products_dataset.csv"),
        "sellers": pd.read_csv(RAW / "olist_sellers_dataset.csv"),
        "translation": pd.read_csv(RAW / "product_category_name_translation.csv"),
    }


def merge_tables(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    # Aggregate items to one row per order before merging
    items_agg = (
        raw["items"]
        .groupby("order_id")
        .agg(
            valor_total=("price", "sum"),
            qtd_itens=("order_item_id", "count"),
            product_id=("product_id", "first"),
            seller_id=("seller_id", "first"),
        )
        .reset_index()
    )

    # Aggregate payments to one row per order (some orders split across types)
    payments_agg = (
        raw["payments"]
        .groupby("order_id")
        .agg(
            forma_pagamento=("payment_type", "first"),
            parcelas=("payment_installments", "max"),
        )
        .reset_index()
    )

    # Keep one review per order (rare duplicates exist in the dataset)
    reviews_dedup = (
        raw["reviews"][["order_id", "review_score", "review_comment_message"]]
        .drop_duplicates("order_id")
    )

    df = (
        raw["orders"]
        .merge(items_agg, on="order_id", how="left", validate="m:1")
        .merge(payments_agg, on="order_id", how="left", validate="m:1")
        .merge(reviews_dedup, on="order_id", how="left", validate="m:1")
        .merge(
            raw["customers"][["customer_id", "customer_state", "customer_city"]],
            on="customer_id",
            how="left",
            validate="m:1",
        )
        .merge(
            raw["products"][["product_id", "product_category_name"]],
            on="product_id",
            how="left",
            validate="m:1",
        )
        .merge(raw["translation"], on="product_category_name", how="left", validate="m:1")
        .merge(
            raw["sellers"][["seller_id", "seller_state"]],
            on="seller_id",
            how="left",
            validate="m:1",
        )
    )

    # Derived columns
    df["dias_entrega_real"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.days
    df["dias_entrega_estimado"] = (
        df["order_estimated_delivery_date"] - df["order_purchase_timestamp"]
    ).dt.days
    df["atraso_dias"] = df["dias_entrega_real"] - df["dias_entrega_estimado"]
    df["atrasado"] = df["atraso_dias"] > 0
    df["mes_ano"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    df["faixa_nota"] = pd.cut(
        df["review_score"],
        bins=[0, 2, 3, 5],
        labels=["insatisfeito", "neutro", "satisfeito"],
    )
    df["processed_at"] = datetime.now().isoformat()

    return df


def save_master(df: pd.DataFrame) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED / "olist_master.parquet", index=False)


if __name__ == "__main__":
    print("Carregando tabelas brutas...")
    raw = load_raw_tables()
    for name, table in raw.items():
        print(f"  {name}: {len(table):,} linhas")

    print("\nExecutando merges e colunas derivadas...")
    master = merge_tables(raw)

    print(f"\nSalvando olist_master.parquet...")
    save_master(master)

    print(f"\nETL concluído:")
    print(f"  Linhas : {len(master):,}")
    print(f"  Colunas: {master.shape[1]}")
    print(f"  Colunas: {list(master.columns)}")
