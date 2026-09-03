"""Reemplazo de PII por tokens en texto plano (camino .md)."""


def anonymize(text: str, matches: list[dict]) -> tuple[str, list[dict]]:
    """Reemplaza cada valor único por un token [TIPO_n]. Devuelve (texto_anonimizado, mapping)."""
    token_of: dict[tuple[str, str], str] = {}
    counters: dict[str, int] = {}
    for m in matches:
        key = (m["type"], m["value"])
        if key not in token_of:
            counters[m["type"]] = counters.get(m["type"], 0) + 1
            token_of[key] = f'[{m["type"]}_{counters[m["type"]]}]'

    result = text
    # reemplaza valores más largos primero para evitar que un valor corto
    # (ej. un nombre de pila) rompa la coincidencia de uno más largo que lo contiene.
    for (type_, value), token in sorted(token_of.items(), key=lambda kv: -len(kv[0][1])):
        result = result.replace(value, token)

    mapping = [{"token": t, "type": k[0], "value": k[1]} for k, t in token_of.items()]
    return result, mapping


def demo():
    text = "Juan Perez (juan@empresa.cl) vive en Av. Siempre Viva 742. Contactar a Juan Perez."
    matches = [
        {"type": "NOMBRE", "value": "Juan Perez"},
        {"type": "EMAIL", "value": "juan@empresa.cl"},
        {"type": "DIRECCION", "value": "Av. Siempre Viva 742"},
    ]
    result, mapping = anonymize(text, matches)
    assert "Juan Perez" not in result
    assert result.count("[NOMBRE_1]") == 2  # las dos apariciones usan el mismo token
    assert len(mapping) == 3
    print("anonymize OK:", result)


if __name__ == "__main__":
    demo()
