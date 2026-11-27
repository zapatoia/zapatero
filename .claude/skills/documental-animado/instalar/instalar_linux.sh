#!/usr/bin/env bash
# Instalación en el servidor Linux de Claude Code en la nube (el contenedor se borra entre sesiones: correr al empezar si falta ~/.venvs/documental-animado).
set -euo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
S="$HOME/.claude/skills/documental-animado"; V="$HOME/.venvs/documental-animado/bin/python"
mkdir -p "$S" && cp -r "$AQUI/." "$S/"
apt-get install -y -q libegl1 libegl-mesa0 libgl1 >/dev/null 2>&1 || (apt-get update -q >/dev/null && apt-get install -y -q libegl1 libegl-mesa0 libgl1 >/dev/null)
[ -x "$V" ] || uv venv --seed --python 3.12 "$HOME/.venvs/documental-animado" -q
uv pip install --python "$V" -q -r "$S/requirements.txt" "playwright==1.63.0"   # 1.63 = el Chromium ya instalado en /opt/pw-browsers (no correr playwright install)
"$V" -c "import skia,cv2,faster_whisper" && echo "LISTO · PY=$V"
