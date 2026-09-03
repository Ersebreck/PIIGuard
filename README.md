# PIIGuard

Servicio interno para anonimizar datos de clientes antes de procesarlos con Claude.

## Qué hace

1. Recibe un archivo con datos de cliente.
2. Detecta información sensible (PII: nombres, RUT/DNI, email, teléfono, dirección, datos bancarios, etc.) usando un LLM local.
3. Reemplaza la PII detectada.
4. Devuelve el archivo anonimizado.

## Por qué LLM local

El procesamiento de detección/reemplazo corre local, para no exponer datos sensibles del cliente a un servicio externo antes de anonimizarlos.

## Uso

Servicio pensado para que otros colegas del equipo lo usen (no solo para uso individual).

## Estado

MVP funcionando end-to-end (FastAPI + frontend simple + detección regex/LLM + anonimización + audit trail en SQLite).

## Cómo lo usa el equipo (remoto/híbrido)

El equipo no comparte una LAN fija, así que el approach es una sola VM (cloud o una
máquina siempre encendida) corriendo Ollama + el server, con **Tailscale** (u otra
VPN mesh) para que todos entren de forma privada sin exponer el servicio a internet
ni tener que construir auth/TLS propios:

1. Levantar una VM (o reusar una máquina existente), instalar Ollama ahí y
   `ollama pull <modelo>` (ver `PIIGUARD_LLM_MODEL` en `ai/detect_graph.py`).
2. Instalar Tailscale en esa VM y en las laptops del equipo, uniéndolas a la misma
   tailnet.
3. Correr el server ahí: `uvicorn backend.app:app --host 0.0.0.0 --port 8000`
   (sin `--reload` en este modo). Mantenerlo vivo con systemd/tmux — no hace falta
   más infra que eso para este tamaño de equipo.
4. El equipo entra por la IP/hostname de Tailscale de esa VM, puerto 8000.

**Importante:** `piiguard.db` en esa VM queda con los valores originales de PII de
*todo* el equipo, en texto plano (es el audit trail). Restringir quién tiene acceso
a esa máquina es tan importante como el modelo de detección.

**Concurrencia:** con subidas simultáneas frecuentes, el server ya no bloquea el
event loop mientras corre el LLM (offload a threads + `PIIGUARD_MAX_CONCURRENT_LLM`
limita cuántas llamadas a Ollama corren a la vez, default 2). El techo real sigue
siendo el hardware de esa VM corriendo Ollama — si el equipo crece mucho o el LLM
tarda demasiado bajo carga, la solución es más CPU/GPU en esa máquina, no más código.
