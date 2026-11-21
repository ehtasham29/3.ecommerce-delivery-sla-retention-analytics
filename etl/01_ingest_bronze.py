import os
import time
from urllib.parse import quote_plus
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 1. Load environment variables securely from .env
load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = quote_plus(os.getenv("MYSQL_PASSWORD", ""))  # Safely escapes '@', '#', '$'
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
RAW_DATA_DIR = os.path.join("data", "raw")

# 2. Explicit mapping of all 9 Kaggle Olist CSVs -> MySQL Bronze table names
FILES_TO_TABLES = {
    "olist_customers_dataset.csv": "customers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_orders_dataset.csv": "orders",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",    
}

# 3. All timestamp columns across the 9 tables to cast into proper DATETIME
DATE_COLS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "shipping_limit_date",
    "review_creation_date",
    "review_answer_timestamp",
]

bronze_engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/olist_bronze"
)
audit_engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/olist_audit"
)


def log_audit(table_name, row_count, col_count, null_cells, duration, status, error_msg=None):
    with audit_engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO etl_run_log 
                    (layer, table_name, row_count, column_count, total_null_cells, duration_sec, status, error_message)
                VALUES 
                    (:layer, :table_name, :row_count, :col_count, :null_cells, :duration, :status, :error_msg)
            """),
            {
                "layer": "bronze",
                "table_name": table_name,
                "row_count": row_count,
                "col_count": col_count,
                "null_cells": null_cells,
                "duration": round(duration, 2),
                "status": status,
                "error_msg": error_msg,
            },
        )


def ingest_bronze():
    print("Starting Bronze Layer Ingestion...\n" + "-" * 65)
    for filename, table_name in FILES_TO_TABLES.items():
        start_time = time.time()
        filepath = os.path.join(RAW_DATA_DIR, filename)

        if not os.path.exists(filepath):
            print(f"[MISSING] {filepath} not found.")
            log_audit(table_name, 0, 0, 0, 0.0, "MISSING_FILE", f"File not found: {filepath}")
            continue

        try:
            df = pd.read_csv(filepath)

            # Parse timestamp columns safely into datetime64[ns]
            for col in DATE_COLS:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

            # Batch insert (chunksize=10000 prevents MySQL max_allowed_packet errors on 1M geolocation rows)
            df.to_sql(
                name=table_name,
                con=bronze_engine,
                if_exists="replace",
                index=False,
                chunksize=10000,
                method="multi",
            )

            elapsed = time.time() - start_time
            row_count, col_count = df.shape
            null_cells = int(df.isna().sum().sum())

            log_audit(table_name, row_count, col_count, null_cells, elapsed, "SUCCESS")
            print(
                f"[SUCCESS] olist_bronze.{table_name:<22} | Rows: {row_count:>9,} | "
                f"Nulls: {null_cells:>7,} | Time: {elapsed:>5.2f}s"
            )

        except Exception as exc:
            elapsed = time.time() - start_time
            log_audit(table_name, 0, 0, 0, elapsed, "FAILED", str(exc))
            print(f"[FAILED]  olist_bronze.{table_name:<22} | Error: {exc}")


if __name__ == "__main__":
    ingest_bronze()