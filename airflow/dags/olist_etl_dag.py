"""Optional Apache Airflow DAG for the Olist ETL pipeline.

This DAG assumes the project is available inside the Airflow worker and that
DATABASE_URL / RAW_DATA_DIR are configured as environment variables.
"""

from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="olist_postgres_elt_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["olist", "postgres", "elt", "portfolio"],
) as dag:
    create_schema = BashOperator(
        task_id="create_schema",
        bash_command="python -m src.run_etl --step schema",
    )

    load_raw = BashOperator(
        task_id="load_raw_csvs",
        bash_command="python -m src.run_etl --step raw",
    )

    build_staging = BashOperator(
        task_id="build_staging",
        bash_command="python -m src.run_etl --step staging",
    )

    load_dwh = BashOperator(
        task_id="load_dwh",
        bash_command="python -m src.run_etl --step dwh",
    )

    build_marts = BashOperator(
        task_id="build_marts",
        bash_command="python -m src.run_etl --step marts",
    )

    run_quality = BashOperator(
        task_id="run_quality_checks",
        bash_command="python -m src.run_etl --step quality --fail-fast-quality",
    )

    create_schema >> load_raw >> build_staging >> load_dwh >> build_marts >> run_quality
