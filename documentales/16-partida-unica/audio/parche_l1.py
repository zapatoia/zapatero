import base64, json, subprocess, sys, urllib.request
from pathlib import Path
import numpy as np, soundfile as sf
MOTOR = Path("/home/user/zapatero/.claude/skills/documental-animado/motor"); sys.path.insert(0, str(MOTOR))
from nucleo.rutas import perfil, clave_eleven, FF
proy = Path(sys.argv[1]); tts = sys.argv[2]; SR = 48000; au = proy / "audio"
dst = au / "parche_l1.mp3"
if not dst.exists():
    body = dict(text=tts, model_id="eleven_v3", language_code="es", voice_settings=dict(stability=.5, similarity_boost=.85))
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{perfil()['voz_id']}/with-timestamps?output_format=mp3_44100_192",
                                 data=json.dumps(body).encode(), headers={"xi-api-key": clave_eleven(), "Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(req, timeout=300).read())
    dst.write_bytes(base64.b64decode(d["audio_base64"])); (au / "parche_l1.json").write_text(json.dumps(dict(texto=tts, al=d["alignment"]), ensure_ascii=False))
al = json.loads((au / "parche_l1.json").read_text())["al"]
x = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", str(dst), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout, np.float32).astype(np.float64)
y, _ = sf.read(proy / "voz.wav"); pal = json.loads((proy / "palabras.json").read_text())
env = lambda a: 20 * np.log10(np.array([np.sqrt(np.mean(a[i:i + 240] ** 2)) + 1e-9 for i in range(0, len(a) - 240, 240)]))
# corte en el original: silencio entre «juegues…» y «seguramente»
ey = env(y); i0, i1 = int(1.9 * 200), int(pal[7]["s"] * 200)
quiet = [i for i in range(i0, i1) if ey[i] < -45]
cut_old = (quiet[len(quiet) // 2] if quiet else i1 - 4) / 200
# parche: quitar silencio inicial, terminar tras la cola real
ex = env(x); ini = max(0, next(i for i, v in enumerate(ex) if v > -45) / 200 - .003)
viv = [i for i, v in enumerate(ex) if v > -48]; j = viv[-1]
while j < len(ex) - 1 and ex[j] > -62: j += 1
fin = j / 200 + .03
seg = x[int(ini * SR):int(fin * SR)].copy()
es = env(seg); cortes = []; k = None
for i, v in enumerate(list(es) + [0]):
    if v < -45 and k is None: k = i
    if v >= -45 and k is not None:
        if (i - k) / 200 > .35: cortes.append(((k / 200) + .125, (i - k) / 200 - .25))
        k = None
keep = np.ones(len(seg), bool)
for c0, d in cortes: keep[int(c0 * SR):int((c0 + d) * SR)] = False
seg = seg[keep]
def mapa(tt):
    q = 0.0
    for c0, d in cortes:
        if tt > c0: q += min(d, tt - c0)
    return tt - q
ref = y[:int(cut_old * SR)]
rms = lambda a: np.sqrt(np.mean(a[np.abs(a) > np.abs(a).max() * .05] ** 2))
seg *= rms(ref) / rms(seg)
pausa = np.zeros(int(.30 * SR))
f6 = int(.04 * SR); seg[-f6:] *= np.linspace(1, 0, f6) ** 2
fi = int(.004 * SR); seg[:fi] *= np.linspace(0, 1, fi)
resto = y[int(cut_old * SR):]
ny = np.concatenate([seg, pausa, resto]); new_cut = (len(seg) + len(pausa)) / SR; delta = new_cut - cut_old
# marcas de la línea 1 desde la alineación del parche
ch = al["characters"]; cs = al["character_start_times_seconds"]; ce = al["character_end_times_seconds"]; full = "".join(ch)
import re
words = [(m.start(), m.end()) for m in re.finditer(r"[^\s\[\]]+", full) if not full[m.start()-1:m.start()] == "[" ]
words = [(a, b) for a, b in words if not re.match(r"^(curious|playful|warm|firm)\]?$", full[a:b]) and re.search(r"\w", full[a:b])]
l1 = [w for w in pal if w["linea"] == 1]
assert len(words) == len(l1), (len(words), len(l1), [full[a:b] for a, b in words])
for w, (a, b) in zip(l1, words):
    w["s"] = round(mapa(max(0.0, cs[a] - ini)), 3); w["e"] = round(min(len(seg) / SR, mapa(ce[b - 1] - ini)), 3)
l1[0]["s"] = 0.0   # la alineación marca «La» tarde: la voz suena desde el primer cuadro
for w in pal:
    if w["linea"] != 1: w["s"] = round(w["s"] + delta, 3); w["e"] = round(w["e"] + delta, 3)
sf.write(proy / "voz.wav", ny.astype(np.float32), SR, subtype="FLOAT")
(proy / "palabras.json").write_text(json.dumps(pal, ensure_ascii=False, indent=0), encoding="utf-8")
print("cortes internos", cortes); print("corte", cut_old, "nuevo", round(new_cut, 3), "delta", round(delta, 3), "dur", round(len(ny) / SR, 2)); print(l1)
