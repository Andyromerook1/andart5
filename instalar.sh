#!/bin/bash
echo "🔧 Actualizando paquetes..."
pkg update && pkg upgrade -y

echo "📦 Instalando dependencias del sistema..."
pkg install python git curl libxml2 libxslt pkg-config clang -y

echo "🐍 Actualizando pip..."
pip install --upgrade pip

echo "📦 Instalando dependencias Python..."
pip install requests beautifulsoup4 lxml ctransformers

echo "📥 Descargando modelo sin censura (~700MB)..."
mkdir -p ~/modelos
cd ~/modelos
if [ ! -f "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
    echo "Descargando con curl (reanudable)..."
    curl -L -O -C - https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
else
    echo "Modelo ya descargado."
fi

echo "✅ Instalación completa. Vuelve a la carpeta del proyecto (cd ~/andart5) y ejecuta python main.py"
