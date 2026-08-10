import os
from ctransformers import AutoModelForCausalLM

class LLMEngine:
    def __init__(self, model_path="~/modelos/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"):
        self.model = AutoModelForCausalLM.from_pretrained(
            os.path.expanduser(model_path),
            model_type="llama"
        )

    def generar(self, prompt):
        # Formato simple para TinyLlama
        texto_completo = f"<|user|>\n{prompt}\n<|assistant|>\n"
        respuesta = self.model(texto_completo, max_new_tokens=512, temperature=0.7)
        return respuesta.strip()
