# Notas / pendientes

Decisiones y hallazgos que quedan anotados pero no implementados por ahora.

## Seguridad del mapping (pendiente)

`backend/piiguard.db` guarda el mapping (token → valor original real) en texto
plano, en el mismo archivo que todo lo demás. Es pseudonimización, no
anonimización (GDPR): mientras exista el mapping, el dato sigue siendo PII.
Buena práctica: mapping separado del resto de la data, cifrado, acceso
restringido (tratarlo como una clave de encripción).

Retomar antes de meter datos reales de cliente en el servidor compartido.

## Presidio (Microsoft) como alternativa a futuro

Framework open-source hecho para PII detection/anonymization (regex + NER +
recognizers custom, extensible). No migrar ahora — perderíamos la
trazabilidad de LangGraph — pero si `detect_regex.py` crece mucho (más
países/tipos), es la opción de "no reinventar esto a mano".
https://github.com/microsoft/presidio

## Validado por la literatura (no requiere cambios)

- Regex + LLM contextual híbrido le gana a NER-solo y a LLM zero-shot-solo.
- Para un tool de redacción, priorizar recall sobre precisión es correcto
  (falso negativo = PII filtrada, peor que falso positivo = sobre-redacción).
  Confirma el criterio ya usado en los regex de PHONE/ID_NUMBER.

## PDF: fallback de extracción a futuro (pendiente, no implementado)

Con PDFs de tablas reales con líneas (ej. certificados de retención), el
heurístico de MarkItDown (`_extract_form_content_from_words`, clustering de
palabras por posición) a veces arma mal la tabla: filas partidas en varias
líneas, separadores `---` sueltos, palabras huérfanas. `pdfplumber.extract_tables()`
directo (basado en las líneas reales de la tabla, no en clustering de texto)
da un resultado más limpio para esos casos.

No vale la pena implementarlo todavía: es solo estético (la detección de PII
fue correcta igual sobre el markdown mal formado) y el peor caso encontrado
(labels pegados tipo "Dirección:Compañía:") no lo arregla ni pdfplumber ni
MarkItDown — el PDF no tiene espacio real entre esas palabras en su texto
subyacente, es puro layout visual.

Si un cliente se queja de que el markdown de salida se ve mal (no de PII mal
detectada), implementar un fallback: extraer con pdfplumber `extract_tables()`
cuando el PDF tenga tablas con líneas, y usar MarkItDown normal para el resto.
