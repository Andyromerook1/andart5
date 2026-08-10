# utils.py
import os

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def guardar_archivo(nombre, contenido):
    nombre_archivo = f"{nombre}.py"
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        f.write(contenido)
    print(f"\n[+] Archivo guardado con éxito como: {nombre_archivo}")