# buscador.py
from duckduckgo_search import DDGS

def buscar_multicanal(consulta, max_results=5, sitio=None):
    """
    Búsqueda en DuckDuckGo, con posibilidad de restringir a un sitio específico.
    Retorna lista de dicts con 'title', 'href', 'body'.
    """
    if sitio:
        consulta += f" site:{sitio}"
    print(f"[*] Buscando: '{consulta}'")
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, max_results=max_results))
            return resultados
    except Exception as e:
        print(f"[-] Error en búsqueda: {e}")
        return []