"""Detección de PII contextual (nombres, direcciones) vía LangGraph + Ollama.

Grafo de 2 nodos: extract_candidates -> verify_candidates.
El checkpointer SQLite persiste el estado de cada nodo por job_id,
eso ES la trazabilidad/auditoría del proceso (no hay logging custom aparte).
"""
import json
import os
import re
import time
from pathlib import Path
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

MODEL = os.environ.get("PIIGUARD_LLM_MODEL", "gemma3")

PROMPTS_DIR = Path(__file__).parent / "prompts"
EXTRACT_PROMPT = PROMPTS_DIR.joinpath("extract_candidates.txt").read_text()
VERIFY_PROMPT = PROMPTS_DIR.joinpath("verify_candidates.txt").read_text()


class GraphState(TypedDict):
    text: str
    candidates: list[dict]
    verified: list[dict]
    timings: dict[str, float]


def _timed(name):
    """Mide cuánto tarda un nodo y lo acumula en state['timings']."""

    def decorator(fn):
        def wrapper(state: GraphState) -> dict:
            start = time.perf_counter()
            update = fn(state)
            elapsed = time.perf_counter() - start
            timings = {**state.get("timings", {}), name: elapsed}
            return {**update, "timings": timings}

        return wrapper

    return decorator


def _parse_json_list(raw: str) -> list[dict]:
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return []
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return []


@_timed("extract_candidates")
def _extract_candidates(state: GraphState) -> dict:
    llm = ChatOllama(model=MODEL, temperature=0)
    resp = llm.invoke(EXTRACT_PROMPT.format(text=state["text"]))
    return {"candidates": _parse_json_list(resp.content)}


@_timed("verify_candidates")
def _verify_candidates(state: GraphState) -> dict:
    if not state["candidates"]:
        return {"verified": []}
    llm = ChatOllama(model=MODEL, temperature=0)
    resp = llm.invoke(
        VERIFY_PROMPT.format(
            candidates=json.dumps(state["candidates"], ensure_ascii=False),
            text=state["text"],
        )
    )
    return {"verified": _parse_json_list(resp.content)}


def _build_graph() -> StateGraph:
    graph = StateGraph(GraphState)
    graph.add_node("extract_candidates", _extract_candidates)
    graph.add_node("verify_candidates", _verify_candidates)
    graph.add_edge(START, "extract_candidates")
    graph.add_edge("extract_candidates", "verify_candidates")
    graph.add_edge("verify_candidates", END)
    return graph


def detect_llm(text: str, job_id: str, db_path: str) -> tuple[list[dict], dict[str, float]]:
    """Corre el grafo para un job. El trace queda en db_path bajo thread_id=job_id.

    Devuelve (candidatos_verificados, timings_por_nodo).
    """
    with SqliteSaver.from_conn_string(db_path) as checkpointer:
        app = _build_graph().compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": job_id}}
        result = app.invoke(
            {"text": text, "candidates": [], "verified": [], "timings": {}}, config=config
        )
    return result["verified"], result["timings"]


def demo():
    """Requiere Ollama corriendo local con MODEL disponible (`ollama pull <modelo>`)."""
    import tempfile

    text = "Juan Perez vive en Av. Siempre Viva 742. La empresa Acme SPA factura mensualmente."
    with tempfile.NamedTemporaryFile(suffix=".sqlite") as f:
        verified, timings = detect_llm(text, job_id="demo-1", db_path=f.name)
    assert set(timings) == {"extract_candidates", "verify_candidates"}, timings
    print("detect_llm OK:", verified, timings)


if __name__ == "__main__":
    demo()
