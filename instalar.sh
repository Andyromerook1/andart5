#!/bin/bash
echo "🔧 Actualizando paquetes..."
pkg update && pkg upgrade -y
pkg install python git wget -y

echo "📦 Instalando dependencias Python..."
pip install requests beautifulsoup4 lxml ctransformers

echo "📥 Descargando modelo sin censura (~700MB)..."
mkdir -p ~/modelos
cd ~/modelos
if [ ! -f "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
    wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
else
    echo "Modelo ya descargado."
fi

echo "✅ Instalación completa. Vuelve a la carpeta del proyecto (cd ~/andart5) y ejecuta python main.py"
