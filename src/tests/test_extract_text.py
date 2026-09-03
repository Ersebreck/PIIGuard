"""Prueba extract_text contra los fixtures reales en test_files/ (sin LLM, determinístico)."""
from pathlib import Path

import pytest

from backend.app import extract_text

TEST_FILES = Path(__file__).parent.parent.parent / "test_files"


@pytest.mark.parametrize("filename", ["sample.md", "sample.docx", "sample.pdf", "sample.xlsx"])
def test_extracts_known_pii_substring(filename):
    content = (TEST_FILES / filename).read_bytes()
    text = extract_text(filename, content)
    assert "camila.torres@clientelatam.com" in text
    assert "1032456789" in text
