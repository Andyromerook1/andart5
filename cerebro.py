# cerebro.py
from investigador import Investigador
from llm_engine import LLMEngine


class CerebroAndart:
    def __init__(self):
        self.historial = []
        self.investigador = Investigador(profundidad=2)
        self.llm = LLMEngine()  # Motor de IA local

    def _requiere_internet(self, texto):
        """Detecta si la consulta necesita búsqueda en internet (hacking,
        exploits, vulnerabilidades, scripts) o si puede responder el modelo
        con su propio conocimiento."""
        PALABRAS_HACKING = [
            "exploit", "cve", "vulnerabilidad", "payload", "hack",
            "pentest", "seguridad", "script", "escanear", "puertos",
            "fuerza bruta", "sql injection", "xss", "csrf", "apache",
            "nginx", "ssh", "ftp", "metasploit", "nmap", "nikto",
            "hackerone", "bug bounty", "0day", "rootkit", "ransomware",
            "backdoor", "malware", "keylogger", "botnet", "ddos",
            "phishing", "spoofing", "sniffing", "mitm", "proxy",
            "tor", "deep web", "dark web", "onion", "auditar",
            "pentesting", "red team", "blue team", "reconocimiento"
        ]
        return any(p in texto.lower() for p in PALABRAS_HACKING)

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

        # Decidir si necesita internet o responde directo con el modelo
        if self._requiere_internet(consulta_real):
            # Andart busca en internet primero
            contenido_web = self.investigador.investigar(consulta_real)
            salida_final = self.llm.responder(
                pregunta=consulta_real,
                contexto_web=contenido_web[:1500] if contenido_web else None,
            )
        else:
            # El modelo responde con su propio conocimiento, sin internet
            salida_final = self.llm.responder(
                pregunta=consulta_real,
                contexto_web=None,
            )

        self.historial.append({"andart": salida_final})
        return "ia_respuesta", explicacion, salida_final
