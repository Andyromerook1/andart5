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

    def generar(self, prompt):
        # Escapar caracteres especiales para el shell
        prompt_escapado = prompt.replace('"', '\\"')
        comando = [
            self.binario,
            "-m", self.model_path,
            "-p", prompt_escapado,
            "-n", "512",
            "--temp", "0.7",
            "--no-display-prompt"
        ]
        proceso = subprocess.run(comando, capture_output=True, text=True, timeout=120)
        if proceso.returncode != 0:
            return f"Error al generar respuesta: {proceso.stderr}"
        return proceso.stdout.strip()
