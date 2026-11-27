"""audio_youtube — reglas de audio (nivel, música bajo la voz, techo).

    import audio_youtube as AY

Regla y la función que la cumple:
  1. «Que la música no se escuche más fuerte que la voz; normalizar todas las pistas y sus partes fuertes»
       normalizar_lufs()           → cada pista al mismo LUFS integrado
       nivelar_corto_plazo()       → loudness de corto plazo (3 s, salto 100 ms) llevado a un nivel CONSTANTE
                                     (ataque ~1 s, liberación ~2 s, corrección limitada a ±10 dB)
       techo_musica()              → en lo hablado la música nunca pasa de voz − 12 LU en ninguna ventana de 3 s
       musica_menos_voz()          → distribución (p50/p95/máx) de música − voz por ventanas de 3 s (objetivo −15 ± 2 dB)
  2. «Quitar la música solo cuando se reproduce el video de ejemplo / el resultado»
       envolvente_musica()         → 0 exacto en insertos/intro con rampas de 0.6 s FUERA del inserto; tarjetas +8 dB
                                     (sube 0.3 s, baja 0.6 s justo cuando vuelve a hablar)
       detectar_reproduccion()     → tramos de una grabación de pantalla donde suena OTRA cosa (un video que reproduce)
  3. «Quitar las respiraciones exageradas sin comerse consonantes»
       detectar_respiraciones()    → huecos entre palabras alineadas, banda 1–6 kHz ≫ 80–300 Hz, sin periodicidad,
                                     audible sobre el piso; protege ±60 ms de cada palabra (más con s/f/j/z)
       ganancia_respiraciones()    → −30 dB con fundidos de 20 ms, SIN cortar tiempo (la sincronía no cambia)
  4. «Usa más las canciones que suenen tech»
       rasgos_pista(), parecido_a_referencia(), armar_playlist()   (librosa; se importa solo aquí)
       pegar_playlist()            → pistas una tras otra, nunca encimadas, cruces de igual potencia de 4 s

Todo trabaja en float a 48 kHz; las señales estéreo son (n, 2). Sin APIs: todo local."""
import math
import numpy as np
from scipy.signal import lfilter, butter, sosfilt
from scipy.ndimage import uniform_filter1d, maximum_filter1d, minimum_filter1d

SR = 48000

# ------------------------------------------------------------------ medición BS.1770
def _kpond(x, sr=SR):
    """Filtro K (BS.1770) — coeficientes para 48 kHz."""
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1, -2, 1], [1, -1.99004745483398, 0.99007225036621]
    return lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0)


def potencia_k(x, sr=SR):
    """Potencia K-ponderada por muestra (suma de canales), float64 1-D."""
    y = _kpond(np.asarray(x, np.float64), sr)
    return (y ** 2).sum(1) if y.ndim > 1 else y ** 2


def lufs_integrado(x, sr=SR):
    """LUFS integrado BS.1770-4 (bloques 400 ms, compuertas −70 y −10)."""
    p = potencia_k(x, sr); blk, hop = int(0.4 * sr), int(0.1 * sr)
    c = np.concatenate([[0.0], np.cumsum(p)]); idx = np.arange(0, len(p) - blk, hop)
    ms = (c[idx + blk] - c[idx]) / blk
    l = -0.691 + 10 * np.log10(ms + 1e-12); ms = ms[l > -70]
    if not len(ms): return -120.0
    rel = -0.691 + 10 * np.log10(ms.mean()) - 10
    ms = ms[(-0.691 + 10 * np.log10(ms)) > rel]
    return float(-0.691 + 10 * np.log10(ms.mean()))


def loudness_corto(x=None, sr=SR, ventana=3.0, salto=0.1, potencia=None):
    """Loudness de corto plazo (ventana CENTRADA de `ventana` s, cada `salto` s). Devuelve (t_centros, LUFS).
    Se puede pasar la potencia K ya calculada (potencia_k) para no repetir el filtro."""
    p = potencia_k(x, sr) if potencia is None else potencia
    c = np.concatenate([[0.0], np.cumsum(p)]); w = int(ventana * sr); h = int(salto * sr)
    t = np.arange(0, len(p), h); a = np.clip(t - w // 2, 0, len(p)); b = np.clip(t + w // 2, 0, len(p))
    ms = (c[b] - c[a]) / np.maximum(b - a, 1)
    return t / sr, -0.691 + 10 * np.log10(ms + 1e-12)


def normalizar_lufs(x, objetivo=-16.0, sr=SR):
    """Lleva una pista a `objetivo` LUFS integrados (todas las canciones al mismo nivel)."""
    return x * 10 ** ((objetivo - lufs_integrado(x, sr)) / 20)


# ------------------------------------------------------------------ suavizado de ganancias
def suavizar_ganancia_db(g_db, salto=0.1, ataque=1.0, liberacion=2.0):
    """Suaviza una curva de ganancia (dB, en la rejilla de `salto` s) con ataque (cuando la ganancia BAJA: la música se puso
    fuerte) y liberación (cuando SUBE). Se hace hacia adelante y hacia atrás y se toma el mínimo: así la bajada empieza
    ANTES de la parte fuerte (sin anticipación, la primera fracción de segundo se escaparía) y sube despacio después."""
    ka, kr = 1 - math.exp(-salto / ataque), 1 - math.exp(-salto / liberacion)
    def pasada(g):
        out = np.empty_like(g); y = g[0]
        for i, v in enumerate(g):
            y += (ka if v < y else kr) * (v - y); out[i] = y
        return out
    return np.minimum(pasada(g_db), pasada(g_db[::-1])[::-1])


def a_muestras(t_rejilla, g_db, n, sr=SR):
    """Curva de ganancia en dB (rejilla) → factor lineal por muestra (float32)."""
    ts = np.arange(n, dtype=np.float64) / sr
    return (10 ** (np.interp(ts, t_rejilla, g_db) / 20)).astype(np.float32)


# ------------------------------------------------------------------ 1 · nivelación de la música
def nivelar_corto_plazo(mus, sr=SR, objetivo=None, ventana=3.0, salto=0.1, ataque=1.0, liberacion=2.0, max_db=10.0,
                        silencio=-50.0):
    """Nivela la música en corto plazo: mide el loudness de 3 s (salto 100 ms) y aplica la ganancia que la deja en un nivel
    CONSTANTE (`objetivo`; por defecto la mediana de la propia música). Suavizado ataque ~1 s / liberación ~2 s (no bombea),
    corrección limitada a ±`max_db`. Lo que está por debajo de `silencio` LUFS (huecos, colas) no se sube.
    Devuelve (música nivelada, ganancia por muestra, dict con medidas antes/después)."""
    t, L = loudness_corto(mus, sr, ventana, salto)
    vivo = L > silencio
    obj = float(np.median(L[vivo])) if objetivo is None else objetivo
    g = np.where(vivo, np.clip(obj - L, -max_db, max_db), 0.0)
    g = suavizar_ganancia_db(g, salto, ataque, liberacion)
    gm = a_muestras(t, g, len(mus), sr)
    out = mus * (gm[:, None] if mus.ndim > 1 else gm)
    _, L2 = loudness_corto(out, sr, ventana, salto)
    v2 = L2 > silencio
    info = dict(objetivo=round(obj, 2), antes_p5_p95=(round(float(np.percentile(L[vivo], 5)), 1), round(float(np.percentile(L[vivo], 95)), 1)),
                despues_p5_p95=(round(float(np.percentile(L2[v2], 5)), 1), round(float(np.percentile(L2[v2], 95)), 1)),
                ganancia_min_max=(round(float(g.min()), 1), round(float(g.max()), 1)))
    return out, gm, info


def _ventanas_habladas(mascara, t, sr, ventana):
    """Ventanas de `ventana` s (centradas en t) que caen ENTERAS dentro de la máscara hablada: las que tocan una tarjeta o la
    pantalla final (donde la música sube a propósito) no cuentan como «parte hablada»."""
    c = np.concatenate([[0], np.cumsum(~mascara)]); h = int(ventana * sr / 2)
    a = np.clip((t * sr).astype(np.int64) - h, 0, len(mascara)); b = np.clip((t * sr).astype(np.int64) + h, 0, len(mascara))
    return (c[b] - c[a]) == 0


def musica_menos_voz(voz, mus, mascara, sr=SR, ventana=3.0, salto=0.1, voz_activa=20.0):
    """Música − voz (LU) por ventanas de 3 s (salto 100 ms) SOLO en lo hablado: ventanas que caen enteras en `mascara`
    (muestras habladas) y cuya voz está a menos de `voz_activa` LU de su mediana (hay habla de verdad, no una pausa larga).
    Devuelve dict(p50, p95, max, n, frac_sobre_-12) y el arreglo de diferencias."""
    t, Lv = loudness_corto(voz, sr, ventana, salto)
    _, Lm = loudness_corto(mus, sr, ventana, salto)
    sel = _ventanas_habladas(mascara, t, sr, ventana) & (Lv > -70)
    sel &= Lv > np.median(Lv[sel]) - voz_activa
    d = (Lm - Lv)[sel]
    return dict(p50=round(float(np.percentile(d, 50)), 1), p95=round(float(np.percentile(d, 95)), 1),
                max=round(float(d.max()), 1), n=int(sel.sum()), sobre_12=round(float((d > -12).mean() * 100), 2)), d


def techo_musica(voz, mus, mascara, sr=SR, techo=-12.5, ventana=3.0, salto=0.1, ataque=1.0, liberacion=2.0, vueltas=4,
                 voz_activa=20.0):
    """Garantiza que en lo hablado la música no pase de voz + `techo` LU en NINGUNA ventana de 3 s: donde se pasa, baja la
    música lo justo (suavizado ataque/liberación, con anticipación), en varias vueltas hasta que no quede ninguna ventana.
    Devuelve (música corregida, ganancia por muestra)."""
    gtot = np.ones(len(mus), np.float32); pv = potencia_k(voz, sr)
    t, Lv = loudness_corto(sr=sr, ventana=ventana, salto=salto, potencia=pv)
    i = (t * sr).astype(np.int64).clip(0, len(mascara) - 1)
    act = _ventanas_habladas(mascara, t, sr, ventana) & (Lv > -70); act &= Lv > np.median(Lv[act]) - voz_activa
    dentro = mascara[i]                                         # la corrección solo se aplica dentro de lo hablado
    m = mus
    for _ in range(vueltas):
        _, Lm = loudness_corto(m, sr, ventana, salto)
        exceso = np.where(act, Lm - Lv - techo, 0.0)
        if exceso.max() <= 0.05: break
        g = -np.clip(exceso + 0.3, 0, None)
        g = minimum_filter1d(g, int(ventana / salto) + 1)       # toda la ventana que contiene el exceso
        g = np.where(dentro, g, 0.0)                            # tarjetas, insertos y pantalla final no se tocan
        g = suavizar_ganancia_db(g, salto, ataque, liberacion)
        gm = a_muestras(t, g, len(mus), sr)
        gtot *= gm; m = mus * (gtot[:, None] if mus.ndim > 1 else gtot)
    return m, gtot


# ------------------------------------------------------------------ 2 · envolvente de la música (insertos, tarjetas)
def _rampa(n, sube=True):
    u = np.linspace(0, 1, max(n, 1)); r = np.sin(u * np.pi / 2) ** 2
    return r if sube else r[::-1]


def envolvente_musica(n, sr, silencios, tarjetas, retornos, sube_db=8.0, rampa_out=0.6, rampa_up=0.3, rampa_down=0.6,
                      extra=None):
    """Ganancia de la música (lineal, por muestra, float32):
      · `silencios` [(a, b)] en segundos → 0 EXACTO dentro; rampas de `rampa_out` s FUERA (baja antes de a, sube después de b);
      · `tarjetas` [(a, b)] → +`sube_db` dB: sube en `rampa_up` s desde a; `retornos[k]` = instante en que vuelve a hablar
        tras la tarjeta k → baja en `rampa_down` s terminando JUSTO en ese instante;
      · `extra` [(a, b, db, sube, baja)] → otros tramos con ganancia propia (p. ej. la pantalla final).
    Los ceros mandan sobre todo lo demás."""
    g = np.ones(n, np.float32)
    def tramo_db(a, b, db, ru, rd, fin_rd=None):
        ia, ib = int(a * sr), int((fin_rd if fin_rd is not None else b) * sr)
        k = 10 ** (db / 20); nu, nd = int(ru * sr), int(rd * sr)
        h = np.full(max(ib - ia, 0), k, np.float32)
        u = min(nu, len(h)); h[:u] = 1 + (k - 1) * _rampa(u)
        dn = min(nd, len(h) - u); h[len(h) - dn:] = 1 + (k - 1) * _rampa(dn, False) if dn > 0 else h[len(h) - dn:]
        g[ia:ia + len(h)] = np.maximum(g[ia:ia + len(h)], h)
    for k, (a, b) in enumerate(tarjetas):
        tramo_db(a, b, sube_db, rampa_up, rampa_down, fin_rd=retornos[k] if retornos else b)
    for a, b, db, ru, rd in (extra or []):
        tramo_db(a, b, db, ru, rd)
    z = np.ones(n, np.float32); no = int(rampa_out * sr)
    for a, b in silencios:
        ia, ib = max(0, int(round(a * sr))), min(n, int(round(b * sr)))
        z[ia:ib] = 0
        i0 = max(0, ia - no); z[i0:ia] = np.minimum(z[i0:ia], _rampa(ia - i0, False)[-(ia - i0):] if ia > i0 else 1)
        i1 = min(n, ib + no); z[ib:i1] = np.minimum(z[ib:i1], _rampa(i1 - ib)[:i1 - ib] if i1 > ib else 1)
    return g * z


def detectar_reproduccion(crudo, voz, sr, palabras, min_dur=1.0, margen=20.0):
    """Tramos (s) de una grabación donde suena algo que NO es la voz del creador (un video que reproduce con su sonido):
    el audio crudo de la grabación está ≥ `margen` dB sobre su piso donde la alineación de su texto no tiene palabras
    (±0.1 s), sostenido ≥ `min_dur` s. `voz` (la voz aislada) solo se usa para la longitud."""
    h = int(0.05 * sr); n = min(len(crudo), len(voz)) // h
    ec = 10 * np.log10(uniform_filter1d(crudo[: n * h] ** 2, 4 * h)[h // 2::h][:n] + 1e-14)
    ev = 10 * np.log10(uniform_filter1d(voz[: n * h] ** 2, 4 * h)[h // 2::h][:n] + 1e-14)
    piso_c = np.percentile(ec, 10); ref_v = np.percentile(ev, 95)
    habla = np.zeros(n, bool)
    for w in palabras: habla[max(0, int((w["s"] - 0.1) / 0.05)):int((w["e"] + 0.1) / 0.05) + 1] = True
    # la voz aislada (Demucs) también conserva la voz de un video reproducido: lo que delata la reproducción es sonido
    # sostenido en la grabación donde la alineación de SU texto no tiene palabras
    otro = (ec > piso_c + margen) & ~habla
    otro = minimum_filter1d(maximum_filter1d(otro.astype(np.uint8), 11), 11) > 0      # cierra huecos de 0.5 s
    d = np.diff(np.concatenate([[0], otro.astype(np.int8), [0]]))
    return [(a * 0.05, b * 0.05) for a, b in zip(np.where(d == 1)[0], np.where(d == -1)[0]) if (b - a) * 0.05 >= min_dur]


# ------------------------------------------------------------------ 3 · respiraciones
FRIC_FIN = ("s", "z", "f", "j", "x")
FRIC_INI = ("s", "z", "f", "j", "x", "ce", "ci", "ch", "ge", "gi")


def _limpia(w):
    import unicodedata, re
    t = unicodedata.normalize("NFKD", w.lower()); t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-zñ0-9]+", "", t)


def _banda(x, a, b, sr):
    return sosfilt(butter(4, [a, b], "band", fs=sr, output="sos"), x)


def detectar_respiraciones(v, sr, palabras, dur_min=0.12, dur_max=0.9, hueco_min=0.12, proteger=0.06, proteger_ataque=0.08,
                           proteger_fric=0.15, sobre_piso=10.0, ratio_min=3.0, periodicidad_max=0.45, nivel_rel=-48.0,
                           nivel_max=-8.0, ref_db=None, piso_db=None):
    """Respiraciones audibles en una pista de voz (mono). Criterios, todos a la vez:
      · solo en huecos entre palabras alineadas (`palabras` [{w, s, e}]) de ≥ `hueco_min` s, dejando `proteger` s tras cada
        palabra y `proteger_ataque` s antes de la siguiente (la alineación forzada marca el arranque ~70 ms tarde: la
        consonante inicial vive ahí); además ±60 ms alrededor de todo cuadro con voz sonora (por si la alineación erró), y `proteger_fric` del lado de una fricativa (palabra que termina en s/z/f/j/x o empieza
        en s/z/f/j/x/ce/ci/ch/ge/gi); nunca menos de ±60 ms;
      · energía 1–6 kHz ≥ `ratio_min` dB sobre 80–300 Hz (aire, no voz) y sin dominancia sibilante (4.5–10 kHz no supera a 1–4 kHz
        por más de 3 dB: eso es una «s», no una respiración);
      · sin periodicidad (autocorrelación normalizada de 80–1000 Hz, pitch 70–400 Hz, < `periodicidad_max`);
      · audible: ≥ `sobre_piso` dB sobre el piso de ruido (sin contar el silencio digital de una compuerta) y ≥ voz + `nivel_rel`
        dB (las «exageradas»), pero ≤ voz + `nivel_max` dB (más fuerte que eso es habla o el audio de otro video, no aire);
      · duración del evento entre `dur_min` y `dur_max` s.
    `ref_db` / `piso_db` fijan la referencia de la voz y el piso de ruido (si no: p95 dentro de las palabras / p5 de los huecos).
    Devuelve lista de dict(s, e, pico_db, sobre_piso, ratio_db, periodicidad)."""
    v = np.asarray(v, np.float64); hop = int(0.01 * sr); win = int(0.03 * sr); n = len(v) // hop
    def env(x, w=win):
        return 10 * np.log10(uniform_filter1d(x ** 2, w)[hop // 2::hop][:n] + 1e-14)
    e_all = env(v); e_hi = env(_banda(v, 1000, 6000, sr)); e_lo = env(_banda(v, 80, 300, sr))
    e_sib = env(_banda(v, 4500, min(10000, sr / 2 - 100), sr)); e_mid = env(_banda(v, 1000, 4000, sr))
    lo_v = _banda(v, 80, 1000, sr)
    pal = sorted(palabras, key=lambda w: w["s"])
    wm = np.zeros(n, bool)
    for w in pal: wm[max(0, int(w["s"] * 100)):int(w["e"] * 100) + 1] = True
    ref = ref_db if ref_db is not None else (np.percentile(e_all[wm], 95) if wm.any() else e_all.max())
    huecos = []
    lim = [None] + pal + [None]
    for w0, w1 in zip(lim[:-1], lim[1:]):
        a = (w0["e"] if w0 else 0.0); b = (w1["s"] if w1 else len(v) / sr)
        if b - a < hueco_min: continue
        pa = proteger_fric if (w0 and _limpia(w0["w"]).endswith(FRIC_FIN)) else proteger
        pb = proteger_fric if (w1 and _limpia(w1["w"]).startswith(FRIC_INI)) else proteger_ataque
        if w0 and w0.get("ok") is False: pa = max(pa, 0.15)
        if w1 and w1.get("ok") is False: pb = max(pb, 0.15)
        if b - pb - (a + pa) >= dur_min: huecos.append((a + pa, b - pb))
    gm = np.zeros(n, bool)
    for a, b in huecos: gm[int(a * 100):int(b * 100)] = True
    # piso de ruido: p5 de los huecos sin el silencio digital de una compuerta (≥ voz − 75 dB)
    vivos = gm & (e_all > -100)
    piso = max(float(np.percentile(e_all[vivos] if vivos.sum() > 50 else e_all[e_all > -100], 5)), ref - 75)
    if piso_db is not None: piso = piso_db
    lag0, lag1 = int(sr / 400), int(sr / 70); fl = int(0.04 * sr)
    def periodicidades(i0, i1):
        """autocorrelación normalizada (pico en lags de 70–400 Hz) de cada cuadro i0…i1-1, vectorizada con FFT."""
        out = np.zeros(i1 - i0)
        for c0 in range(i0, i1, 2000):
            c1 = min(i1, c0 + 2000); cs = np.arange(c0, c1) * hop + hop // 2 - fl // 2
            ok = (cs >= 0) & (cs + fl <= len(lo_v))
            if not ok.any(): continue
            F = lo_v[cs[ok][:, None] + np.arange(fl)[None, :]]
            F = F - F.mean(1, keepdims=True)
            R = np.fft.irfft(np.abs(np.fft.rfft(F, 2 * fl, axis=1)) ** 2, axis=1)[:, :lag1]
            r = R[:, lag0:lag1].max(1) / np.maximum(R[:, 0], 1e-20)
            tmp = np.zeros(c1 - c0); tmp[ok] = r; out[c0 - i0:c1 - i0] = tmp
        return out
    out = []
    for a, b in huecos:
        i0, i1 = int(a * 100), min(n, int(b * 100))
        cand = ((e_all[i0:i1] > piso + sobre_piso) & (e_all[i0:i1] > ref + nivel_rel) &
                (e_hi[i0:i1] - e_lo[i0:i1] > ratio_min) & (e_sib[i0:i1] - e_mid[i0:i1] < 3.0))
        if not cand.any(): continue
        # voz sonora (periódica) dentro del hueco: la alineación pudo errar → se protege ±60 ms alrededor de cada cuadro sonoro
        per_f = periodicidades(i0, i1)
        sonoro = maximum_filter1d(((per_f > 0.6) & (e_lo[i0:i1] > ref - 30)).astype(np.uint8), 13) > 0
        cand &= ~sonoro
        cand = minimum_filter1d(maximum_filter1d(cand.astype(np.uint8), 5), 5) > 0           # cierra huecos de 40 ms
        cand &= ~sonoro
        d = np.diff(np.concatenate([[0], cand.astype(np.int8), [0]]))
        for s, t in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
            if (t - s) / 100 < dur_min * 0.66: continue
            per = per_f[s:t]
            if np.median(per) >= periodicidad_max or (per > 0.7).mean() > 0.25: continue
            # el evento se extiende hacia sus colas (energía > piso + 4 dB) sin salir del hueco protegido ni tocar voz sonora
            ss, tt = s, t
            while ss > 0 and not sonoro[ss - 1] and e_all[i0 + ss - 1] > piso + 4 and (s - ss) < 15: ss -= 1
            while i0 + tt < i1 and not sonoro[tt] and e_all[i0 + tt] > piso + 4 and (tt - t) < 15: tt += 1
            dur = (tt - ss) / 100
            if dur < dur_min or dur > dur_max: continue
            seg = slice(i0 + ss, i0 + tt)
            if e_all[seg].max() > ref + nivel_max: continue
            out.append(dict(s=round((i0 + ss) / 100, 3), e=round((i0 + tt) / 100, 3), pico_db=round(float(e_all[seg].max() - ref), 1),
                            sobre_piso=round(float(e_all[seg].max() - piso), 1),
                            ratio_db=round(float(np.median(e_hi[seg] - e_lo[seg])), 1), periodicidad=round(float(np.median(per)), 2)))
    return out


def respiraciones_en_tramos(v, sr, palabras, tramos, nivel_max_libre=-10.0, **kw):
    """Detección en dos pasadas sobre los tramos que SÍ quedan en el video (`tramos` [(a, b)] en s de la grabación):
      1. por huecos de la alineación (detectar_respiraciones con `palabras`);
      2. «libre» (la alineación forzada a veces se corre 50–150 ms y deja la respiración «dentro» de una palabra): todo el
         tramo como un hueco, con la misma referencia y el mismo piso; se acepta solo si el evento no toca palabras con
         fricativas sordas largas (j, ge/gi, x, f, s final/inicial pegada), no se mete más de 40 % en una palabra alineada y es
         ≤ voz + `nivel_max_libre` dB. Siempre ±60 ms de toda voz sonora.
    Devuelve la unión ordenada (sin duplicados), cada una con 'pasada' = 'alineada' | 'libre'."""
    from scipy.ndimage import uniform_filter1d as _uf
    hop = int(0.01 * sr)
    e = 10 * np.log10(_uf(np.asarray(v, np.float64) ** 2, int(0.03 * sr))[hop // 2::hop] + 1e-14)
    wm = np.zeros(len(e), bool)
    for w in palabras: wm[int(w["s"] * 100):int(w["e"] * 100) + 1] = True
    ref = float(np.percentile(e[wm], 95))
    piso = float(max(np.percentile(e[(~wm) & (e > -100)], 5), ref - 75))
    A = [dict(b, pasada="alineada") for b in detectar_respiraciones(v, sr, palabras, ref_db=ref, piso_db=piso, **kw)
         if any(a <= b["s"] and b["e"] <= z for a, z in tramos)]
    bordes = []
    for a, z in tramos: bordes += [dict(w="|", s=a - 0.2, e=a), dict(w="|", s=z, e=z + 0.2)]
    L = detectar_respiraciones(v, sr, bordes, ref_db=ref, piso_db=piso, proteger=0.0, proteger_ataque=0.0, proteger_fric=0.0,
                               nivel_max=nivel_max_libre, **{k: x for k, x in kw.items() if k not in ("proteger", "proteger_ataque", "proteger_fric", "nivel_max")})
    LARGAS = ("j", "ge", "gi", "x", "f")
    out = list(A)
    for b in L:
        if not any(a <= b["s"] and b["e"] <= z for a, z in tramos): continue
        if any(min(b["e"], c["e"]) - max(b["s"], c["s"]) > 0 for c in out): continue
        dur = b["e"] - b["s"]; ok = True
        for w in palabras:
            ov = min(b["e"], w["e"]) - max(b["s"], w["s"])
            if w["e"] < b["s"] - 0.15 or w["s"] > b["e"] + 0.15: continue
            t = _limpia(w["w"])
            cerca_fin = abs(w["e"] - b["s"]) < 0.15 or ov > 0
            cerca_ini = abs(b["e"] - w["s"]) < 0.15 or ov > 0
            if ov > 0 and any(k in t for k in LARGAS): ok = False
            if (cerca_fin and t.endswith(FRIC_FIN)) and b["s"] < w["e"] + 0.06: ok = False
            if (cerca_ini and t.startswith(FRIC_INI)) and b["e"] > w["s"] - 0.06: ok = False
            if ov > 0.4 * dur: ok = False
        if ok: out.append(dict(b, pasada="libre"))
    return sorted(out, key=lambda b: b["s"])


def ganancia_respiraciones(n, sr, resp, atenuacion_db=-30.0, fundido=0.02):
    """Ganancia por muestra (float32) que baja cada respiración `atenuacion_db` con fundidos de `fundido` s DENTRO del tramo
    detectado (que ya respeta la protección de las palabras). No quita tiempo: la sincronía no cambia."""
    g = np.ones(n, np.float32); k = 10 ** (atenuacion_db / 20); f = int(fundido * sr)
    for r in resp:
        a, b = int(r["s"] * sr), min(n, int(r["e"] * sr))
        if b - a < 2 * f + 1: continue
        h = np.full(b - a, k, np.float32)
        u = np.sin(np.linspace(0, np.pi / 2, f)) ** 2                # en dB se ve como una curva suave
        h[:f] = 1 + (k - 1) * u; h[-f:] = 1 + (k - 1) * u[::-1]
        g[a:b] = np.minimum(g[a:b], h)
    return g


# ------------------------------------------------------------------ 4 · música tech
def rasgos_pista(path, sr=22050, max_s=240):
    """Rasgos de una pista con librosa: timbre (MFCC 20, media y desviación), centroide/ancho/rolloff/planitud espectral,
    tempo, proporción percusiva (HPSS), regularidad del pulso (pulso electrónico), energía de bombo 40–110 Hz,
    «sintetizador» (armónico + planitud baja + brillo estable). Devuelve dict de escalares + vector 'v'."""
    import librosa
    y, _ = librosa.load(path, sr=sr, mono=True, duration=max_s)
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    mf = librosa.feature.mfcc(S=librosa.amplitude_to_db(S ** 2 + 1e-10), sr=sr, n_mfcc=20)
    cen = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
    bw = librosa.feature.spectral_bandwidth(S=S, sr=sr)[0]
    ro = librosa.feature.spectral_rolloff(S=S, sr=sr)[0]
    fl = librosa.feature.spectral_flatness(S=S)[0]
    H, P = librosa.decompose.hpss(S)
    perc = float((P ** 2).sum() / ((H ** 2).sum() + (P ** 2).sum() + 1e-12))
    onset = librosa.onset.onset_strength(S=librosa.amplitude_to_db(S ** 2 + 1e-10), sr=sr)
    tempo = float(np.atleast_1d(librosa.feature.tempo(onset_envelope=onset, sr=sr))[0])
    ac = librosa.autocorrelate(onset - onset.mean()); ac = ac / (ac[0] + 1e-12)
    lag = int(round(60 / tempo * sr / 512)) if tempo > 0 else 0
    pulso = float(ac[lag]) if 0 < lag < len(ac) else 0.0                     # pulso regular (caja de ritmos)
    fr = librosa.fft_frequencies(sr=sr, n_fft=2048)
    bombo = float((P[(fr >= 40) & (fr <= 110)] ** 2).sum() / ((P ** 2).sum() + 1e-12))
    sint = float((1 - perc) * (1 - np.median(fl) * 10) * (1 - np.std(cen) / (np.mean(cen) + 1e-9)))
    d = dict(centroide=float(np.mean(cen)), ancho=float(np.mean(bw)), rolloff=float(np.mean(ro)), planitud=float(np.mean(fl)),
             tempo=tempo, percusivo=perc, pulso=pulso, bombo=bombo, sintetizador=sint)
    d["v"] = np.concatenate([mf.mean(1), mf.std(1), [d[k] for k in ("centroide", "ancho", "rolloff", "planitud", "tempo",
                                                                    "percusivo", "pulso", "bombo", "sintetizador")]])
    return d


def parecido_a_referencia(rasgos, referencia, pesos_timbre=1.0, pesos_tech=2.0):
    """Puntaje 0–100 de parecido de cada pista a la referencia: distancia euclídea sobre rasgos estandarizados (z) entre
    todas las pistas; el timbre (MFCC) pesa `pesos_timbre` y los rasgos «tech» (centroide, tempo, percusión, pulso, bombo,
    sintetizador…) pesan `pesos_tech`. 100 = la referencia misma. Devuelve {nombre: puntaje}."""
    nombres = list(rasgos); M = np.stack([rasgos[k]["v"] for k in nombres])
    Z = (M - M.mean(0)) / (M.std(0) + 1e-9)
    w = np.ones(M.shape[1]); w[:40] = pesos_timbre / 40 * 9; w[40:] = pesos_tech
    r = Z[nombres.index(referencia)]
    dist = np.sqrt((((Z - r) ** 2) * w).sum(1))
    dmax = dist.max() + 1e-9
    return {k: round(float(100 * (1 - dist[i] / dmax)), 1) for i, k in enumerate(nombres)}


def armar_playlist(puntajes, duraciones, necesario, referencia, xf=4.0, minimo=None, al_final=True):
    """Playlist que cubre `necesario` s: primero las más parecidas (de mayor a menor), la referencia AL FINAL (sigue sonando
    hasta la última palabra) y nunca la misma dos veces seguidas. Se quedan fuera las de puntaje < `minimo` (por defecto:
    mediana − 1 desviación). Si no alcanza, se reutilizan en el mismo orden. Devuelve lista de nombres."""
    if minimo is None:
        p = np.array(list(puntajes.values())); minimo = float(np.median(p) - p.std())
    orden = [k for k in sorted(puntajes, key=lambda k: -puntajes[k]) if k != referencia and puntajes[k] >= minimo]
    lista, total = [], duraciones[referencia] - xf
    i = 0
    while total < necesario and orden:
        k = orden[i % len(orden)]
        if lista and lista[-1] == k: i += 1; continue
        lista.append(k); total += duraciones[k] - xf; i += 1
    return lista + [referencia] if al_final else [referencia] + lista


def pegar_playlist(pistas, n, sr=SR, xf=4.0, final_en=None):
    """Pega las pistas (arreglos (m, 2) ya normalizados) una tras otra, NUNCA encimadas: la siguiente entra solo en el cruce
    de igual potencia de `xf` s. Si `final_en` (muestra) se da, la ÚLTIMA pista se coloca para que su final natural
    caiga ahí (la anterior se recorta con el mismo cruce). Devuelve (música (n, 2) float32, [(nombre_idx, inicio_s, fin_s)])."""
    X = int(xf * sr); mus = np.zeros((n, 2), np.float32); marcas = []
    a_in = np.sqrt(np.sin(np.linspace(0, np.pi / 2, X)) ** 2).astype(np.float32)        # √ de seno² = cruce de igual potencia
    a_out = np.sqrt(np.cos(np.linspace(0, np.pi / 2, X)) ** 2).astype(np.float32)
    ini = []; p = 0
    for k, tr in enumerate(pistas):
        ini.append(p); p += len(tr) - X
    if final_en is not None:
        ini[-1] = min(ini[-1], final_en - len(pistas[-1]))
        ini[-1] = max(ini[-1], ini[-2] + X if len(ini) > 1 else 0)
    for k, tr in enumerate(pistas):
        tr = tr.astype(np.float32).copy()
        a = ini[k]; b = ini[k + 1] + X if k + 1 < len(pistas) else a + len(tr)
        L = min(len(tr), b - a); tr = tr[:L]
        if k > 0: tr[:X] *= a_in[:, None]
        if k + 1 < len(pistas) and L >= X: tr[L - X:] *= a_out[:, None]
        a0, a1 = max(0, a), min(n, a + L)
        if a1 > a0: mus[a0:a1] += tr[a0 - a:a1 - a]
        marcas.append((k, round(a / sr, 2), round((a + L) / sr, 2)))
    return mus, marcas
