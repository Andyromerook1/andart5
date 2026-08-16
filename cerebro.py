# cerebro.py
from investigador import Investigador
from llm_engine import LLMEngine
class CerebroAndart:
    def __init__(self):
        self.historial = []  # lista de dicts {"usuario": ..., "andart": ...}
        self.investigador = Investigador(profundidad=2)
        self.llm = LLMEngine()  # Motor de IA local
    def _requiere_internet(self, texto):
        """Detecta si la consulta necesita información actual/externa
        (precios, noticias, clima, eventos recientes, datos específicos de
        una persona/empresa/lugar) o si es una pregunta de conocimiento
        general que el modelo puede responder con lo que ya sabe."""
        SEÑALES_ACTUALIDAD = [
            "hoy", "ahora", "actual", "actualidad", "reciente", "último",
            "última", "noticia", "noticias", "precio", "cotización",
            "clima", "tiempo en", "quién es", "quien es", "cuándo",
            "cuando fue", "resultado", "versión más nueva", "última versión",
            # Palabras de bug bounty: sin esto, pedidos como "dame payloads
            # de XSS" no disparaban la investigación (ni el atajo a
            # PayloadsAllTheThings, ni la búsqueda en HackerOne), y el
            # modelo respondía solo de memoria en vez de ir a buscar algo
            # más fresco.
            "payload", "payloads", "exploit", "vulnerabilidad",
            "vulnerabilidades", "bypass", "cve", "poc", "writeup",
        ]
        return any(s in texto.lower() for s in SEÑALES_ACTUALIDAD)
    def _historial_para_llm(self):
        """Convierte self.historial (lista de dicts) al formato que espera
        LLMEngine: lista de tuplas (pregunta, respuesta), para que el
        modelo tenga memoria de la conversación."""
        turnos = []
        pendiente = None
        for entrada in self.historial:
            if "usuario" in entrada:
                pendiente = entrada["usuario"]
            elif "andart" in entrada and pendiente is not None:
                turnos.append((pendiente, entrada["andart"]))
                pendiente = None
        return turnos
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
        # Turnos previos (sin contar la pregunta actual, que ya se agregó
        # arriba) para que el modelo recuerde de qué venimos hablando.
        historial_para_llm = self._historial_para_llm()
        if self._requiere_internet(consulta_real):
            contenido_web = self.investigador.investigar(consulta_real)
            salida_final = self.llm.responder(
                pregunta=consulta_real,
                contexto_web=contenido_web if contenido_web else None,
                historial=historial_para_llm,
            )
        else:
            explicacion = "Generando respuesta con IA..."
            salida_final = self.llm.responder(
                pregunta=consulta_real,
                contexto_web=None,
                historial=historial_para_llm,
            )
        self.historial.append({"andart": salida_final})
        return "ia_respuesta", explicacion, salida_final
