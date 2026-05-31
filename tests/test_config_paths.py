from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import settings


def test_schema_sql_path_prefers_dedicated_schema_file():
    assert settings.schema_sql_path.name == "00_create_schemas_and_tables.sql"


def test_marts_sql_path_prefers_dedicated_marts_file():
    assert settings.marts_sql_path.name == "01_create_marts.sql"


def test_quality_sql_path_points_to_quality_checks_file():
    assert settings.quality_sql_path.name == "99_quality_checks.sql"
    assert settings.quality_sql_path == ROOT / "sql" / "99_quality_checks.sql"
