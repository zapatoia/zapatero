#!/usr/bin/env python3
"""Comando único: guion JSON → voz con timestamps → escenas → render → subtítulos → MP4.

  python make_video.py scripts/01-perro-lame.json --dry      # storyboard sin voz (tiempos estimados)
  python make_video.py scripts/01-perro-lame.json --cost     # caracteres/créditos que costaría la voz
  python make_video.py scripts/01-perro-lame.json --tts      # genera la voz (UNA toma, se cachea)
  python make_video.py scripts/01-perro-lame.json            # render final (requiere voz en caché)
  python make_video.py scripts/01-perro-lame.json --contact  # + hoja de fotogramas de revisión

Opciones: --preview (540x960, rápido), --from/--to (segundos), --out ruta.mp4
"""
import argparse
import json
import math
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from retro3d import audio as A  # noqa: E402
from retro3d import voice as V  # noqa: E402
from retro3d.production import Production  # noqa: E402
from retro3d.subtitles import Subtitles  # noqa: E402
from retro3d.style import RENDER  # noqa: E402


def tts_text(script):
    return " ".join(s["text"].strip() for s in script["segments"])


def build_dir(script):
    d = os.path.join(ROOT, "build", script["id"])
    os.makedirs(d, exist_ok=True)
    return d


# ---------------------------------------------------------------- voz → palabras

def prepare_voice(script, bdir, log):
    text = tts_text(script)
    cfg = V.load_config()
    mp3, al = V.synthesize(text, cfg, allow_api=False)
    x = A.decode(mp3)
    words = A.words_from_alignment(al)
    n_script = len(text.split())
    assert len(words) == n_script, f"palabras alineadas {len(words)} != guion {n_script}"
    lag, agree, agree0 = A.check_alignment(x, words)
    log["alignment"] = {"lag_s": lag, "agreement_before": agree0, "agreement_after": agree}
    if abs(lag) >= 0.03:
        A.shift_words(words, lag)
        print(f"  timestamps desplazados {lag:+.2f} s (acuerdo con la envolvente {agree0:.2f} → {agree:.2f})")
    else:
        print(f"  timestamps OK (desfase {lag:+.2f} s, acuerdo {agree0:.2f})")
    y, words, cuts, removed = A.shorten_pauses(x, words)
    log["pauses"] = {"cuts": cuts, "removed_s": removed}
    print(f"  pausas recortadas: {len(cuts)} cortes, {removed:.2f} s eliminados")
    lag2, _, agree3 = A.check_alignment(y, words)
    log["alignment"]["after_trim"] = {"residual_lag_s": lag2, "agreement": agree3}
    print(f"  tras recortar: desfase residual {lag2:+.2f} s, acuerdo {agree3:.2f}")
    wav = os.path.join(bdir, "voice.wav")
    A.write_wav(wav, y)
    with open(os.path.join(bdir, "words.json"), "w") as f:
        json.dump([{k: w[k] for k in ("text", "start", "end")} for w in words], f, ensure_ascii=False, indent=1)
    dur = len(y) / A.SR + 0.25
    return y, words, dur, A.envelope(y)


# ---------------------------------------------------------------- utilidades

def label(img, text, sub=None):
    im = Image.fromarray(img) if isinstance(img, np.ndarray) else img
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(os.path.join(ROOT, "assets/fonts/Montserrat-Black.ttf"), max(14, im.width // 22))
    d.rectangle([0, 0, im.width, f.size * (2.6 if sub else 1.4)], fill=(20, 12, 8))
    d.text((8, 4), text, font=f, fill=(255, 210, 63))
    if sub:
        f2 = f.font_variant(size=int(f.size * 0.8))
        d.text((8, 4 + f.size * 1.2), sub, font=f2, fill=(240, 240, 240))
    return im


def sheet(images, cols, path):
    w, h = images[0].size
    rows = math.ceil(len(images) / cols)
    out = Image.new("RGB", (w * cols, h * rows), (12, 8, 6))
    for i, im in enumerate(images):
        out.paste(im, ((i % cols) * w, (i // cols) * h))
    out.save(path, quality=88)
    return path


def words_text(words, t0, t1):
    return " ".join(w["text"] for w in words if w["start"] < t1 and w["end"] > t0)


# ---------------------------------------------------------------- modos

def storyboard(script, words, dur, bdir, W, H, env=None, name="storyboard"):
    prod = Production(script, words, dur, W, H, env=env)
    subs = Subtitles(words, W, H)
    ims = []
    for i, t0, t1, sh in prod.shot_report():
        t = t0 + (t1 - t0) * 0.6
        img, _ = prod.frame(t)
        img = subs.composite(img, t)
        ims.append(label(img, f"Plano {i + 1}  {t0:.1f}-{t1:.1f}s  ({t1 - t0:.1f}s)",
                         words_text(words, t0, t1)[:60]))
    p = sheet(ims, 5, os.path.join(bdir, name + ".jpg"))
    # informe de duración de planos
    bad = [(i, t1 - t0) for i, t0, t1, _ in prod.shot_report() if t1 - t0 > 3.3 or t1 - t0 < 0.9]
    return p, prod, bad


def render_video(script, words, dur, env, bdir, W, H, t_from=0.0, t_to=None, contact=False, fps=30):
    prod = Production(script, words, dur, W, H, env=env, fps=fps)
    subs = Subtitles(words, W, H)
    t_to = dur if t_to is None else min(t_to, dur)
    n0, n1 = int(t_from * fps), int(math.ceil(t_to * fps))
    vid = os.path.join(bdir, "video.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", vid], stdin=subprocess.PIPE)
    contact_imgs = []
    safe_viol = []
    t_start = time.time()
    for k in range(n0, n1):
        t = k / fps
        img, cam = prod.frame(t)
        bb = subs.bbox(t)
        if bb and (bb[3] > H * 0.8 or bb[2] > W * 0.88):
            safe_viol.append((round(t, 2), bb))
        img = subs.composite(img, t)
        ff.stdin.write(img.tobytes())
        if contact and k % int(fps * 1.0) == 0:
            contact_imgs.append(label(Image.fromarray(img).resize((W // 3, H // 3)), f"{t:.1f}s"))
        if (k - n0) % 90 == 0:
            el = time.time() - t_start
            print(f"  fotograma {k - n0}/{n1 - n0}  ({el:.0f} s, {el / max(1, k - n0 + 1):.2f} s/fot)", flush=True)
    ff.stdin.close()
    ff.wait()
    secs = time.time() - t_start
    cpath = sheet(contact_imgs, 6, os.path.join(bdir, "contact.jpg")) if contact_imgs else None
    return vid, prod, secs, n1 - n0, cpath, safe_viol


def make_audio(prod, voice, dur, bdir, t_from=0.0):
    events = sorted(prod.sfx)
    mix = A.mix(voice, events, dur)
    if t_from:
        mix = mix[int(t_from * A.SR):]
    raw = os.path.join(bdir, "mix_raw.wav")
    A.write_wav(raw, mix)
    norm = os.path.join(bdir, "mix_norm.wav")
    y, L, tp = A.master(mix)
    print(f"  máster: {L:.2f} LUFS, pico verdadero {tp:.2f} dBTP (antes de AAC)")
    A.write_wav(norm, y)
    return norm, events


def mux(vid, aud, out):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", aud, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "44100", "-shortest", "-movflags", "+faststart", out], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--dry", action="store_true", help="storyboard sin voz con tiempos estimados")
    ap.add_argument("--cost", action="store_true", help="muestra caracteres y créditos estimados")
    ap.add_argument("--tts", action="store_true", help="genera la voz (una toma) y la cachea")
    ap.add_argument("--contact", action="store_true", help="hoja de fotogramas de revisión")
    ap.add_argument("--storyboard", action="store_true", help="storyboard con la voz real")
    ap.add_argument("--preview", action="store_true", help="540x960")
    ap.add_argument("--from", dest="t_from", type=float, default=0.0)
    ap.add_argument("--to", dest="t_to", type=float, default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    with open(a.script) as f:
        script = json.load(f)
    bdir = build_dir(script)
    text = tts_text(script)
    W, H = (540, 960) if a.preview else (RENDER["width"], RENDER["height"])
    n_words = len(text.split())
    print(f"Guion «{script['title']}»: {n_words} palabras, {V.estimate(text)} caracteres")

    if a.cost:
        hit = V.cached(text, V.load_config())
        print(f"  coste estimado de la voz: ~{V.estimate(text)} créditos (≈1 por carácter)"
              + ("  [YA EN CACHÉ: coste 0]" if hit else ""))
        return
    if a.dry:
        words, dur = A.estimate_words(text)
        print(f"  duración estimada: {dur:.1f} s")
        p, prod, bad = storyboard(script, words, dur, bdir, 540, 960)
        print(f"  storyboard: {p}")
        for i, d in bad:
            print(f"  ⚠ plano {i + 1} dura {d:.1f} s")
        return
    if a.tts:
        cfg = V.load_config()
        if V.cached(text, cfg):
            print("  La voz ya está en caché; no se gasta nada.")
            return
        print(f"  Generando voz: {len(text)} caracteres…")
        mp3, al = V.synthesize(text, cfg, allow_api=True)
        print(f"  OK → {os.path.relpath(mp3, ROOT)}")
        return

    log = {"script": a.script}
    voice, words, dur, env = prepare_voice(script, bdir, log)
    print(f"  duración final: {dur:.2f} s")
    if a.storyboard:
        p, prod, bad = storyboard(script, words, dur, bdir, 540, 960, env=env, name="storyboard_voz")
        print(f"  storyboard: {p}")
        for i, d in bad:
            print(f"  ⚠ plano {i + 1} dura {d:.1f} s")
        return
    vid, prod, secs, nf, cpath, viol = render_video(script, words, dur, env, bdir, W, H, a.t_from, a.t_to, a.contact)
    print(f"  render: {nf} fotogramas en {secs:.0f} s ({secs / nf:.2f} s/fotograma)")
    aud, events = make_audio(prod, voice, dur if a.t_to is None else a.t_to, bdir, a.t_from)
    out = a.out or os.path.join(ROOT, "videos", script["id"] + ("-preview" if a.preview else "") + ".mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mux(vid, aud, out)
    I, tp = A.ebur128(out)
    print(f"  sonoridad MP4: {I:.1f} LUFS, pico verdadero {tp:.1f} dBTP")
    log.update({"render_s": secs, "frames": nf, "lufs": I, "true_peak": tp, "safe_zone_violations": len(viol),
                "duration": dur, "sfx": len(events)})
    with open(os.path.join(bdir, "report.json"), "w") as f:
        json.dump(log, f, indent=1, default=float)
    if viol:
        print(f"  ⚠ subtítulos fuera de zona segura en {len(viol)} fotogramas")
    if cpath:
        print(f"  hoja de contacto: {cpath}")
    print(f"  → {out}")


if __name__ == "__main__":
    main()
