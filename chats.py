"""
chats.py — Persistencia de conversaciones en disco.

Cada chat se guarda como un archivo JSON chico en ~/.andart/chats/. Esto
NO usa RAM del modelo ni la comparte con él: son archivos de texto plano,
livianos incluso con conversaciones largas (hablamos de unos pocos KB por
chat). El modelo sigue siendo uno solo, cargado una vez — elegir/guardar
chats no lo recarga ni lo duplica.
"""

import os
import json
import time

CHATS_DIR = os.path.expanduser("~/.andart/chats")


def _asegurar_carpeta():
    os.makedirs(CHATS_DIR, exist_ok=True)


def _ruta(chat_id):
    return os.path.join(CHATS_DIR, f"{chat_id}.json")


def nuevo_id():
    """ID simple basado en el momento de creación (milisegundos), así
    los chats se pueden ordenar por fecha sin guardar un campo aparte."""
    return str(int(time.time() * 1000))


def _generar_titulo(historial):
    """Usa el primer mensaje del usuario como título, recortado, igual
    que hacen las interfaces de chat conocidas."""
    for entrada in historial:
        texto = entrada.get("usuario", "").strip() if isinstance(entrada, dict) else ""
        if texto:
            return texto[:42] + ("…" if len(texto) > 42 else "")
    return "Chat nuevo"


def guardar_chat(chat_id, historial):
    """Guarda (o actualiza) un chat. Si el historial está vacío no
    escribe nada — evita llenar el disco de archivos basura cada vez
    que alguien abre 'nuevo chat' sin llegar a escribir un mensaje."""
    if not historial:
        return
    _asegurar_carpeta()
    data = {
        "id": chat_id,
        "titulo": _generar_titulo(historial),
        "actualizado": time.time(),
        "historial": historial,
    }
    with open(_ruta(chat_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cargar_chat(chat_id):
    try:
        with open(_ruta(chat_id), encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def listar_chats():
    """Lista todos los chats guardados, más nuevo primero, con solo los
    datos necesarios para mostrarlos en la lista (no el historial
    completo de cada uno, para que listar sea liviano)."""
    _asegurar_carpeta()
    chats = []
    for nombre in os.listdir(CHATS_DIR):
        if not nombre.endswith(".json"):
            continue
        try:
            with open(os.path.join(CHATS_DIR, nombre), encoding="utf-8") as f:
                data = json.load(f)
            chats.append({
                "id": data["id"],
                "titulo": data.get("titulo", "Chat"),
                "actualizado": data.get("actualizado", 0),
                "mensajes": len(data.get("historial", [])),
            })
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    chats.sort(key=lambda c: c["actualizado"], reverse=True)
    return chats


def borrar_chat(chat_id):
    try:
        os.remove(_ruta(chat_id))
        return True
    except FileNotFoundError:
        return False
