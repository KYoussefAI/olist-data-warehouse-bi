from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    def load_dotenv() -> bool:
        return False

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://olist:olist@localhost:5432/olist_dw",
    )
    raw_data_dir: Path = Path(os.getenv("RAW_DATA_DIR", "data/raw"))
    project_root: Path = Path(__file__).resolve().parents[1]

    @property
    def sql_dir(self) -> Path:
        return self.project_root / "sql"

    @property
    def schema_sql_path(self) -> Path:
        candidates = [
            self.sql_dir / "00_create_schemas_and_tables.sql",
            self.sql_dir / "olist_postgresql_ddl.sql",
        ]
        for path in candidates:
            if path.exists():
                return path
        return candidates[0]

    @property
    def marts_sql_path(self) -> Path:
        candidates = [
            self.sql_dir / "01_create_marts.sql",
            self.sql_dir / "olist_postgresql_ddl.sql",
        ]
        for path in candidates:
            if path.exists():
                return path
        return candidates[0]

    @property
    def quality_sql_path(self) -> Path:
        return self.sql_dir / "99_quality_checks.sql"


settings = Settings()
