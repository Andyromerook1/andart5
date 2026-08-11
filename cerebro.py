# cerebro.py
from investigador import Investigador
from llm_engine import LLMEngine


class CerebroAndart:
    def __init__(self):
        self.historial = []
        self.investigador = Investigador(profundidad=2)
        self.llm = LLMEngine()  # Motor de IA local

    def procesar(self, texto):
        self.historial.append({"usuario": texto})
        t = texto.lower()

        # Detectar si es continuación explícita
        es_continuacion = len(self.historial) > 2 and any(
            w in t for w in ["siguiente", "continua", "sigue", "agrega", "modifica", "cambia", "2", "parte", "otra", "mas"]
        )

        if es_continuacion:
            ultimo_tema = self.historial[-3]["usuario"] if len(self.historial) >= 3 else ""
            consulta_real = f"{ultimo_tema} {texto}" if ultimo_tema else texto
            self.investigador.profundidad = 1
            explicacion = "Ampliando con IA..."
        else:
            consulta_real = texto
            self.investigador.profundidad = 2
            explicacion = "Investigando y generando respuesta con IA..."

        # 1. Obtener contenido crudo de la web
        contenido_web = self.investigador.investigar(consulta_real)

        # 2. Generar respuesta: el LLMEngine arma el prompt de chat correcto
        #    (formato Zephyr de TinyLlama) y lo manda al modelo por archivo,
        #    no hace falta armar el prompt a mano acá.
        salida_final = self.llm.responder(
            pregunta=consulta_real,
            contexto_web=contenido_web[:1500] if contenido_web else None,
        )

        self.historial.append({"andart": salida_final})
        return "ia_respuesta", explicacion, salida_final
