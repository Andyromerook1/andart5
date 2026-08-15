"""
servidor.py — Backend web para Andart.

Expone CerebroAndart (el mismo motor que usa main.py en consola) a través
de una API HTTP simple, para que static/index.html pueda chatear con él
desde el navegador. Pensado para correr en Termux y exponerse afuera con
Tailscale Funnel (ver instrucciones al final de este archivo).

Uso:
    cd ~/andart5          # carpeta raíz del proyecto (donde está cerebro.py)
    python servidor.py
    # abrí http://127.0.0.1:8000 en el navegador del mismo celular
"""

import os
from flask import Flask, request, jsonify, send_from_directory

from cerebro import CerebroAndart
import chats

app = Flask(__name__, static_folder="static", static_url_path="")

# Una sola instancia global: así el modelo se carga una vez y todos los
# chats de la sesión web comparten el mismo modelo cargado (cambiar de
# chat NO recarga el modelo — solo cambia qué historial de texto se le
# manda, que es liviano).
cerebro = CerebroAndart()

# ID del chat actualmente activo. Empieza como uno nuevo sin guardar
# todavía (recién se persiste a disco cuando tiene al menos un mensaje).
chat_actual_id = chats.nuevo_id()


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/mensaje", methods=["POST"])
def mensaje():
    data = request.get_json(silent=True) or {}
    texto = (data.get("mensaje") or "").strip()

    if not texto:
        return jsonify({"error": "Mensaje vacío."}), 400

    try:
        _tipo, explicacion, salida = cerebro.procesar(texto)
        # Guardamos en disco después de cada intercambio, así nunca se
        # pierde una conversación aunque cierres la app sin querer.
        chats.guardar_chat(chat_actual_id, cerebro.historial)
        return jsonify({"respuesta": salida, "estado": explicacion})
    except Exception as e:
        # No dejamos que un error interno tumbe el server; el frontend
        # muestra el mensaje de error como si fuera una respuesta más.
        return jsonify({"error": f"Error interno: {e}"}), 500


@app.route("/api/salud")
def salud():
    """Endpoint simple para que el frontend confirme que el server está
    vivo antes de dejar escribir (evita mandar el primer mensaje a un
    server que todavía está cargando el modelo)."""
    return jsonify({"ok": True})


@app.route("/api/nuevo_chat", methods=["POST"])
def nuevo_chat():
    """Empieza un chat nuevo. El chat anterior YA está guardado en disco
    (se guarda solo después de cada mensaje), así que acá solo hace
    falta vaciar el historial en memoria y asignar un id nuevo — no se
    pierde nada de lo anterior, sigue disponible en /api/chats."""
    global chat_actual_id
    cerebro.historial = []
    chat_actual_id = chats.nuevo_id()
    return jsonify({"ok": True, "chat_id": chat_actual_id})


@app.route("/api/chats", methods=["GET"])
def listar_chats():
    return jsonify({"chats": chats.listar_chats(), "chat_actual": chat_actual_id})


@app.route("/api/chats/<chat_id>", methods=["GET"])
def cargar_chat(chat_id):
    """Carga un chat guardado como el activo. El modelo NO se recarga
    (sigue siendo la misma instancia cargada) — solo cambia qué
    historial de texto usamos de acá en adelante."""
    global chat_actual_id
    data = chats.cargar_chat(chat_id)
    if data is None:
        return jsonify({"error": "Ese chat no existe."}), 404

    cerebro.historial = data["historial"]
    chat_actual_id = chat_id
    return jsonify({"ok": True, "historial": cerebro.historial})


@app.route("/api/chats/<chat_id>", methods=["DELETE"])
def eliminar_chat(chat_id):
    global chat_actual_id
    chats.borrar_chat(chat_id)
    if chat_id == chat_actual_id:
        # Si borraste el chat que tenías abierto, arrancamos uno nuevo
        # para no quedar apuntando a un archivo que ya no existe.
        cerebro.historial = []
        chat_actual_id = chats.nuevo_id()
    return jsonify({"ok": True})


if __name__ == "__main__":
    # host="127.0.0.1": solo accesible desde el propio celular por
    # defecto. Tailscale Funnel expone este puerto hacia afuera sin que
    # tengas que cambiar esto a 0.0.0.0 ni abrir nada en el router.
    #
    # threaded=True porque generar() puede tardar bastante (el modelo
    # corriendo en CPU) y no queremos que una request bloquee a otra
    # (por ejemplo, el polling de /api/salud) mientras tanto.
    #
    # Instrucciones para exponerlo con Tailscale Funnel, una vez que
    # este server esté corriendo en otra pestaña/sesión de Termux:
    #   pkg install tailscale
    #   tailscale up
    #   tailscale funnel 8000
    # Eso te da una URL pública HTTPS que sirve exactamente esta misma
    # interfaz, sin abrir puertos en tu router.
    app.run(host="127.0.0.1", port=8000, threaded=True)
