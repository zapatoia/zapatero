"""ElevenLabs en ESPAÑOL correcto. Lo usa nucleo/voz.py (que fija modelo eleven_v4 y ajustes).

- tts(txt): reescritura FONÉTICA del texto que se manda al TTS (los subtítulos conservan la ortografía real).
- crudo(A, i, who, txt): devuelve audio/lineas/NN-raw.mp3 generándolo SOLO si no existe o si su ficha NN-raw.json no
  coincide (texto/modelo/semilla/ajustes) → nunca se paga dos veces lo mismo.
- Gasto por video en <proyecto>/audio/eleven_gasto.json (+ total en <skill>/gasto_eleven_total.json).

La voz sale de perfil.json («voz_id» = la voz del usuario en su cuenta de ElevenLabs; «voz_id_2» = segunda voz opcional).
La clave sale de ELEVENLABS_API_KEY (variable de entorno o archivo .env) y JAMÁS se imprime.
"""
import json, os, re, subprocess, sys, time, urllib.request

MV = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # carpeta de la skill
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ffruta import ffmpeg, leer_texto   # todo JSON en UTF-8: en Windows open() sin encoding es cp1252
FF = ffmpeg()


def _perfil():
    f = os.path.join(MV, 'perfil.json')
    return json.loads(leer_texto(f)) if os.path.exists(f) else {}


_P = _perfil()
VOZ_PRINCIPAL = _P.get('voz_id', '')
VOZ_SEGUNDA = _P.get('voz_id_2', '') or VOZ_PRINCIPAL
VOZ_DEFECTO = VOZ_PRINCIPAL          # compatibilidad: fichas viejas sin campo «voz»
VOCES = {'D': VOZ_PRINCIPAL, 'C': VOZ_SEGUNDA, 'X': VOZ_SEGUNDA}

MODELO = os.environ.get('ELEVEN_MODELO', 'eleven_v4')
LANG = 'es'   # language_code: fuerza la normalización y el acento en español

AJUSTES = {
    'D': {'stability': 0.50, 'similarity_boost': 0.85},
    'C': {'stability': 0.50, 'similarity_boost': 0.85},
    'X': {'stability': 0.50, 'similarity_boost': 0.85},
}
AJUSTES_PREV = {}
CTX = {}
TONO_X = 41013
TOPE_TAREA = 10 ** 9

# ---------------------------------------------------------------- reescritura fonética (solo para el TTS)
_UNI = ['cero', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez', 'once', 'doce',
        'trece', 'catorce', 'quince', 'dieciséis', 'diecisiete', 'dieciocho', 'diecinueve', 'veinte']
_DEC = {30: 'treinta', 40: 'cuarenta', 50: 'cincuenta', 60: 'sesenta', 70: 'setenta', 80: 'ochenta', 90: 'noventa'}
_CEN = {100: 'cien', 200: 'doscientos', 300: 'trescientos', 400: 'cuatrocientos', 500: 'quinientos', 600: 'seiscientos',
        700: 'setecientos', 800: 'ochocientos', 900: 'novecientos'}


def numero(n):
    n = int(n)
    if n <= 20: return _UNI[n]
    if n < 30: return 'veinti' + ['', 'uno', 'dós', 'trés', 'cuatro', 'cinco', 'séis', 'siete', 'ocho', 'nueve'][n - 20]
    if n < 100: return _DEC[n // 10 * 10] + ('' if n % 10 == 0 else ' y ' + _UNI[n % 10])
    if n < 1000:
        if n == 100: return 'cien'
        c = n // 100 * 100; r = n - c
        return ('ciento' if c == 100 else _CEN[c]) + ('' if r == 0 else ' ' + numero(r))
    if n < 1000000:
        m, r = divmod(n, 1000)
        return ('mil' if m == 1 else numero(m) + ' mil') + ('' if r == 0 else ' ' + numero(r))
    m, r = divmod(n, 1000000)
    return ('un millón' if m == 1 else numero(m) + ' millones') + ('' if r == 0 else ' ' + numero(r))


REGLAS = [  # (patrón, reemplazo, nota) — se aplican en orden; las notas van al reporte
    (r'\bClaude\b', 'Clod', 'Claude → Clod'),
    (r'\bCodex\b', 'Códex', 'Codex → Códex'),
    (r'\b(?:OK|Ok|ok|Okey|okey|Okay|okay)\b', 'oquéi', 'OK/Okey → oquéi'),
    (r'\bYouTube\b', 'Yutub', 'YouTube → Yutub'),
    (r'\bcardio\b', 'cárdio', 'cardio → cárdio'),
    (r'\bCardio\b', 'Cárdio', 'Cardio → Cárdio'),
    (r'(?<![«\w])mmm(?![\w»])', '«mmm»', 'mmm → «mmm»'),
]
PRO = os.environ.get('ELEVEN_PRO', 'pro')   # «pro» o «prou» según la prueba A/B


def tts(txt, notas=None):
    """Texto que se manda a ElevenLabs. Los subtítulos NO pasan por aquí."""
    t = txt
    for pat, rep, nota in REGLAS:
        t2 = re.sub(pat, rep, t)
        if t2 != t and notas is not None: notas.add(nota)
        t = t2
    t2 = re.sub(r'\b([Pp])ro\b', lambda m: m.group(1) + PRO[1:], t)
    if t2 != t and notas is not None and PRO != 'pro': notas.add(f'pro → {PRO}')
    t = t2
    t2 = re.sub(r'(\d+(?:,\d{3})*)', lambda m: numero(m.group(1).replace(',', '')), t)
    if t2 != t and notas is not None: notas.add('cifras → palabras')
    t = t2.replace('…', '...')
    return t


# ---------------------------------------------------------------- API
def clave():
    if os.environ.get('ELEVENLABS_API_KEY'): return os.environ['ELEVENLABS_API_KEY'].strip()
    for d in (os.getcwd(), MV):
        f = os.path.join(d, '.env')
        if os.path.exists(f):
            for ln in leer_texto(f).splitlines():
                if ln.strip().startswith('ELEVENLABS_API_KEY='): return ln.split('=', 1)[1].strip().strip('"').strip("'")
    raise SystemExit('Falta ELEVENLABS_API_KEY en el archivo .env junto a la skill (no la pegues en el chat).')


def saldo():
    r = json.load(urllib.request.urlopen(urllib.request.Request('https://api.elevenlabs.io/v1/user/subscription',
                                                                headers={'xi-api-key': clave()})))
    return r['character_limit'] - r['character_count']


def _gasto_total():
    f = os.path.join(MV, 'gasto_eleven_total.json')
    return f, (json.loads(leer_texto(f)) if os.path.exists(f) else {'total': 0, 'llamadas': []})


def gastado_tarea():
    return _gasto_total()[1]['total']


def registrar(A, etiqueta, who, txt, modelo, seed):
    f = os.path.join(A, 'eleven_gasto.json')
    g = json.loads(leer_texto(f)) if os.path.exists(f) else {'total': 0, 'llamadas': []}
    g.setdefault('total_es', 0); g.setdefault('llamadas_es', [])
    g['total_es'] += len(txt)
    g['llamadas_es'].append({'linea': etiqueta, 'who': who, 'texto': txt, 'caracteres': len(txt), 'modelo': modelo,
                             'seed': seed, 'fecha': time.strftime('%Y-%m-%d %H:%M')})
    json.dump(g, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    ft, t = _gasto_total(); t['total'] += len(txt)
    t['llamadas'].append([os.path.basename(os.path.dirname(A)), etiqueta, len(txt), modelo])
    os.makedirs(os.path.dirname(ft), exist_ok=True); json.dump(t, open(ft, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def pedir(who, txt, modelo=None, seed=None, lang=True):
    modelo = modelo or MODELO
    body = {'text': txt, 'model_id': modelo, 'voice_settings': AJUSTES[who]}
    if lang and modelo != 'eleven_multilingual_v2': body['language_code'] = LANG
    if seed is not None: body['seed'] = int(seed)
    for k_ in ('previous_text', 'next_text'):
        if CTX.get(k_): body[k_] = CTX[k_]
    req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{VOCES[who]}?output_format=mp3_44100_128',
                                 data=json.dumps(body).encode(), headers={'xi-api-key': clave(), 'Content-Type': 'application/json'})
    if gastado_tarea() + len(txt) > TOPE_TAREA: raise SystemExit(f'Tope de la tarea ({TOPE_TAREA} caracteres) alcanzado')
    return urllib.request.urlopen(req, timeout=120).read()


def tono_x(raw, out):
    subprocess.run([FF, '-v', 'error', '-y', '-i', raw, '-af', f'asetrate={TONO_X},aresample=44100', out], check=True)
    return out


def restaurar(A, i, k):
    """Vuelve a poner como línea i el intento k guardado en lineas/intentos (sin gastar)."""
    import shutil; L = os.path.join(A, 'lineas'); I = os.path.join(L, 'intentos')
    shutil.copy(os.path.join(I, f'{i:02d}-{k}.mp3'), os.path.join(L, f'{i:02d}-raw.mp3'))
    shutil.copy(os.path.join(I, f'{i:02d}-{k}.json'), os.path.join(L, f'{i:02d}-raw.json'))
    fi = ficha(A, i)
    if fi['who'] == 'X': tono_x(os.path.join(L, f'{i:02d}-raw.mp3'), os.path.join(L, f'{i:02d}-raw-x.wav'))


def ficha(A, i):
    f = os.path.join(A, 'lineas', f'{i:02d}-raw.json')
    return json.loads(leer_texto(f)) if os.path.exists(f) else None


def crudo(A, i, who, txt_guion, seed=None, forzar=False, texto=None):
    """Ruta del audio crudo de la línea i (Codex ya con tono ×0.93). Genera solo si hace falta.
    txt_guion = texto TTS del guion (se le aplica tts()); texto = reescritura manual que lo sustituye."""
    L = os.path.join(A, 'lineas'); os.makedirs(L, exist_ok=True)
    raw = os.path.join(L, f'{i:02d}-raw.mp3'); fj = os.path.join(L, f'{i:02d}-raw.json')
    t = texto or tts(txt_guion)
    fi = ficha(A, i)
    vale = (fi and os.path.exists(raw) and os.path.getsize(raw) > 1000 and fi.get('guion') == txt_guion and fi['modelo'] == MODELO
            and fi.get('voz', VOZ_DEFECTO) == VOCES[who]
            and fi['ajustes'] in (AJUSTES[who], AJUSTES_PREV.get(who)) and (texto is None or fi['texto'] == t) and (seed is None or fi.get('seed') == seed))
    if forzar or not vale:
        data = pedir(who, t, seed=seed)
        open(raw, 'wb').write(data)
        json.dump({'texto': t, 'guion': txt_guion, 'modelo': MODELO, 'seed': seed, 'ajustes': AJUSTES[who], 'who': who, 'voz': VOCES[who],
                   'lang': LANG if MODELO != 'eleven_multilingual_v2' else None}, open(fj, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        registrar(A, i, who, t, MODELO, seed)
        I = os.path.join(L, 'intentos'); os.makedirs(I, exist_ok=True); k = len([f for f in os.listdir(I) if f.startswith(f'{i:02d}-') and f.endswith('.mp3')])
        import shutil; shutil.copy(raw, os.path.join(I, f'{i:02d}-{k}.mp3')); shutil.copy(fj, os.path.join(I, f'{i:02d}-{k}.json'))
        print(f'  ElevenLabs línea {i} ({who}, {MODELO}, seed {seed}): {len(t)} caracteres «{t}»')
    if who == 'X':
        out = os.path.join(L, f'{i:02d}-raw-x.wav')
        if forzar or not vale or not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(raw): tono_x(raw, out)
        return out
    return raw
