#!/usr/bin/env python3
"""Tu voz grabada como voz del video (sin ElevenLabs, no gasta nada). Lo corre Claude.

  PY voz_propia.py <proyecto> <archivo de audio>

El usuario lee el guion de corrido (nota de voz del celular: m4a, mp3, wav, ogg, opus, aac… o un video: se toma su audio).
Se convierte, se le quitan las pausas largas, se marca cada palabra con Whisper y quedan voz.wav, palabras.json y
voz-verificacion.json en el proyecto, igual que si viniera de ElevenLabs. Después se sigue el flujo normal (anclas, prueba, render).
Si la verificación dice que algo no coincide con el guion, el usuario dijo otra cosa: cambia el «texto» de esa línea del guion
a lo que dijo y vuelve a correr este comando (no hay que grabar otra vez).
"""
import json, subprocess, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "motor" / "nucleo"))
sys.path.insert(0, str(SKILL / "motor" / "herramientas"))


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    proy = Path(sys.argv[1]).expanduser().resolve()
    audio = Path(sys.argv[2].strip().strip('"').strip("'")).expanduser().resolve()
    if not (proy / "guion.json").exists(): sys.exit(f"No encuentro {proy / 'guion.json'}")
    if not audio.exists(): sys.exit(f"No encuentro el audio {audio}")
    import voz as VZ                                   # motor/nucleo/voz.py de esta skill
    from rutas import leer_texto
    g = json.loads(leer_texto(proy / "guion.json"))
    lineas = g["lineas"]
    tts = " ".join(ln.get("tts") or VZ.E.tts(ln["texto"]) for ln in lineas)
    A = proy / "audio" / "corrida"; (A / "lineas").mkdir(parents=True, exist_ok=True)
    raw = A / "lineas" / "01-raw.mp3"
    r = subprocess.run([VZ.FF, "-v", "error", "-y", "-i", str(audio), "-vn", "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "320k", str(raw)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode: sys.exit("No pude leer ese audio: " + r.stderr[-400:])
    # La toma ya «está pagada»: se marca como buena para que voz.py solo la arme (nunca llama a ElevenLabs).
    (A / "verificacion.json").write_text(json.dumps(dict(ok=True, tts=tts, modelo=VZ.MODELO, propia=True, archivo=audio.name),
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    VZ.corrida(proy, g, "armar")
    vf = proy / "voz-verificacion.json"
    rep = json.loads(leer_texto(vf)) if vf.exists() else {}
    print("Tu voz quedó lista (voz.wav + palabras.json)." if rep.get("ok") else
          "Tu voz quedó armada, pero no coincide con el guion en lo de arriba: ajusta el «texto» del guion a lo que dijo y vuelve a correr esto.")


if __name__ == "__main__":
    main()
