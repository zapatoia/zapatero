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


def _project_box(prod, cam, pr):
    """Caja en pantalla (px) de un bocadillo/cartel visible, para detectar texto cortado."""
    M = getattr(pr, "_last_M", None)
    if M is None or not pr.parts:
        return None
    pts = []
    for (mn, mx) in getattr(pr, "_bounds", []):
        for x in (mn[0], mx[0]):
            for y in (mn[1], mx[1]):
                for z in (mn[2], mx[2]):
                    pts.append((M @ np.array([x, y, z, 1.0]))[:3])
    if not pts:
        return None
    P = prod.r.project(cam, np.array(pts))
    if (P[:, 2] <= 0).any():
        return None
    return P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max()


def render_video(script, words, dur, env, bdir, W, H, t_from=0.0, t_to=None, contact=False, fps=30):
    prod = Production(script, words, dur, W, H, env=env, fps=fps)
    subs = Subtitles(words, W, H)
    t_to = dur if t_to is None else min(t_to, dur)
    n0, n1 = int(t_from * fps), int(math.ceil(t_to * fps))
    vid = os.path.join(bdir, "video.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", vid], stdin=subprocess.PIPE)
    shots = prod.shot_report()
    mids = {int(round((t0 + (t1 - t0) * 0.6) * fps)): i for i, t0, t1, _ in shots}
    qa = {"penetrations": [], "safe_zone": [], "text_cut": [], "contacts": [], "shot_frames": {},
          "mouth_agree": [], "floating": []}
    first_contact = {}
    t_start = time.time()
    for k in range(n0, n1):
        t = k / fps
        img, cam = prod.frame(t)
        # 1) interpenetraciones (volúmenes de colisión por pieza)
        for a_, b_, dep in prod.check_penetrations():
            qa["penetrations"].append((round(t, 2), f"{a_.owner}.{a_.node}", f"{b_.owner}.{b_.node}", round(dep, 3)))
        # 2) pies: ninguno por debajo del suelo ni flotando fuera de un salto
        for name, ch in prod.cast.items():
            from retro3d import physics as PH
            gz = prod.world.height(ch.transform[0, 3], ch.transform[1, 3])
            dz = PH.lowest(ch, ch.FEET) - gz
            air = ch.kind == "dog" and np.asarray(ch.cur_pose.get("root.p", np.zeros(3)))[2] > 0.005
            if dz < -0.015 or (dz > 0.02 and not air):
                qa["floating"].append((round(t, 2), name, round(float(dz), 3)))
        # 3) contactos lengua→superficie
        for name, info in getattr(prod, "contacts", {}).items():
            if info.get("contact"):
                acts = [e for e in prod.cast[name].timeline if e[0] <= t and e[1] in ("lick", "lick_paw")]
                key = (name, acts[-1][0] if acts else 0)
                if key not in first_contact:
                    first_contact[key] = t
                    qa["contacts"].append((round(t, 2), name, info.get("gap")))
        # 4) textos 3D cortados (bocadillos / carteles visibles)
        for pr in prod.props:
            if getattr(pr, "text_spec", None) is not None and pr.alive(t) and pr.alpha_at(t) > 0.5 and pr.scale_at(t) > 0.95:
                bx = _project_box(prod, cam, pr)
                if bx and (bx[0] < 0 or bx[1] < 0 or bx[2] > W or bx[3] > H):
                    qa["text_cut"].append((round(t, 2), [round(v) for v in bx]))
        # 5) subtítulos en zona segura
        bb = subs.bbox(t)
        if bb and (bb[3] > H * 0.8 or bb[2] > W * 0.88 or bb[0] < 0 or bb[1] < 0):
            qa["safe_zone"].append((round(t, 2), bb))
        img = subs.composite(img, t)
        ff.stdin.write(img.tobytes())
        if k in mids:
            i = mids[k]
            t0_, t1_ = shots[i][1], shots[i][2]
            sh = shots[i][3]
            qa["shot_frames"][i] = label(Image.fromarray(img).resize((W // 2, H // 2)),
                                         f"{i + 1} {sh.get('type')}/{sh.get('size', 'medium')} {t1_ - t0_:.1f}s",
                                         words_text(words, t0_, t1_)[:44])
        # 6) boca: abierta cuando hay voz, cerrada en silencio
        if env is not None:
            lv = prod.lips.level(t)
            m = prod.mouth[min(k, len(prod.mouth) - 1)]
            qa["mouth_agree"].append((lv > 0.12) == (m != "X") or 0.08 < lv < 0.16)
        if (k - n0) % 90 == 0:
            el = time.time() - t_start
            print(f"  fotograma {k - n0}/{n1 - n0}  ({el:.0f} s, {el / max(1, k - n0 + 1):.2f} s/fot)", flush=True)
    ff.stdin.close()
    ff.wait()
    secs = time.time() - t_start
    # hoja de contacto: 1 fotograma por plano
    ims = [qa["shot_frames"][i] for i in sorted(qa["shot_frames"])]
    cpath = sheet(ims, 6, os.path.join(bdir, "contact.jpg")) if ims else None
    ctpath = contact_closeups(prod, qa["contacts"], bdir, W, H)
    qa["render_s"] = secs
    return vid, prod, secs, n1 - n0, cpath, qa, ctpath


def contact_closeups(prod, contacts, bdir, W, H):
    """Primer plano de cada momento de contacto (lado y 3/4 elevado) para revisión."""
    from retro3d.render import Camera
    closes = []
    for (t, name, gap) in contacts:
        prod.frame(t)
        dog = prod.cast[name]
        tip = (dog.world_matrices()["tongue"] @ np.array([0, -0.15, 0, 1.0]))[:3]   # punta = punto de contacto
        yaw = math.atan2(-dog.transform[0, 1], dog.transform[1, 1])
        for az, el, lab_ in ((90, 0.15, "lado"), (50, 0.5, "3/4 alto")):
            a_ = yaw + math.radians(az)
            eye = tip + np.array([math.sin(a_), -math.cos(a_), el]) * 1.7
            img, _ = prod.frame(t, cam=Camera(eye, tip, 32))
            closes.append(label(Image.fromarray(img).crop((0, H // 2 - W // 2, W, H // 2 + W // 2)).resize((400, 400)),
                                f"{name} {t:.2f}s {lab_}"))
    return sheet(closes, 4, os.path.join(bdir, "contactos.jpg")) if closes else None


def write_qa(prod, qa, bdir, lufs=None, tp=None, sfx_rep=None):
    from retro3d import camera as CAM
    issues = CAM.validate(prod.shots, prod.duration)
    L = ["# Revisión automática antes de entregar", ""]
    L.append(f"- Planos: {len(prod.shots)}; reglas de montaje: " + ("OK" if not issues else f"{len(issues)} avisos"))
    L += [f"  - {x}" for x in issues]
    clr = min(prod.clearance.values()) if prod.clearance else None
    L.append(f"- Cámara dentro de modelos/suelo: holgura mínima {clr:.2f} m (mín. exigido {prod.MIN_CLEAR} m)" if clr is not None else "- Cámara: sin datos")
    L.append(f"- Interpenetraciones (>{2} cm) en fotogramas: {len(qa['penetrations'])}")
    for x in qa["penetrations"][:15]:
        L.append(f"  - {x}")
    L.append(f"- Pies hundidos/flotando: {len(qa['floating'])}")
    for x in qa["floating"][:10]:
        L.append(f"  - {x}")
    L.append(f"- Contactos lengua→superficie detectados: {len(qa['contacts'])} (ver contactos.jpg)")
    L.append(f"- Subtítulos fuera de zona segura: {len(qa['safe_zone'])}")
    L.append(f"- Textos 3D cortados por el borde: {len(qa['text_cut'])}")
    for x in qa["text_cut"][:10]:
        L.append(f"  - {x}")
    if qa["mouth_agree"]:
        L.append(f"- Boca abierta/cerrada coherente con la voz: {100 * np.mean(qa['mouth_agree']):.1f} % de fotogramas")
    if lufs is not None:
        L.append(f"- Sonoridad MP4: {lufs:.1f} LUFS, pico verdadero {tp:.1f} dBTP")
    if sfx_rep is not None:
        L.append(f"- Efectos: {len(sfx_rep['events'])} eventos; sostenidos >1 s: {len(sfx_rep['sustained_over_1s'])}")
    with open(os.path.join(bdir, "qa.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    return issues


def make_audio(prod, voice, dur, bdir, t_from=0.0):
    events = sorted(prod.sfx, key=lambda e: e["t"])
    mix, bus, detail = A.mix(voice, events, dur, ambience_db=prod.script.get("ambience_db"))
    scenes = []
    for i, t0, t1, sh in prod.shot_report():
        scenes.append((f"plano {i + 1}", t0, t1))
    rep = A.sfx_report(bus, detail, voice, scenes)
    prod.sfx_rep = rep
    with open(os.path.join(bdir, "sfx_report.json"), "w") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    write_sfx_md(rep, os.path.join(bdir, "sfx_report.md"))
    print(f"  efectos: {len(detail)} eventos, sostenidos >1 s: {len(rep['sustained_over_1s'])}")
    if t_from:
        mix = mix[int(t_from * A.SR):]
    raw = os.path.join(bdir, "mix_raw.wav")
    A.write_wav(raw, mix)
    norm = os.path.join(bdir, "mix_norm.wav")
    y, L, tp = A.master(mix)
    print(f"  máster: {L:.2f} LUFS, pico verdadero {tp:.2f} dBTP (antes de AAC)")
    A.write_wav(norm, y)
    return norm, events


def write_sfx_md(rep, path):
    L = ["# Efectos de sonido", "", f"RMS de la voz hablada: {rep['voice_rms_dbfs']} dBFS. "
         "Niveles relativos a la voz (regla: entre -18 y -24 dB), con atenuación extra de 6 dB mientras se habla.", "",
         "| # | tiempo (s) | tipo | dur (s) | nivel vs voz | motivo |", "|---|---|---|---|---|---|"]
    for i, e in enumerate(rep["events"], 1):
        L.append(f"| {i} | {e['t']:.2f} | {e['type']} | {e['dur']} | {e['rel_db']} dB | {e.get('why', '')} |")
    L += ["", "## Energía del bus de efectos por plano", "", "| plano | inicio | fin | eventos | RMS efectos vs voz |",
          "|---|---|---|---|---|"]
    for sc in rep["scenes"]:
        lv = "silencio" if sc["events"] == 0 else f"{sc['sfx_rms_db_rel_voice']} dB"
        L.append(f"| {sc['scene']} | {sc['start']} | {sc['end']} | {sc['events']} | {lv} |")
    L += ["", "## Sonidos sostenidos > 1 s", ""]
    L += [f"- {x['start']}-{x['end']} s" for x in rep["sustained_over_1s"]] or ["Ninguno."]
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


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
    vid, prod, secs, nf, cpath, qa, ctpath = render_video(script, words, dur, env, bdir, W, H, a.t_from, a.t_to, a.contact)
    viol = qa["safe_zone"]
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
    issues = write_qa(prod, qa, bdir, I, tp, getattr(prod, "sfx_rep", None))
    print(open(os.path.join(bdir, "qa.md")).read())
    if ctpath:
        print(f"  primeros planos de contactos: {ctpath}")
    if cpath:
        print(f"  hoja de contacto: {cpath}")
    print(f"  → {out}")


if __name__ == "__main__":
    main()
