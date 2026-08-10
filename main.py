# main.py
from utils import limpiar_pantalla, guardar_archivo
from cerebro import CerebroAndart
from api_connector import APIConnector   # <--- NUEVO

def banner():
    print("="*75)
    print("   🏴‍☠️ ANDART V5.1 — Asistente Híbrido (APIs + Web Profunda)")
    print("="*75)
    print("   Capacidades: APIs sin límites, investigación web, código, tutoriales.")
    print("   Comandos: 'salir' | 'limpiar' | 'guardar <nombre>' | '!api <consulta>'")
    print("="*75 + "\n")

def main():
    limpiar_pantalla()
    banner()
    
    cerebro = CerebroAndart()
    api_directa = APIConnector()    # Instancia para el comando !api
    ultimo_resultado = "print('Andart inicializado')"
    
    while True:
        try:
            entrada = input("\n[Andart] >>> ").strip()
            if not entrada:
                continue
                
            cmd = entrada.lower()

            # --- COMANDOS DIRECTOS ---
            if cmd == "salir":
                print("\n[*] Sesión finalizada. ¡Hasta la próxima!")
                break

            elif cmd == "limpiar":
                limpiar_pantalla()
                banner()
                continue

            elif cmd.startswith("guardar "):
                nombre = cmd.split(" ", 1)[1]
                guardar_archivo(nombre, ultimo_resultado)
                continue

            # --- NUEVO COMANDO !api ---
            elif cmd.startswith("!api"):
                consulta_api = entrada[5:].strip()
                if not consulta_api:
                    print("[!] Uso: !api <tipo> <consulta> (ej: !api clima Buenos Aires)")
                    continue
                resultado_api = api_directa.try_api(consulta_api)
                if resultado_api:
                    print(f"\n🤖 {resultado_api}")
                    ultimo_resultado = resultado_api
                else:
                    print("[!] No se encontró una API adecuada o falló. Usa la búsqueda normal sin !api.")
                continue

            # --- INVESTIGACIÓN NORMAL (híbrida) ---
            else:
                tipo, explicacion, salida = cerebro.procesar(entrada)
                print(f"\n🤖 {explicacion}\n")
                print(salida)
                ultimo_resultado = salida

        except KeyboardInterrupt:
            print("\n\n[*] Operación interrumpida por el usuario.")
            break

if __name__ == "__main__":
    main()