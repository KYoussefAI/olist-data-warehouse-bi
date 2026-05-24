from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


@dataclass
class QualityCheckResult:
    name: str
    value: Any
    passed: bool
    expectation: str


CHECKS = [
    (
        "raw_orders_loaded",
        "SELECT COUNT(*) FROM raw.olist_orders",
        lambda x: x > 0,
        "> 0 rows",
    ),
    (
        "dwh_fact_orders_loaded",
        "SELECT COUNT(*) FROM dwh.fact_orders",
        lambda x: x > 0,
        "> 0 rows",
    ),
    (
        "fact_order_items_missing_order_key",
        "SELECT COUNT(*) FROM dwh.fact_order_items WHERE order_key IS NULL",
        lambda x: x == 0,
        "0 missing order_key",
    ),
    (
        "fact_order_items_missing_product_key",
        "SELECT COUNT(*) FROM dwh.fact_order_items WHERE product_key IS NULL",
        lambda x: x == 0,
        "0 missing product_key",
    ),
    (
        "fact_order_items_missing_seller_key",
        "SELECT COUNT(*) FROM dwh.fact_order_items WHERE seller_key IS NULL",
        lambda x: x == 0,
        "0 missing seller_key",
    ),
    (
        "fact_payments_missing_order_key",
        "SELECT COUNT(*) FROM dwh.fact_payments WHERE order_key IS NULL",
        lambda x: x == 0,
        "0 missing order_key",
    ),
    (
        "fact_reviews_missing_order_key",
        "SELECT COUNT(*) FROM dwh.fact_reviews WHERE order_key IS NULL",
        lambda x: x == 0,
        "0 missing order_key",
    ),
    (
        "reviews_outside_1_5",
        "SELECT COUNT(*) FROM dwh.fact_reviews WHERE review_score NOT BETWEEN 1 AND 5",
        lambda x: x == 0,
        "0 reviews outside 1..5",
    ),
]


def run_quality_checks(engine: Engine, fail_fast: bool = False) -> list[QualityCheckResult]:
    results: list[QualityCheckResult] = []
    with engine.connect() as conn:
        for name, sql, predicate, expectation in CHECKS:
            value = conn.execute(text(sql)).scalar()
            passed = bool(predicate(value))
            result = QualityCheckResult(name, value, passed, expectation)
            results.append(result)
            status = "PASS" if passed else "FAIL"
            logger.info("%s | %s | value=%s | expected=%s", status, name, value, expectation)
            if fail_fast and not passed:
                raise RuntimeError(f"Quality check failed: {name}. Value={value}, expected={expectation}")
    return results


def print_quality_report(results: list[QualityCheckResult]) -> None:
    print("\nQuality check report")
    print("-" * 80)
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"{status:4} | {r.name:40} | value={r.value!s:10} | expected={r.expectation}")
    print("-" * 80)
    failed = [r for r in results if not r.passed]
    print(f"Total checks: {len(results)} | Failed: {len(failed)}")
