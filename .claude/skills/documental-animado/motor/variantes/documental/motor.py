#!/usr/bin/env python
"""Variante DOCUMENTAL: video HORIZONTAL 1920×1080 100 % animado (mapas, fechas, cifras, listas, fotos 2.5D) con voz palabra por palabra.

El dibujo lo hace el motor HTML/JS de esta carpeta (motor.html + lib/ + vendor/) dentro de Chromium sin ventana (Playwright).
Este archivo levanta un servidor local en 127.0.0.1, abre el motor, pide cada cuadro y lo manda a ffmpeg. El audio, el master
(−14 LUFS / ≤ −1 dBTP) y el QA son los del núcleo del kit.

  python motor.py <proyecto> prueba 0.5 3.2 …            → revision/prueba.jpg (cuadros sueltos, 3 por fila)
  python motor.py <proyecto> secuencia 7.9 [12]          → revision/seq-7.9.jpg (cuadros seguidos)
  python motor.py <proyecto> escenas                     → lista de escenas con su segundo de entrada
  python motor.py <proyecto> render [--procesos 2] [--fps 60]  → final/<proyecto>.mp4 + -hoja.jpg + qa.json
  python motor.py <proyecto> audio | qa                  → solo remezcla | solo QA
  python motor.py <proyecto> demo 0 8 [salida.mp4]       → clip mudo con loop (para mostrar el estilo)

<proyecto>/guion.json: {"titulo", "tema": "editorial"|"club", "tope_caracteres", "lineas": [{"texto", "tts", "escena": {...}, "key": "palabra"}]}
  Cada línea es UNA frase del motor. Si trae "escena", ahí empieza una escena nueva; si no, sigue la anterior.
  Sin palabras.json (antes de pagar la voz) el motor usa tiempos de palabra inventados.
"""
import base64, functools, json, math, os, subprocess, sys, threading, time
import http.server, socketserver, urllib.parse
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def _motor_dir():
    """Dónde está motor/ de la skill: variable KIT_MOTOR, la carpeta de la skill (si este archivo vive ahí) o la skill instalada."""
    for d in (os.environ.get("KIT_MOTOR"), AQUI.parents[1] if len(AQUI.parents) > 1 else None, Path.home() / ".claude" / "skills" / "documental-animado" / "motor"):
        if d and (Path(d) / "nucleo" / "__init__.py").exists(): return Path(d)
    raise SystemExit("No encuentro motor/ de la skill: define KIT_MOTOR con su ruta (<skill>/motor).")


MOTOR = _motor_dir(); sys.path.insert(0, str(MOTOR))
from nucleo import audio as A, qa as Q, render as R       # noqa: E402
from nucleo.estilo import palabras_sinteticas, guardar_jpg  # noqa: E402
from nucleo.rutas import FF, perfil, salida_dir, leer_texto # noqa: E402

W, H = 1920, 1080
FPS = int(os.environ.get("DOC_FPS", "60"))
COLA = .40                                   # s tras la última palabra (regla: cierre ≤ 0.6 s; el estilo pide ≤ 0.3–0.4)
CALIDAD = .95                                # JPEG por cuadro (del navegador a ffmpeg)
NUC = MOTOR / "nucleo"
CAMPOS_FRASE = ("key", "keys", "cap", "ctx", "ctxMax", "labels")


class Proyecto:
    def __init__(self, ruta):
        self.proy = Path(ruta).resolve()
        self.guion = json.loads(leer_texto(self.proy / "guion.json"))
        pal = self.proy / "palabras.json"
        self.sintetico = not pal.exists()
        self.palabras = json.loads(leer_texto(pal)) if pal.exists() else palabras_sinteticas(self.guion)
        self.fin_s = self.palabras[-1]["e"] + COLA
        self.nf = int(math.ceil(self.fin_s * FPS))

    def json_motor(self):
        g = self.guion; p = perfil(); bloques = []
        for ln in g["lineas"]:
            if ln.get("bloque") or not bloques: bloques.append({"title": ln.get("bloque") or g.get("titulo", "Video"), "phrases": []})
            ph = {"text": ln["texto"]}
            if ln.get("escena"): ph["scene"] = ln["escena"]
            for k in CAMPOS_FRASE:
                if k in ln: ph[k] = ln[k]
            bloques[-1]["phrases"].append(ph)
        logo = ""
        if p.get("logo"):                          # logo PROPIO del usuario (opcional): se copia al proyecto y sale chico arriba a la derecha
            src = Path(p["logo"]).expanduser()
            if src.exists():
                dst = self.proy / "fotos" / ("logo" + src.suffix.lower()); dst.parent.mkdir(exist_ok=True)
                if not dst.exists(): dst.write_bytes(src.read_bytes())
                logo = "fotos/" + dst.name
        tema = dict(g.get("tema_opciones", {})); tema.update(name=g.get("tema", "editorial"), logo=logo)
        return {"title": g.get("titulo", ""), "engine": "v2", "theme": tema, "words": [dict(w=w["w"], s=w["s"], e=w["e"]) for w in self.palabras], "blocks": bloques}

    def faltantes(self):
        """Fotos que pide el guion y no están en el proyecto."""
        malos = []
        def ver(S):
            if not isinstance(S, dict): return
            for k in ("src", "bg", "photo", "backdrop"):
                if isinstance(S.get(k), str) and not S[k].startswith("http") and not (self.proy / S[k]).exists(): malos.append(S[k])
            for it in S.get("items", []) or []:
                if isinstance(it, dict) and isinstance(it.get("src"), str) and not (self.proy / it["src"]).exists(): malos.append(it["src"])
            for f in S.get("photos", []) or []:
                if isinstance(f, str) and not (self.proy / f).exists(): malos.append(f)
            for sh in S.get("shots", []) or []: ver(sh); ver(sh.get("scene") if isinstance(sh, dict) else None)
        for ln in self.guion["lineas"]: ver(ln.get("escena"))
        return malos


# ------------------------------------------------------------------ servidor local (solo 127.0.0.1)
class _H(http.server.SimpleHTTPRequestHandler):
    raices = []; pj = b"{}"
    # Tipos fijos: en Windows `mimetypes` lee el registro y a veces da .js como text/plain o .json raro según lo que haya instalado.
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".html": "text/html", ".js": "text/javascript",
                      ".json": "application/json", ".css": "text/css", ".svg": "image/svg+xml", ".ttf": "font/ttf",
                      ".woff2": "font/woff2", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/__proyecto.json":
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(self.pj))); self.end_headers(); self.wfile.write(self.pj); return
        return super().do_GET()

    def translate_path(self, path):
        rel = urllib.parse.unquote(urllib.parse.urlparse(path).path).lstrip("/")
        if ".." in Path(rel).parts or Path(rel).is_absolute() or Path(rel).drive: return str(self.raices[0] / "__no__")   # Windows: «C:/…» o «\\…»
        for r in self.raices:
            f = r / rel
            if f.exists(): return str(f)
        return str(self.raices[0] / rel)

    def log_message(self, *a): pass


def servidor(P):
    _H.raices = [P.proy, AQUI, NUC]; _H.pj = json.dumps(P.json_motor(), ensure_ascii=False).encode("utf-8")
    s = socketserver.ThreadingTCPServer(("127.0.0.1", 0), _H); s.daemon_threads = True
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, s.server_address[1]


JS_GRAB = """async ([t, q]) => { const c = window.__cv || (window.__cv = mkCanvas(1920, 1080)), x = c.getContext('2d');
  await preRender(t); render(x, t); const b = await c.convertToBlob({ type: 'image/jpeg', quality: q });
  return await new Promise(r => { const fr = new FileReader(); fr.onload = () => r(fr.result.split(',')[1]); fr.readAsDataURL(b); }); }"""


class Navegador:
    """Chromium sin ventana con el motor cargado y el proyecto listo."""
    def __init__(self, P):
        from playwright.sync_api import sync_playwright
        self.P = P; self.srv, port = servidor(P); self.pw = sync_playwright().start()
        self.b = self.pw.chromium.launch(headless=True, args=["--disable-background-timer-throttling", "--disable-renderer-backgrounding", "--force-color-profile=srgb"])
        self.page = self.b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
        errores = []; self.page.on("pageerror", lambda e: errores.append(str(e)))
        self.page.goto(f"http://127.0.0.1:{port}/motor.html?proyecto=__proyecto.json", wait_until="load")
        self.page.wait_for_function("window.__ready === true", timeout=120000)
        self.page.evaluate(f"() => {{ voiceEnd = () => {P.fin_s - COLA:.3f}; }}")       # la voz manda: el video dura lo que dura la voz
        self.page.evaluate("async () => { await ensureAssets(); }")
        self.page.wait_for_timeout(300)
        if errores: print("Errores del motor:", errores[:3])
        self.grab(0.0, .5)                                                               # primer cuadro de calentamiento (carga imágenes)

    def grab(self, t, q=CALIDAD): return base64.b64decode(self.page.evaluate(JS_GRAB, [float(t), q]))

    def cuadro(self, t):
        import cv2, numpy as np
        return cv2.imdecode(np.frombuffer(self.grab(t), np.uint8), cv2.IMREAD_COLOR)[..., ::-1]

    def escenas(self):
        return self.page.evaluate("() => P.map((p, i) => p.scene ? { i, t: +starts[i].toFixed(2), tipo: p.scene.type, texto: p.text, transicion: V2.transOf(i).ty, superficie: V2.state.surf[i] } : null).filter(Boolean)")

    def sfx(self):
        return self.page.evaluate("() => V2.sfxEvents()")

    def cerrar(self):
        try: self.b.close(); self.pw.stop()
        finally: self.srv.shutdown()


def ffmpeg_jpg(salida, fps):
    return subprocess.Popen([FF, "-v", "error", "-y", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(fps), "-i", "-",
                             "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
                             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-g", str(2 * fps), "-an", str(salida)], stdin=subprocess.PIPE)


def hilera(N, ts, ruta, esc=.5, cols=3):
    import cv2, numpy as np
    ims = [cv2.resize(N.cuadro(t), None, fx=esc, fy=esc, interpolation=cv2.INTER_AREA) for t in ts]
    filas = [np.hstack(ims[i:i + cols] + [np.zeros_like(ims[0])] * (cols - len(ims[i:i + cols]))) for i in range(0, len(ims), cols)]
    guardar_jpg(np.vstack(filas), ruta)


JS_TEXTOS = """(ts) => { const pr = [CanvasRenderingContext2D.prototype, OffscreenCanvasRenderingContext2D.prototype], orig = pr.map(p => p.fillText), out = []; let cur = null;
  pr.forEach((p, i) => p.fillText = function (txt, x0, y0, mw) { const t = String(txt);
    if (this.globalAlpha > .3 && t.trim() && this.canvas.width >= 1900) { const m = this.measureText(t), tr = this.getTransform();
      const q = [[x0 - m.actualBoundingBoxLeft, y0 - m.actualBoundingBoxAscent], [x0 + m.actualBoundingBoxRight, y0 + m.actualBoundingBoxDescent]].map(([a, c]) => [tr.a * a + tr.c * c + tr.e, tr.b * a + tr.d * c + tr.f]);
      cur.push({ t, x1: Math.min(q[0][0], q[1][0]), y1: Math.min(q[0][1], q[1][1]), x2: Math.max(q[0][0], q[1][0]), y2: Math.max(q[0][1], q[1][1]) }); }
    return orig[i].call(this, txt, x0, y0, mw); });
  const c = mkCanvas(1920, 1080), x = c.getContext('2d');
  try { for (const t of ts) { cur = []; render(x, t); out.push([t, cur]); } } finally { pr.forEach((p, i) => p.fillText = orig[i]); }
  return out; }"""


def zona_segura_h(N, P, arriba=50, abajo=1020, lado=60, transitorio_s=.3):
    """Zona segura HORIZONTAL (YouTube), medida en el propio motor: cada 0.25 s se registra la caja de cada texto visible (alfa > 0.3)
    y ninguno puede quedar a menos de 60 px de los lados, 50 px de arriba ni abajo de y=1020 (ahí va la barra de YouTube) por más de
    `transitorio_s` seguidos. Los textos que pasan de largo (fuera del cuadro) no cuentan. Los fondos a sangre sí pueden tocar los bordes."""
    ts = [k / 4 for k in range(int(P.fin_s * 4) + 1)]; res = N.page.evaluate(JS_TEXTOS, ts); malos = []; run = mx = 0
    for t, cajas in res:
        b = [c for c in cajas if c["x2"] > 0 and c["x1"] < W and c["y2"] > 0 and c["y1"] < H and (c["x1"] < lado or c["x2"] > W - lado or c["y1"] < arriba or c["y2"] > abajo)]
        run = run + 1 if b else 0; mx = max(mx, run)
        if b: malos.append(dict(t=t, textos=[(c["t"][:30], round(c["x1"]), round(c["y1"]), round(c["x2"]), round(c["y2"])) for c in b[:3]]))
    return dict(muestras=len(ts), con_texto_en_borde=len(malos), tramo_s=mx * .25, ejemplos=malos[:5], ok=mx * .25 <= transitorio_s,
                nota="horizontal 1920×1080: textos a ≥ 60 px de los lados, ≥ 50 px de arriba y arriba de y=1020")


def reporte(P, video):
    N = Navegador(P)
    try: zona = zona_segura_h(N, P); avisos = N.page.evaluate("() => qaScenes()")
    finally: N.cerrar()
    graves = [x for x in avisos if "desconocido" in x or "nunca aparecería" in x or "no se encontró" in x]
    rep = dict(video=str(video), duracion_s=round(Q.duracion(video), 2), nivel=Q.nivel(video), zona_segura=zona,
               escenas=dict(avisos=avisos, ok=not graves), contenido=Q.contenido_prohibido(P.guion))
    voz = P.proy / "voz.wav"
    if voz.exists() and not P.sintetico:
        rep["voz_cuadro_0"] = Q.voz_en_cuadro_0(voz, video, P.palabras)
        rep["pausas"] = Q.pausas_y_cierre(voz, P.palabras, P.fin_s)
        rep["palabras_completas"] = Q.palabras_completas(voz, P.palabras)
        rep["literal_final"] = Q.literal_final(P.proy, voz)
        rep["transitorios"] = Q.transitorios_fuera_de_palabras(voz, P.palabras)
    else:
        rep["voz"] = dict(ok=False, nota="sin voz.wav/palabras.json: es una prueba con tiempos inventados, no un video terminado")
    for k, razon in (P.guion.get("qa_aceptadas") or {}).items():
        if isinstance(rep.get(k), dict) and not rep[k].get("ok", True): rep[k]["aceptada"] = razon
    rep["ok"] = all(v.get("ok", True) or v.get("aceptada") for v in rep.values() if isinstance(v, dict))
    return rep


def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(1)
    global FPS
    if "--fps" in a: FPS = int(a[a.index("--fps") + 1]); os.environ["DOC_FPS"] = str(FPS)
    P = Proyecto(a[0]); cmd = a[1]; rev = P.proy / "revision"; rev.mkdir(exist_ok=True)
    falta = P.faltantes()
    if falta and cmd not in ("qa", "audio"): print("OJO, faltan fotos en el proyecto (la escena saldrá vacía):", falta)
    if cmd == "_trozo":
        f0, f1, out = int(a[2]), int(a[3]), a[4]; N = Navegador(P); p = ffmpeg_jpg(out, FPS)
        try:
            for f in range(f0, f1): p.stdin.write(N.grab(f / FPS))
        finally:
            p.stdin.close(); N.cerrar()
        if p.wait(): raise SystemExit("ffmpeg falló en el trozo")
        return
    if cmd in ("prueba", "secuencia", "escenas", "demo"):
        N = Navegador(P)
        try:
            if cmd == "prueba":
                hilera(N, [float(x) for x in a[2:] if not x.startswith("--")], rev / "prueba.jpg"); print(rev / "prueba.jpg")
            elif cmd == "secuencia":
                t = float(a[2]); n = int(a[3]) if len(a) > 3 and not a[3].startswith("--") else 12; r = rev / f"seq-{t}.jpg"
                hilera(N, [t + k / FPS for k in range(n)], r, .25, 6); print(r)
            elif cmd == "escenas":
                for e in N.escenas(): print(f"{e['t']:6.2f} s  {e['tipo']:<9} {e['transicion']:<6} {e['superficie'] or '':<6} «{e['texto']}»")
            else:
                t0, t1 = float(a[2]), float(a[3]); sal = Path(a[4]).resolve() if len(a) > 4 and not a[4].startswith("--") else rev / "demo.mp4"
                fd = 30; crudo = rev / "demo-crudo.mp4"; p = ffmpeg_jpg(crudo, fd)
                for k in range(int(round((t1 - t0) * fd))): p.stdin.write(N.grab(t0 + k / fd))
                p.stdin.close(); p.wait(); T = t1 - t0; X = .5
                fc = f"[0]split[a][b];[b]trim=0:{X},setpts=PTS-STARTPTS[ini];[a]trim={X},setpts=PTS-STARTPTS[resto];[resto][ini]xfade=transition=fade:duration={X}:offset={T - 2 * X:.3f},format=yuv420p[v]"
                subprocess.run([FF, "-v", "error", "-y", "-i", str(crudo), "-filter_complex", fc, "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-movflags", "+faststart", str(sal)], check=True)
                crudo.unlink(missing_ok=True); print(sal)
        finally:
            N.cerrar()
        return
    salida = salida_dir(P.proy) / f"{P.proy.name}.mp4"; T = P.proy / ".render"; T.mkdir(exist_ok=True); mudo = T / "mudo.mp4"
    if P.sintetico and cmd in ("render", "audio"): print("OJO: no hay palabras.json; el render usa tiempos inventados y sale sin voz (sirve solo de prueba).")
    if cmd == "render":
        procesos = int(a[a.index("--procesos") + 1]) if "--procesos" in a else 2
        seg = R.render_paralelo(Path(__file__).resolve(), P.proy, P.nf, T, mudo, procesos); print(f"Video mudo: {P.nf} cuadros a {FPS} fps en {seg:.1f} s ({P.nf / seg:.1f} c/s)")
        N = Navegador(P)
        try: ev = N.sfx()
        finally: N.cerrar()
        (T / "sfx.json").write_text(json.dumps(ev), encoding="utf-8")
    if cmd in ("render", "audio") and P.sintetico:          # prueba sin voz: pista muda (no se masteriza silencio ni se suben los efectos)
        subprocess.run([FF, "-v", "error", "-y", "-i", str(mudo), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(salida)], check=True)
        R.hoja_cuadros(salida, salida.with_name(salida.stem + "-hoja.jpg"), cada=1.0, cols=6, ancho=320)
    elif cmd in ("render", "audio"):
        ev = json.loads(leer_texto(T / "sfx.json")) if (T / "sfx.json").exists() else []
        eventos = [dict(f=int(round(e["t"] * 30)), sfx="whoosh", vol=.45 if e["s"] == "whoosh_bajo" else .6) for e in ev] if P.guion.get("sfx", True) else []
        w = T / "mezcla.wav"; voz = P.proy / "voz.wav"
        info = A.mezclar(w, P.fin_s, voz=voz if voz.exists() and not P.sintetico else None, palabras=P.palabras if not P.sintetico else None, eventos=eventos, musica=P.guion.get("musica"))
        lu, tp = A.montar(mudo, w, salida); info.update(lufs=lu, dbtp=tp); (P.proy / "audio-info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Master: {lu} LUFS, {tp} dBTP · {info.get('efectos')} efectos · música {info.get('musica')}")
        R.hoja_cuadros(salida, salida.with_name(salida.stem + "-hoja.jpg"), cada=1.0, cols=6, ancho=320)
    if cmd in ("render", "audio", "qa"):
        rep = reporte(P, salida); (P.proy / "qa.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8"); Q.imprimir(rep)


if __name__ == "__main__":
    main()
