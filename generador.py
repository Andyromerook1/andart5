# generador.py

def obtener_script_web():
    return """# Andart - Script Real de Fuzzing y Verificación Web
import requests
import concurrent.futures
import sys

def comprobar(url):
    headers = {"User-Agent": "Mozilla/5.0", "X-Forwarded-For": "127.0.0.1"}
    try:
        r = requests.get(url, headers=headers, timeout=5, allow_redirects=False)
        if r.status_code != 404:
            print(f"[+] [HTTP {r.status_code}] Hallado: {url} | Tamaño: {len(r.content)} bytes")
    except Exception:
        pass

def ejecutar(base, wordlist):
    print(f"[*] Iniciando análisis masivo sobre: {base}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        for w in wordlist:
            target = f"{base.rstrip('/')}/{w}"
            executor.submit(comprobar, target)

if __name__ == "__main__":
    lista = ["admin", "config", ".env", "api/v1/users", "debug", "backup.sql", "server-status", "graphql"]
    objetivo = sys.argv[1] if len(sys.argv) > 1 else "http://localhost"
    ejecutar(objetivo, lista)
"""

def obtener_script_red():
    return """# Andart - Analizador y Capturador de Tráfico Local por Sockets
import socket
import sys

def iniciar_captura(puerto):
    print(f"[*] Escuchando tráfico en puerto local {puerto}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", puerto))
    s.listen(5)
    
    while True:
        conn, addr = s.accept()
        print(f"[+] Conexión interceptada desde: {addr[0]}:{addr[1]}")
        try:
            data = conn.recv(4096)
            print(f"--- Datos Crudos ---\\n{data.decode('utf-8', errors='ignore')}\\n--------------------")
        except:
            pass
        conn.close()

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    iniciar_captura(p)
"""

def obtener_script_general():
    return """# Andart - Script Base Personalizado
import sys

def main():
    print("[*] Ejecutando tarea solicitada a Andart...")
    if len(sys.argv) > 1:
        print(f"[+] Parámetro recibido: {sys.argv[1]}")
    else:
        print("[+] Operación completada con éxito.")

if __name__ == "__main__":
    main()
"""