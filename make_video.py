#!/usr/bin/env python3
"""Estudio del zapato: guion JSON → MP4 1080x1920 listo para reels.

Uso:
  python make_video.py scripts/01-trading.json            # todo el flujo
  python make_video.py scripts/01-trading.json --estimate # solo caracteres y créditos
  python make_video.py scripts/01-trading.json --check    # revisa reglas del guion
  python make_video.py scripts/01-trading.json --contact  # hoja de fotogramas para revisar
  python make_video.py scripts/01-trading.json --stills 1.0,4.5,9

La voz se genera UNA vez por texto y queda en build/voice_cache (no se repite
la llamada a la API si el texto no cambia). Para generar voz nueva hace falta
confirmar (o pasar --yes).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

BANNED = [
    "en el mundo actual", "descubre cómo", "sin más dilación", "es importante destacar",
    "revolucionario", "revolucionaria", "desbloquea", "te voy a contar", "en este vídeo",
    "en este video", "hazte rico", "dinero fácil", "rentabilidad garantizada",
    "sumérgete", "no te lo pierdas", "en resumen", "cabe destacar",
]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def check_script(script, voice_text, words):
    problems = []
    n = len(words)
    if not 85 <= n <= 115:
        problems.append(f"Tiene {n} palabras (debe estar entre 85 y 115).")
    low = " ".join(w.display for w in words).lower()
    for b in BANNED:
        if b in low:
            problems.append(f"Expresión prohibida: «{b}».")
    if EMOJI.search(low):
        problems.append("Contiene emojis.")
    catch = script.get("catchphrase")
    if catch and catch.lower().rstrip(".") not in low:
        problems.append(f"Falta la coletilla «{catch}».")
    hook = script["beats"][0]
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script")
    ap.add_argument("--out", help="ruta del MP4 (por defecto videos/<slug>.mp4)")
    ap.add_argument("--estimate", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--contact", action="store_true", help="hoja de contacto cada ~1,5 s")
    ap.add_argument("--stills", help="lista de segundos separados por comas")
    ap.add_argument("--yes", action="store_true", help="no preguntar antes de generar voz")
    ap.add_argument("--dry", action="store_true",
                    help="previsualizar sin voz (tiempos estimados, no gasta créditos)")
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()

    from studio.timeline import parse_beats
    from studio.voice import cached, estimate, load_config

    script = json.loads(Path(a.script).read_text(encoding="utf-8"))
    voice_text, beats, words = parse_beats(script["beats"])
    cfg = load_config()
    chars, credits = estimate(voice_text, cfg)
    slug = script.get("slug", Path(a.script).stem)
    print(f"[{slug}] {len(words)} palabras · {chars} caracteres · ~{credits:.0f} créditos "
          f"({cfg['model_id']}, voz {cfg['voice_name']})")
    problems = check_script(script, voice_text, words)
    for p in problems:
        print("  ⚠", p)
    if a.estimate or a.check:
        if a.check:
            print("  texto hablado:\n  " + voice_text)
        return 0 if not problems else 1

    if not a.dry and not cached(voice_text, cfg):
        if not a.yes:
            if not sys.stdin.isatty():
                print("La voz no está en caché. Repite con --yes para generarla.")
                return 2
            if input(f"¿Generar voz ({chars} caracteres, ~{credits:.0f} créditos)? [s/N] ").lower() != "s":
                return 2
        print("  generando voz con ElevenLabs…")

    from studio.render import Video, render_stills, render_video

    t0 = time.time()
    video = Video(a.script, allow_api=True, dry=a.dry)
    if a.dry:
        slug = slug + "_dry"
        video.slug = slug
    print(f"  voz: {video.audio_dur:.1f} s · vídeo: {video.duration:.2f} s · "
          f"{len(video.scenes)} escenas · preparado en {time.time() - t0:.1f} s")

    if a.contact or a.stills:
        if a.stills:
            times = [float(x) for x in a.stills.split(",")]
        else:
            times = []
            for s in video.scenes:   # un fotograma al principio y otro al final de cada escena
                times.append(round(s.start + min(0.6, s.dur * 0.3), 2))
                if s.dur > 1.6:
                    times.append(round(s.end - 0.35, 2))
        sheet = ROOT / "build" / f"{slug}_contact.png"
        render_stills(video, times, ROOT / "build" / "stills" / slug, sheet=str(sheet))
        print(f"  hoja de contacto: {sheet}")
        return 0

    out = Path(a.out) if a.out else ROOT / "videos" / f"{slug}.mp4"
    elapsed = render_video(video, out, workers=a.workers)
    print(f"  ✔ {out.relative_to(ROOT)} · render {elapsed:.1f} s · total {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
