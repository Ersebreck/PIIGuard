import sqlite3

import pytest

from backend.storage import get_stats, init_db, record_job, save_mapping, save_timings


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.sqlite"
    init_db(path)
    return path


def test_record_job_and_mapping_feed_stats(db_path):
    record_job("job-1", "test.txt", db_path)
    save_mapping(
        "job-1", [{"token": "[NAME_1]", "type": "NAME", "value": "Juan Perez"}], db_path
    )
    assert get_stats(db_path) == {"files_processed": 1, "fields_anonymized": 1}


def test_save_timings(db_path):
    save_timings("job-1", {"detect_regex": 0.01, "ai.total": 1.2}, db_path)
    conn = sqlite3.connect(db_path)
    rows = dict(conn.execute("SELECT phase, duration_seconds FROM timings").fetchall())
    conn.close()
    assert rows == {"detect_regex": 0.01, "ai.total": 1.2}
