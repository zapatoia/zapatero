#!/usr/bin/env python3
"""Instalador automático de la skill (Mac y Windows). Lo lanzan instalar.sh (Mac) o instalar.ps1 (Windows).

Hace TODO sin preguntar nada:
  1. copia la skill a ~/.claude/skills/<skill>
  2. crea su Python con las librerías (con uv: sin contraseña ni administrador)
  3. instala Blender si el formato lo usa (descarga oficial de blender.org, en una carpeta propia)
  4. baja el modelo de Whisper (verifica la voz y marca cada palabra)
  5. deja perfil.json con valores por defecto
  6. hace una prueba sin voz (no gasta nada)

Se puede correr las veces que haga falta: cada paso se salta si ya quedó hecho.
La salida es corta; el detalle completo va al registro (~/.club-videos/registro/instalar-<skill>.log).
"""
import json, os, platform, re, shutil, subprocess, sys, tempfile, time, zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace"); sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

AQUI = Path(__file__).resolve().parent
ORIGEN = AQUI.parent
KIT = json.loads((AQUI / "kit.json").read_text(encoding="utf-8"))
SLUG = KIT["slug"]
WIN = os.name == "nt"
MAC = sys.platform == "darwin"
HOME = Path.home()
BASE = HOME / ".club-videos"
LOG = BASE / "registro" / f"instalar-{SLUG}.log"
DESTINO = HOME / ".claude" / "skills" / SLUG
VENV = HOME / ".venvs" / SLUG
VPY = VENV / ("Scripts/python.exe" if WIN else "bin/python")
UV = os.environ.get("UV_EXE") or shutil.which("uv") or ""
PY_REQ = os.environ.get("PY_REQ") or KIT.get("python", "3.12")
PASOS = 6
ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", HF_HUB_DISABLE_SYMLINKS_WARNING="1",
           UV_PYTHON_PREFERENCE="only-managed", PIP_DISABLE_PIP_VERSION_CHECK="1")


class Falla(Exception):
    pass


def log(txt):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(txt if txt.endswith("\n") else txt + "\n")


def di(txt):
    print(txt, flush=True); log(txt)


def corre(cmd, check=True, cwd=None, timeout=None):
    """Corre un comando; su salida va al registro (no a la pantalla)."""
    cmd = [str(c) for c in cmd]
    log("$ " + " ".join(cmd))
    try:
        r = subprocess.run(cmd, cwd=cwd, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
                           text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError as e:
        raise Falla(f"no existe el programa {cmd[0]} ({e})")
    except subprocess.TimeoutExpired:
        raise Falla(f"tardó demasiado: {' '.join(cmd[:3])}")
    log(r.stdout or "")
    if check and r.returncode:
        raise Falla(f"el comando terminó con error ({r.returncode}): {' '.join(cmd[:4])}")
    return r


def descarga(url, destino):
    """Con curl (viene en Mac y en Windows 10/11): usa los certificados del sistema y aguanta cortes."""
    destino = Path(destino); destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(destino.name + ".parcial")
    curl = "curl.exe" if WIN else "curl"
    for intento in range(3):
        r = corre([curl, "-fL", "--retry", "3", "--retry-delay", "5", "-sS", "-C", "-", "-o", tmp, url], check=False)
        if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
            os.replace(tmp, destino); return destino
        time.sleep(5)
    raise Falla(f"no se pudo descargar {url} (revisa el internet y vuelve a correr el instalador)")


def texto_url(url):
    r = corre(["curl.exe" if WIN else "curl", "-fsSL", "--retry", "2", url], check=False)
    return r.stdout if r.returncode == 0 else ""


def ruta(p):
    return str(p).replace("\\", "/")


# ── 1 · la skill en su lugar ────────────────────────────────────────────────────────────────
def paso_skill():
    if ORIGEN.resolve() == DESTINO.resolve():
        return "ya estaba en su lugar"
    DESTINO.mkdir(parents=True, exist_ok=True)
    if (DESTINO / "SKILL.md").exists() and (ORIGEN / "SKILL.md").read_bytes() != (DESTINO / "SKILL.md").read_bytes():
        shutil.copy2(DESTINO / "SKILL.md", DESTINO / "SKILL.anterior.md")       # por si tenía reglas suyas en la sección 7
    ignora = shutil.ignore_patterns("__pycache__", ".DS_Store", "._*", "perfil.json", ".env")
    shutil.copytree(ORIGEN, DESTINO, dirs_exist_ok=True, ignore=ignora)         # perfil.json y .env del usuario no se tocan
    return ruta(DESTINO)


# ── 2 · Python y librerías ──────────────────────────────────────────────────────────────────
def _version_ok(py):
    want = re.search(r"(\d+)\.(\d+)", PY_REQ)
    r = subprocess.run([str(py), "-c", "import sys;print('%d.%d'%sys.version_info[:2])"], capture_output=True, text=True)
    if r.returncode: return False
    return not want or r.stdout.strip() == f"{want[1]}.{want[2]}"


def paso_python():
    if not UV:
        raise Falla("falta uv (lo baja instalar.sh / instalar.ps1: corre ese archivo, no este)")
    if not (VPY.exists() and _version_ok(VPY)):
        if VENV.exists(): shutil.rmtree(VENV, ignore_errors=True)
        corre([UV, "venv", "--seed", "--python", PY_REQ, VENV])
    req = DESTINO / "requirements.txt"
    di("   instalando librerías (la primera vez tarda varios minutos)…")
    corre([UV, "pip", "install", "--python", VPY, "-r", req])
    if KIT.get("playwright"):
        di("   instalando el navegador sin ventana…")
        corre([VPY, "-m", "playwright", "install", "chromium"])
    v = subprocess.run([str(VPY), "-c", "import sys;print(sys.version.split()[0])"], capture_output=True, text=True).stdout.strip()
    return f"Python {v} · {ruta(VPY)}"


# ── 3 · Blender ─────────────────────────────────────────────────────────────────────────────
def _ver_blender(exe):
    try:
        r = subprocess.run([str(exe), "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    except Exception:
        return None
    m = re.search(r"Blender (\d+)\.(\d+)(?:\.(\d+))?", r.stdout or "")
    return (int(m[1]), int(m[2]), int(m[3] or 0)) if m else None


def _candidatos():
    c = [os.environ.get("BLENDER"), _perfil().get("blender"), shutil.which("blender")]
    if MAC:
        c += ["/Applications/Blender.app/Contents/MacOS/Blender", HOME / "Applications/Blender.app/Contents/MacOS/Blender",
              BASE / "blender/Blender.app/Contents/MacOS/Blender"]
    if WIN:
        pf = [Path(d) for d in dict.fromkeys(os.environ.get(v) for v in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)")) if d]
        for d in pf + [Path("C:/Program Files")]:
            c += list((d / "Blender Foundation").glob("Blender*/blender.exe"))
            c.append(d / "Steam/steamapps/common/Blender/blender.exe")
        for raiz in (Path("C:/Blender"), BASE / "blender"):
            c += list(raiz.glob("blender.exe")) + list(raiz.glob("*/blender.exe"))
    salen = []
    for p in c:
        if not p: continue
        q = Path(os.path.expanduser(str(p).strip().strip('"').strip("'")))
        if q.is_dir():
            q = next((x for x in (q / "blender.exe", q / "Contents/MacOS/Blender", q / "blender") if x.is_file()), q)
        if q.name.lower() == "blender-launcher.exe": q = q.with_name("blender.exe")
        if q.is_file() and q not in salen: salen.append(q)
    return salen


def _url_blender():
    if MAC:
        serie, suf = ("5.2", "macos-arm64.dmg") if platform.machine() == "arm64" else ("4.2", "macos-x64.dmg")
    else:
        arm = "ARM" in os.environ.get("PROCESSOR_IDENTIFIER", "").upper() or os.environ.get("PROCESSOR_ARCHITECTURE") == "ARM64" \
            or os.environ.get("PROCESSOR_ARCHITEW6432") == "ARM64"
        serie, suf = "5.2", ("windows-arm64.zip" if arm else "windows-x64.zip")
    base = f"https://download.blender.org/release/Blender{serie}/"
    vers = re.findall(rf"blender-({re.escape(serie)}\.\d+)-{re.escape(suf)}", texto_url(base))
    v = max(vers, key=lambda s: tuple(map(int, s.split(".")))) if vers else {"5.2": "5.2.5", "4.2": "4.2.23"}[serie]
    return base + f"blender-{v}-{suf}", v


def _instala_blender():
    url, v = _url_blender()
    nombre = url.rsplit("/", 1)[1]
    di(f"   descargando Blender {v} de blender.org (unos 400 MB)…")
    arch = descarga(url, BASE / "descargas" / nombre)
    if MAC:
        mnt = Path(tempfile.mkdtemp(prefix="blender-"))
        corre(["hdiutil", "attach", "-nobrowse", "-readonly", "-noautoopen", "-mountpoint", mnt, arch])
        try:
            app = next(mnt.glob("*.app"))
            dest = BASE / "blender" / "Blender.app"
            if dest.exists(): shutil.rmtree(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            di("   copiando Blender…")
            corre(["ditto", app, dest])
        finally:
            corre(["hdiutil", "detach", mnt, "-quiet"], check=False)
        exe = dest / "Contents/MacOS/Blender"
    else:
        raiz = Path("C:/Blender")
        try:
            raiz.mkdir(exist_ok=True); (raiz / ".prueba").write_text("ok"); (raiz / ".prueba").unlink()
        except OSError:
            raiz = BASE / "blender"; raiz.mkdir(parents=True, exist_ok=True)
        di(f"   descomprimiendo Blender en {raiz}…")
        with zipfile.ZipFile(arch) as z:
            z.extractall("\\\\?\\" + str(raiz.resolve()))          # \\?\ = rutas largas (Blender trae carpetas muy hondas)
        exe = next(raiz.glob(f"blender-{v}*/blender.exe"), None) or next(raiz.glob("*/blender.exe"))
    try: arch.unlink()
    except OSError: pass
    return exe


def paso_blender():
    if not KIT.get("blender"):
        return None
    mejor = None
    for q in ([] if os.environ.get("CLUB_FORZAR_BLENDER") else _candidatos()):      # CLUB_FORZAR_BLENDER: solo para probar la descarga
        v = _ver_blender(q)
        log(f"Blender candidato {q}: {v}")
        if v and v >= (4, 2, 0) and (not mejor or v > mejor[1]): mejor = (q, v)
    if not mejor:
        exe = _instala_blender(); v = _ver_blender(exe)
        if not v: raise Falla(f"Blender quedó en {exe} pero no arranca")
        mejor = (exe, v)
    exe, v = mejor
    r = corre([exe, "-b", "--factory-startup", "--python-expr", "import bpy;print('BLENDER_OK', bpy.app.version_string)"], check=False, timeout=600)
    if "BLENDER_OK" not in (r.stdout or ""):
        raise Falla("Blender no arranca sin ventana (revisa los drivers de la tarjeta gráfica)")
    _guarda_perfil({"blender": ruta(exe)})
    return f"Blender {'.'.join(map(str, v))} · {ruta(exe)}"


# ── 4 · Whisper ─────────────────────────────────────────────────────────────────────────────
WHISPER = r'''
try:
    import mlx_whisper  # Mac con chip Apple
    from huggingface_hub import snapshot_download
    snapshot_download("mlx-community/whisper-large-v3-turbo"); print("WHISPER_OK mlx")
except ImportError:
    from faster_whisper.utils import download_model
    download_model("large-v3-turbo"); print("WHISPER_OK faster")
'''


def paso_whisper():
    if not KIT.get("whisper", True):
        return None
    if WIN and not str(HOME).isascii() and not os.environ.get("HF_HOME"):
        ENV["HF_HOME"] = "C:\\hf"                                    # usuario con acentos o ñ: Whisper no abre el modelo
        corre(["setx", "HF_HOME", "C:\\hf"], check=False)
    di("   bajando el modelo de Whisper (≈1.6 GB, solo la primera vez)…")
    r = corre([VPY, "-c", WHISPER], check=False)
    if "WHISPER_OK" not in (r.stdout or ""):
        raise Falla("no se pudo bajar el modelo de Whisper")
    return "modelo large-v3-turbo"


# ── 5 · perfil.json ─────────────────────────────────────────────────────────────────────────
MARCADORES = ("tu_cuenta", "Tu Nombre", "/ruta/", "ID_DE_TU", "TU_VOZ")


def _perfil():
    p = DESTINO / "perfil.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except ValueError:
        return {}


def _guarda_perfil(cambios):
    p = DESTINO / "perfil.json"; d = _perfil(); d.update(cambios)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def paso_perfil():
    d = _perfil(); ej = DESTINO / "perfil.ejemplo.json"
    base = json.loads(ej.read_text(encoding="utf-8")) if ej.exists() else {}
    for k, v in base.items():
        if k in d: continue
        if isinstance(v, str) and (any(m in v for m in MARCADORES) or (k in ("avatar", "foto") and not (DESTINO / v).exists())):
            v = ""
        d[k] = v
    d["python"] = ruta(VPY)
    voz = BASE / "voz.json"                                          # voz con IA ya configurada en otra skill del Club
    if KIT.get("voz") == "eleven" and voz.exists():
        try:
            vj = json.loads(voz.read_text(encoding="utf-8"))
            if vj.get("voz_id") and not d.get("voz_id"): d["voz_id"] = vj["voz_id"]
        except ValueError:
            pass
    clave = BASE / "elevenlabs.env"
    if KIT.get("voz") == "eleven" and clave.exists() and not (DESTINO / ".env").exists():
        shutil.copy2(clave, DESTINO / ".env")
    (DESTINO / "perfil.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return "valores por defecto (sin firma, sin avatar, sin música)"


# ── 6 · prueba ──────────────────────────────────────────────────────────────────────────────
def paso_prueba():
    pr = KIT.get("prueba") or {}
    P = BASE / "pruebas" / SLUG
    if P.exists(): shutil.rmtree(P, ignore_errors=True)
    P.parent.mkdir(parents=True, exist_ok=True)
    if pr.get("copia"):
        shutil.copytree(DESTINO / pr["copia"], P)
    else:
        P.mkdir(parents=True, exist_ok=True)
    for c in pr.get("comandos", []):
        cmd = [str(x).replace("{P}", str(P)).replace("{SKILL}", str(DESTINO)) for x in c]
        corre([VPY] + cmd, cwd=DESTINO, timeout=3600)
    sale = pr.get("sale")
    if sale:
        f = P / sale
        if not f.exists() or (f.is_dir() and not any(f.iterdir())):
            raise Falla(f"la prueba no dejó {ruta(f)}")
        return ruta(f)
    return "ok"


def estado_voz():
    if KIT.get("voz") != "eleven":
        return None
    vj = BASE / "voz.json"
    if (DESTINO / ".env").exists() and vj.exists():
        try: return "con IA (voz «%s»)" % json.loads(vj.read_text(encoding="utf-8")).get("voz_nombre", "?")
        except ValueError: pass
    if (BASE / "sin-voz-ia").exists():
        return "su voz grabada (eligió no usar voz con IA)"
    return "falta preguntarle si quiere voz con IA"


def main():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    log(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} · {SLUG} · {platform.platform()} · Python {sys.version.split()[0]}")
    di(f"Instalando «{KIT.get('nombre', SLUG)}»…")
    pasos = [("La skill en su carpeta", paso_skill), ("Python y librerías", paso_python), ("Blender", paso_blender),
             ("Modelo de Whisper", paso_whisper), ("Perfil", paso_perfil), ("Prueba sin voz", paso_prueba)]
    hechos = {}
    for n, (nom, f) in enumerate(pasos, 1):
        di(f"[{n}/{PASOS}] {nom}…")
        try:
            r = f()
        except Falla as e:
            fin = (LOG.read_text(encoding="utf-8", errors="replace").splitlines() if LOG.exists() else [])[-25:]
            print("\n".join(fin))
            di(f"\nFALLÓ en el paso {n} ({nom}): {e}\nRegistro completo: {ruta(LOG)}\n"
               "Arregla la causa y vuelve a correr el instalador: sigue donde se quedó.")
            sys.exit(1)
        except Exception as e:
            log(repr(e)); di(f"\nFALLÓ en el paso {n} ({nom}): {e!r}\nRegistro completo: {ruta(LOG)}"); raise
        hechos[nom] = r
        di(f"      {'listo' if r is None or r == 'ok' else r}" if r is not None else "      no hace falta")
    (DESTINO / "instalado.json").write_text(json.dumps(dict(fecha=time.strftime("%Y-%m-%d %H:%M"), python=ruta(VPY),
        blender=_perfil().get("blender"), kit=KIT.get("version")), ensure_ascii=False, indent=1), encoding="utf-8")
    PYq = f'"{ruta(VPY)}"'
    print()
    di(f"LISTO · «{KIT.get('nombre', SLUG)}» quedó instalado y probado.")
    di(f"PY = {PYq}")
    di(f"Skill: {ruta(DESTINO)}")
    if hechos.get("Prueba sin voz") not in (None, "ok"): di(f"Prueba: {hechos['Prueba sin voz']}")
    ev = estado_voz()
    if ev:
        di(f"Voz: {ev}")
        di(f"  · con IA:   {PYq} \"{ruta(DESTINO / 'instalar/voz_ia.py')}\" --clave <SU_API_KEY>   (o --sin-ia)")
        di(f"  · grabada:  {PYq} \"{ruta(DESTINO / 'instalar/voz_propia.py')}\" <proyecto> <archivo de audio>")


if __name__ == "__main__":
    main()
