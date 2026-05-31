from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_entrypoint_exists():
    assert (ROOT / "dashboard" / "app.py").exists()


def test_required_sql_files_exist():
    assert (ROOT / "sql" / "01_create_marts.sql").exists()
    assert (ROOT / "sql" / "99_quality_checks.sql").exists()


def test_requirements_include_dashboard_dependencies():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "streamlit" in requirements.lower()
    assert "plotly" in requirements.lower()


def test_raw_data_readme_exists():
    assert (ROOT / "data" / "raw" / "README.md").exists()
