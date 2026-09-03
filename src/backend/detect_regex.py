"""Detección determinística de PII estructurada (sin LLM)."""
import re

PATTERNS = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    # Genérico LATAM: código de país +5X (1-3 dígitos) + número nacional,
    # con o sin separadores. Exige el "+" a propósito: así no choca con ID_NUMBER
    # (que siempre es dígitos sueltos, sin prefijo).
    "PHONE": re.compile(r"\+5\d{1,3}(?:[\s-]?\d{1,4}){2,5}\b"),
    # NIT Colombia: dígito de verificación separado por guion, con o sin puntos de miles.
    "NIT": re.compile(r"\b\d{1,3}(?:\.\d{3}){2,3}-\d\b|\b\d{9,10}-\d\b"),
    # ponytail: cédula/DNI/RUT no tienen dígito verificador -> cualquier número
    # de 6-10 dígitos matchea (riesgo de falsos positivos con montos, folios, y con
    # el bloque de dígitos de un NIT o de un PHONE). anonymize.py reemplaza el match
    # más largo primero, así que el texto final queda bien igual, solo deja una fila
    # de mapping huérfana. Si hace falta, ampliar con resolución de spans por posición.
    "ID_NUMBER": re.compile(r"\b\d{6,10}\b(?!-\d)"),
}


def detect_regex(text: str) -> list[dict]:
    """Devuelve matches únicos [{"type": ..., "value": ...}, ...]."""
    seen = set()
    matches = []
    for type_, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            value = m.group().strip()
            key = (type_, value)
            if value and key not in seen:
                seen.add(key)
                matches.append({"type": type_, "value": value})
    return matches


def demo():
    text = (
        "Contacto: Juan Perez, juan.perez@empresa.co, +56 9 1234 5678, "
        "Cedula 79523148, NIT 900.123.456-7."
    )
    matches = detect_regex(text)
    types = {m["type"] for m in matches}
    assert types == {"EMAIL", "PHONE", "ID_NUMBER", "NIT"}, matches
    assert {"type": "EMAIL", "value": "juan.perez@empresa.co"} in matches
    assert {"type": "NIT", "value": "900.123.456-7"} in matches
    assert {"type": "ID_NUMBER", "value": "79523148"} in matches
    print("detect_regex OK:", matches)


if __name__ == "__main__":
    demo()
