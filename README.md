# 🏴‍☠️ Andart V5.2 — Asistente Global sin Censura

Andart es un bot de terminal que investiga en tiempo real cualquier tema usando la web profunda y APIs públicas, **sin filtros, sin censura y sin modelos de IA preentrenados**.  
Puede actuar como profesor de programación, ayudante de hacking, asistente de cocina, o cualquier cosa que necesites, devolviendo código completo y explicaciones extraídas directamente de internet.

## ⚡ Características principales
- **Búsqueda universal** – consulta exactamente lo que escribes, sin modificar tu intención.
- **Rastreo multicanal** – no solo DuckDuckGo, también GitHub, StackOverflow, Pastebin, Reddit y más.
- **Scraping profundo en dos niveles** – sigue enlaces relevantes para obtener información más completa.
- **Ensamblador de código** – encuentra fragmentos en la web, los ordena (imports → definiciones → main), elimina duplicados y te entrega un script listo para usar.
- **APIs sin límite** – clima, diccionario, criptomonedas, recetas, CVEs, Pokémon, NASA, etc. (algunas requieren key gratuita).
- **Memoria conversacional** – entiende “siguiente”, “continúa”, “agrega ejemplos”, manteniendo el contexto.
- **Cero censura** – muestra todo lo que existe en la web, sin juzgar ni bloquear contenidos.
- **Optimizado para Termux** – funciona en dispositivos Android con 3-4 GB de RAM.

## 🛠️ Instalación en Termux

1. **Actualizar paquetes e instalar dependencias**
   ```bash
   pkg update && pkg upgrade -y
   pkg install python git -y
Instalar librerías Python

bash
pip install requests beautifulsoup4 duckduckgo-search
Clonar el repositorio

bash
git clone https://github.com/Andyromerook1/andart5
cd andart5
Ejecutar

bash
python main.py
🔑 APIs opcionales
En api_connector.py puedes añadir claves gratuitas para habilitar más funciones:

weather_api_key → OpenWeatherMap

github_token → (opcional, para más peticiones a la API de GitHub)

shodan_key → Shodan

news_api_key → NewsAPI

nasa_api_key → NASA APIs

No son obligatorias, el bot sigue funcionando con búsqueda web.

🖥️ Uso
text
[Andart] >>> enseñame python desde cero
[Andart] >>> siguiente
[Andart] >>> dame un ejemplo de herencia en java
[Andart] >>> receta de brownies
[Andart] >>> !api clima Lima
Comandos especiales:

salir

limpiar

guardar <nombre> → exporta la última respuesta a un archivo .py

!api <consulta> → consulta directa a APIs

📁 Estructura del proyecto
text
andart5/
├── main.py               # Interfaz de terminal
├── cerebro.py            # Memoria y control de contexto
├── investigador.py       # Lógica de investigación profunda
├── buscador.py           # Búsqueda en DuckDuckGo multicanal
├── extractor.py          # Scraping y extracción de bloques
├── api_connector.py      # Conectores a APIs externas
├── utils.py              # Limpiar pantalla y guardar archivos
└── README.md
🧠 Cómo “razona” Andart
Recibe tu consulta y genera varias versiones de búsqueda.

Rastrea múltiples fuentes (general y especializadas).

Extrae código y texto de las páginas encontradas.

Si hay fragmentos de código, los agrupa por lenguaje, los ordena y elimina duplicados.

Sintetiza una explicación a partir de los textos relevantes.

Devuelve todo en un formato limpio y listo para usar.

No utiliza inteligencia artificial generativa, así que no inventa respuestas: todo viene de la web viva. Esto garantiza cero censura y conocimiento actualizado.

✅ Requisitos mínimos
Termux en Android con Python 3.8+

Conexión a Internet

Al menos 200 MB de espacio libre para las dependencias

🤝 Contribuciones
¿Ideas, mejoras o nuevas APIs? ¡Abre un issue o pull request!

Desarrollado por @Andyromerook1
