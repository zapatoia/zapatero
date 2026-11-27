"""Verifica (y regenera si falla) que CADA línea de voz de un episodio sea español correcto — 14 oct 2026.

  (módulo interno: lo usa nucleo/voz.py)

Por cada línea del guion (scripts/guion.py) obtiene su audio con eleven_es.crudo() (lo genera solo si falta) y lo mide con
Whisper large-v3-turbo (mlx-whisper en Mac Apple, faster-whisper en lo demás) en DOS pasadas:
  1) language=None → probabilidad de español del detector de idioma (debe ser > 0.9) + idioma ganador.
  2) language='es' con palabras → texto normalizado (minúsculas, sin signos, cifras en palabras, sin acentos y con
     equivalencias fonéticas Clod≈Claude, Códex≈Codex, oquéi≈OK) igual al guion, y NINGUNA palabra < 0.5 de probabilidad.
Si falla, regenera con otra semilla (y en el último intento con una variante de puntuación) hasta --intentos.
Reporte: audio/verificacion_es.json.
"""
import json, os, re, subprocess, sys, unicodedata
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eleven_es as E

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ffruta import ffmpeg, leer_texto   # JSON en UTF-8 (Windows)
FF = ffmpeg()
REPO = 'whisper-large-v3-turbo'
_M = {}


def audio16(path):
    out = subprocess.run([FF, '-v', 'error', '-i', path, '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(out, np.int16).astype(np.float32) / 32768


from transcriptor import prob_idioma, transcribe as _tr  # noqa: E402


EQUIV = {  # formas que Whisper puede escribir para la MISMA pronunciación en español
    'claude': 'clod', 'clod': 'clod', 'clot': 'clod', 'clodd': 'clod', 'klod': 'clod',
    'codex': 'codex', 'kodex': 'codex', 'kodeks': 'codex', 'codeks': 'codex',
    'oquei': 'oquei', 'okey': 'oquei', 'ok': 'oquei', 'okay': 'oquei', 'oke': 'oquei', 'oquey': 'oquei', 'okei': 'oquei',
    'yutub': 'yutub', 'youtube': 'yutub', 'yutube': 'yutub',
    'mmm': 'mmm', 'mm': 'mmm', 'mmmm': 'mmm', 'hmm': 'mmm', 'mhm': 'mmm', 'em': 'mmm', 'hm': 'mmm',
    'prou': 'pro', 'pro': 'pro', 'cardio': 'cardio',
    # 15 oct 2026 (reels con la voz clonada): el TTS lee «rils/cheklist» y Whisper escribe la ortografía inglesa (misma pronunciación)
    'reels': 'rils', 'rils': 'rils', 'reel': 'ril', 'checklist': 'cheklist', 'cheklist': 'cheklist',
    # 7 nov 2026 (reel3d «links de skills»): el TTS dice «eskils/plaguins/eme ce pes/guit jab» y Whisper escribe la ortografía inglesa
    'skills': 'eskils', 'eskils': 'eskils', 'eskills': 'eskils', 'skill': 'eskil', 'eskil': 'eskil', 'esquil': 'eskil', 'eskill': 'eskil',
    'plugins': 'plaguins', 'plaguins': 'plaguins', 'plagins': 'plaguins', 'plugin': 'plaguin', 'plaguin': 'plaguin', 'plagin': 'plaguin',
    'mcps': 'eme ce pes', 'emecepes': 'eme ce pes', 'github': 'guit jab', 'guitjab': 'guit jab', 'gitjab': 'guit jab', 'githab': 'guit jab', 'guithub': 'guit jab', 'gitjap': 'guit jab', 'guitjap': 'guit jab', 'cloud': 'clod', 'cloth': 'clod',
    'whatsapp': 'whatsapp', 'whatsap': 'whatsapp', 'wasap': 'whatsapp', 'guatsap': 'whatsapp',
}


def norm(t):
    t = re.sub(r'(\d+):00', r'\1', t)
    t = re.sub(r'\b(\d+)\s*[dD]\b', r'\1 de', t)          # 7 nov 2026: «3D» se dice «tres de» (Whisper escribe 3D)
    t = re.sub(r'(\d+)[.,](\d{1,2})(?!\d)', lambda m: f' {E.numero(m.group(1))} punto {" ".join(E.numero(c) for c in m.group(2))} ', t)
    t = re.sub(r'(\d+(?:[.,]\d{3})*)', lambda m: ' ' + E.numero(m.group(1).replace(',', '').replace('.', '')) + ' ', t)
    t = t.replace('%', ' por ciento ')
    t = unicodedata.normalize('NFD', t.lower())
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    t = re.sub(r"[^a-zñ ]+", ' ', t)
    t = re.sub(r'\b(cv|cb|ceve|seve)\b', 'se ve', t)
    t = re.sub(r'\bpe de efe\b', 'pdf', t)              # ep. 8: el TTS dice «pe de efe» y Whisper escribe «PDF» (misma pronunciación)   # seseo + b = v: «CV/CB» es como se oye «se ve» en español latino
    w = [EQUIV.get(p, p) for p in t.split()]
    # «mmm» repetido o pegado se cuenta una vez
    out = []
    for p in w:
        if p == 'mmm' and out and out[-1] == 'mmm': continue
        out.append(p)
    return ' '.join(out)


PROMPT_LIT = 'Eh, y, y quinto... este, mmm, eh, ehhh. Transcripción literal con muletillas, repeticiones y titubeos.'
MULETILLAS = {'eh', 'ehh', 'ehhh', 'eeh', 'este', 'mmm', 'ah', 'ahh', 'em', 'emm', 'mm', 'hmm', 'mhm', 'o sea'}


ACENTO = {'que', 'como', 'cuando', 'donde', 'quien', 'cual', 'cuanto', 'mas', 'si', 'tu', 'el', 'mi', 'solo', 'aun'}


def literal(x, esperado, ref=None):
    """Corrección real (se oyeron titubeos «Y, y quinto», «Leeee»): Whisper normal LIMPIA los titubeos. Pasada LITERAL con prompt de
    muletillas. Falla si: palabra repetida consecutiva que no está en el guion · muletilla de más · palabra ≤ 4 letras
    > 0.45 s o cualquiera > 0.9 s · vocal estirada (3+ iguales) · prob < 0.5 · nº de palabras distinto al guion ·
    primera palabra alargada (> 0.16 s por letra)."""
    r = _tr(x, language='es', temperature=0.0, word_timestamps=True,
                               condition_on_previous_text=False, initial_prompt=PROMPT_LIT)
    ws = [(w['word'].strip(), float(w['start']), float(w['end']), float(w['probability'])) for sg in r['segments'] for w in sg.get('words', [])]
    esp = norm(esperado).split(); got = norm(' '.join(w[0] for w in ws)).split()
    mot = []
    pega_ = lambda t: ''.join(t)
    if len(got) != len(esp) and pega_(got) != pega_(esp): mot.append(f'nº de palabras {len(got)} ≠ {len(esp)}')
    for a_, b_ in zip(got, got[1:]):
        if a_ == b_ and f'{a_} {b_}' not in ' '.join(esp): mot.append(f'repetida «{a_} {b_}»')
    from collections import Counter
    ce, cg = Counter(esp), Counter(got)
    for m_ in MULETILLAS:
        m2 = EQUIV.get(m_, m_)
        if cg[m2] > ce[m2]: mot.append(f'muletilla «{m2}»')
    for k_, (w, a0, a1, p) in enumerate(ws):
        n = norm(w).replace(' ', ''); d = a1 - a0
        if not n: continue
        if re.search(r'([aeiou])\1\1', unicodedata.normalize('NFD', w.lower())): mot.append(f'vocal estirada «{w}»')
        ultima = k_ == len(ws) - 1
        if len(n) <= 4 and d > 0.45 and not ultima: mot.append(f'«{w}» dura {d:.2f} s')
        if d > 0.9: mot.append(f'«{w}» dura {d:.2f} s')
        if p < 0.5:
            # «que/qué», «tu/tú»…: el prompt literal no trae acentos y Whisper reparte la probabilidad entre las dos grafías
            # (MISMO sonido). Vale si en la pasada normal esa misma aparición tiene prob ≥ 0.5.
            occ = sum(1 for w_, *_ in ws[:k_] if norm(w_).replace(' ', '') == n)
            rp = [pp for ww_, pp in (ref or []) if norm(ww_).replace(' ', '') == n]
            if not (n in ACENTO and occ < len(rp) and rp[occ] >= 0.5): mot.append(f'«{w}» prob {p:.2f}')
    if ws:
        w, a0, a1, p = ws[0]; n = norm(w).replace(' ', '')
        if n and (a1 - a0) / len(n) > 0.16 and (a1 - a0) > 0.30: mot.append(f'arranque alargado «{w}» {a1 - a0:.2f} s')
    return {'ok': not mot, 'motivos': mot, 'texto': r['text'].strip(), 'palabras': [(w, round(a0, 2), round(a1 - a0, 2), round(p, 2)) for w, a0, a1, p in ws]}


def medir(path, esperado):
    """Mide un audio contra el texto esperado. Devuelve dict con todas las métricas y 'ok'."""
    x = audio16(path)
    p_es, top = prob_idioma(x)
    r1 = _tr(x, language=None, temperature=0.0, condition_on_previous_text=False)
    r2 = _tr(x, language='es', temperature=0.0, word_timestamps=True,
                                condition_on_previous_text=False)
    words = [(w['word'].strip(), round(float(w['probability']), 3)) for s in r2['segments'] for w in s.get('words', [])]
    lp = [s['avg_logprob'] for s in r2['segments']]
    txt2 = r2['text'].strip(); n_esp = norm(esperado); n_got = norm(txt2)
    pega = lambda t: re.sub(r's+', 's', t.replace(' ', '').replace('cientas', 'cientos'))   # (+ «400» = cuatrocientas/os)   # «llevabas seis» = «llevaba seis»: la s final se funde con la s siguiente
    coincide = n_esp == n_got or n_esp.replace(' ', '') == n_got.replace(' ', '') or pega(n_esp) == pega(n_got)
    if not coincide and words:
        # Whisper a veces se come la PRIMERA palabra antes de una pausa («Códex. ¿Qué hiciste?» → «¿Qué hiciste?»):
        # se parte el audio en la primera pausa ≥ 0.25 s (energía en ventanas de 50 ms) y se transcribe cada tramo.
        e = np.array([np.sqrt(np.mean(x[i:i + 800] ** 2)) for i in range(0, len(x), 800)])
        habla = np.where(e > 0.03)[0]; corte = None
        if len(habla):
            k = habla[0]
            while k < len(e) - 5:
                if e[k] < 0.012 and np.all(e[k:k + 5] < 0.012) and np.any(e[k + 5:] > 0.03): corte = k + 2; break
                k += 1
        if corte:
            partes = [x[:corte * 800], x[corte * 800:]]; tx, ws = [], []
            for xp in partes:
                rp = _tr(xp, language='es', temperature=0.0, word_timestamps=True,
                                            condition_on_previous_text=False)
                tx.append(rp['text'].strip()); ws += [(w['word'].strip(), round(float(w['probability']), 3)) for sg in rp['segments'] for w in sg.get('words', [])]
            n2 = norm(' '.join(tx))
            if n2 == n_esp or pega(n2) == pega(n_esp):
                txt2 = ' '.join(tx); n_got = n2; words = ws; coincide = True
    pmin = min([p for _, p in words], default=0.0)
    bajas = [(w, p) for w, p in words if p < 0.5]
    lit = literal(x, esperado, words)
    ok = p_es > 0.9 and coincide and not bajas and lit['ok']
    motivos = []
    if p_es <= 0.9: motivos.append(f'idioma: es={p_es:.3f} {top}')
    if not coincide: motivos.append(f'texto: «{n_got}» ≠ «{n_esp}»')
    if bajas: motivos.append(f'palabras < 0.5: {bajas}')
    if not lit['ok']: motivos.append('LITERAL: ' + '; '.join(lit['motivos']) + f" «{lit['texto']}»")
    return {'ok': ok, 'p_es': round(p_es, 4), 'top_idiomas': top, 'idioma_pasada1': r1.get('language'),
            'texto_pasada1': r1['text'].strip(), 'texto_es': txt2, 'esperado_norm': n_esp, 'obtenido_norm': n_got,
            'coincide': coincide, 'avg_logprob': round(float(np.mean(lp)) if lp else -9, 3), 'p_palabra_min': pmin,
            'palabras': words, 'literal': lit, 'duracion_s': round(len(x) / 16000, 3), 'motivos': motivos}


def variante(t):
    """Reescritura para el último intento: «pro» → «prou»; si no, otra puntuación (misma frase, otra prosodia)."""
    if re.search(r'\b[Pp]ro\b', t): return re.sub(r'\b([Pp])ro\b', r'\1rou', t)
    if t.endswith('...'): return t
    if ', ' in t: return t.replace(', ', '... ', 1)
    if t.endswith('.') and len(t) < 16: return '¡' + t[:-1] + '!'
    return t


ALT = {'Códex.': ['Códecs.', 'Kódex.'], 'Se ve pro.': ['¡Se ve pro!', 'Se ve pro...'], 'Listo.': ['¡Listo!', 'Listo...']}
BANCO = os.path.join(E.MV, '.cache', 'banco_voz')   # banco local de tomas ya pagadas


def nombres(txt):
    w = re.findall(r'\w+', E.tts(txt)); return len(w) <= 4 and sum(p in ('Clod', 'Códex') for p in w) >= 2


def corta(txt):
    return len(txt) <= 15


def plan(i, txt):
    """Intentos (seed, texto) por línea: la toma base + 2 reintentos (semilla nueva; el último con variante de
    puntuación / «prou»). Semillas al azar (registradas en la ficha): repetir una semilla daría el mismo audio."""
    import random
    base = E.tts(txt); sd = lambda: random.randint(1, 2 ** 31 - 1)
    alt = ([a for a in ALT.get(base, []) if a != base] + [variante(base)])[0] if corta(txt) else variante(base)
    return [(None, None), (sd(), None), (sd(), alt)]


def pasa_corta(m):
    return m['coincide'] and m['p_palabra_min'] >= 0.5 and m.get('literal', {}).get('ok', True)


def banco_get(who, txt):
    f = os.path.join(BANCO, 'index.json'); idx = json.loads(leer_texto(f)) if os.path.exists(f) else {}
    return idx.get(f'{who}|{txt}'), idx


def banco_put(A, i, who, txt, m):
    import shutil
    os.makedirs(BANCO, exist_ok=True); e, idx = banco_get(who, txt)
    if e and e['p_es'] >= m['p_es'] and e['ok'] >= m['ok']: return
    key = f'{who}|{txt}'; nom = f'{len(idx):03d}' if not e else e['nom']
    shutil.copy(os.path.join(A, 'lineas', f'{i:02d}-raw.mp3'), os.path.join(BANCO, nom + '.mp3'))
    shutil.copy(os.path.join(A, 'lineas', f'{i:02d}-raw.json'), os.path.join(BANCO, nom + '.json'))
    idx[key] = {'nom': nom, 'p_es': m['p_es'], 'ok': m['ok'], 'origen': f'{os.path.basename(os.path.dirname(A))}#{i}'}
    json.dump(idx, open(os.path.join(BANCO, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def banco_usar(A, i, who, txt):
    """Copia al proyecto la toma ya verificada de otra línea idéntica (mismo personaje y texto): 0 caracteres."""
    import shutil
    e, _ = banco_get(who, txt)
    if not e: return False
    L = os.path.join(A, 'lineas'); I = os.path.join(L, 'intentos'); os.makedirs(I, exist_ok=True)
    k = len([f for f in os.listdir(I) if f.startswith(f'{i:02d}-') and f.endswith('.mp3')])
    for ext in ('.mp3', '.json'):
        shutil.copy(os.path.join(BANCO, e['nom'] + ext), os.path.join(I, f'{i:02d}-{k}{ext}'))
    E.restaurar(A, i, k); return e['origen']


def medir_linea(A, i, who, txt):
    fi = E.ficha(A, i) or {}
    path = os.path.join(A, 'lineas', f'{i:02d}-raw-x.wav' if who == 'X' else f'{i:02d}-raw.mp3')
    m = medir(path, fi.get('texto') or E.tts(txt)); m['seed'] = fi.get('seed'); m['texto_tts'] = fi.get('texto')
    I = os.path.join(A, 'lineas', 'intentos')
    m['intento'] = max([int(f[3:-4]) for f in os.listdir(I) if f.startswith(f'{i:02d}-') and f.endswith('.mp3')], default=None) if os.path.isdir(I) else None
    return m


def main():
    proj = os.path.abspath(sys.argv[1]); A = os.path.join(proj, 'audio')
    generar = '--sin-generar' not in sys.argv
    tope_ep = int(sys.argv[sys.argv.index('--tope') + 1]) if '--tope' in sys.argv else 1300
    sys.path.insert(0, os.path.join(proj, 'scripts'))
    from guion import LINEAS
    notas = set(); n = 0
    for i, ln in enumerate(LINEAS, 1):
        if ln[0] == 'SFX' or not ln[2]: continue
        E.tts(ln[2], notas); fi = E.ficha(A, i)
        if not (fi and fi.get('guion') == ln[2] and fi['modelo'] == E.MODELO and fi.get('voz', E.VOZ_DEFECTO) == E.VOCES[ln[0]]) and not banco_get(ln[0], ln[2])[0]: n += len(E.tts(ln[2]))
    g0 = E.gastado_tarea()
    print(f'{os.path.basename(proj)}: por generar ≈ {n} caracteres (sin reintentos) · gastado en la tarea {g0}')
    if n and generar:
        s = E.saldo(); print('saldo ElevenLabs:', s)
        if n > s or g0 + n > E.TOPE_TAREA: sys.exit('No cabe en el saldo/tope: no genero nada')
    rep = {'proyecto': os.path.basename(proj), 'modelo': E.MODELO, 'lang': None, 'whisper': REPO,
           'reglas': {'p_es_min': 0.9, 'p_palabra_min': 0.5, 'texto': 'igual al guion normalizado'},
           'reescrituras': sorted(notas), 'lineas': []}
    for i, ln in enumerate(LINEAS, 1):
        who, sub, txt = ln[:3]
        if who == 'SFX' or not txt: continue
        _v = [l for l in LINEAS if l[0] != 'SFX' and l[2]]; _k = _v.index(ln)
        E.CTX = {'previous_text': E.tts(_v[_k - 1][2]) if _k > 0 else None, 'next_text': E.tts(_v[_k + 1][2]) if _k + 1 < len(_v) else None}
        hist = []; fi = E.ficha(A, i); origen = None
        ya = fi and fi.get('guion') == txt and fi['modelo'] == E.MODELO and fi.get('voz', E.VOZ_DEFECTO) == E.VOCES[who] and fi['ajustes'] in (E.AJUSTES[who], E.AJUSTES_PREV.get(who))
        if not ya and corta(txt) and generar: origen = banco_usar(A, i, who, txt)
        if origen:   # toma del banco: si ya cumple (o es excepción de frase corta) no se gasta nada
            m = medir_linea(A, i, who, txt); m['de_banco'] = origen; hist.append(m)
            print(f"  {i:02d} {who} {'OK ' if m['ok'] else 'exc' if pasa_corta(m) else 'MAL'} es={m['p_es']:.3f} pmin={m['p_palabra_min']:.2f} «{m['texto_es']}» [banco {origen}]")
            ya = True
            if m['ok'] or pasa_corta(m): previos = None
        pasos = plan(i, txt)
        I = os.path.join(A, 'lineas', 'intentos')
        if hist and (hist[-1]['ok'] or pasa_corta(hist[-1])): pasos = []
        previos = [] if hist else sorted(int(f[3:-4]) for f in os.listdir(I) if f.startswith(f'{i:02d}-') and f.endswith('.mp3')) if os.path.isdir(I) else []
        if ya and len(previos) > 1:   # ya hay tomas pagadas: se miden todas (gratis) antes de gastar en otra
            for kk in sorted(previos, reverse=True):   # 15 oct: la toma más NUEVA primero (la regenerada a propósito)
                _fk = json.loads(leer_texto(os.path.join(I, f'{i:02d}-{kk}.json')))
                if _fk.get('guion') != txt or _fk.get('voz', E.VOZ_DEFECTO) != E.VOCES[who] or _fk.get('ajustes') not in (E.AJUSTES[who], E.AJUSTES_PREV.get(who)): continue
                E.restaurar(A, i, kk); m = medir_linea(A, i, who, txt); m['intento'] = kk; m['de_banco'] = None; hist.append(m)
                print(f"  {i:02d} {who} toma {kk}: {'OK ' if m['ok'] else 'MAL'} es={m['p_es']:.3f} pmin={m['p_palabra_min']:.2f} «{m['texto_es']}»")
                if m['ok']: break
            if hist and (hist[-1]['ok'] or (corta(txt) and any(pasa_corta(h) for h in hist))): pasos = []
            else: pasos = pasos[len(previos):] if len(previos) < len(pasos) else []   # las tomas ya pagadas cuentan como intentos
        for k, (seed, texto) in enumerate(pasos):
            if seed is None and texto is None:
                if not (ya or origen):
                    if not generar: break
                    E.crudo(A, i, who, txt)
            else:
                if not generar or E.gastado_tarea() - g0 >= tope_ep: print('  (tope de reintentos del episodio)'); break
                E.crudo(A, i, who, txt, seed=seed, forzar=True, texto=texto)
            m = medir_linea(A, i, who, txt); m['de_banco'] = origen if k == 0 else None; hist.append(m)
            print(f"  {i:02d} {who} {'OK ' if m['ok'] else 'MAL'} es={m['p_es']:.3f} lp={m['avg_logprob']:.2f} pmin={m['p_palabra_min']:.2f} «{m['texto_es']}»"
                  + (f' [banco {origen}]' if k == 0 and origen else '') + ('' if m['ok'] else '  ← ' + ' | '.join(m['motivos'])))
            if m['ok']: break
        if not hist: continue
        fin = hist[-1]; excepcion = None
        if not fin['ok']:
            # ninguna pasó: se queda la MEJOR toma (texto correcto y palabras ≥ 0.5 primero, luego mayor prob. de español)
            mejor = max(hist, key=lambda m: (m['coincide'] and m['p_palabra_min'] >= 0.5, m['coincide'], m['p_es'] + 0.3 * m['p_palabra_min']))
            if mejor is not fin and mejor['intento'] is not None: E.restaurar(A, i, mejor['intento'])
            fin = mejor
            solo_mmm = fin['coincide'] and fin['p_es'] > 0.9 and all(norm(w) == 'mmm' for w, p in fin['palabras'] if p < 0.5)
            if solo_mmm:
                excepcion = ('interjección «mmm»: Whisper siempre da baja confianza a un murmullo no léxico; '
                             'idioma > 0.9, texto igual al guion y todas las demás palabras ≥ 0.5')
            elif nombres(txt) and fin['coincide'] and fin['p_palabra_min'] >= 0.5:
                excepcion = ('línea dominada por nombres propios (Clod/Códex): el detector de idioma los toma por inglés; '
                             'texto y palabras sí pasan')
            elif corta(txt) and fin['coincide'] and fin['p_palabra_min'] >= 0.5:
                excepcion = ('frase corta: el detector de idioma de Whisper no es concluyente con 1–3 sílabas '
                             '(control: las voces nativas es_MX de macOS también dan p(es) < 0.9 con estas palabras); '
                             'texto y palabras sí pasan')
        if excepcion and not fin['literal']['ok']: excepcion = None   # titubeos/repeticiones NUNCA son excepción
        if corta(txt) and (fin['ok'] or (excepcion and 'frase corta' in excepcion)): banco_put(A, i, who, txt, fin)
        rep['lineas'].append({'i': i, 'who': who, 'subtitulo': sub, 'texto_tts': fin.get('texto_tts'), 'ok': fin['ok'],
                              'excepcion': excepcion, 'intentos': len(hist), 'final': fin,
                              'anteriores': [h for h in hist if h is not fin]})
    rep['ok'] = all(l['ok'] or l['excepcion'] for l in rep['lineas'])
    rep['resumen'] = {'lineas': len(rep['lineas']), 'ok_estricto': sum(l['ok'] for l in rep['lineas']),
                      'excepciones': [l['i'] for l in rep['lineas'] if not l['ok'] and l['excepcion']],
                      'fallas': [l['i'] for l in rep['lineas'] if not l['ok'] and not l['excepcion']],
                      'regeneradas': sum(l['intentos'] > 1 for l in rep['lineas']),
                      'p_es_min': min(l['final']['p_es'] for l in rep['lineas']),
                      'p_es_media': round(sum(l['final']['p_es'] for l in rep['lineas']) / len(rep['lineas']), 4),
                      'p_palabra_min': min(l['final']['p_palabra_min'] for l in rep['lineas']),
                      'caracteres_gastados_esta_corrida': E.gastado_tarea() - g0}
    json.dump(rep, open(os.path.join(A, 'verificacion_es.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('RESUMEN', rep['resumen'], 'TODO OK' if rep['ok'] else 'HAY FALLAS')


if __name__ == '__main__':
    main()
