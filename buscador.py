# buscador.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse

def buscar_multicanal(consulta, max_results=3, sitio=None):
    """
    Busca en DuckDuckGo (HTML) y devuelve lista de dicts
    con 'title', 'href' (URL absoluta), 'body'.
    """
    query = consulta
    if sitio:
        query += f" site:{sitio}"
    
    url = "https://html.duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0 (Android; Linux arm64; Termux)"}
    params = {"q": query, "kl": "us-en"}
    
    try:
        resp = requests.post(url, data=params, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for item in soup.select(".result__body"):
            title_tag = item.select_one(".result__title a")
            snippet_tag = item.select_one(".result__snippet")
            link_tag = item.select_one(".result__url")
            if not title_tag:
                continue
            
            title = title_tag.get_text(strip=True)
            body = snippet_tag.get_text(strip=True) if snippet_tag else ""
            
            # Intentar extraer la URL real del enlace de redirección de DuckDuckGo
            raw_href = title_tag.get("href", "")
            real_url = ""
            if "uddg=" in raw_href:
                # El formato es /l/?kh=...&uddg=https%3A%2F%2Fwww.pagina.com%2F...
                uddg_start = raw_href.find("uddg=") + 5
                uddg_end = raw_href.find("&", uddg_start)
                if uddg_end == -1:
                    uddg_end = len(raw_href)
                encoded_url = raw_href[uddg_start:uddg_end]
                real_url = unquote(encoded_url)
            else:
                # Fallback: usar el texto visible y añadir https:// si falta
                visible_url = link_tag.get_text(strip=True) if link_tag else ""
                if visible_url and not visible_url.startswith("http"):
                    visible_url = "https://" + visible_url
                real_url = visible_url
            
            if real_url:
                results.append({"title": title, "href": real_url, "body": body})
                if len(results) >= max_results:
                    break
        return results
    except Exception as e:
        print(f"[-] Error en búsqueda: {e}")
        return []
