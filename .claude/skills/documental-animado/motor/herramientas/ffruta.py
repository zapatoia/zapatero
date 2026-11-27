"""ffmpeg sin rutas fijas: variable FFMPEG, el del sistema o el de imageio-ffmpeg.

Windows: también deja la salida en UTF-8 y trae leer_texto() (lo usan las demás herramientas). En Mac no cambia nada."""
import os, shutil, sys
from pathlib import Path


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


def ffmpeg():
    if os.environ.get("FFMPEG"): return os.path.expanduser(os.environ["FFMPEG"].strip().strip('"'))   # «Copiar como ruta» de Windows trae comillas
    for n in ("ffmpeg", "ffmpeg.exe"):
        p = shutil.which(n)
        if p: return p
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()
