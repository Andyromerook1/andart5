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

if [ ! -f "build/bin/llama-completion" ]; then
    echo "❌ La compilación terminó pero no se generó build/bin/llama-completion."
    echo "   Revisa el log de arriba en busca de la primera línea que diga 'error:' (no 'warning:')."
    exit 1
fi

mkdir -p ~/bin
cp build/bin/llama-cli ~/bin/
chmod +x ~/bin/llama-cli
cp build/bin/llama-completion ~/bin/
chmod +x ~/bin/llama-completion
export PATH=$PATH:~/bin
if ! grep -q '~/bin' ~/.bashrc 2>/dev/null; then
    echo "export PATH=\$PATH:~/bin" >> ~/.bashrc
fi

echo "🔍 Detectando RAM del dispositivo..."
RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
RAM_MB=$((RAM_KB / 1024))
echo "RAM total detectada: ${RAM_MB}MB"

# Elegimos el modelo según la RAM real del dispositivo, para que Andart
# nunca reviente por falta de memoria. Todo esto sigue corriendo 100%
# local: nada sale del equipo.
#
# Los tres escalones usan Qwen2.5-Coder abliterated (versión de bartowski
# en HuggingFace): mejor que TinyLlama en generación/explicación de código,
# y sin el reflejo de rechazo del modelo base. Mismo formato de chat
# (chatml) en los tres, para no tener que mezclar formatos en el resto
# de la app.
if [ "$RAM_MB" -le 2200 ]; then
    MODEL_URL="https://huggingface.co/bartowski/Qwen2.5-Coder-1.5B-Instruct-abliterated-GGUF/resolve/main/Qwen2.5-Coder-1.5B-Instruct-abliterated-Q4_K_M.gguf"
    MODEL_FILE="Qwen2.5-Coder-1.5B-Instruct-abliterated-Q4_K_M.gguf"
    MODEL_FORMATO="chatml"
    CTX_SIZE=2048
    N_PREDICT=350
    HISTORIAL_TURNOS=1
    echo "📦 Perfil detectado: RAM baja (~${RAM_MB}MB) → Qwen2.5-Coder-1.5B, ctx=2048, n_predict=350, historial=1 turno"
elif [ "$RAM_MB" -le 3500 ]; then
    MODEL_URL="https://huggingface.co/bartowski/Qwen2.5-Coder-1.5B-Instruct-abliterated-GGUF/resolve/main/Qwen2.5-Coder-1.5B-Instruct-abliterated-Q4_K_M.gguf"
    MODEL_FILE="Qwen2.5-Coder-1.5B-Instruct-abliterated-Q4_K_M.gguf"
    MODEL_FORMATO="chatml"
    CTX_SIZE=4096
    N_PREDICT=500
    HISTORIAL_TURNOS=2
    echo "📦 Perfil detectado: RAM media (~${RAM_MB}MB) → Qwen2.5-Coder-1.5B, ctx=4096, n_predict=500, historial=2 turnos"
else
    MODEL_URL="https://huggingface.co/bartowski/Qwen2.5-Coder-3B-Instruct-abliterated-GGUF/resolve/main/Qwen2.5-Coder-3B-Instruct-abliterated-Q4_K_M.gguf"
    MODEL_FILE="Qwen2.5-Coder-3B-Instruct-abliterated-Q4_K_M.gguf"
    MODEL_FORMATO="chatml"
    CTX_SIZE=4096
    N_PREDICT=700
    HISTORIAL_TURNOS=3
    echo "📦 Perfil detectado: RAM media-alta (~${RAM_MB}MB) → Qwen2.5-Coder-3B, ctx=4096, n_predict=700, historial=3 turnos"
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
  "ctx_size": $CTX_SIZE,
  "n_predict": $N_PREDICT,
  "historial_turnos": $HISTORIAL_TURNOS,
  "ram_detectada_mb": $RAM_MB
}
EOF

echo ""
echo "✅ Instalación completa."
~/bin/llama-cli --version
echo "Vuelve a la carpeta del proyecto (cd ~/andart5) y ejecuta python servidor.py"
