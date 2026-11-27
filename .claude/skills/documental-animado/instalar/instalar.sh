#!/usr/bin/env bash
# Instalador automático de la skill · Mac (en Windows se usa instalar.ps1; si esto se corre desde Git Bash, lo llama solo).
# No pide contraseña ni Homebrew. Se puede correr las veces que haga falta: sigue donde se quedó.
set -euo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$AQUI/instalar.ps1")" "$@" ;;
esac
UV_VER="0.11.32"
HERR="$HOME/.club-videos/bin"; mkdir -p "$HERR"
UV="$HERR/uv"
if ! [ -x "$UV" ]; then
  case "$(uname -m)" in arm64|aarch64) A=aarch64 ;; *) A=x86_64 ;; esac
  echo "Bajando uv (instala Python sin contraseña)…"
  T="$(mktemp -d)"
  curl -fsSL --retry 3 -o "$T/uv.tar.gz" "https://github.com/astral-sh/uv/releases/download/$UV_VER/uv-$A-apple-darwin.tar.gz"
  tar -xzf "$T/uv.tar.gz" -C "$T"
  cp "$(find "$T" -name uv -type f | head -1)" "$UV"; chmod +x "$UV"; rm -rf "$T"
fi
PYV="$(sed -n 's/.*"python" *: *"\([0-9.]*\)".*/\1/p' "$AQUI/kit.json" | head -1)"
export UV_EXE="$UV" PY_REQ="${PYV:-3.12}" UV_PYTHON_PREFERENCE=only-managed PYTHONUTF8=1
exec "$UV" run --quiet --no-project --python "$PY_REQ" "$AQUI/instalar.py" "$@"
