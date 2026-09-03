"""Persistencia del mapping token<->valor original (SQLite, un archivo)."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "piiguard.db"


def init_db(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")  # concurrent writers (team use) without lock errors
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mapping (
            job_id TEXT NOT NULL,
            token TEXT NOT NULL,
            type TEXT NOT NULL,
            value TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # un row por archivo procesado, aunque no tenga PII detectada
    # (mapping solo tiene rows cuando hay campos anonimizados).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS timings (
            job_id TEXT NOT NULL,
            phase TEXT NOT NULL,
            duration_seconds REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def record_job(job_id: str, filename: str, db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO jobs (job_id, filename) VALUES (?, ?)", (job_id, filename))
    conn.commit()
    conn.close()


def save_mapping(job_id: str, mapping: list[dict], db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO mapping (job_id, token, type, value) VALUES (?, ?, ?, ?)",
        [(job_id, m["token"], m["type"], m["value"]) for m in mapping],
    )
    conn.commit()
    conn.close()


def save_timings(job_id: str, timings: dict[str, float], db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO timings (job_id, phase, duration_seconds) VALUES (?, ?, ?)",
        [(job_id, phase, duration) for phase, duration in timings.items()],
    )
    conn.commit()
    conn.close()


def get_stats(db_path: Path = DB_PATH) -> dict:
    conn = sqlite3.connect(db_path)
    files_processed = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    fields_anonymized = conn.execute("SELECT COUNT(*) FROM mapping").fetchone()[0]
    conn.close()
    return {"files_processed": files_processed, "fields_anonymized": fields_anonymized}


def demo():
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".sqlite") as f:
        init_db(f.name)
        record_job("job-1", "test.txt", f.name)
        save_mapping("job-1", [{"token": "[NAME_1]", "type": "NAME", "value": "Juan Perez"}], f.name)
        conn = sqlite3.connect(f.name)
        rows = conn.execute("SELECT job_id, token, value FROM mapping").fetchall()
        conn.close()
        assert rows == [("job-1", "[NAME_1]", "Juan Perez")], rows
        stats = get_stats(f.name)
        assert stats == {"files_processed": 1, "fields_anonymized": 1}, stats
        save_timings("job-1", {"detect_regex": 0.01, "ai.total": 1.2}, f.name)
        conn = sqlite3.connect(f.name)
        timing_rows = conn.execute("SELECT phase, duration_seconds FROM timings").fetchall()
        conn.close()
        assert dict(timing_rows) == {"detect_regex": 0.01, "ai.total": 1.2}, timing_rows
    print("storage OK:", rows, stats, timing_rows)


if __name__ == "__main__":
    demo()
