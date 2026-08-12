# extractor.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Lista de patrones basura que descartar
PATRONES_BASURA = [
    "cookie", "subscribe", "click here", "sign up", "log in",
    "all rights reserved", "privacy policy", "terms of service",
    "please enable javascript", "you need to enable",
    "©", "©️", "{{", "}}", "function(", "javascript:",
    "omcat", "findstr", "C:\\Program Files",  # Scripts rotos
    "menu", "sidebar", "widget", "footer", "header",
]

def extraer_contenido_y_enlaces(url, profundizar=False):
    """
    Extrae bloques estructurados (código y texto) y enlaces relevantes de una página.
    Retorna (lista_de_bloques, lista_de_enlaces).
    Cada bloque es un dict: {"tipo": "codigo"|"texto", "lenguaje": "", "contenido": "..."}
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Android; Linux arm64; Termux)"}
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return [], []
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()

        # Eliminar elementos con clases típicas de menús o barras
        for cls in ["menu", "sidebar", "widget", "footer", "header", "cookie"]:
            for tag in soup.find_all(class_=lambda x: x and cls in x.lower() if x else False):
                tag.decompose()

        bloques = []

        # Extraer bloques de código
        codigos = soup.find_all(["pre", "code", "textarea"])
        for bloque in codigos[:5]:
            codigo = bloque.get_text().strip()
            if len(codigo) > 15:
                # Descartar si es basura
                if any(basura in codigo.lower() for basura in PATRONES_BASURA):
                    continue
                lang = ""
                clases = bloque.get("class", [])
                for c in clases:
                    if c.startswith("language-"):
                        lang = c.replace("language-", "")
                        break
                bloques.append({
                    "tipo": "codigo",
                    "lenguaje": lang,
                    "contenido": codigo
                })

        # Extraer texto relevante
        textos = soup.find_all(["p", "h1", "h2", "h3", "li"])
        for elem in textos[:30]:
            txt = elem.get_text().strip()
            if len(txt) > 30:
                # Descartar si contiene basura
                if any(basura in txt.lower() for basura in PATRONES_BASURA):
                    continue
                # Descartar si es solo números o símbolos
                if not any(c.isalpha() for c in txt):
                    continue
                bloques.append({
                    "tipo": "texto",
                    "contenido": txt
                })

        # Si no se extrajo nada, agregar el texto completo como respaldo
        if not bloques:
            texto_completo = soup.get_text()[:2000]
            if texto_completo:
                # Limpiar el texto de respaldo también
                if not any(basura in texto_completo.lower() for basura in PATRONES_BASURA):
                    bloques.append({
                        "tipo": "texto",
                        "contenido": texto_completo
                    })

        # Recolectar enlaces internos útiles
        enlaces = []
        if profundizar:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                texto_enlace = a.get_text().strip().lower()
                if any(palabra in texto_enlace for palabra in ["tutorial", "ejemplo", "guía", "código", "script", "paso", "receta", "hack"]):
                    full_url = urljoin(url, href)
                    enlaces.append(full_url)

        return bloques, enlaces[:5]

    except Exception as e:
        return [{"tipo": "texto", "contenido": f"[-] Error: {e}"}], []
