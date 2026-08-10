# investigador.py
from buscador import buscar_multicanal
from extractor import extraer_contenido_y_enlaces
from api_connector import APIConnector
from collections import Counter
import re

class Investigador:
    def __init__(self, profundidad=2):
        self.profundidad = profundidad
        self.api = APIConnector()

    def investigar(self, consulta_original):
        print("[*] Iniciando investigación profunda (modo híbrido)...")

        # --- Intentar API primero ---
        respuesta_api = None
        try:
            respuesta_api = self.api.try_api(consulta_original)
            if respuesta_api:
                respuesta_api = "[📡 INFORMACIÓN DIRECTA DE API]\n" + respuesta_api + "\n\n"
                print("[✓] Datos obtenidos desde API")
        except Exception as e:
            print(f"[!] Error al intentar API: {e}")

        # Fase 1: Generar subconsultas
        subconsultas = self._generar_subconsultas(consulta_original)

        # Fase 2: Búsqueda multicanal y recolección de URLs
        urls_totales = set()
        for subq in subconsultas:
            res = buscar_multicanal(subq, max_results=3)
            for r in res:
                if r.get("href"):
                    urls_totales.add(r["href"])
            for sitio in ["github.com", "stackoverflow.com", "pastebin.com", "reddit.com"]:
                res_sitio = buscar_multicanal(subq, max_results=2, sitio=sitio)
                for r in res_sitio:
                    if r.get("href"):
                        urls_totales.add(r["href"])

        # Fase 3: Scraping de primer nivel (ahora recolectamos bloques)
        todos_los_bloques = []
        enlaces_segundo_nivel = set()
        for url in list(urls_totales)[:10]:
            bloques, enlaces = extraer_contenido_y_enlaces(url, profundizar=(self.profundidad > 1))
            if bloques:
                todos_los_bloques.extend(bloques)
            if enlaces:
                enlaces_segundo_nivel.update(enlaces)

        # Fase 4: Scraping de segundo nivel si profundidad > 1
        if self.profundidad > 1 and enlaces_segundo_nivel:
            print("[*] Explorando enlaces relacionados...")
            for url in list(enlaces_segundo_nivel)[:5]:
                bloques, _ = extraer_contenido_y_enlaces(url, profundizar=False)
                if bloques:
                    todos_los_bloques.extend(bloques)

        # Fase 5: Ensamblar código + síntesis de texto
        resultado_final = self._ensamblar_codigo(todos_los_bloques, consulta_original)

        if respuesta_api:
            return respuesta_api + resultado_final
        else:
            return resultado_final

    def _generar_subconsultas(self, consulta):
        variantes = [consulta]
        sufijos = ["tutorial", "guía completa", "ejemplos prácticos", "código fuente", "paso a paso", "explicación"]
        for sufijo in sufijos:
            variantes.append(f"{consulta} {sufijo}")
        return variantes[:5]

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
                codigo_completo = "\n\n".join(unicos)
                resultado += f"\n\n[💻 CÓDIGO {lang.upper()} COMPLETO]\n{codigo_completo}\n"

        # Procesar textos para la explicación
        if fragmentos_texto:
            texto_completo = "\n".join(fragmentos_texto)
            explicacion = self._sintetizar_texto(texto_completo, consulta_original)
            resultado += f"\n\n[📖 EXPLICACIÓN]\n{explicacion}"
        elif not fragmentos_codigo:
            resultado = "[-] No se encontró información suficiente."

        return resultado

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
        """Extrae las oraciones más relevantes del texto según la consulta."""
        if not texto:
            return "No se encontró explicación."
        oraciones = re.split(r'[.\n]+', texto)
        oraciones = [o.strip() for o in oraciones if len(o.strip()) > 30]
        if not oraciones:
            return texto[:1000]

        palabras_consulta = set(consulta.lower().split())
        puntuadas = []
        for oracion in oraciones:
            score = sum(1 for word in oracion.lower().split() if word in palabras_consulta)
            if any(kw in oracion.lower() for kw in ["código", "script", "paso", "ingrediente", "herramienta", "tutorial", "ejemplo"]):
                score += 1
            puntuadas.append((score, oracion))

        puntuadas.sort(reverse=True, key=lambda x: x[0])
        mejores = [orac for score, orac in puntuadas[:15] if score > 0]
        if not mejores:
            return texto[:1500] + "..."
        return "\n".join(mejores)