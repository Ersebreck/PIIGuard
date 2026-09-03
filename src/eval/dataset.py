"""Casos etiquetados a mano para evaluar detect_llm (NAME/ADDRESS contextual).

EMAIL/PHONE/NIT/ID_NUMBER no van aquí: esos son regex determinístico, ya cubiertos
por tests unitarios normales (src/tests/), no necesitan evaluación de calidad LLM.
"""

CASES = [
    {
        "id": "simple_name_address",
        "text": "Juan Perez vive en Av. Siempre Viva 742. La empresa Acme SPA factura mensualmente.",
        "expected": {("NAME", "Juan Perez"), ("ADDRESS", "Av. Siempre Viva 742")},
    },
    {
        "id": "repeated_name",
        "text": (
            "Camila Torres escribio para pedir soporte. "
            "Camila Torres vive en Calle 45 #12-30, Bogota."
        ),
        "expected": {("NAME", "Camila Torres"), ("ADDRESS", "Calle 45 #12-30, Bogota")},
    },
    {
        # trampa: no debería marcar el nombre de la empresa como PII de persona
        "id": "company_not_person",
        "text": "La factura fue emitida por Grupo Oval SAS a nombre del cliente Andres Gomez.",
        "expected": {("NAME", "Andres Gomez")},
    },
    {
        "id": "no_pii",
        "text": "El sistema procesa archivos PDF, DOCX y XLSX antes de enviarlos al LLM.",
        "expected": set(),
    },
    {
        # trampa: lugar genérico, no una dirección real de alguien
        "id": "generic_place_not_address",
        "text": "La reunion sera en la oficina de Bogota, no en una direccion especifica del cliente.",
        "expected": set(),
    },
]
