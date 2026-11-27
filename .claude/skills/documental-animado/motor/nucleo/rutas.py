"""Rutas del kit: nada fijo. Todo sale de dónde está instalada la skill, de perfil.json y de variables de entorno.

  SKILL   = carpeta de la skill (la que tiene SKILL.md y perfil.json)
  MOTOR   = SKILL/motor
  FF      = ffmpeg: variable FFMPEG, el del sistema (PATH) o el que trae el paquete imageio-ffmpeg
  perfil  = SKILL/perfil.json (lo crea Claude la primera vez; ver SKILL.md § 0)
  clave   = ELEVENLABS_API_KEY de una variable de entorno o de un archivo .env (SKILL/.env o la carpeta del proyecto). Jamás se imprime.

Windows: todo archivo de texto se lee y escribe en UTF-8 (allá Python usa cp1252 si no se le dice) y la salida pasa a UTF-8.
"""
import json, os, shutil, sys
from pathlib import Path

MOTOR = Path(__file__).resolve().parents[1]
SKILL = MOTOR.parent
HERRAMIENTAS = MOTOR / "herramientas"


def consola_utf8():
    """Windows: con la salida redirigida (Claude Code la lee por una tubería) Python escribe en cp1252 y un «✓», «→» o «−» truena con
    UnicodeEncodeError. Se pasa a UTF-8. En Mac la salida ya es UTF-8: no cambia nada."""
    for s in (sys.stdout, sys.stderr):
        enc = (getattr(s, "encoding", None) or "").lower().replace("-", "").replace("_", "")
        if enc and enc != "utf8" and hasattr(s, "reconfigure"):
            try: s.reconfigure(encoding="utf-8", errors="replace")
            except Exception: pass


consola_utf8()


def leer_texto(p):
    """Texto de un archivo sin depender de la codificación del sistema: UTF-8 (con o sin BOM), UTF-16 (lo que deja `>` en PowerShell 5)
    o cp1252 (un archivo viejo que escribió Windows antes de fijar UTF-8). Saltos de línea como read_text(). En Mac: igual que read_text()."""
    b = Path(p).read_bytes()
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"): t = b.decode("utf-16")
    else:
        try: t = b.decode("utf-8-sig")
        except UnicodeDecodeError: t = b.decode("cp1252", errors="replace")
    return t.replace("\r\n", "\n").replace("\r", "\n")


def _ffmpeg():
    if os.environ.get("FFMPEG"): return os.path.expanduser(os.environ["FFMPEG"].strip().strip('"'))   # «Copiar como ruta» de Windows trae comillas
    for n in ("ffmpeg", "ffmpeg.exe"):
        p = shutil.which(n)
        if p: return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise SystemExit("No encuentro ffmpeg. Instálalo (ver INSTALAR.md) o `pip install imageio-ffmpeg`.")


FF = _ffmpeg()


def perfil():
    p = SKILL / "perfil.json"
    return json.loads(leer_texto(p)) if p.exists() else {}


def clave_eleven(proy=None):
    """Lee la clave sin imprimirla. Orden: variable de entorno, <proyecto>/.env, <skill>/.env."""
    if os.environ.get("ELEVENLABS_API_KEY"): return os.environ["ELEVENLABS_API_KEY"].strip()
    for d in ([Path(proy)] if proy else []) + [Path.cwd(), SKILL]:
        f = Path(d) / ".env"
        if f.exists():
            for ln in leer_texto(f).splitlines():
                if ln.strip().startswith("ELEVENLABS_API_KEY="):
                    return ln.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("Falta la clave de ElevenLabs: crea un archivo .env con ELEVENLABS_API_KEY=... junto a la skill (ver SKILL.md § 0). No la pegues en el chat.")


def salida_dir(proy):
    """Dónde queda el video terminado: variable NUCLEO_EXPORTS o <proyecto>/final."""
    d = Path(os.environ["NUCLEO_EXPORTS"].strip().strip('"')).expanduser() if os.environ.get("NUCLEO_EXPORTS") else Path(proy) / "final"
    d.mkdir(parents=True, exist_ok=True); return d
