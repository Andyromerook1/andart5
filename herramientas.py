"""
herramientas.py — Ejecuta herramientas de recon (nmap y las que se vayan
agregando) de forma controlada, para que Andart pueda usarlas él mismo
cuando responde, en vez de que tengas que correrlas vos a mano y
copiarle el resultado.

Controles de seguridad (no son opcionales, protegen a VOS mismo de un
uso accidental fuera de scope, no son "restricciones" arbitrarias):

  1. Solo binarios en HERRAMIENTAS (lista blanca) — nada arbitrario.
  2. El objetivo (dominio/IP) tiene que estar en scope.txt.
  3. Solo los flags explícitamente permitidos por herramienta pasan —
     el resto se descarta en silencio.
  4. Nunca se usa shell=True — se ejecuta como lista de argumentos,
     así no hay forma de inyectar comandos extra con ; o | etc.
  5. Timeout por herramienta, para que un escaneo colgado no cuelgue
     el chat entero.
"""

import subprocess
import shlex
import os
import re

SCOPE_PATH = os.path.expanduser("~/andart5/scope.txt")

# Para agregar una herramienta nueva: sumar una entrada acá con el
# binario real (tiene que estar en el PATH de Termux) y qué flags están
# permitidos. subfinder/httpx no vienen por "pkg install" — necesitan
# Go instalado primero (`pkg install golang`) y compilarlos con
# `go install github.com/projectdiscovery/...@latest`. Los dejamos acá
# ya preparados para cuando estén instalados.
HERRAMIENTAS = {
    "nmap": {
        "binario": "nmap",
        "flags_permitidos": {"-sV", "-sT", "-Pn", "-F", "-p", "-T4", "-A"},
        "timeout": 120,
        "instalar": "pkg install nmap",
    },
    "subfinder": {
        "binario": "subfinder",
        "flags_permitidos": {"-silent", "-d"},
        "timeout": 90,
        "instalar": "pkg install golang && go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
    },
    "httpx": {
        "binario": "httpx",
        "flags_permitidos": {"-silent", "-title", "-tech-detect", "-status-code"},
        "timeout": 60,
        "instalar": "pkg install golang && go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
    },
}

_PATRON_DOMINIO = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    r"|^\d{1,3}(?:\.\d{1,3}){3}$"
)


def _cargar_scope():
    try:
        with open(SCOPE_PATH, encoding="utf-8") as f:
            return {
                linea.strip().lower()
                for linea in f
                if linea.strip() and not linea.strip().startswith("#")
            }
    except FileNotFoundError:
        return set()


def _objetivo_en_scope(objetivo):
    scope = _cargar_scope()
    objetivo = objetivo.lower()
    # El dominio exacto, o un subdominio de uno autorizado.
    return any(objetivo == d or objetivo.endswith("." + d) for d in scope)


def herramientas_disponibles():
    """Nombres de herramientas configuradas (instaladas o no — solo
    dice cuáles conoce Andart, no si el binario ya está en el celular)."""
    return list(HERRAMIENTAS.keys())


def ejecutar(nombre_herramienta, argumentos_texto):
    """
    nombre_herramienta: clave en HERRAMIENTAS (ej: 'nmap').
    argumentos_texto: string tal como lo pidió el modelo,
                       ej: '-sV -Pn objetivo.com'.

    Devuelve (ok: bool, mensaje: str). Si ok=False, mensaje explica el
    rechazo (para que el modelo se lo explique al usuario en lenguaje
    natural, en vez de solo fallar en silencio).
    """
    nombre_herramienta = nombre_herramienta.lower().strip()

    if nombre_herramienta not in HERRAMIENTAS:
        disponibles = ", ".join(herramientas_disponibles())
        return False, f"'{nombre_herramienta}' no está habilitada. Disponibles: {disponibles}."

    config = HERRAMIENTAS[nombre_herramienta]

    try:
        partes = shlex.split(argumentos_texto)
    except ValueError as e:
        return False, f"No se pudieron interpretar los argumentos: {e}"

    if not partes:
        return False, "Faltan argumentos (¿cuál es el objetivo?)."

    # Buscamos, entre los argumentos, algo con forma de dominio o IP.
    objetivo = next(
        (t for t in partes if not t.startswith("-") and _PATRON_DOMINIO.match(t)),
        None,
    )

    if objetivo is None:
        return False, "No se identificó un dominio/IP válido en los argumentos."

    if not _objetivo_en_scope(objetivo):
        return False, (
            f"'{objetivo}' no está en tu scope.txt. Si de verdad tenés "
            "autorización de ese programa de bug bounty para testearlo, "
            "agregalo ahí primero."
        )

    # Solo dejamos pasar flags de la lista blanca; el resto se descarta.
    permitidos = config["flags_permitidos"]
    args_filtrados = []
    for token in partes:
        if token.startswith("-"):
            flag_base = token.split("=")[0]
            if flag_base in permitidos:
                args_filtrados.append(token)
        else:
            args_filtrados.append(token)

    comando = [config["binario"]] + args_filtrados

    try:
        proceso = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=config["timeout"],
        )
    except FileNotFoundError:
        return False, (
            f"El binario '{config['binario']}' no está instalado todavía. "
            f"Corré: {config['instalar']}"
        )
    except subprocess.TimeoutExpired:
        return False, f"'{nombre_herramienta}' tardó demasiado y fue cancelado."

    salida = ((proceso.stdout or "") + (proceso.stderr or "")).strip()
    # Techo de seguridad generoso (no un recorte de uso normal): un scan
    # típico de nmap con estos flags no se acerca ni de lejos a esto.
    # Esto solo protege contra un caso patológico de salida gigante, no
    # limita la información real que te llega.
    salida = salida[:8000] if salida else "(sin salida)"

    return True, salida
