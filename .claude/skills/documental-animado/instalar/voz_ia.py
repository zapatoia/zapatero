#!/usr/bin/env python3
"""Voz con IA (ElevenLabs) para TODAS las skills de video del Club de esta computadora. Lo corre Claude, no el usuario.

  PY voz_ia.py --clave <API_KEY>     valida la clave, la guarda (solo en esta computadora), elige la voz y dice el saldo
  PY voz_ia.py --voz "<nombre o ID>" cambia la voz (una de su cuenta de ElevenLabs)
  PY voz_ia.py --voces               lista las voces de su cuenta
  PY voz_ia.py --estado              dice si hay voz con IA y cuál (nunca muestra la clave)
  PY voz_ia.py --sin-ia              el usuario no quiere voz con IA: sus videos van con su voz grabada (voz_propia.py)

La clave se guarda en ~/.club-videos/elevenlabs.env y en el .env de cada skill de video instalada. JAMÁS se imprime.
La voz elegida: la suya (clonada o profesional) si tiene; si no, una voz de la biblioteca de ElevenLabs.
"""
import json, os, sys, urllib.error, urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = Path.home() / ".club-videos"
SKILLS = Path.home() / ".claude" / "skills"
CLAVE_F = BASE / "elevenlabs.env"
VOZ_F = BASE / "voz.json"
SIN_F = BASE / "sin-voz-ia"
API = "https://api.elevenlabs.io"
PREFERIDAS = ["Sarah", "Brian", "Laura", "George", "Jessica", "Adam", "Rachel", "Daniel"]


def pide(ruta, clave):
    req = urllib.request.Request(API + ruta, headers={"xi-api-key": clave, "User-Agent": "club-videos/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def lee_clave():
    if CLAVE_F.exists():
        for ln in CLAVE_F.read_text(encoding="utf-8").splitlines():
            if ln.startswith("ELEVENLABS_API_KEY="): return ln.split("=", 1)[1].strip()
    return ""


def skills_con_voz():
    """Skills de video instaladas que usan ElevenLabs (traen env.ejemplo o su kit.json dice voz=eleven)."""
    out = []
    for d in sorted(SKILLS.glob("*")) if SKILLS.exists() else []:
        k = d / "instalar" / "kit.json"
        try:
            usa = json.loads(k.read_text(encoding="utf-8")).get("voz") == "eleven" if k.exists() else (d / "env.ejemplo").exists()
        except ValueError:
            usa = False
        if usa: out.append(d)
    return out


def _voces_kit(d):
    try: return int(json.loads((d / "instalar" / "kit.json").read_text(encoding="utf-8")).get("voces", 1))
    except Exception: return 1


def pon_perfil(d, voz_id, forzar):
    p = d / "perfil.json"
    try: pf = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except ValueError: pf = {}
    actual = str(pf.get("voz_id", ""))
    if forzar or not actual or "ID_DE_TU" in actual:
        pf["voz_id"] = voz_id
        p.write_text(json.dumps(pf, ensure_ascii=False, indent=1), encoding="utf-8")


def voces(clave):
    try:
        return pide("/v1/voices", clave).get("voices", [])
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8", "replace")
        if "missing_permissions" in cuerpo: return None              # clave restringida sin permiso de leer voces
        if e.code in (400, 401, 403) or "invalid_api_key" in cuerpo:
            sys.exit("Esa clave no funciona (ElevenLabs la rechaza). Pídele que la copie completa de elevenlabs.io → Developers → API Keys.")
        sys.exit(f"ElevenLabs no contestó bien ({e.code}). Vuelve a intentarlo en un momento.")
    except urllib.error.URLError as e:
        sys.exit(f"No hay conexión con ElevenLabs ({e.reason}). Revisa el internet y vuelve a intentarlo.")


def elige(lista, pedida=None):
    if pedida:
        for v in lista:
            if pedida in (v.get("voice_id"), v.get("name")) or v.get("name", "").lower().startswith(pedida.lower()): return v
        sys.exit(f"No encuentro la voz «{pedida}» en su cuenta. Usa --voces para ver cuáles tiene.")
    propias = [v for v in lista if v.get("category") in ("professional", "cloned")]
    if propias: return sorted(propias, key=lambda v: v.get("category") != "professional")[0]
    for n in PREFERIDAS:
        for v in lista:
            if v.get("name", "").split()[0] == n: return v
    return lista[0] if lista else None


def saldo(clave):
    try:
        s = pide("/v1/user/subscription", clave)
        return int(s.get("character_limit", 0)) - int(s.get("character_count", 0)), s.get("tier", "")
    except Exception:
        return None, ""


def segunda(lista, v):
    """Para los formatos de dos personajes: otra voz (otra suya si tiene; si no, una de ElevenLabs de otro género)."""
    if not lista or not v: return None
    otras = [x for x in lista if x.get("voice_id") != v.get("voice_id")]
    propias = [x for x in otras if x.get("category") in ("professional", "cloned")]
    if propias: return propias[0]
    g = (v.get("labels") or {}).get("gender")
    distinto = [x for x in otras if (x.get("labels") or {}).get("gender") not in (None, g)]
    return (distinto or otras or [None])[0]


def guarda(clave, v, forzar, v2=None):
    BASE.mkdir(parents=True, exist_ok=True)
    CLAVE_F.write_text(f"ELEVENLABS_API_KEY={clave}\n", encoding="utf-8")
    try: os.chmod(CLAVE_F, 0o600)
    except OSError: pass
    if v: VOZ_F.write_text(json.dumps({"voz_id": v["voice_id"], "voz_nombre": v.get("name", ""), "categoria": v.get("category", "")},
                                      ensure_ascii=False, indent=1), encoding="utf-8")
    if SIN_F.exists(): SIN_F.unlink()
    n = 0
    for d in skills_con_voz():
        (d / ".env").write_text(f"ELEVENLABS_API_KEY={clave}\n", encoding="utf-8")
        if v: pon_perfil(d, v["voice_id"], forzar)
        if v2 and _voces_kit(d) == 2:
            p = d / "perfil.json"
            try: pf = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
            except ValueError: pf = {}
            if forzar or not pf.get("voz_id_2"):
                pf["voz_id_2"] = v2["voice_id"]; p.write_text(json.dumps(pf, ensure_ascii=False, indent=1), encoding="utf-8")
        n += 1
    return n


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"): print(__doc__); return
    if a[0] == "--sin-ia":
        BASE.mkdir(parents=True, exist_ok=True); SIN_F.write_text("eligió su voz grabada\n", encoding="utf-8")
        print("Listo: sus videos van con su voz grabada (instalar/voz_propia.py). Si luego quiere voz con IA: --clave <API_KEY>."); return
    if a[0] == "--clave":
        clave = (a[1] if len(a) > 1 and a[1] != "-" else sys.stdin.read()).strip().strip('"').strip("'")
        if clave.startswith("ELEVENLABS_API_KEY="): clave = clave.split("=", 1)[1].strip()
        if len(clave) < 20: sys.exit("Eso no parece una API key de ElevenLabs (es más larga). Pídele que la copie completa.")
        lista = voces(clave)
        v = elige(lista) if lista else None
        if lista is None:                                              # clave sin permiso de leer voces: se valida con el saldo
            if saldo(clave)[0] is None: sys.exit("Esa clave no tiene permisos suficientes. Que cree una nueva con todos los permisos (Developers → API Keys).")
            v = {"voice_id": "EXAVITQu4vr4xnAvoVFk", "name": "Sarah", "category": "premade"}     # voz pública de la biblioteca
        n = guarda(clave, v, forzar=False, v2=segunda(lista, v))
        s, plan = saldo(clave)
        quien = ("su voz «%s»" if v and v.get("category") in ("professional", "cloned") else "voz «%s» de ElevenLabs") % (v or {}).get("name", "?")
        print(f"Voz con IA lista · {quien} · " + (f"saldo: {s:,} caracteres{' (plan ' + plan + ')' if plan else ''}" if s is not None else "saldo: no disponible")
              + f" · guardada en {n} skill(s).")
        if v and v.get("category") not in ("professional", "cloned"):
            print("(No tiene una voz propia clonada en ElevenLabs; si crea una, se cambia con --voz \"<nombre>\".)")
        if not lista and lista is not None: print("Su cuenta no tiene voces: que agregue una en elevenlabs.io → Voices y corre --voz.")
        return
    clave = lee_clave()
    if a[0] == "--estado":
        if SIN_F.exists() and not clave: print("Sin voz con IA: usa su voz grabada."); return
        if not clave: print("Voz con IA: sin configurar (falta preguntarle)."); return
        vj = json.loads(VOZ_F.read_text(encoding="utf-8")) if VOZ_F.exists() else {}
        s, _ = saldo(clave)
        print(f"Voz con IA: configurada · voz «{vj.get('voz_nombre', '?')}» · " + (f"saldo {s:,} caracteres" if s is not None else "saldo no disponible")); return
    if not clave: sys.exit("Primero: --clave <API_KEY>.")
    if a[0] == "--voces":
        for v in voces(clave) or []: print(f"{v.get('name')} · {v.get('category')} · {v.get('voice_id')}")
        return
    if a[0] == "--voz" and len(a) > 1:
        v = elige(voces(clave) or [], a[1]); n = guarda(clave, v, forzar=True)
        print(f"Voz cambiada a «{v.get('name')}» en {n} skill(s)."); return
    print(__doc__)


if __name__ == "__main__":
    main()
