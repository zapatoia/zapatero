"""Clase base de un motor de estilo y su línea de comandos. Ver LEEME.md.

  python motor.py <proyecto> prueba 0.5 3.2 …    → revision/prueba.jpg (cuadros sueltos en hilera)
  …                                     secuencia 7.9 [12]            → revision/seq-7.9.jpg (cuadros seguidos)
  …                                     render [--procesos 4]         → exports/<proyecto>.mp4 + -hoja.jpg, copia a exports/Reels animados/ y QA
  …                                     audio                         → solo remezcla sobre el mudo ya hecho
  …                                     qa                            → solo QA del video final
  …                                     eventos                       → lista de SFX
"""
import json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

import numpy as np

from .tiempo import W, H, FPS, f_de_t, LineaTiempo
from .lienzo import Lienzo
from . import audio as A, render as R, qa as Q

from .rutas import MOTOR as MV, FF, salida_dir, leer_texto
EXPORTS = None   # el video final queda en <proyecto>/final (o en NUCLEO_EXPORTS)


class Estilo:
    NOMBRE = "estilo"
    COLA = .45                # s tras la última palabra (regla: cierre ≤ 0.6)
    DUR_S = None              # solo sin voz: duración total
    ZONAS = {}                # kwargs de qa.zona_segura
    LOOP = False              # True: el QA exige que el último cuadro ≈ el primero

    def __init__(self, proyecto):
        self.proy = Path(proyecto).resolve()
        self.guion = json.loads(leer_texto(self.proy / "guion.json"))      # UTF-8 siempre (en Windows read_text() usa cp1252: «canción» saldría «canciÃ³n»)
        pal = self.proy / "palabras.json"
        self.sintetico = not pal.exists() and bool(self.guion.get("lineas"))
        self.palabras = json.loads(leer_texto(pal)) if pal.exists() else (palabras_sinteticas(self.guion) if self.sintetico else [])
        self.tl = LineaTiempo(self.palabras, alias=self.guion.get("alias"))
        fin = self.palabras[-1]["e"] + self.COLA if self.palabras else (self.DUR_S or 10.0)
        self.fin_s = fin; self.nf = f_de_t(fin)
        self.ev = []          # eventos de SFX: {"f","sfx","vol"}
        self.L = Lienzo()
        self.preparar()

    # ---- lo que escribe cada estilo
    def preparar(self): pass
    def dibujar(self, L, f): raise NotImplementedError      # L.canvas / L.arr. Función pura de f.
    def post(self, arr, f): return arr                       # post numpy opcional
    def base_musical(self): return None                      # (n,2) float para estilos sin voz (RelojMusical.sintetizar)

    def sfx(self, f, nombre, vol=1.0): self.ev.append(dict(f=int(f), sfx=nombre, vol=vol))

    # ---- núcleo
    def cuadro(self, f):
        self.dibujar(self.L, f)
        return self.post(self.L.arr, f)

    def mezcla(self, wav):
        voz = self.proy / "voz.wav"
        return A.mezclar(wav, self.fin_s, voz=voz if voz.exists() else None, palabras=self.palabras or None, eventos=self.ev,
                         musica=self.guion.get("musica"), base=self.base_musical())


def palabras_sinteticas(guion, ritmo=1.0):
    """Tiempos de palabra INVENTADOS (sin voz) para ver la animación antes de pagar la voz y para las demos sin sonido.
    ~0.12 s + 0.055 s por letra, pausa tras coma (0.18 s) y tras fin de línea (0.30 s). Al llegar la voz real, palabras.json manda."""
    out = []; t = 0.0
    for n, l in enumerate(guion["lineas"], 1):
        ws = l["texto"].split()
        for w in ws:
            d = (.12 + .055 * len(w)) * ritmo; out.append(dict(w=w, s=round(t, 3), e=round(t + d * .92, 3), linea=n)); t += d
            if w[-1] in ",:;": t += .18
        t += .30
    return out


def tmp_dir(proy):
    base = os.environ.get("NUCLEO_TMP")
    d = Path(base.strip().strip('"')).expanduser() / proy.name if base else proy / ".render"
    d.mkdir(parents=True, exist_ok=True); return d


def guardar_jpg(arr, ruta, q=92):
    """cv2.imwrite no abre rutas con acentos en Windows («C:\\Users\\José\\…»): se codifica en memoria y Python escribe el archivo. Mismos bytes."""
    import cv2; ok, buf = cv2.imencode(Path(ruta).suffix or ".jpg", arr[..., [2, 1, 0]], [cv2.IMWRITE_JPEG_QUALITY, q])
    if ok: buf.tofile(str(ruta))


def hilera(estilo, fs, ruta, esc=.5, cols=None):
    import cv2
    ims = [cv2.resize(estilo.cuadro(f)[..., :3].copy(), None, fx=esc, fy=esc, interpolation=cv2.INTER_AREA) for f in fs]
    cols = cols or len(ims); filas = [np.hstack(ims[i:i + cols] + [np.zeros_like(ims[0])] * (cols - len(ims[i:i + cols]))) for i in range(0, len(ims), cols)]
    guardar_jpg(np.vstack(filas), ruta)


def principal(Clase, motor_py):
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(1)
    proy, cmd = a[0], a[1]; e = Clase(proy); rev = e.proy / "revision"; rev.mkdir(exist_ok=True)
    if cmd == "_trozo":
        R.render_trozo(e, int(a[2]), int(a[3]), a[4]); return
    if cmd == "prueba":
        hilera(e, [f_de_t(float(x)) for x in a[2:]], rev / "prueba.jpg", .5, 6); print(rev / "prueba.jpg"); return
    if cmd == "secuencia":
        t = float(a[2]); n = int(a[3]) if len(a) > 3 else 12; f = f_de_t(t)
        r = rev / f"seq-{t}.jpg"; hilera(e, range(f, f + n), r, .25, 12); print(r); return
    if cmd == "demo":
        # demo sin sonido para la tarjeta: cuadros de t0 a t1, con subtítulo, y loop con fundido de 0.5 s del final al inicio
        t0, t1 = float(a[2]), float(a[3]); sal = Path(a[4]).resolve() if len(a) > 4 else rev / "demo.mp4"; f0, f1 = f_de_t(t0), f_de_t(t1)
        crudo = rev / "demo-crudo.mp4"; p = R.abrir_ffmpeg(crudo)
        for f in range(f0, f1): p.stdin.write(np.ascontiguousarray(e.cuadro(f)).tobytes())
        p.stdin.close(); p.wait(); T = (f1 - f0) / FPS; X = .5
        fc = f"[0]split[a][b];[b]trim=0:{X},setpts=PTS-STARTPTS[ini];[a]trim={X},setpts=PTS-STARTPTS[resto];[resto][ini]xfade=transition=fade:duration={X}:offset={T - 2 * X:.3f},format=yuv420p[v]"
        subprocess.run([FF, "-v", "error", "-y", "-i", str(crudo), "-filter_complex", fc, "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-movflags", "+faststart", str(sal)], check=True)
        crudo.unlink(missing_ok=True); print(sal); return
    if cmd == "eventos":
        print(json.dumps(e.ev, ensure_ascii=False)); return
    salida = salida_dir(e.proy) / f"{e.proy.name}.mp4"; T = tmp_dir(e.proy); mudo = T / "mudo.mp4"
    if cmd == "render":
        p = int(a[a.index("--procesos") + 1]) if "--procesos" in a else 4; t0 = time.time()
        seg = R.render_paralelo(motor_py, e.proy, e.nf, T, mudo, p); print(f"Video mudo: {e.nf} cuadros en {seg:.1f} s ({e.nf / seg:.1f} c/s)")
    if cmd in ("render", "audio"):
        w = T / "mezcla.wav"; info = e.mezcla(w); lu, tp = A.montar(mudo, w, salida)
        info.update(lufs=lu, dbtp=tp); (e.proy / "audio-info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Master: {lu} LUFS, {tp} dBTP · {info.get('efectos')} efectos · música {info.get('musica')} {info.get('musica_menos_voz')}")
        R.hoja_cuadros(salida, salida.with_name(salida.stem + "-hoja.jpg"))
    if cmd in ("render", "audio", "qa"):
        rep = Q.reporte(e, salida); (e.proy / "qa.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        Q.imprimir(rep)
