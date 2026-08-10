import subprocess
import os
import tempfile


class LLMEngine:
    def __init__(self, model_path="~/modelos/qwen2.5-0.5b-instruct-q4_k_m.gguf"):
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

    def armar_prompt_chat(self, pregunta, contexto_web=None, system_prompt=None):
        """
        Arma el prompt en el formato de chat que espera Qwen2.5-Instruct
        (ChatML: <|im_start|>...<|im_end|>). Si hay contexto_web (texto
        sacado de internet por tu investigador.py), lo mete en el mensaje
        de usuario junto con la pregunta.
        """
        if system_prompt is None:
            system_prompt = (
                "Eres Andart, un asistente preciso y directo que responde "
                "en español. Si se te da información extraída de internet, "
                "básate únicamente en ella para responder. No inventes "
                "datos que no estén en esa información."
            )

        if contexto_web:
            mensaje_usuario = (
                f"INFORMACIÓN WEB:\n{contexto_web}\n\n"
                f"PREGUNTA DEL USUARIO: {pregunta}"
            )
        else:
            mensaje_usuario = pregunta

        return (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\n{mensaje_usuario}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

    def generar(self, prompt, timeout=180, ctx_size=4096, n_predict=512):
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
