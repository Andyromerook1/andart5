# api_connector.py
import requests
import re

class APIConnector:
    def __init__(self):
        # Ninguna clave requerida. Solo APIs gratuitas y sin registro.
        pass

    # ------------------------------------------------------------
    # Método principal que decide qué API usar
    # ------------------------------------------------------------
    def try_api(self, consulta):
        consulta_lower = consulta.lower()

        # --- Diccionario / definición ---
        if any(w in consulta_lower for w in ["definición", "significado", "qué es", "definir"]):
            return self._definicion(consulta)

        # --- Criptomonedas (precio) ---
        if any(w in consulta_lower for w in ["bitcoin", "ethereum", "precio de", "cripto"]):
            return self._cripto_precio(consulta)

        # --- Repositorio de GitHub (sin token, límite 60 peticiones/hora) ---
        if "github" in consulta_lower or "repo" in consulta_lower:
            return self._github_repo(consulta)

        # --- Paquete npm ---
        if "npm" in consulta_lower or "paquete npm" in consulta_lower:
            return self._npm_package(consulta)

        # --- Paquete PyPI ---
        if "pypi" in consulta_lower or "paquete python" in consulta_lower:
            return self._pypi_package(consulta)

        # --- StackOverflow ---
        if any(w in consulta_lower for w in ["stackoverflow", "error", "exception"]):
            return self._stackoverflow(consulta)

        # --- Wikipedia ---
        if "wikipedia" in consulta_lower or "wiki" in consulta_lower:
            return self._wikipedia(consulta)

        # --- Recetas (MealDB) ---
        if any(w in consulta_lower for w in ["receta", "cocinar", "ingredientes", "plato"]):
            return self._receta(consulta)

        # --- CVE / vulnerabilidades ---
        if any(w in consulta_lower for w in ["cve", "vulnerabilidad", "exploit", "hack", "pentest", "seguridad"]):
            return self._cve_info(consulta)

        # --- Acortador de URL ---
        if "acortar" in consulta_lower or "shorten" in consulta_lower:
            return self._shorten_url(consulta)

        # --- Chistes ---
        if "chiste" in consulta_lower or "broma" in consulta_lower:
            return self._chiste()

        # --- Usuario aleatorio ---
        if "usuario aleatorio" in consulta_lower or "fake user" in consulta_lower:
            return self._random_user()

        # --- Pokémon ---
        if "pokémon" in consulta_lower or "pokemon" in consulta_lower:
            return self._pokemon(consulta)

        # --- Traducción (LibreTranslate, sin clave) ---
        if "traduce" in consulta_lower or "translate" in consulta_lower:
            return self._traducir(consulta)

        return None

    # ============================================================
    # CONECTORES PÚBLICOS
    # ============================================================

    def _definicion(self, consulta):
        palabra = consulta.lower().replace("definición de", "").replace("significado de", "").replace("qué es", "").replace("definir", "").strip()
        if not palabra:
            return None
        url = f"https://api.dictionaryapi.dev/api/v2/entries/es/{palabra}"
        try:
            resp = requests.get(url, timeout=5).json()
            if isinstance(resp, list) and len(resp) > 0:
                definicion = resp[0]["meanings"][0]["definitions"][0]["definition"]
                return f"📖 Definición de '{palabra}': {definicion}"
        except:
            pass
        return None

    def _cripto_precio(self, consulta):
        if "bitcoin" in consulta.lower():
            moneda = "bitcoin"
        elif "ethereum" in consulta.lower():
            moneda = "ethereum"
        else:
            moneda = "bitcoin"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={moneda}&vs_currencies=usd"
        try:
            resp = requests.get(url, timeout=5).json()
            precio = resp[moneda]["usd"]
            return f"💰 {moneda.capitalize()}: ${precio} USD"
        except:
            return None

    def _github_repo(self, consulta):
        if "repo" in consulta:
            nombre = consulta.split("repo")[-1].strip()
        else:
            nombre = consulta.replace("github", "").strip()
        if not nombre:
            return None
        url = f"https://api.github.com/search/repositories?q={nombre}&per_page=1"
        headers = {"Accept": "application/vnd.github.v3+json"}
        try:
            resp = requests.get(url, headers=headers, timeout=5).json()
            items = resp.get("items", [])
            if items:
                repo = items[0]
                return f"🐙 GitHub: {repo['full_name']} - ⭐ {repo['stargazers_count']}\n{repo['html_url']}\n{repo['description']}"
        except:
            pass
        return None

    def _npm_package(self, consulta):
        nombre = consulta.lower().replace("npm", "").replace("paquete", "").strip()
        if not nombre:
            return None
        url = f"https://registry.npmjs.org/{nombre}"
        try:
            resp = requests.get(url, timeout=5).json()
            if "name" in resp:
                desc = resp.get("description", "")
                return f"📦 npm: {resp['name']} - {desc}\nhttps://www.npmjs.com/package/{nombre}"
        except:
            pass
        return None

    def _pypi_package(self, consulta):
        nombre = consulta.lower().replace("pypi", "").replace("paquete python", "").strip()
        if not nombre:
            return None
        url = f"https://pypi.org/pypi/{nombre}/json"
        try:
            resp = requests.get(url, timeout=5).json()
            info = resp.get("info", {})
            name = info.get("name")
            summary = info.get("summary")
            return f"🐍 PyPI: {name} - {summary}\nhttps://pypi.org/project/{nombre}"
        except:
            pass
        return None

    def _stackoverflow(self, consulta):
        query = consulta.strip()
        url = f"https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance&q={query}&site=stackoverflow"
        try:
            resp = requests.get(url, timeout=5).json()
            items = resp.get("items", [])
            if items:
                pregunta = items[0]["title"]
                enlace = items[0]["link"]
                return f"💬 StackOverflow: {pregunta}\n{enlace}"
        except:
            pass
        return None

    def _wikipedia(self, consulta):
        termino = consulta.lower().replace("wikipedia", "").replace("wiki", "").strip()
        if not termino:
            return None
        url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{termino}"
        headers = {"User-Agent": "Andart/5.3"}
        try:
            resp = requests.get(url, headers=headers, timeout=5).json()
            if "extract" in resp:
                return f"📚 Wikipedia: {resp['title']}\n{resp['extract'][:500]}..."
        except:
            pass
        return None

    def _receta(self, consulta):
        match = re.search(r'receta de ([\w\s]+)', consulta)
        plato = match.group(1).strip() if match else "chicken"
        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={plato}"
        try:
            resp = requests.get(url, timeout=5).json()
            meals = resp.get("meals")
            if meals:
                meal = meals[0]
                nombre = meal["strMeal"]
                instrucciones = meal["strInstructions"][:400]
                return f"🍳 Receta: {nombre}\n📝 {instrucciones}..."
        except:
            pass
        return None

    def _cve_info(self, consulta):
        match = re.search(r'CVE-\d{4}-\d+', consulta.upper())
        if match:
            cve_id = match.group(0)
        else:
            keyword = consulta.replace("cve", "").replace("vulnerabilidad", "").strip()
            return f"🔒 CVE Search: búsqueda por '{keyword}'. Mejor usa !api CVE-XXXX-YYYYY."
        url = f"https://cve.circl.lu/api/cve/{cve_id}"
        try:
            resp = requests.get(url, timeout=5).json()
            if "summary" in resp:
                summary = resp["summary"]
                cvss = resp.get("cvss", "N/A")
                return f"🛡️ {cve_id} - CVSS: {cvss}\n📄 {summary}"
        except:
            pass
        return None

    def _shorten_url(self, consulta):
        match = re.search(r'https?://[^\s]+', consulta)
        if match:
            long_url = match.group(0)
            url_api = f"https://clck.ru/--?url={long_url}"
            try:
                resp = requests.get(url_api, timeout=5)
                if resp.status_code == 200:
                    return f"🔗 URL acortada: {resp.text.strip()}"
            except:
                pass
        return None

    def _chiste(self):
        url = "https://v2.jokeapi.dev/joke/Any?lang=es"
        try:
            resp = requests.get(url, timeout=5).json()
            if resp["type"] == "single":
                return f"😂 {resp['joke']}"
            else:
                return f"😂 {resp['setup']} - {resp['delivery']}"
        except:
            return None

    def _random_user(self):
        url = "https://randomuser.me/api/"
        try:
            resp = requests.get(url, timeout=5).json()
            user = resp["results"][0]
            nombre = f"{user['name']['first']} {user['name']['last']}"
            email = user["email"]
            return f"👤 Usuario aleatorio: {nombre}\n📧 {email}"
        except:
            return None

    def _pokemon(self, consulta):
        nombre = consulta.lower().replace("pokémon", "").replace("pokemon", "").strip()
        if not nombre:
            nombre = "pikachu"
        url = f"https://pokeapi.co/api/v2/pokemon/{nombre}"
        try:
            resp = requests.get(url, timeout=5).json()
            name = resp["name"].capitalize()
            types = ", ".join(t["type"]["name"] for t in resp["types"])
            return f"⚡ Pokémon: {name} - Tipo: {types}"
        except:
            return None

    def _traducir(self, consulta):
        match = re.search(r'traduce (.+?) al (\w+)', consulta.lower())
        if not match:
            return "ℹ️ Uso: traduce <texto> al <idioma>"
        texto, idioma = match.group(1), match.group(2)
        url = "https://libretranslate.de/translate"
        payload = {"q": texto, "source": "auto", "target": idioma}
        try:
            resp = requests.post(url, json=payload, timeout=5).json()
            trad = resp.get("translatedText")
            return f"🌐 Traducción: {trad}"
        except:
            return None
