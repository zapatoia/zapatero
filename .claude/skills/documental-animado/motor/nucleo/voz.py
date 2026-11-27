#!/usr/bin/env python
"""Voz: ElevenLabs eleven_v4 en TOMA CORRIDA + verificación literal con Whisper + marcas por palabra → voz.wav, palabras.json, voz-verificacion.json.
Nunca se corta una palabra. Ver SKILL.md § Voz.

  python motor/nucleo/voz.py <proyecto> saldo             → caracteres que costará + saldo de tu cuenta (NO gasta)
  python motor/nucleo/voz.py <proyecto> [--intentos 2]    → genera SOLO lo que falte o falle, verifica y arma
  python motor/nucleo/voz.py <proyecto> armar             → re-arma voz.wav y palabras.json sin gastar
  python motor/nucleo/voz.py <proyecto> verificar         → pasada literal sobre el voz.wav actual (no gasta); la exige el QA
  python motor/nucleo/voz.py <proyecto> rehacer 3,5       → fuerza a regenerar esas líneas (1-based)

<proyecto>/guion.json: {"lineas":[{"who":"D","texto":"…","sub":"BLOQUE UNO / BLOQUE *DOS","tts":"[curious] … [short pause] …","toma":1,"recorte_ini":.42}]}
  texto = lo que se ve; tts = lo que se manda (etiquetas de emoción y pausa entre [...], no cuentan como texto esperado).
        Una emoción por frase. En un mismo guion: o pausas con etiqueta, o con puntos suspensivos, nunca las dos (validar_tts corta antes de gastar).
  toma = fija una toma ya pagada (0 = la primera), sin gastar. recorte_ini = s que se quitan al inicio (solo silencio o un «Eh» real).
  Cifras: Whisper duda entre «1,000» y «uno mil»; si la pasada literal coincide y solo fallan numerales, la línea PASA (no pagues reintentos por eso).
who: "D" = tu voz (perfil.json → voz_id) · "C" = segunda voz opcional (voz_id_2).
Tope por video: 2,500 caracteres (reintentos incluidos). Registro: <proyecto>/audio/eleven_gasto.json y <skill>/gasto_eleven_total.json.
La clave sale de ELEVENLABS_API_KEY (.env) y jamás se imprime.
"""
import hashlib, json, os, re, subprocess, sys, wave
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
MV = AQUI.parent
sys.path.insert(0, str(MV / "herramientas"))
sys.path.insert(0, str(AQUI))
from rutas import FF as _FF, leer_texto  # noqa: E402   (leer_texto: UTF-8 siempre; en Windows read_text() es cp1252)
import eleven_es as E          # noqa: E402
import verificar_es as V       # noqa: E402

FF = _FF
SR = 48000
E.TOPE_TAREA = 10 ** 9         # el tope de esta tarea es por video (abajo); el de eleven_es era de otra tarea

# Estándar de voz. Se fija aquí y no en eleven_es porque ese módulo también lo usan otros proyectos.
MODELO = "eleven_v4"
AJUSTES_V4 = {"stability": .5, "similarity_boost": .85}     # v4 no acepta style ni speed
E.MODELO = MODELO; E.AJUSTES = {k: dict(AJUSTES_V4) for k in E.AJUSTES}; E.AJUSTES_PREV = {}
TOPE_VIDEO = 2500
PAUSA_MAX = .80                # solo una pausa mayor se acorta, y solo dentro del silencio real
UMBRAL_COLA = -50              # dB rel. al pico en voz seca: abajo de esto ya no hay palabra
COLA_SEG = .20                 # lo mínimo que se conserva tras caer a UMBRAL_COLA
COLA_ARCHIVO = .25


def decod(path, sr=SR):
    raw = subprocess.run([FF, "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def wav16(path, x, sr=SR):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def rms_db(x, ven=240):
    n = len(x) // ven; r = np.sqrt((x[:n * ven].reshape(n, ven) ** 2).mean(1)) + 1e-9; return 20 * np.log10(r)


def recortar(x, pausa_max=PAUSA_MAX, umbral=UMBRAL_COLA, pre=.0, post=COLA_ARCHIVO):
    """Solo quita lo que está fuera de la voz. Regla: ningún corte dentro de una palabra ni de su cola.
    · Arranque: en la primera energía sobre `umbral` (una inhalación larga antes de la voz fuerte no cuenta).
    · Pausas: solo > pausa_max (nunca menos de PAUSA_MAX, aunque un guion viejo pida 0.3) y solo si TODO el hueco está bajo `umbral`. Se quita el centro: quedan 0.40 s de cola y 0.30 s antes de la palabra siguiente.
    · Final: toda la cola natural + `post` tras caer a `umbral`, con fundido solo en los últimos 20 ms. Si la toma acaba antes con energía (lo hace ElevenLabs), funde 60 ms al final de la toma y rellena con silencio.
    `umbral` se mide en seco: la cadena de locutor sube ~20 dB estas colas, así que −42 dB en seco no es silencio."""
    pausa_max = max(pausa_max, PAUSA_MAX); post = max(post, COLA_SEG); ven = 240; db = rms_db(x, ven); pk = db.max(); voz = db > pk + umbral; idx = np.where(voz)[0]; dt = ven / SR
    fuerte = int(np.argmax(db > pk - 30)); a = int(idx[0]); tope = int(.18 / dt)
    if fuerte - a > tope:                              # hay aire antes de la voz: se empieza donde la voz sube, sin comerse una «s» inicial
        a = fuerte
        while a > 0 and fuerte - a < tope and voz[a - 1]: a -= 1
    a_m = max(a * ven - int(pre * SR), 0); fin_v = (int(idx[-1]) + 1) * ven; trozos = []; ini = a_m; i = a; mx = int(pausa_max / dt); cola = int(.40 / dt); ante = int(.30 / dt)
    while i <= idx[-1]:
        if not voz[i]:
            j = i
            while j <= idx[-1] and not voz[j]: j += 1
            if j - i > mx:
                trozos.append((ini, (i + cola) * ven)); ini = (j - ante) * ven
            i = j
        else: i += 1
    b = min(fin_v + int(post * SR), len(x)); trozos.append((ini, b)); xf = int(.012 * SR); out = np.zeros(0, np.float32)
    for s, e in trozos:
        y = x[s:e].copy()
        if len(out) >= xf and len(y) >= xf:
            r = np.linspace(0, 1, xf, dtype=np.float32); y[:xf] = y[:xf] * r + out[-xf:] * (1 - r); out = out[:-xf]
        out = np.concatenate([out, y])
    k = int(.003 * SR); out[:k] *= np.linspace(0, 1, k, dtype=np.float32)
    falta = fin_v + int(post * SR) - b; k = int(.06 * SR) if falta > 0 and rms_db(out[-480:], 480).max() > pk - 60 else int(.02 * SR)
    out[-k:] *= np.linspace(1, 0, k, dtype=np.float32)
    return np.concatenate([out, np.zeros(max(falta, 0), np.float32)])


def fin_voz(x, umbral=UMBRAL_COLA):
    """s donde la voz cae a `umbral` por última vez: el final completo de la última palabra."""
    db = rms_db(x, 240); return (int(np.where(db > db.max() + umbral)[0][-1]) + 1) * 240 / SR


def sin_etiquetas(t):
    return re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", " ", t)).strip()


def validar_tts(tts, disp=None):
    """Antes de gastar. Pausas con etiqueta y pausas con puntos suspensivos no se mezclan en un guion; el texto hablado debe ser el del guion."""
    if re.search(r"\[[^\]]*pause[^\]]*\]", tts, re.I) and re.search(r"\.\.\.|…", tts): sys.exit("tts mezcla [pause] con puntos suspensivos: usa solo uno de los dos. No gasté nada.")
    if disp and V.norm(sin_etiquetas(tts)) != V.norm(E.tts(disp)): print(f"  OJO: el tts no dice lo mismo que el texto:\n    tts   {V.norm(sin_etiquetas(tts))}\n    texto {V.norm(E.tts(disp))}")


def gasto_v4(d):
    """Caracteres de v4 en esta carpeta. Lo gastado antes con v2 no cuenta para el tope."""
    f = Path(d) / "eleven_gasto.json"
    return sum(c["caracteres"] for c in json.loads(leer_texto(f)).get("llamadas_es", []) if c.get("modelo") == MODELO) if f.exists() else 0


def _expandir(w):
    return V.norm(E.tts(w)).split() or [""]


def tramos_de_voz(x, hueco=.18, umbral=-40):
    """[(s0, s1)] de voz continua, separados por silencios ≥ hueco (un cierre de consonante dura menos)."""
    ven = 240; dt = ven / SR; db = rms_db(x, ven); voz = db > db.max() + umbral; res = []; i = 0; n = len(voz); ini = None; ult = None
    while i < n:
        if voz[i]:
            if ini is None: ini = i
            ult = i
        elif ini is not None and (i - ult) * dt >= hueco:
            res.append((ini, ult)); ini = None
        i += 1
    if ini is not None: res.append((ini, ult))
    return [(max(a * dt - .02, 0.0), min((b + 1) * dt + .02, len(x) / SR)) for a, b in res]


def marcas(linea_x, display):
    """Marcas por palabra (mlx_whisper) mapeadas a las palabras TAL COMO SE VEN. Whisper puede escribir 1000 por «mil»: se comparan normalizadas."""
    import difflib
    from transcriptor import transcribe as _tr
    # Con pausas reales Whisper reparte mal las marcas: en «video [pausa] es una» daba a «es» 0.65 s que eran la cola de «video» y el silencio. Por eso se transcribe cada tramo de voz por separado:
    # una palabra no puede cruzar un silencio, y la última de cada tramo termina donde termina su energía.
    PAD = .4; tok = []; x16 = decod_arr(linea_x)
    tramos = tramos_de_voz(linea_x)
    for a_, b_ in tramos:
        z = np.concatenate([np.zeros(int(PAD * 16000), np.float32), x16[int(a_ * 16000):int(b_ * 16000)], np.zeros(int(PAD * 16000), np.float32)])     # Whisper marca mal si la voz arranca en la muestra 0
        r = _tr(z, language="es", temperature=0.0, word_timestamps=True, condition_on_previous_text=False, initial_prompt=" ".join(display)); n0 = len(tok)
        for sg in r["segments"]:
            for w in sg.get("words", []):
                for n in (V.norm(w["word"]).split() or []): tok.append((n, min(max(float(w["start"]) - PAD + a_, a_), b_), min(max(float(w["end"]) - PAD + a_, a_), b_)))
        if len(tok) > n0: tok[-1] = (tok[-1][0], tok[-1][1], b_)
    esp = []
    for i, d in enumerate(display):
        for n in _expandir(d): esp.append((n, i))
    sm = difflib.SequenceMatcher(a=[t[0] for t in tok], b=[e[0] for e in esp], autojunk=False)
    ini = [None] * len(display); fin = [None] * len(display)
    for bl in sm.get_matching_blocks():
        for k in range(bl.size):
            t, (_, i) = tok[bl.a + k], esp[bl.b + k]
            if ini[i] is None: ini[i] = t[1]
            fin[i] = t[2]
    dur = len(linea_x) / SR; n = len(display)
    # huecos: interpola por caracteres entre vecinos conocidos
    for i in range(n):
        if ini[i] is None:
            a = next((fin[j] for j in range(i - 1, -1, -1) if fin[j] is not None), 0.0); bj = next((j for j in range(i + 1, n) if ini[j] is not None), None); b = ini[bj] if bj is not None else dur
            m = (bj if bj is not None else n) - i; ini[i] = a + (b - a) * 0 ; fin[i] = a + (b - a) / m
            libres = [q for q in tramos if q[0] >= a - .03 and q[1] <= b + .03]      # Whisper no oye una «y» suelta entre dos pausas, pero su tramo de voz está ahí sin dueño: esa es su marca
            if libres: ini[i] = libres[0][0]; fin[i] = ini[i] + (libres[-1][1] - ini[i]) / m
    # afina arranques con la energía: Whisper falla hasta 150 ms tras una pausa («Uno: mil», «año, o»). Si hay un borde de subida tras silencio
    # (≥ 50 ms bajo −28 dB del pico) a ±150 ms de la marca, ese es el arranque real.
    db = rms_db(linea_x, 96); dt = 96 / SR; bajo = db < db.max() - 28; bordes = []; run = 0
    for k, v in enumerate(bajo):
        if v: run += 1
        else:
            if run * dt >= .05: bordes.append(k * dt)
            run = 0
    orig = list(ini)
    for b_ in bordes:                                  # cada borde se asigna a UNA palabra: la de marca más cercana
        i = min(range(n), key=lambda k: abs(orig[k] - b_))
        if i > 0 and abs(orig[i] - b_) <= .15: ini[i] = b_
    for i in range(1, n):
        if ini[i] <= ini[i - 1]: ini[i] = ini[i - 1] + .06
    for i in range(n):
        if i + 1 < n: fin[i] = min(fin[i], ini[i + 1])
        if fin[i] <= ini[i]: fin[i] = ini[i] + .04
    fin[-1] = min(max(fin[-1], ini[-1] + .05), dur)
    return [dict(w=d, s=round(ini[i], 3), e=round(fin[i], 3)) for i, d in enumerate(display)]


def decod_arr(x):
    from math import gcd
    from scipy.signal import resample_poly
    return resample_poly(x, 1, 3).astype(np.float32)


def cadena_pro():
    """La cadena de locutor de herramientas/voz_pro.py (sin DeepFilterNet: la voz sintética no trae ruido)."""
    t = (MV / "herramientas" / "voz_pro.py").read_text(encoding="utf-8"); m = re.search(r"CADENA_EQ = \((.*?)\n\)", t, re.S)
    return "".join(re.findall(r'"([^"]*)"', m.group(1)))


def duraciones_falsas(x16, lit):
    """Whisper estira la marca de la palabra que sigue a una pausa («es» de 0.78 s tras [short pause]) y eso no es una vocal alargada. Se decide con la señal:
    mide el tramo CONTINUO de voz más largo (sobre −40 dB del pico) dentro de la marca; una vocal estirada es continua y una pausa la parte. Si cabe en el límite de verificar_es, el motivo se retira con su medida; si no, se queda."""
    ven = 80; db = rms_db(x16, ven); pk = db.max(); dt = ven / 16000; quedan = []; retirados = []; usados = {}
    for mot in lit["motivos"]:
        m = re.match(r"^(arranque alargado )?«(.+?)»( dura)? ([\d.]+) s$", mot)
        if not m: quedan.append(mot); continue
        w = m.group(2); cand = [p_ for p_ in lit["palabras"] if p_[0] == w and abs(p_[2] - float(m.group(4))) < .011]
        if not cand: quedan.append(mot); continue
        pal = cand[min(usados.get((w, m.group(4)), 0), len(cand) - 1)]; usados[(w, m.group(4))] = usados.get((w, m.group(4)), 0) + 1
        run = mx_ = 0
        for v_ in db[int(pal[1] / dt):int((pal[1] + pal[2]) / dt)] > pk - 40: run = run + 1 if v_ else 0; mx_ = max(mx_, run)
        voz = mx_ * dt; n = len(V.norm(w).replace(" ", ""))
        lim = .16 * n if m.group(1) else (.45 if n <= 4 else .9)
        if voz <= lim: retirados.append(dict(oido=[w], guion=[w], razon=f"marca de {pal[2]:.2f} s pero {voz:.2f} s de voz continua: es la pausa, no una vocal alargada"))
        else: quedan.append(f"{mot} ({voz:.2f} s con voz)")
    return quedan, retirados


NUMERALES = set("uno una dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince veinte treinta cuarenta cincuenta sesenta setenta ochenta noventa cien mil millon millones".split())


def medir_linea(path, esperado, recorte=0.0):
    """V.medir sobre la toma ya recortada + excepción de numerales."""
    import tempfile
    esperado = sin_etiquetas(esperado); d = tempfile.mkdtemp(); f = os.path.join(d, "l.wav"); x = decod(path); wav16(f, x[int(recorte * SR):])
    m = V.medir(f, esperado)
    if not m["literal"]["ok"]:
        quedan, ret = duraciones_falsas(V.audio16(f), m["literal"])
        if ret:
            m["literal"]["motivos"] = quedan; m["literal"]["ok"] = not quedan; m["motivos"] = [c for c in m["motivos"] if not c.startswith("LITERAL")] + ([f"LITERAL: {'; '.join(quedan)}"] if quedan else []); m["ok"] = not m["motivos"]; m["retirados"] = ret
    if not m["ok"] and m["p_es"] > .9 and V.norm(m["literal"]["texto"]) == V.norm(esperado):
        bajas = [w for w, p in m["palabras"] if p < .5]; lit = m["literal"]["motivos"]
        solo_num = all(re.match(r"^«(.+?)» prob", x_) and V.norm(re.match(r"^«(.+?)» prob", x_).group(1)) in NUMERALES for x_ in lit)
        if solo_num and all((V.norm(w).split() or [""])[0] in NUMERALES for w in bajas):
            m["ok"] = True; m["motivos"] = []; m["excepcion"] = "numerales: literal igual al guion"
    return m


def masterizar(proy, x, pal):
    crudo = proy / "voz-seca.wav"; wav16(crudo, x)
    r = subprocess.run([FF, "-v", "error", "-y", "-i", str(crudo), "-af", cadena_pro(), "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s24le", str(proy / "voz.wav")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode: raise RuntimeError(r.stderr[-600:])
    (proy / "palabras.json").write_text(json.dumps(pal, ensure_ascii=False, indent=0), encoding="utf-8")


def _canon(w):
    """Misma pronunciación en español de México: h muda, b=v, s=c=z, ll=y."""
    w = re.sub(r"c([ei])", r"s\1", w.replace("h", "").replace("v", "b").replace("z", "s")); return w.replace("ll", "y")


MARCAS = {"cloudcode": "clodcod", "claudecode": "clodcod", "cloud": "clod", "claude": "clod", "app": "ap", "skill": "eskil", "studio": "estudio", "3d": "tresde", "pixel": "pixel", "cyberpunk": "ciberpunk", "skills": "eskils", "plugins": "plaguins", "plugin": "plaguin", "mcps": "emecepes", "github": "guitjab", "gitjap": "guitjab", "cloth": "clod", "whatsapp": "whatsapp", "discord": "discord"}     # Whisper las escribe en inglés aunque la toma diga «Clod», «ap», «eskil»


def comparar_literal(oido, esperado):
    """Compara palabra por palabra lo que Whisper oyó contra el guion. Toda diferencia es falla salvo que tenga razón escrita aquí:
    espacios («porque» / «por qué»), cifras, homófonos, y una «s» final fundida con la «s» de la palabra siguiente. Una palabra que se oye a medias nunca pasa."""
    import difflib
    a, b = V.norm(oido).split(), V.norm(esperado).split(); fallas = []; aceptadas = []
    for op, i0, i1, j0, j1 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op == "equal": continue
        ga, ge = a[i0:i1], b[j0:j1]; ja, je = "".join(ga), "".join(ge); sig = b[j1] if j1 < len(b) else ""
        if ja == je: aceptadas.append(dict(oido=ga, guion=ge, razon="solo espacios")); continue
        if ga and ge and all(w in NUMERALES for w in ga + ge): aceptadas.append(dict(oido=ga, guion=ge, razon="cifra")); continue
        if _canon(ja) == _canon(je): aceptadas.append(dict(oido=ga, guion=ge, razon="homófonos")); continue
        if MARCAS.get(ja) == je: aceptadas.append(dict(oido=ga, guion=ge, razon="marca en inglés: el guion la escribe como se pronuncia")); continue
        if ja and je == ja + "s" and sig.startswith("s"): aceptadas.append(dict(oido=ga, guion=ge, razon="s fundida con la s siguiente")); continue
        if ja and len(ja) < len(je) and je.startswith(ja): fallas.append(f"TRUNCADA «{' '.join(ga)}» por «{' '.join(ge)}»")
        elif not ga: fallas.append(f"falta «{' '.join(ge)}»")
        elif not ge: fallas.append(f"sobra «{' '.join(ga)}»")
        else: fallas.append(f"distinta «{' '.join(ga)}» por «{' '.join(ge)}»")
    return fallas, aceptadas


def verificar_final(proy, g=None):
    """Pasada LITERAL sobre el voz.wav ya terminado, no sobre la toma cruda: ahí se ve lo que cortó el armado. Deja voz-verificacion.json, que el QA exige y compara por sha1."""
    g = g or json.loads(leer_texto(proy / "guion.json")); esperado = sin_etiquetas(" ".join(ln.get("tts") or E.tts(ln["texto"]) for ln in g["lineas"]))
    x = V.audio16(str(proy / "voz.wav")); x = np.concatenate([np.zeros(6400, np.float32), x, np.zeros(16000, np.float32)])    # sin relleno Whisper pierde la cola de la última palabra
    lit = V.literal(x, esperado); db = rms_db(x, 80); pk = db.max(); dt = 80 / 16000; oido = []; alucinadas = []
    for w, a0, d, p_ in lit["palabras"]:                                # en el silencio del relleno Whisper inventa palabras («Gracias.»). Solo se descarta si esa marca no tiene energía de voz.
        if (db[int(a0 / dt):int((a0 + d) / dt) + 1] > pk - 45).any(): oido.append(w)
        else: alucinadas.append(dict(oido=[w], guion=[], razon=f"sin energía de voz en {a0:.2f}-{a0 + d:.2f} s: Whisper la inventó en silencio"))
    lit["motivos"] = [m for m in lit["motivos"] if not any(f"«{a['oido'][0]}»" in m for a in alucinadas)]
    lit["motivos"] = [m for m in lit["motivos"] if not (" prob " in m and any(f"«{k}" in m.lower() for k in MARCAS))]     # Whisper duda en las marcas en inglés; la palabra se compara abajo
    texto = " ".join(oido); fallas, acept = comparar_literal(texto, esperado); quedan, ret = duraciones_falsas(x, lit); acept += alucinadas + ret
    resto = [m for m in quedan if not m.startswith("nº de palabras") and not (re.match(r"^«(.+?)» prob", m) and (V.norm(re.match(r"^«(.+?)» prob", m).group(1)).split() or [""])[0] in NUMERALES)]
    rep = dict(ok=not fallas and not resto, sha1=hashlib.sha1((proy / "voz.wav").read_bytes()).hexdigest(), modelo=MODELO, literal=texto, fallas=fallas, motivos=resto, aceptadas=acept, palabras=lit["palabras"])
    (proy / "voz-verificacion.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"pasada literal de voz.wav: {'OK' if rep['ok'] else 'FALLA'}" + (f" · {fallas + resto}" if not rep["ok"] else "") + (f" · aceptadas {[(a['oido'], a['razon']) for a in acept]}" if acept else "") + f"\n  «{texto}»")
    return rep


def armar(proy, g, lineas):
    A = proy / "audio"; pausa = g.get("pausa_s", .20); pm = g.get("pausa_max_s", .30); bloques = []; pal = []; t = 0.0; L = A / "lineas"
    for i, ln in lineas:
        x0 = decod(L / f"{i:02d}-raw.mp3")[int(ln.get("recorte_ini", 0) * SR):]; x = recortar(x0, pm); disp = ln["texto"].split()       # con puntuación: cada subtítulo decide si la muestra
        ms = marcas(x, disp); ms[-1]["e"] = round(max(ms[-1]["s"] + .05, fin_voz(x)), 3)
        for m in ms: pal.append(dict(w=m["w"], s=round(m["s"] + t, 3), e=round(m["e"] + t, 3), linea=i))
        bloques.append(x); t += len(x) / SR
        bloques.append(np.zeros(int(pausa * SR), np.float32)); t += pausa
    voz = np.concatenate(bloques[:-1]); pal[0]["s"] = 0.0; masterizar(proy, voz, pal)
    print(f"voz.wav {len(voz) / SR:.2f} s · {len(pal)} palabras · {g.get('pausa_s', .2)} s entre líneas")
    verificar_final(proy, g)


def corrida(proy, g, cmd="generar", intentos=1):
    """TOMA CORRIDA (regla fija): cuando habla una sola voz, TODO el guion se genera en UNA toma, sin next_text.
    Generar por líneas y pegarlas deja silencios digitales entre frases y «ecos» de palabras incompletas (next_text hace que el clon
    empiece a decir la palabra siguiente al final de la toma). Las pausas son las que la voz hace al respirar; solo se acortan las largas."""
    A = proy / "audio" / "corrida"; os.makedirs(A, exist_ok=True); lineas = g["lineas"]; who = lineas[0].get("who", "D")
    disp = " ".join(ln["texto"] for ln in lineas); tts = " ".join(ln.get("tts") or E.tts(ln["texto"]) for ln in lineas); validar_tts(tts, disp)
    fv = A / "verificacion.json"; rep = json.loads(leer_texto(fv)) if fv.exists() else {}; raw = A / "lineas" / "01-raw.mp3"; tope = g.get("tope_caracteres", TOPE_VIDEO)
    print(f"{proy.name}: TOMA CORRIDA {MODELO} · {len(tts)} caracteres · gastado en v4 {gasto_v4(A)} · tope {tope}")
    if cmd == "saldo": print("saldo ElevenLabs:", E.saldo()); return
    if cmd != "armar" and not (rep.get("ok") and rep.get("tts") == tts and rep.get("modelo") == MODELO and raw.exists()):
        import random
        if len(tts) > E.saldo(): sys.exit("No cabe en el saldo de ElevenLabs.")
        E.CTX = {"previous_text": g["previous_text"]} if g.get("previous_text") else {}    # sin contexto (así suena más natural). Si una toma arranca con «Eh», recorte_ini (gratis). Nunca next_text.
        mejor = None
        for j in range(intentos):
            if gasto_v4(A) + len(tts) > tope: print("  (tope del video: sin más tomas)"); break
            seed = random.randint(1, 2 ** 31 - 1)
            E.crudo(str(A), 1, who, disp, seed=seed, forzar=True, texto=tts)
            m = medir_linea(raw, tts); nm = len(m["motivos"])
            print(f"  toma {j} {'OK ' if m['ok'] else 'MAL'} es={m['p_es']:.3f} «{m['literal']['texto']}»" + ("" if m["ok"] else "  ← " + " | ".join(m["motivos"])))
            if mejor is None or nm < mejor[0]: mejor = (nm, raw.read_bytes(), m)
            if m["ok"]: break
        if mejor:
            raw.write_bytes(mejor[1]); rep = dict(ok=mejor[2]["ok"], tts=tts, modelo=MODELO, n_motivos=mejor[0], motivos=mejor[2]["motivos"], literal=mejor[2]["literal"]["texto"], p_es=mejor[2]["p_es"])
            fv.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    elif cmd == "armar" and raw.exists() and rep.get("tts") == tts and rep.get("modelo") == MODELO and not rep.get("ok"):      # gratis: re-mide la toma ya pagada con las reglas vigentes
        m = medir_linea(raw, tts); rep.update(ok=m["ok"], n_motivos=len(m["motivos"]), motivos=m["motivos"], literal=m["literal"]["texto"], p_es=m["p_es"], retirados=m.get("retirados", [])); fv.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    x = recortar(decod(raw)[int(g.get("recorte_ini", 0) * SR):], g.get("pausa_max_s", PAUSA_MAX))
    pal_d = disp.split(); ids = [i for i, ln in enumerate(lineas, 1) for _ in ln["texto"].split()]; pal = [dict(w=m["w"], s=m["s"], e=m["e"], linea=ids[k]) for k, m in enumerate(marcas(x, pal_d))]
    pal[0]["s"] = 0.0; pal[-1]["e"] = round(max(pal[-1]["s"] + .05, fin_voz(x)), 3)      # el cierre se cuenta desde el final completo de la última palabra, no desde la marca de Whisper
    masterizar(proy, x, pal)
    print(f"voz.wav {len(x) / SR:.2f} s · {len(pal)} palabras · toma corrida · verificación de la toma: {'OK' if rep.get('ok') else rep.get('motivos')}")
    verificar_final(proy, g)


def main():
    proy = Path(sys.argv[1]).resolve(); cmd = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "generar"
    g = json.loads(leer_texto(proy / "guion.json")); A = str(proy / "audio"); tope = g.get("tope_caracteres", TOPE_VIDEO); intentos = int(sys.argv[sys.argv.index("--intentos") + 1]) if "--intentos" in sys.argv else 1
    if cmd == "verificar": return verificar_final(proy, g)
    if g.get("modo", "corrida" if len({l.get("who", "D") for l in g["lineas"]}) == 1 else "lineas") == "corrida": return corrida(proy, g, cmd, intentos)
    lineas = list(enumerate(g["lineas"], 1)); os.makedirs(A, exist_ok=True); fv = proy / "audio" / "verificacion.json"; rep = json.loads(leer_texto(fv)) if fv.exists() else {}
    tx = lambda ln: ln.get("tts") or E.tts(ln["texto"])
    gasto = lambda: gasto_v4(A)
    vigente = lambda fi, ln: fi and fi.get("guion") == ln["texto"] and fi.get("modelo") == MODELO and fi.get("texto") == tx(ln)     # una toma de v2 o con otro tts no sirve
    validar_tts(" ".join(tx(ln) for _, ln in lineas))
    por = sum(len(tx(ln)) for i, ln in lineas if not vigente(E.ficha(A, i), ln))
    print(f"{proy.name}: {sum(len(tx(l)) for _, l in lineas)} caracteres de guion · por generar {por} · gastado en v4 {gasto()} · tope {tope}")
    if cmd == "saldo": print("saldo ElevenLabs:", E.saldo()); return
    if cmd == "armar": armar(proy, g, lineas); return
    rehacer = {int(x) for x in sys.argv[3].split(",")} if cmd == "rehacer" else set()
    if por + gasto() > tope: sys.exit("No cabe en el tope del video: no genero nada.")
    if por and por > E.saldo(): sys.exit("No cabe en el saldo de ElevenLabs.")
    for k, (i, ln) in enumerate(lineas):
        E.CTX = {"previous_text": sin_etiquetas(tx(lineas[k - 1][1])) if k else None}   # sin next_text: deja «ecos» de la palabra siguiente al final de la toma
        pendiente = rep.get(str(i), {}); fi = E.ficha(A, i); rec = ln.get("recorte_ini", 0)
        if "toma" in ln:
            E.restaurar(A, i, ln["toma"]); fi = E.ficha(A, i); ln_txt = fi.get("texto") or tx(ln)
            m = medir_linea(os.path.join(A, "lineas", f"{i:02d}-raw.mp3"), ln_txt, rec)
            print(f"  {i:02d} toma {ln['toma']} {'OK ' if m['ok'] else 'MAL'} {m.get('excepcion', '')} «{m['literal']['texto']}»" + ("" if m["ok"] else "  ← " + " | ".join(m["motivos"])))
            rep[str(i)] = dict(ok=m["ok"], motivos=m["motivos"], p_es=m["p_es"], literal=m["literal"]["texto"], toma=ln["toma"], recorte_ini=rec, excepcion=m.get("excepcion")); fv.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8"); continue
        if i not in rehacer and pendiente.get("ok") and vigente(fi, ln): print(f"  {i:02d} ya verificada"); continue
        planes = [(s, a) for s, a in V.plan(i, sin_etiquetas(tx(ln)))]; mejor = None
        if i in rehacer or (fi and not vigente(fi, ln)): planes = planes[1:]
        for j, (seed, alt) in enumerate(planes[:intentos]):
            t = tx(ln) if not alt or "[" in tx(ln) else alt; forzar = seed is not None
            if forzar and gasto() + len(t) > tope: print("  (tope: sin más reintentos)"); break
            E.crudo(A, i, ln.get("who", "D"), ln["texto"], seed=seed, forzar=forzar, texto=t)
            m = medir_linea(os.path.join(A, "lineas", f"{i:02d}-raw.mp3"), (E.ficha(A, i) or {}).get("texto") or t, rec)
            print(f"  {i:02d} {'OK ' if m['ok'] else 'MAL'} es={m['p_es']:.3f} pmin={m['p_palabra_min']:.2f} «{m['texto_es']}»" + ("" if m["ok"] else "  ← " + " | ".join(m["motivos"])))
            rep[str(i)] = dict(ok=m["ok"], motivos=m["motivos"], p_es=m["p_es"], literal=m["literal"]["texto"], intentos=j + 1)
            fv.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
            if m["ok"]: break
    fallas = [k for k, v in rep.items() if not v["ok"]]
    print("Gastado en este video:", gasto(), "· fallas:", fallas or "ninguna")
    armar(proy, g, lineas)


if __name__ == "__main__":
    main()
