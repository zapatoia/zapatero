"""QA automático del video final. `reporte(estilo, video)` junta todo; cada función se puede usar sola.

zona_segura · voz_en_cuadro_0 · pausas_y_cierre · palabras_completas · literal_final · transitorios_fuera_de_palabras · contenido_prohibido · nivel · loop
"""
import hashlib, json, os, re, subprocess
from pathlib import Path

import numpy as np

from .tiempo import W, H, FPS

from .rutas import FF, leer_texto
SR = 48000


def cuadros(video, cada=.25, esc=2):
    """Cuadros en gris muestreados (ancho W/esc) como arreglo (n, h, w)."""
    w, h = W // esc, H // esc
    raw = subprocess.run([FF, "-v", "error", "-i", str(video), "-vf", f"fps=1/{cada},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w)


def zona_segura(video, arriba=230, abajo=1500, derecha=985, der_y=(1150, 1500), umbral=40, ignorar_arriba=False, ignorar_abajo=False, min_px=30, transitorio_s=.3):
    """Nada importante arriba de y≈230 ni tapado por la interfaz de Instagram (abajo y columna derecha de botones).
    Contenido = píxel que difiere de la mediana temporal más de `umbral`. El sobrepaso de un POP (≤ transitorio_s) no cuenta.
    Devuelve % de muestras con contenido en cada zona y el tramo seguido más largo en segundos."""
    C = cuadros(video); med = np.median(C, 0); d = np.abs(C.astype(np.float32) - med) > umbral; k = 2
    z = {"arriba": d[:, :arriba // k, :], "abajo": d[:, abajo // k:, :], "derecha": d[:, der_y[0] // k:der_y[1] // k, derecha // k:]}
    if ignorar_arriba: z.pop("arriba")
    if ignorar_abajo: z.pop("abajo")
    res = {}; tramo = {}
    for n, m in z.items():
        on = m.reshape(len(m), -1).sum(1) > min_px; res[n] = round(float(on.mean()) * 100, 1); run = mx = 0
        for v in on: run = run + 1 if v else 0; mx = max(mx, run)
        tramo[n] = mx * .25
    return dict(pct_muestras=res, tramo_s=tramo, ok=all(v <= transitorio_s for v in tramo.values()))


def _leer_mono(ruta):
    raw = subprocess.run([FF, "-v", "error", "-i", str(ruta), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def _rms_db(x, ven=240):
    n = len(x) // ven; r = np.sqrt((x[:n * ven].reshape(n, ven) ** 2).mean(1)) + 1e-9; return 20 * np.log10(r)


def voz_en_cuadro_0(voz_wav, video=None, palabras=None):
    """La voz arranca en el cuadro 0: energía ≥ −45 dB rel. al pico dentro de los primeros 33 ms de voz.wav y marca de 1.ª palabra ≤ 1 cuadro."""
    v = _leer_mono(voz_wav); pk = np.abs(v).max() + 1e-9; n = int(SR / FPS); db = 20 * np.log10(np.abs(v[:n]).max() / pk + 1e-9)
    prim = next((i for i, m in enumerate(np.abs(v)) if m > pk * .03), 0) / SR
    r = dict(onset_s=round(prim, 4), pico_cuadro0_db=round(float(db), 1), primera_palabra_s=palabras[0]["s"] if palabras else None)
    if video:
        a = _leer_mono(video); r["video_cuadro0_rms_db"] = round(float(_rms_db(a[:n]).max()), 1)
    r["ok"] = prim <= 1 / FPS and (not palabras or palabras[0]["s"] <= 1 / FPS)
    return r


def _envolvente(x, ven=240, salto=48):
    """RMS en dB: ventana de 5 ms cada 1 ms. Sirve para medir caídas de 15 ms, que rms_db (5 ms sin traslape) no resuelve."""
    n = max((len(x) - ven) // salto, 1); c = np.concatenate([[0.0], np.cumsum(x.astype(np.float64) ** 2)]); i = np.arange(n) * salto
    return 10 * np.log10((c[i + ven] - c[i]) / ven + 1e-12)


def pausas_y_cierre(voz_wav, palabras, fin_s, pausa_max=.8, cola_max=.6, umbral_db=-42, umbral_fin=-50):
    """Mide en la SEÑAL. Pausa: tramo bajo umbral dentro del rango hablado; también el hueco mayor entre marcas (ahí cuenta una respiración, que para la señal no es silencio).
    Cierre: desde el final completo de la última palabra (última energía sobre umbral_fin), no desde la marca de Whisper. Falla si el video acaba antes de que la voz termine."""
    v = _leer_mono(voz_wav); db = _rms_db(v, 240); dt = 240 / SR; pk = db.max(); ini = int(palabras[0]["s"] / dt); fin = int(palabras[-1]["e"] / dt)
    sil = db[ini:fin] < pk + umbral_db; mx = run = 0
    for s in sil:
        run = run + 1 if s else 0; mx = max(mx, run)
    fin_v = (int(np.where(db > pk + umbral_fin)[0][-1]) + 1) * dt; fin_v = max(fin_v, palabras[-1]["e"]); cola = fin_s - fin_v
    hueco = max((b["s"] - a["e"] for a, b in zip(palabras, palabras[1:])), default=0.0)
    return dict(pausa_max_s=round(mx * dt, 3), hueco_entre_marcas_s=round(hueco, 3), fin_voz_s=round(fin_v, 3), cierre_s=round(cola, 3), ok=mx * dt <= pausa_max and 0 <= cola <= cola_max)


def palabras_completas(voz_wav, palabras, caida_db=25, en_ms=15, nivel_db=-40):
    """Regla: ninguna palabra se corta. En cada palabra final de frase (fin de línea o signo . ? ! :) mide la mayor caída de energía en `en_ms`:
    falla si baja más de `caida_db` partiendo de un nivel audible (> nivel_db rel. al pico). La voz termina con una caída natural más lenta; un corte o una toma que acaba con energía, no.
    El archivo se rellena con silencio para que un final brusco también cuente."""
    v = np.concatenate([_leer_mono(voz_wav), np.zeros(int(.1 * SR), np.float32)]); E = _envolvente(v); dt = 48 / SR; pk = E.max(); k = max(int(round(en_ms / 1000 / dt)), 1); det = []; malas = []
    for i, p in enumerate(palabras):
        sig = palabras[i + 1] if i + 1 < len(palabras) else None
        if sig is not None and sig["linea"] == p["linea"] and not re.search(r"[.?!:…]$", p["w"]): continue
        a = int(max(p["e"] - .12, p["s"]) / dt); b = min(int((sig["s"] if sig else p["e"] + .5) / dt), len(E) - k - 1)
        if b <= a: continue
        d = np.where(E[a:b] > pk + nivel_db, E[a:b] - E[a + k:b + k], 0.0); j = int(np.argmax(d)); caida = float(d[j])
        det.append(dict(w=p["w"], t=round((a + j) * dt, 3), caida_db=round(caida, 1), desde_db=round(float(E[a + j] - pk), 1)))
        if caida > caida_db: malas.append(det[-1])
    return dict(n=len(det), peor=max(det, key=lambda x: x["caida_db"]) if det else None, malas=malas, detalle=det, ok=not malas)


def literal_final(proy, voz_wav):
    """La pasada literal contra el guion necesita Whisper: la hace `voz.py <proy> verificar` y deja voz-verificacion.json. Aquí se exige que exista, que sea de ESTE voz.wav y que no tenga fallas."""
    f = Path(proy) / "voz-verificacion.json"
    if not f.exists(): return dict(ok=False, motivo="falta: corre nucleo/voz.py <proyecto> verificar")
    r = json.loads(leer_texto(f))
    if r.get("sha1") != hashlib.sha1(Path(voz_wav).read_bytes()).hexdigest(): return dict(ok=False, motivo="es de otro voz.wav: corre nucleo/voz.py <proyecto> verificar")
    return dict(ok=bool(r.get("ok")), fallas=r.get("fallas", []), motivos=r.get("motivos", []), aceptadas=[(a["oido"], a["guion"], a["razon"]) for a in r.get("aceptadas", [])])


def transitorios_fuera_de_palabras(voz_wav, palabras, margen=.05, salto_db=18, nivel_db=-40):
    """Saltos bruscos de energía (clics) en voz.wav fuera de las palabras: deben ser cero."""
    v = _leer_mono(voz_wav); ven = 96; db = _rms_db(v, ven); dt = ven / SR; fuera = np.ones(len(db), bool)
    for p in palabras: fuera[int(max(p["s"] - margen, 0) / dt):int((p["e"] + margen) / dt)] = False
    d = np.diff(db, prepend=db[0]); pk = db.max(); malos = np.where(fuera & (d > salto_db) & (db > pk + nivel_db))[0]
    return dict(n=int(len(malos)), t=[round(float(i * dt), 3) for i in malos[:10]], ok=len(malos) == 0)


from .rutas import perfil as _perfil
PROHIBIDO = [r"faceless"] + [re.escape(v) for v in _perfil().get("vetos_texto", [])]   # palabras que el usuario nunca quiere en pantalla (perfil.json)


def contenido_prohibido(guion, plan_txt=""):
    t = " ".join(l.get("texto", "") for l in guion.get("lineas", [])) + " " + json.dumps(guion.get("titulos", ""), ensure_ascii=False) + " " + plan_txt
    hal = [p for p in PROHIBIDO if re.search(p, t, re.I)]
    return dict(hallazgos=hal, ok=not hal)


def nivel(video, lufs=-14.0, tol=.5, tp_max=-1.0):
    r = subprocess.run([FF, "-hide_banner", "-i", str(video), "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    lu = float(r.split("I:")[-1].split("LUFS")[0]); tp = float(r.split("Peak:")[-1].split("dBFS")[0])
    return dict(lufs=lu, dbtp=tp, ok=abs(lu - lufs) <= tol and tp <= tp_max)


def loop(video, max_dif=1.0):
    """Diferencia media (0–255) entre primer y último cuadro: requisito de sonificación (0.14 en el viral, 0.02 en la serie C)."""
    C = cuadros(video, 1 / FPS); d = float(np.abs(C[0].astype(np.float32) - C[-1].astype(np.float32)).mean())
    return dict(dif=round(d, 3), ok=d <= max_dif)


def duracion(video):
    r = subprocess.run([FF, "-hide_banner", "-i", str(video)], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r).groups(); return int(h) * 3600 + int(m) * 60 + float(s)


def reporte(e, video):
    rep = dict(video=str(video), duracion_s=round(duracion(video), 2), nivel=nivel(video), zona_segura=zona_segura(video, **e.ZONAS))
    plan = e.proy / "plan.json"
    rep["contenido"] = contenido_prohibido(e.guion, leer_texto(plan) if plan.exists() else "")
    voz = e.proy / "voz.wav"
    if voz.exists() and e.palabras:
        rep["voz_cuadro_0"] = voz_en_cuadro_0(voz, video, e.palabras)
        rep["pausas"] = pausas_y_cierre(voz, e.palabras, e.fin_s)
        rep["palabras_completas"] = palabras_completas(voz, e.palabras)
        rep["literal_final"] = literal_final(e.proy, voz)
        rep["transitorios"] = transitorios_fuera_de_palabras(voz, e.palabras)
    if e.LOOP: rep["loop"] = loop(video)
    # Falsos positivos MEDIDOS: guion.json → "qa_aceptadas": {"palabras_completas": "razón medida"}.
    # El chequeo se queda en el reporte con su falla; solo deja de tumbar el ok general.
    acept = (e.guion or {}).get("qa_aceptadas", {}) if isinstance(e.guion, dict) else {}
    for k, razon in acept.items():
        if isinstance(rep.get(k), dict) and not rep[k].get("ok", True): rep[k]["aceptada"] = razon
    rep["ok"] = all(v.get("ok", True) or v.get("aceptada") for v in rep.values() if isinstance(v, dict))
    return rep


def imprimir(rep):
    print(f"QA {'OK' if rep['ok'] else 'CON FALLAS'} · {rep['duracion_s']} s")
    for k, v in rep.items():
        if isinstance(v, dict): print(f"  {'ok ' if v.get('ok', True) else 'MAL'} {k}: { {a: b for a, b in v.items() if a not in ('ok', 'detalle')} }")
