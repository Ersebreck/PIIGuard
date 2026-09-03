from backend.anonymize import anonymize


def test_same_value_gets_same_token():
    text = "Juan Perez (juan@empresa.co) vive en Av. Siempre Viva 742. Contactar a Juan Perez."
    matches = [
        {"type": "NAME", "value": "Juan Perez"},
        {"type": "EMAIL", "value": "juan@empresa.co"},
        {"type": "ADDRESS", "value": "Av. Siempre Viva 742"},
    ]
    result, mapping = anonymize(text, matches)
    assert "Juan Perez" not in result
    assert result.count("[NAME_1]") == 2
    assert len(mapping) == 3


def test_no_matches_returns_text_unchanged():
    result, mapping = anonymize("texto sin PII", [])
    assert result == "texto sin PII"
    assert mapping == []
