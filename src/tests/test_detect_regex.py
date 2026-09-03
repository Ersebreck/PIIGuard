from backend.detect_regex import detect_regex


def test_detects_email_phone_nit_id_number():
    text = (
        "Contacto: Juan Perez, juan.perez@empresa.co, +56 9 1234 5678, "
        "Cedula 79523148, NIT 900.123.456-7."
    )
    matches = detect_regex(text)
    types = {m["type"] for m in matches}
    assert types == {"EMAIL", "PHONE", "ID_NUMBER", "NIT"}
    assert {"type": "EMAIL", "value": "juan.perez@empresa.co"} in matches
    assert {"type": "NIT", "value": "900.123.456-7"} in matches
    assert {"type": "ID_NUMBER", "value": "79523148"} in matches


def test_no_false_positive_on_plain_text():
    assert detect_regex("Hola, esto es un texto sin PII estructurada.") == []
