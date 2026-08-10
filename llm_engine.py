import os
from llama_cpp import Llama

class LLMEngine:
    def __init__(self, model_path="~/modelos/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"):
        self.model = Llama(
            model_path=os.path.expanduser(model_path),
            n_ctx=2048,
            n_threads=4,
            verbose=False
        )

    def generar(self, prompt):
        output = self.model.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.7
        )
        return output['choices'][0]['message']['content']
