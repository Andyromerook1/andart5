# cerebro.py
from investigador import Investigador

class CerebroAndart:
    def __init__(self):
        self.historial = []
        self.investigador = Investigador(profundidad=2)  # Ajustable según RAM disponible

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
            # Para continuaciones reducimos la profundidad (más rápido)
            self.investigador.profundidad = 1
            explicacion = "Ampliando la investigación previa..."
        else:
            consulta_real = texto
            self.investigador.profundidad = 2
            explicacion = "Investigando a fondo (esto puede tardar unos segundos)..."

        # Ejecutar investigación profunda
        resultado_investigacion = self.investigador.investigar(consulta_real)
        salida_final = resultado_investigacion
        self.historial.append({"andart": salida_final})
        return "investigacion", explicacion, salida_final