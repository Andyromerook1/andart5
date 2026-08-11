import subprocess
import os
import json
import tempfile

CONFIG_PATH = os.path.expanduser("~/.andart/config.json")


def _cargar_config():
    """Lee la config generada por el instalador (modelo elegido según RAM
    del dispositivo). Si no existe, devolvemos un dict vacío y usamos
    valores por defecto más abajo."""
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _ram_disponible_mb():
    """RAM libre en este momento (no la total), leyendo /proc/meminfo.
    Funciona igual en dispositivos de 32 o 64 bits. Devuelve None si no
    se puede leer (por ejemplo, en un sistema que no sea Linux/Android)."""
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except (FileNotFoundError, ValueError, IndexError):
        pass
    return None


class LLMEngine:
    def __init__(self, model_path=None, formato_chat=None):
        config = _cargar_config()

        # Si no se pasa nada explícito, usamos lo que el instalador detectó
        # automáticamente según la RAM del dispositivo. Si tampoco hay
        # config (por ejemplo, instalación manual vieja), caemos a un
        # default razonable.
        if model_path is None:
            model_path = config.get(
                "model_path",
                "~/modelos/TinyLlama-1.1B-Chat-v1.0-Heretic.Q4_K_M.gguf",
            )
        if formato_chat is None:
            formato_chat = config.get("formato_chat", "zephyr")

        self.model_path = os.path.expanduser(model_path)
        self.formato_chat = formato_chat
        self.binario = os.path.expanduser("~/bin/llama-cli")

        # Verificar que el binario exista
        if not os.path.isfile(self.binario):
            raise FileNotFoundError(
                f"No se encuentra {self.binario}. "
                "Asegúrate de haber compilado llama.cpp y copiado el binario a ~/bin/"
            )

        # Verificar que el modelo exista
        if not os.path.isfile(self.model_path):
            raise FileNotFoundError(
                f"No se encuentra el modelo en {self.model_path}. "
                "Verifica la ruta o corré el instalador de nuevo."
            )

    def armar_prompt_chat(self, pregunta, contexto_web=None, system_prompt=None):
        """
        Arma el prompt en el formato de chat correcto según el modelo
        instalado: Zephyr (<|system|>/<|user|>/<|assistant|>) para
        TinyLlama, o ChatML (<|im_start|>/<|im_end|>) para Qwen. El
        formato se elige solo, según lo que haya detectado el instalador.
        """
        if system_prompt is None:
            system_prompt = (
                "Eres Andart. Respondes en español, de forma clara y "
                "breve, explicando paso a paso como un profesor. Usa tu "
                "propio conocimiento. Ignora publicidad si aparece en la "
                "información web."
            )

        if contexto_web:
            mensaje_usuario = (
                f"INFORMACIÓN WEB:\n{contexto_web}\n\n"
                f"PREGUNTA DEL USUARIO: {pregunta}"
            )
        else:
            mensaje_usuario = pregunta

        if self.formato_chat == "chatml":
            return (
                f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
                f"<|im_start|>user\n{mensaje_usuario}<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )

        # default: zephyr (TinyLlama)
        return (
            f"<|system|>\n{system_prompt}</s>\n"
            f"<|user|>\n{mensaje_usuario}</s>\n"
            f"<|assistant|>\n"
        )

    def _reverse_prompts(self):
        """Tokens de corte para que el modelo no siga alucinando turnos
        nuevos de conversación, según el formato de chat en uso."""
        if self.formato_chat == "chatml":
            return ["<|im_start|>"]
        return ["<|user|>", "<|system|>"]

    def generar(self, prompt, timeout=300, ctx_size=2048, n_predict=200):
        # Chequeo de RAM libre ANTES de arrancar: si está muy baja, Android
        # puede matar el proceso a mitad de la generación, lo que da un
        # error confuso. Mejor avisar claro de entrada.
        ram_libre = _ram_disponible_mb()
        if ram_libre is not None and ram_libre < 250:
            return (
                f"⚠️ Muy poca RAM libre en este momento ({ram_libre}MB). "
                "Cerrá otras apps en segundo plano y probá de nuevo."
            )

        # Para prompts largos (texto de internet incluido) es más robusto
        # escribirlo a un archivo temporal y usar -f, en vez de pasarlo
        # como argumento de línea de comandos con -p.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(prompt)
            tmp_path = tmp.name

        try:
            comando = [
                self.binario,
                "-m", self.model_path,
                "-f", tmp_path,
                "-c", str(ctx_size),
                "-n", str(n_predict),
                "--temp", "0.7",
                "--no-display-prompt",
                "-no-cnv",
            ]
            for rp in self._reverse_prompts():
                comando += ["-r", rp]

            try:
                proceso = subprocess.run(
                    comando,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                return "Error: la generación tardó demasiado y fue cancelada (timeout)."
            except Exception as e:
                return f"Error inesperado al ejecutar el modelo: {e}"

            if proceso.returncode != 0:
                return f"Error al generar respuesta: {proceso.stderr.strip()}"

            return proceso.stdout.strip()
        finally:
            # Limpiar el archivo temporal siempre, haya salido bien o mal
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    def responder(self, pregunta, contexto_web=None, system_prompt=None, **kwargs):
        """
        Método de conveniencia: arma el prompt de chat y genera la respuesta
        en un solo paso. Esto es lo que llamarías desde cerebro.py.
        """
        prompt = self.armar_prompt_chat(pregunta, contexto_web, system_prompt)
        return self.generar(prompt, **kwargs)
