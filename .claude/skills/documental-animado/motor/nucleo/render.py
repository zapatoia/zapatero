"""Render en paralelo por trozos (≤ 4 procesos, sin pasar de 80 % de RAM) + unión + hoja de cuadros."""
import json, os, re, subprocess, sys, time
from pathlib import Path

from .tiempo import W, H, FPS

from .rutas import FF
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
       "-vf", "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p",
       "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-g", "60", "-bf", "2", "-an"]


def ram_usada():
    """Fracción de RAM en uso. macOS: activa + wired + comprimida. Windows: lo que reporta GlobalMemoryStatusEx (sin vm_stat ni sysctl)."""
    if sys.platform == "win32":
        try:
            import ctypes
            class _Mem(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [(k, ctypes.c_ulonglong) for k in (
                    "ullTotalPhys", "ullAvailPhys", "ullTotalPageFile", "ullAvailPageFile", "ullTotalVirtual", "ullAvailVirtual", "ullAvailExtendedVirtual")]
            m = _Mem(); m.dwLength = ctypes.sizeof(_Mem)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)) and m.ullTotalPhys: return 1 - m.ullAvailPhys / m.ullTotalPhys
        except Exception:
            pass
        return 0.0
    try:
        s = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout; pag = int(re.search(r"page size of (\d+)", s).group(1))
        g = lambda k: int(re.search(rf"{k}:\s+(\d+)", s).group(1)) * pag
        tot = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout)
        return (g("Pages active") + g("Pages wired down") + g("Pages occupied by compressor")) / tot
    except Exception:
        return 0.0


def abrir_ffmpeg(salida):
    return subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *ENC, str(salida)], stdin=subprocess.PIPE)


def render_trozo(estilo, a, b, salida):
    import cv2; cv2.setNumThreads(1)
    p = abrir_ffmpeg(salida)
    for f in range(a, b): p.stdin.write(estilo.cuadro(f).data)
    p.stdin.close()
    if p.wait(): raise RuntimeError("ffmpeg falló en el trozo")


def render_paralelo(motor_py, proyecto, nf, tmp, salida, procesos=4, tope_ram=.80):
    """Lanza `python motor.py <proyecto> _trozo a b salida` por trozo. Más trozos que procesos: arranca conforme se liberan."""
    procesos = min(procesos, 4); tmp = Path(tmp); tmp.mkdir(parents=True, exist_ok=True)
    n = max(procesos * 2, 1); tam = max(30, nf // n + 1); rangos = [(i, min(i + tam, nf)) for i in range(0, nf, tam)]; vivos = []; ok = []; t0 = time.time(); falla = None
    for k, (a, b) in enumerate(rangos):
        while len(vivos) >= procesos or (vivos and ram_usada() > tope_ram):
            for v in list(vivos):
                if v[0].poll() is not None:
                    vivos.remove(v); falla = falla or (v[0].returncode and v[1])
            time.sleep(.1)
        out = tmp / f"t{k:03d}.mp4"; ok.append(out)
        vivos.append((subprocess.Popen([sys.executable, str(motor_py), str(proyecto), "_trozo", str(a), str(b), str(out)]), out))
    for p, o in vivos:
        if p.wait(): falla = falla or o
    if falla: raise RuntimeError(f"Trozo fallido: {falla}")
    # UTF-8 (ffmpeg lee la lista así; en Windows Python escribiría cp1252 y una carpeta «José» no abre). Una ' en la ruta se escapa como pide ffmpeg.
    lista = tmp / "lista.txt"; lista.write_text("".join("file '" + str(x).replace("'", "'\\''") + "'\n" for x in ok), encoding="utf-8")
    subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", "-movflags", "+faststart", str(salida)], check=True)
    for x in ok: x.unlink(missing_ok=True)
    return time.time() - t0


def hoja_cuadros(video, salida, cada=1.0, cols=8, ancho=270):
    """Hoja de contacto del video final."""
    r = subprocess.run([FF, "-hide_banner", "-i", str(video)], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r).groups(); dur = int(h) * 3600 + int(m) * 60 + float(s)
    filas = int(dur / cada + .999) // cols + 1
    subprocess.run([FF, "-v", "error", "-y", "-i", str(video), "-vf", f"fps=1/{cada},scale={ancho}:-1,tile={cols}x{filas}:padding=4:color=0x202020", "-frames:v", "1", "-q:v", "3", str(salida)], check=True)
    return salida
