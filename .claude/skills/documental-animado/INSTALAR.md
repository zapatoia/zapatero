# Instalar «documental-animado» (Mac y Windows)

> **Ya no hace falta seguir esto a mano.** Un solo comando instala todo: Mac `bash instalar/instalar.sh` · Windows
> `powershell -NoProfile -ExecutionPolicy Bypass -File instalar\instalar.ps1` (desde la carpeta de la skill). Esta guía queda
> por si algo falla y hay que arreglarlo a mano.

El video se dibuja en tu computadora: un motor HTML/JS corre dentro de un Chromium sin ventana (lo instala Playwright) y ffmpeg une
los cuadros. Lo único de pago es la voz (ElevenLabs). Whisper (verifica la voz) corre local y gratis: la primera vez baja su modelo
(~1.6 GB) y después funciona sin internet. Mapas, librerías y fuentes vienen en el kit: para dibujar no hace falta internet.

**Requisitos:** Python **3.12** (o 3.11), ~6 GB libres (incluye el Chromium del motor, ~0.3 GB), 16 GB de RAM recomendados (8 GB con `--procesos 1`).
No hace falta ser administrador en ningún paso.

Los comandos de abajo los corre Claude: en Mac en la Terminal y en Windows en Git Bash (lo que usa Claude Code), con rutas con «/».

## 1 · Python

**Mac**
- Sin contraseña de administrador (recomendado): `curl -LsSf https://astral.sh/uv/install.sh | sh` y luego `~/.local/bin/uv python install 3.12`.
  Queda en `~/.local/bin/python3.12`.
- O el instalador de <https://www.python.org/downloads/macos/> (pide la contraseña de la Mac). **Después** abre
  `/Applications/Python 3.12/Install Certificates.command`: sin eso la conexión con ElevenLabs falla con `CERTIFICATE_VERIFY_FAILED`.

**Windows 10/11**
- `winget install -e --id Python.Python.3.12 --scope user` (sin administrador).
- O el instalador «Windows installer (64-bit)» de <https://www.python.org/downloads/windows/> → **Install Now** (se instala solo para tu
  usuario) y marca «Add python.exe to PATH».
- **PC con procesador ARM** (Snapdragon / Copilot+): instala la versión **x64**, no la ARM64 (`winget … --architecture x64`).
  OpenCV no tiene versión ARM64 para Windows y `pip` falla con «No matching distribution».
- Usa siempre `py -3.12`: el `python` que trae Windows de fábrica solo abre la Microsoft Store.

## 2 · ffmpeg

No hace falta instalar nada: `requirements.txt` trae `imageio-ffmpeg`, que incluye un ffmpeg para Mac (Apple e Intel) y Windows, y el kit
lo usa solo si no encuentra otro. Si prefieres uno propio:
- **Mac, sin Homebrew:** un ffmpeg estático (por ejemplo de <https://evermeet.cx/ffmpeg/>). Bájalo con `curl` (así macOS no lo pone en
  cuarentena), `chmod +x ffmpeg` y déjalo en `~/.local/bin/` o apúntalo con la variable `FFMPEG=/ruta/ffmpeg`.
- **Windows:** `winget install -e --id Gyan.FFmpeg` (sin administrador). Queda en el PATH de las terminales **nuevas**: cierra y vuelve a abrir
  Claude Code. O el zip «ffmpeg-release-essentials» de <https://www.gyan.dev/ffmpeg/builds/> descomprimido en `C:\ffmpeg` y
  `setx FFMPEG C:\ffmpeg\bin\ffmpeg.exe` (sin comillas).

## 3 · Entorno virtual y paquetes

Siempre en el disco interno (en un disco externo exFAT `pip` falla). Desde la carpeta de la skill (la que tiene `requirements.txt`):

**Mac** (Terminal)
```bash
python3.12 -m venv ~/.venvs/documental-animado
PY=~/.venvs/documental-animado/bin/python
$PY -m pip install --upgrade pip
$PY -m pip install -r requirements.txt
$PY -m playwright install chromium
```

**Windows** — lo que corre Claude Code (Git Bash):
```bash
py -3.12 -m venv "$HOME/.venvs/documental-animado"
PY="$HOME/.venvs/documental-animado/Scripts/python.exe"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt
"$PY" -m playwright install chromium
```
Si lo haces tú a mano en PowerShell:
```powershell
py -3.12 -m venv "$HOME\.venvs\documental-animado"
$PY = "$HOME\.venvs\documental-animado\Scripts\python.exe"
& $PY -m pip install --upgrade pip
& $PY -m pip install -r requirements.txt
& $PY -m playwright install chromium
```
La única diferencia entre sistemas es dónde queda Python: `.venvs/documental-animado/bin/python` en Mac y `.venvs\documental-animado\Scripts\python.exe` en Windows.
Si al importar algo sale «DLL load failed»: `winget install -e --id Microsoft.VCRedist.2015+.x64` y vuelve a probar.

**Navegador del motor:** `playwright install chromium` (arriba) baja un Chromium sin ventana (~0.3 GB) a `~/Library/Caches/ms-playwright`
(Mac) o `%LOCALAPPDATA%\ms-playwright` (Windows). No pide administrador ni toca tu Chrome. El motor levanta un servidor local solo en
`127.0.0.1` mientras dibuja: si el firewall de Windows pregunta, puedes negarlo (no necesita la red).

**Whisper:** en Mac con chip Apple se instala `mlx-whisper` (GPU); en Mac Intel y en Windows, `faster-whisper` (CPU). En Windows con tarjeta
NVIDIA y CUDA 12 + cuDNN 9 instalados puedes usar la GPU con `setx WHISPER_CUDA 1` (sin eso va en CPU: con una NVIDIA sin cuDNN el
proceso se cerraría sin avisar). El modelo se guarda en `~/.cache/huggingface` (Windows: `C:\Users\<tú>\.cache\huggingface`). Si tu usuario de
Windows tiene acentos o ñ y Whisper no abre el modelo: `setx HF_HOME C:\hf` y abre una terminal nueva.

## 4 · Clave de ElevenLabs
Copia `env.ejemplo` como `.env` dentro de la carpeta de la skill (Mac/Git Bash: `cp env.ejemplo .env`) y pega tu clave después del `=`
con TextEdit o el Bloc de notas. Nunca la pegues en el chat.

## 5 · Prueba (sin voz, no gasta nada)
```bash
cp -R ejemplos/canal-de-panama ~/prueba-documental-animado
"$PY" motor/variantes/documental/motor.py ~/prueba-documental-animado prueba 1 4 8      # → ~/prueba-documental-animado/revision/prueba.jpg
```

## Dónde guardar tus proyectos
En una carpeta corta de tu disco: `~/reels` (Mac) o `C:\Users\<tú>\reels` (Windows). En Windows, **fuera de OneDrive** (el Escritorio y
Documentos suelen estar dentro): OneDrive bloquea archivos mientras los sube y ffmpeg falla con «Permission denied». Lo mismo si el video
final está abierto en un reproductor al volver a renderizar: ciérralo.

## Estado de Windows
Revisado para Windows 10/11 el 16 nov 2026 (núcleo y código propio de este kit): textos y JSON siempre en UTF-8, salida en UTF-8, rutas con
acentos o apóstrofo, fuentes e imágenes leídas por Python, servidor local con tipos de archivo fijos, tope de RAM del render y Whisper en CPU.
Probado en Mac (mismos cuadros que antes). **En una PC con Windows todavía no se ha corrido de punta a punta:** si algo falla, Claude debe
leer el error y arreglarlo.
