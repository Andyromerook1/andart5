# investigador.py
from buscador import buscar_multicanal
from extractor import extraer_contenido_y_enlaces
from api_connector import APIConnector
from collections import Counter
import re
import requests

# Frases/patrones típicos de ruido publicitario, legal o de redes sociales
# que no aportan nada a una respuesta técnica y suelen colarse en el scraping.
PATRONES_RUIDO = [
    "suscrib", "suscript", "síguenos", "sigueme", "sígueme",
    "newsletter", "boletín", "boletin",
    "política de privacidad", "politica de privacidad",
    "aviso legal", "términos y condiciones", "terminos y condiciones",
    "copyright", "derechos reservados", "todos los derechos",
    "cookie", "publicidad", "anuncio patrocinado",
    "oferta especial", "descuento", "compra ahora",
    "haz clic aquí", "haz click aqui", "click aquí",
    "twitch.tv", "instagram.com", "facebook.com", "tiktok.com",
    "síguenos en", "únete a nuestro", "unete a nuestro",
    "descarga la app", "descarga nuestra app",
]

# Presupuesto de caracteres para el resultado final que se le manda al
# modelo. Antes cerebro.py cortaba a lo bruto con contenido_web[:1500],
# arriesgándose a cortar a mitad de un bloque de código o una oración.
# Ahora el propio investigador arma el resultado respetando este límite
# desde el vamos, priorizando código (más valioso para bug bounty) sobre
# texto explicativo.
PRESUPUESTO_CARACTERES = 1400

# Sitios técnicos que priorizamos en la búsqueda para consultas de
# seguridad. hackerone.com primero: son reportes de vulnerabilidades ya
# DIVULGADOS PÚBLICAMENTE por HackerOne — la señal más directa que
# existe de "esto funcionó de verdad, en un programa real, hace poco".
# Mucho más valioso para encontrar algo nuevo que un payload de manual.
SITIOS_SEGURIDAD = ["hackerone.com", "github.com", "hacktricks.xyz", "portswigger.net"]

# Atajo directo a PayloadsAllTheThings (swisskyrepo/PayloadsAllTheThings
# en GitHub): un repo con payloads reales ya organizados por tipo de
# vulnerabilidad, mantenido por la comunidad de seguridad ofensiva. Si
# la consulta menciona alguno de estos tipos, bajamos el archivo
# directo en vez de pasar por todo el pipeline de búsqueda+scraping —
# más rápido (una sola descarga) y con contenido mucho más confiable.
BASE_PAYLOADS = "https://raw.githubusercontent.com/swisskyrepo/PayloadsAllTheThings/master"
MAPA_PAYLOADS = {
    "xss": "XSS Injection",
    "cross site scripting": "XSS Injection",
    "sqli": "SQL Injection",
    "sql injection": "SQL Injection",
    "inyeccion sql": "SQL Injection",
    "inyección sql": "SQL Injection",
    "ssrf": "Server Side Request Forgery",
    "lfi": "File Inclusion",
    "file inclusion": "File Inclusion",
    "rce": "Command Injection",
    "command injection": "Command Injection",
    "csrf": "CSRF Injection",
    "xxe": "XXE Injection",
    "idor": "Insecure Direct Object References",
    "ssti": "Server Side Template Injection",
    "open redirect": "Open Redirect",
    "redireccion abierta": "Open Redirect",
    "path traversal": "Directory Traversal",
    "directory traversal": "Directory Traversal",
}


class Investigador:
    def __init__(self, profundidad=2):
        self.profundidad = profundidad
        self.api = APIConnector()

    def _intentar_payloads_conocidos(self, consulta):
        """Si la consulta menciona un tipo de vulnerabilidad conocido
        (XSS, SQLi, SSRF, etc.), baja directo el archivo correspondiente
        de PayloadsAllTheThings. Devuelve None si no hay match o si
        falla la descarga (en ese caso, investigar() sigue con el
        pipeline normal de búsqueda como respaldo)."""
        low = consulta.lower()
        carpeta = None
        for palabra_clave, nombre_carpeta in MAPA_PAYLOADS.items():
            if palabra_clave in low:
                carpeta = nombre_carpeta
                break

        if carpeta is None:
            return None

        url = f"{BASE_PAYLOADS}/{carpeta}/README.md"
        try:
            resp = requests.get(url, timeout=6)
            if resp.status_code != 200 or not resp.text.strip():
                return None
            contenido = resp.text.strip()
            return (
                f"[💻 PAYLOADS: {carpeta.upper()} — fuente: PayloadsAllTheThings]\n"
                f"{contenido}"
            )
        except requests.RequestException:
            return None

    def investigar(self, consulta_original):
        print("[*] Iniciando investigación (modo híbrido)...")

        # --- Atajo: si la consulta es sobre un tipo de vulnerabilidad
        # conocido, vamos directo a PayloadsAllTheThings en vez de todo
        # el pipeline de búsqueda+scraping. Más rápido (una descarga) y
        # con payloads reales y confiables, en vez de lo que traiga una
        # búsqueda genérica.
        payloads_directos = self._intentar_payloads_conocidos(consulta_original)
        if payloads_directos:
            print("[✓] Encontrado en PayloadsAllTheThings, salteando búsqueda genérica")
            return payloads_directos[:PRESUPUESTO_CARACTERES]

        # --- Intentar API primero ---
        respuesta_api = None
        try:
            respuesta_api = self.api.try_api(consulta_original)
            if respuesta_api:
                respuesta_api = "[📡 INFORMACIÓN DIRECTA DE API]\n" + respuesta_api + "\n\n"
                print("[✓] Datos obtenidos desde API")
        except Exception as e:
            print(f"[!] Error al intentar API: {e}")

        # Fase 1: Generar subconsultas.
        # Antes generaba 5 variantes con sufijos de tutorial genérico
        # ("para principiantes", "paso a paso"...), pensados para un bot
        # de aprendizaje general, no para bug bounty. Ahora son solo 2:
        # la consulta tal cual, más UNA variante orientada a
        # vulnerabilidades/seguridad técnica. Menos variantes = menos
        # búsquedas = mucho menos tiempo de red, que es el cuello de
        # botella real en un celular con datos móviles inestables.
        subconsultas = self._generar_subconsultas(consulta_original)

        # Fase 2: Búsqueda multicanal y recolección de URLs.
        # Antes: por cada subconsulta se hacían 1 búsqueda general + 4
        # sitios específicos (github/stackoverflow/pastebin/reddit) = 5
        # requests. Con 5 subconsultas eran hasta 25 llamadas de red
        # solo acá. Ahora: solo la PRIMERA subconsulta (la pregunta
        # original) busca también en sitios técnicos; las demás
        # subconsultas solo hacen la búsqueda general. Esto baja el
        # total a ~7 llamadas en el peor caso.
        urls_totales = set()
        for i, subq in enumerate(subconsultas):
            res = buscar_multicanal(subq, max_results=3, periodo="y")
            for r in res:
                if r.get("href"):
                    urls_totales.add(r["href"])

            if i == 0:
                # Solo para la consulta original, no para cada variante.
                for sitio in SITIOS_SEGURIDAD:
                    res_sitio = buscar_multicanal(subq, max_results=2, sitio=sitio, periodo="y")
                    for r in res_sitio:
                        if r.get("href"):
                            urls_totales.add(r["href"])

        # Fase 3: Scraping de primer nivel.
        # Antes: hasta 10 páginas. Ahora: 5 — sigue siendo variedad
        # suficiente para armar una buena respuesta, con la mitad del
        # tiempo de red.
        todos_los_bloques = []
        enlaces_segundo_nivel = set()
        for url in list(urls_totales)[:5]:
            bloques, enlaces = extraer_contenido_y_enlaces(url, profundizar=(self.profundidad > 1))
            if bloques:
                todos_los_bloques.extend(bloques)
            if enlaces:
                enlaces_segundo_nivel.update(enlaces)

        # Fase 4: Scraping de segundo nivel si profundidad > 1.
        # Antes: hasta 5 páginas más. Ahora: 2. El segundo nivel es
        # "nice to have", no vale la pena pagar tanto tiempo de red por
        # una mejora marginal en la respuesta.
        if self.profundidad > 1 and enlaces_segundo_nivel:
            print("[*] Explorando enlaces relacionados...")
            for url in list(enlaces_segundo_nivel)[:2]:
                bloques, _ = extraer_contenido_y_enlaces(url, profundizar=False)
                if bloques:
                    todos_los_bloques.extend(bloques)

        # Fase 5: Ensamblar código + síntesis de texto, respetando el
        # presupuesto de caracteres desde acá (no lo corta cerebro.py
        # después a lo bruto).
        resultado_final = self._ensamblar_codigo(todos_los_bloques, consulta_original)

        if respuesta_api:
            resultado_final = respuesta_api + resultado_final

        return resultado_final[:PRESUPUESTO_CARACTERES]

    def _generar_subconsultas(self, consulta):
        """Dos variantes en vez de seis: la consulta tal cual, y una
        orientada a contexto técnico/de seguridad. Menos volumen de red,
        más relevancia para el caso de uso real (bug bounty), en vez de
        sufijos de tutorial genérico que no aportan acá."""
        return [consulta, f"{consulta} vulnerabilidad seguridad técnico"]

    def _es_ruido(self, texto):
        """Detecta si un fragmento es contenido promocional, legal o de
        redes sociales que no aporta valor técnico/educativo."""
        low = texto.lower()
        if "http://" in low or "https://" in low:
            return True
        return any(patron in low for patron in PATRONES_RUIDO)

    def _ensamblar_codigo(self, bloques, consulta_original):
        """Toma bloques de código/texto y devuelve un script cohesionado con explicación."""
        # Separar código y texto
        fragmentos_codigo = []
        fragmentos_texto = []
        for b in bloques:
            if b["tipo"] == "codigo":
                fragmentos_codigo.append(b)
            else:
                fragmentos_texto.append(b["contenido"])

        resultado = ""

        # Si hay código, ensamblar
        if fragmentos_codigo:
            # Agrupar por lenguaje
            por_lenguaje = {}
            for f in fragmentos_codigo:
                lang = f.get("lenguaje", "plain")
                if not lang:
                    lang = self._adivinar_lenguaje(f["contenido"])
                por_lenguaje.setdefault(lang, []).append(f["contenido"])

            for lang, fragmentos in por_lenguaje.items():
                if not fragmentos:
                    continue
                # Ordenar inteligentemente
                ordenados = self._ordenar_fragmentos(fragmentos, lang)
                # Eliminar duplicados simples (contenido casi idéntico)
                unicos = self._eliminar_duplicados(ordenados)
                # Limpiar líneas de ruido promocional dentro de cada fragmento
                unicos_limpios = [self._limpiar_lineas_ruido(f) for f in unicos]
                unicos_limpios = [f for f in unicos_limpios if f.strip()]
                if unicos_limpios:
                    codigo_completo = "\n\n".join(unicos_limpios)
                    resultado += f"\n\n[💻 CÓDIGO {lang.upper()} COMPLETO]\n{codigo_completo}\n"

        # Procesar textos para la explicación, solo si todavía queda
        # margen dentro del presupuesto de caracteres (el código va
        # primero porque es lo más valioso para bug bounty).
        margen_restante = PRESUPUESTO_CARACTERES - len(resultado)
        if fragmentos_texto and margen_restante > 100:
            texto_completo = "\n".join(fragmentos_texto)
            explicacion = self._sintetizar_texto(texto_completo, consulta_original)
            if explicacion:
                resultado += f"\n\n[📖 EXPLICACIÓN]\n{explicacion}"
        elif not fragmentos_codigo:
            resultado = "[-] No se encontró información suficiente."

        if not resultado.strip():
            resultado = "[-] No se encontró información suficiente."

        return resultado

    def _limpiar_lineas_ruido(self, fragmento):
        """Saca del fragmento de código las líneas que en realidad son
        texto promocional/publicitario colado por el scraping."""
        lineas = fragmento.split("\n")
        lineas_limpias = [l for l in lineas if not self._es_ruido(l)]
        return "\n".join(lineas_limpias)

    def _adivinar_lenguaje(self, codigo):
        """Intenta adivinar el lenguaje basándose en palabras clave."""
        primeras_lineas = codigo.strip().split('\n')[:5]
        texto = ' '.join(primeras_lineas).lower()
        if 'def ' in texto or 'import ' in texto or 'print(' in texto:
            return 'python'
        if 'function ' in texto or 'const ' in texto or 'let ' in texto:
            return 'javascript'
        if 'public class ' in texto or 'System.out' in texto:
            return 'java'
        if '#include' in texto or 'int main' in texto:
            return 'c/c++'
        if '<html>' in texto or '<div' in texto:
            return 'html'
        return 'plain'

    def _ordenar_fragmentos(self, fragmentos, lenguaje):
        """Ordena fragmentos: imports/dependencias → definiciones → otros."""
        imports = []
        definiciones = []
        otros = []
        for frag in fragmentos:
            primeras_lineas = frag.strip().split('\n')[:3]
            texto = ' '.join(primeras_lineas).lower()
            if any(p in texto for p in ['import ', 'from ', 'require ', 'using ', '#include']):
                imports.append(frag)
            elif any(p in texto for p in ['def ', 'function ', 'class ', 'public class']):
                definiciones.append(frag)
            else:
                otros.append(frag)
        return imports + definiciones + otros

    def _eliminar_duplicados(self, fragmentos):
        """Elimina fragmentos que son muy similares entre sí."""
        unicos = []
        for frag in fragmentos:
            es_dup = False
            for existente in unicos:
                similitud = self._similitud(frag, existente)
                if similitud > 0.8:
                    es_dup = True
                    break
            if not es_dup:
                unicos.append(frag)
        return unicos

    def _similitud(self, a, b):
        """Calcula una similitud simple basada en palabras comunes."""
        palabras_a = set(a.split())
        palabras_b = set(b.split())
        if not palabras_a or not palabras_b:
            return 0
        comunes = palabras_a.intersection(palabras_b)
        return len(comunes) / max(len(palabras_a), len(palabras_b))

    def _sintetizar_texto(self, texto, consulta):
        """Extrae las oraciones más relevantes del texto según la consulta,
        descartando ruido promocional/legal y exigiendo que la oración
        realmente tenga que ver con lo que se preguntó."""
        if not texto:
            return ""
        oraciones = re.split(r'[.\n]+', texto)
        oraciones = [o.strip() for o in oraciones if len(o.strip()) > 30]
        if not oraciones:
            return ""

        palabras_consulta = set(consulta.lower().split())
        puntuadas = []
        for oracion in oraciones:
            if self._es_ruido(oracion):
                continue

            low = oracion.lower()
            coincidencias_reales = sum(1 for word in low.split() if word in palabras_consulta)

            # Exigimos al menos una coincidencia real con palabras de la
            # consulta; el bonus por palabras "tutorial/paso/ejemplo" ya no
            # alcanza por sí solo para calificar, evita que cuele texto
            # genérico sin relación con lo que se preguntó.
            if coincidencias_reales == 0:
                continue

            score = coincidencias_reales
            if any(kw in low for kw in ["código", "script", "paso", "ingrediente", "herramienta", "tutorial", "ejemplo"]):
                score += 1
            puntuadas.append((score, oracion))

        puntuadas.sort(reverse=True, key=lambda x: x[0])
        # Antes tomaba las 15 mejores oraciones sin importar el largo
        # total. Ahora corta apenas se acerca al presupuesto de
        # caracteres, para no generar un bloque de texto larguísimo que
        # después haya que truncar a lo bruto.
        mejores = []
        largo_acumulado = 0
        for score, oracion in puntuadas:
            if largo_acumulado + len(oracion) > 900:
                break
            mejores.append(oracion)
            largo_acumulado += len(oracion)

        if not mejores:
            # Si el filtro estricto no dejó nada, mejor no mandar ruido:
            # que el LLM use su propio conocimiento en vez de basura del scraping.
            return ""

        return "\n".join(mejores)
