# buscador.py
import requests
from bs4 import BeautifulSoup

def buscar_multicanal(consulta, max_results=3, sitio=None):
    """
    Busca en DuckDuckGo (HTML) y devuelve lista de dicts
    con 'title', 'href', 'body'.
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
        # Los resultados están en elementos con clase "result__body"
        for item in soup.select(".result__body"):
            title_tag = item.select_one(".result__title a")
            snippet_tag = item.select_one(".result__snippet")
            link_tag = item.select_one(".result__url")
            if title_tag:
                title = title_tag.get_text(strip=True)
                href = link_tag.get_text(strip=True) if link_tag else ""
                body = snippet_tag.get_text(strip=True) if snippet_tag else ""
                results.append({"title": title, "href": href, "body": body})
                if len(results) >= max_results:
                    break
        return results
    except Exception as e:
        print(f"[-] Error en búsqueda: {e}")
        return []
