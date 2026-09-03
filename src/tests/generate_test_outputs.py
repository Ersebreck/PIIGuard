"""Corre el pipeline completo sobre cada fixture de test_files/ y guarda el
resultado en test_files/output/ para comparar a ojo. No es un test (no lo
recoge pytest) porque el LLM no es 100% determinístico entre corridas -
para eso están los tests reales en tests/ y la evaluación en eval/.

Uso: cd src && python -m tests.generate_test_outputs   (requiere Ollama corriendo local)
"""
import tempfile
from pathlib import Path

from ai.detect_graph import detect_llm
from backend.anonymize import anonymize
from backend.app import extract_text
from backend.detect_regex import detect_regex

TEST_FILES = Path(__file__).parent.parent.parent / "test_files"
OUTPUT_DIR = TEST_FILES / "output"


def run():
    OUTPUT_DIR.mkdir(exist_ok=True)
    inputs = sorted(p for p in TEST_FILES.glob("sample.*") if p.is_file())

    with tempfile.NamedTemporaryFile(suffix=".sqlite") as f:
        for path in inputs:
            text = extract_text(path.name, path.read_bytes())
            regex_matches = detect_regex(text)
            llm_matches, _timings = detect_llm(text, job_id=path.stem + path.suffix, db_path=f.name)
            anonymized_text, _mapping = anonymize(text, regex_matches + llm_matches)

            out_path = OUTPUT_DIR / f"{path.stem}_{path.suffix.lstrip('.')}.md"
            out_path.write_text(anonymized_text)
            print(f"{path.name} -> {out_path.relative_to(TEST_FILES.parent)}")


if __name__ == "__main__":
    run()
