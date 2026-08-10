#!/bin/bash
echo "🔧 Actualizando paquetes..."
pkg update && pkg upgrade -y
pkg install python git cmake build-essential curl libxml2 libxslt pkg-config clang -y

echo "📦 Instalando dependencias Python..."
pip install requests beautifulsoup4 lxml

echo "🔨 Compilando llama.cpp..."
cd ~
if [ ! -d "llama.cpp" ]; then
    git clone https://github.com/ggml-org/llama.cpp.git
fi
cd llama.cpp
git pull
rm -rf build
cmake -B build -DLLAMA_BUILD_SERVER=OFF -DGGML_NATIVE=OFF
cmake --build build --config Release -j4
mkdir -p ~/bin
cp build/bin/llama-cli ~/bin/
chmod +x ~/bin/llama-cli
export PATH=$PATH:~/bin
echo "export PATH=\$PATH:~/bin" >> ~/.bashrc

echo "📥 Descargando modelo sin censura (~700MB)..."
mkdir -p ~/modelos
cd ~/modelos
if [ ! -f "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
    curl -L -O -C - https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
else
    echo "Modelo ya descargado."
fi

echo "✅ Instalación completa. Vuelve a la carpeta del proyecto (cd ~/andart5) y ejecuta python main.py"
