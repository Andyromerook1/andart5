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

echo "🩹 Aplicando parche de compatibilidad ARM/clang (vcvtnq_s32_f32)..."
PATCH_FILE="ggml/src/ggml-cpu/ggml-cpu-impl.h"
if grep -q "^inline static int32x4_t vcvtnq_s32_f32" "$PATCH_FILE"; then
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
    echo "✅ El archivo ya está parcheado o no contiene el bloque conflictivo. Continuando..."
fi

cmake -B build -DLLAMA_BUILD_SERVER=OFF -DGGML_NATIVE=ON
cmake --build build --config Release -j4

mkdir -p ~/bin
cp build/bin/llama-cli ~/bin/
chmod +x ~/bin/llama-cli
export PATH=$PATH:~/bin
echo "export PATH=\$PATH:~/bin" >> ~/.bashrc

echo "📥 Descargando modelo Qwen2.5-0.5B-Instruct (~500MB)..."
mkdir -p ~/modelos
cd ~/modelos
if [ ! -f "qwen2.5-0.5b-instruct-q4_k_m.gguf" ]; then
    curl -L -O -C - https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf
else
    echo "Modelo ya descargado."
fi

echo "✅ Instalación completa. Vuelve a la carpeta del proyecto (cd ~/andart5) y ejecuta python main.py"
