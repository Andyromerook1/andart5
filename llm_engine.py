import subprocess
import os


class LLMEngine:
    def __init__(self, model_path="~/modelos/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"):
        self.model_path = os.path.expanduser(model_path)
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
                "Verifica la ruta o descárgalo primero."
            )

    def generar(self, prompt, timeout=180):
        # No hace falta escapar nada: subprocess.run con una lista
        # (sin shell=True) pasa cada argumento directo al proceso.
        comando = [
            self.binario,
            "-m", self.model_path,
            "-p", prompt,
            "-n", "512",
            "--temp", "0.7",
            "--no-display-prompt",
        ]

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
