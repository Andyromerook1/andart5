# extractor.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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

        bloques = []

        # Extraer bloques de código
        codigos = soup.find_all(["pre", "code", "textarea"])
        for bloque in codigos[:5]:
            codigo = bloque.get_text().strip()
            if len(codigo) > 15:
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
                bloques.append({
                    "tipo": "texto",
                    "contenido": txt
                })

        # Si no se extrajo nada, agregar el texto completo como respaldo
        if not bloques:
            texto_completo = soup.get_text()[:2000]
            if texto_completo:
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