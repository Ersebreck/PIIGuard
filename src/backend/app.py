"""PIIGuard - esqueleto. Camino .md end-to-end: upload -> detect -> anonimiza -> descarga.

Correr desde src/: uvicorn backend.app:app --reload
Requiere Ollama corriendo local (ver PIIGUARD_LLM_MODEL en ai/detect_graph.py).
"""
import asyncio
import io
import json
import os
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile
from fastapi.responses import HTMLResponse, Response
from markitdown import MarkItDown

from ai.detect_graph import detect_llm
from backend.anonymize import anonymize
from backend.detect_regex import detect_regex
from backend.storage import DB_PATH, get_stats, init_db, record_job, save_mapping, save_timings

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app = FastAPI(title="PIIGuard")
init_db()

# ponytail: fixed cap on concurrent local-LLM calls so a burst of uploads queues
# instead of piling every request onto one Ollama instance at once. Raise via
# PIIGUARD_MAX_CONCURRENT_LLM if/when this runs on beefier hardware.
LLM_SEMAPHORE = asyncio.Semaphore(int(os.environ.get("PIIGUARD_MAX_CONCURRENT_LLM", "2")))


def extract_text(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext in (".txt", ".md"):
        return content.decode("utf-8", errors="ignore")
    result = MarkItDown().convert_stream(io.BytesIO(content), file_extension=ext)
    return result.markdown


@app.get("/", response_class=HTMLResponse)
def index():
    return FRONTEND_DIR.joinpath("index.html").read_text()


@app.post("/anonymize")
async def anonymize_file(file: UploadFile):
    t0 = time.perf_counter()
    content = await file.read()

    t = time.perf_counter()
    text = await asyncio.to_thread(extract_text, file.filename, content)
    timings = {"extract_text": time.perf_counter() - t}

    job_id = uuid.uuid4().hex
    record_job(job_id, file.filename)

    t = time.perf_counter()
    regex_matches = detect_regex(text)
    timings["detect_regex"] = time.perf_counter() - t

    t = time.perf_counter()
    async with LLM_SEMAPHORE:
        llm_matches, ai_timings = await asyncio.to_thread(detect_llm, text, job_id, str(DB_PATH))
    timings["ai.total"] = time.perf_counter() - t
    timings.update({f"ai.{k}": v for k, v in ai_timings.items()})

    t = time.perf_counter()
    anonymized_text, mapping = anonymize(text, regex_matches + llm_matches)
    timings["anonymize"] = time.perf_counter() - t

    save_mapping(job_id, mapping)
    timings["total"] = time.perf_counter() - t0
    save_timings(job_id, timings)

    out_name = Path(file.filename).stem + ".md"
    return Response(
        content=anonymized_text,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{out_name}"',
            "X-Job-Id": job_id,
            "X-Timings": json.dumps(timings),
        },
    )


@app.get("/stats")
def stats():
    return get_stats()
