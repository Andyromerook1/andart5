#!/bin/bash
set -e  # Si algo falla de verdad, cortar en vez de seguir como si nada

# Versión de llama.cpp a la que fijamos el build. No usamos "master" porque
# el proyecto cambia constantemente y a veces introduce cosas que rompen en
# Termux (ej: el binario unificado "llama-app" agregado en mayo 2026).
# Esta versión es anterior a ese cambio y compila bien en Android/Termux.
LLAMA_CPP_TAG="b8163"

echo "🔧 Actualizando paquetes..."
pkg update && pkg upgrade -y
pkg install python git cmake build-essential curl libxml2 libxslt pkg-config clang -y

echo "📦 Instalando dependencias Python..."
pip install requests beautifulsoup4 lxml

echo "🔨 Preparando llama.cpp (versión fijada: $LLAMA_CPP_TAG)..."
cd ~
if [ ! -d "llama.cpp" ]; then
    git clone https://github.com/ggml-org/llama.cpp.git
fi
cd llama.cpp

echo "🔖 Descartando cambios locales y trayendo etiquetas..."
git fetch --tags
git reset --hard
git checkout "$LLAMA_CPP_TAG"

rm -rf build

echo "🩹 Aplicando parche de compatibilidad ARM/clang (vcvtnq_s32_f32)..."
PATCH_FILE="ggml/src/ggml-cpu/ggml-cpu-impl.h"
if [ -f "$PATCH_FILE" ] && grep -q "^inline static int32x4_t vcvtnq_s32_f32" "$PATCH_FILE"; then
    python3 - <<'EOF'
path = "ggml/src/ggml-cpu/ggml-cpu-impl.h"
with open(path) as f:
    lines = f.readlines()

start = None
for i, line in enumerate(lines):
    if "int32x4_t vcvtnq_s32_f32" in line and "inline" in line:
        start = i
        break

if start is None:
    print("⚠️  No se encontró la función. Puede que ya esté parcheada.")
else:
    if start > 0 and "#ifndef __clang__" in lines[start-1]:
        print("✅ Ya estaba parcheada. Nada que hacer.")
    else:
        depth = 0
        end = None
        for j in range(start, len(lines)):
            depth += lines[j].count("{")
            depth -= lines[j].count("}")
            if depth == 0 and j > start:
                end = j
                break
        if end is None:
            print("⚠️  No se pudo encontrar el cierre de la función.")
        else:
            lines.insert(end + 1, "#endif\n")
            lines.insert(start, "#ifndef __clang__\n")
            with open(path, "w") as f:
                f.writelines(lines)
            print(f"✅ Parche aplicado (líneas {start+1} a {end+1}).")
EOF
else
    echo "✅ El archivo no contiene el bloque conflictivo en esta versión. Continuando..."
fi

echo "🔨 Compilando llama.cpp..."
cmake -B build -DGGML_NATIVE=ON -DLLAMA_BUILD_TESTS=OFF
cmake --build build --config Release -j4

if [ ! -f "build/bin/llama-cli" ]; then
    echo "❌ La compilación terminó pero no se generó build/bin/llama-cli."
    echo "   Revisa el log de arriba en busca de la primera línea que diga 'error:' (no 'warning:')."
    exit 1
fi

mkdir -p ~/bin
cp build/bin/llama-cli ~/bin/
chmod +x ~/bin/llama-cli
export PATH=$PATH:~/bin
if ! grep -q '~/bin' ~/.bashrc 2>/dev/null; then
    echo "export PATH=\$PATH:~/bin" >> ~/.bashrc
fi

echo "🔍 Detectando RAM del dispositivo..."
RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
RAM_MB=$((RAM_KB / 1024))
echo "RAM total detectada: ${RAM_MB}MB"

# Elegimos el modelo según la RAM real del dispositivo, para que Andart
# nunca reviente por falta de memoria, sin importar si el teléfono tiene
# 2GB o 8GB. Todo esto sigue corriendo 100% local: nada sale del equipo.
if [ "$RAM_MB" -le 2200 ]; then
    MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
    MODEL_FILE="qwen2.5-0.5b-instruct-q4_k_m.gguf"
    MODEL_FORMATO="chatml"
    echo "📦 Perfil detectado: RAM baja (~${RAM_MB}MB) → Qwen2.5-0.5B-Instruct"
else
    MODEL_URL="https://huggingface.co/mradermacher/TinyLlama-1.1B-Chat-v1.0-Heretic-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0-Heretic.Q4_K_M.gguf"
    MODEL_FILE="TinyLlama-1.1B-Chat-v1.0-Heretic.Q4_K_M.gguf"
    MODEL_FORMATO="zephyr"
    echo "📦 Perfil detectado: RAM media/alta (~${RAM_MB}MB) → TinyLlama-1.1B Heretic (uncensored)"
fi

echo "📥 Descargando modelo ($MODEL_FILE)..."
mkdir -p ~/modelos
cd ~/modelos
if [ ! -f "$MODEL_FILE" ]; then
    curl -L -O -C - "$MODEL_URL"
else
    echo "Modelo ya descargado, verificando integridad..."
fi

echo "🔎 Verificando que el archivo sea un GGUF válido..."
MAGIC=$(head -c 4 "$MODEL_FILE")
if [ "$MAGIC" != "GGUF" ]; then
    echo "❌ El archivo descargado NO es un modelo GGUF válido (probablemente"
    echo "   se bajó una página de error en vez del modelo). Primeros bytes:"
    head -c 200 "$MODEL_FILE"
    echo ""
    echo "   Borrando archivo corrupto para no dejar algo roto instalado."
    rm -f "$MODEL_FILE"
    exit 1
fi
echo "✅ Archivo GGUF verificado correctamente."

echo "📝 Guardando configuración en ~/.andart/config.json..."
mkdir -p ~/.andart
cat > ~/.andart/config.json <<EOF
{
  "model_path": "~/modelos/$MODEL_FILE",
  "formato_chat": "$MODEL_FORMATO",
  "ram_detectada_mb": $RAM_MB
}
EOF

echo ""
echo "✅ Instalación completa."
~/bin/llama-cli --version
echo "Vuelve a la carpeta del proyecto (cd ~/andart5) y ejecuta python main.py"
