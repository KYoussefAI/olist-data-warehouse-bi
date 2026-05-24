from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import NoReturn

from sqlalchemy.exc import OperationalError

from .config import settings
from .db import execute_sql_file, get_engine
from .extract_load_raw import load_all_raw
from .load_dwh import load_dwh
from .quality_checks import print_quality_report, run_quality_checks
from .transform_staging import build_staging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def _raise_database_unavailable(exc: OperationalError) -> NoReturn:
    logger.error(
        "Could not connect to PostgreSQL. Start the database first and verify "
        "DATABASE_URL. Current value: %s",
        settings.database_url,
    )
    raise SystemExit(1) from exc


def create_schema() -> None:
    engine = get_engine()
    execute_sql_file(engine, settings.schema_sql_path)
    logger.info("Schemas and tables are ready")


def create_marts() -> None:
    engine = get_engine()
    execute_sql_file(engine, settings.marts_sql_path)
    logger.info("Marts are ready")


def run_all(raw_data_dir: Path | None = None, fail_fast_quality: bool = False) -> None:
    engine = get_engine()
    logger.info("Starting full Olist ELT pipeline")

    execute_sql_file(engine, settings.schema_sql_path)
    load_all_raw(engine, raw_data_dir or settings.raw_data_dir)
    build_staging(engine)
    load_dwh(engine)
    execute_sql_file(engine, settings.marts_sql_path)
    results = run_quality_checks(engine, fail_fast=fail_fast_quality)
    print_quality_report(results)

    logger.info("Pipeline completed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Olist PostgreSQL ELT pipeline.")
    parser.add_argument(
        "--step",
        choices=["schema", "raw", "staging", "dwh", "marts", "quality", "all"],
        default="all",
        help="Pipeline step to run.",
    )
    parser.add_argument(
        "--raw-data-dir",
        type=Path,
        default=settings.raw_data_dir,
        help="Path to the folder containing raw CSV files.",
    )
    parser.add_argument(
        "--fail-fast-quality",
        action="store_true",
        help="Raise an error if a quality check fails.",
    )
    args = parser.parse_args()

    engine = get_engine()

    if args.step == "schema":
        execute_sql_file(engine, settings.schema_sql_path)
    elif args.step == "raw":
        load_all_raw(engine, args.raw_data_dir)
    elif args.step == "staging":
        build_staging(engine)
    elif args.step == "dwh":
        load_dwh(engine)
    elif args.step == "marts":
        execute_sql_file(engine, settings.marts_sql_path)
    elif args.step == "quality":
        results = run_quality_checks(engine, fail_fast=args.fail_fast_quality)
        print_quality_report(results)
    elif args.step == "all":
        run_all(args.raw_data_dir, args.fail_fast_quality)


if __name__ == "__main__":
    try:
        main()
    except OperationalError as exc:
        _raise_database_unavailable(exc)
