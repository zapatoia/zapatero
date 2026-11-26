#!/usr/bin/env python3
"""Hoja de diseño del narrador: vistas (frente, 3/4, perfil, espalda), 5 bocas,
6 expresiones, 5 poses y un clip de 3 s hablando (con la voz en caché del vídeo 01).
Uso: python tools/narrator_sheet.py [salida_dir]"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from retro3d.render import Renderer, Camera, Item  # noqa
from retro3d import mesh as M  # noqa
from retro3d.characters.narrator import Narrator  # noqa
from retro3d.lipsync import LipSync  # noqa
from retro3d import audio as A  # noqa

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "build", "narrador")
os.makedirs(OUT, exist_ok=True)
FONT = ImageFont.truetype(os.path.join(ROOT, "assets/fonts/Montserrat-Black.ttf"), 26)

W, H = 540, 960
r = Renderer(W, H)
floor = M.cylinder(6, 6, 0.02, 24, (0.86, 0.80, 0.70, 1), center=(0, 0, -0.01))
studio = [Item(r.upload(floor), np.eye(4), tex="white")]
n = Narrator()
n.upload(r)
print("triángulos narrador:", n.tri_count())


def lab(img, text):
    im = Image.fromarray(img) if isinstance(img, np.ndarray) else img
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, 38], fill=(24, 16, 20))
    d.text((10, 4), text, font=FONT, fill=(255, 210, 63))
    return im


def pose(act, t=1.2, **params):
    n.timeline = [(0, act, params)]
    n._last_t = None
    n.face_override = None
    n.update(t)


def shot(az, dist=3.4, h=0.95, el=8, fov=36, tgt=None):
    a, e = math.radians(az), math.radians(el)
    P = np.array([0, 0, h]) if tgt is None else np.asarray(tgt)
    eye = P + np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)]) * dist
    r.shadow_center = np.zeros(3); r.shadow_radius = 4
    return r.render(Camera(eye, P, fov), studio + n.items())


def face_shot(az=0):
    return Image.fromarray(shot(az, dist=1.9, tgt=(0, 0, 1.4), el=4, fov=30)).crop((40, 250, 500, 710)).resize((360, 360))


def row(ims, path=None):
    w = sum(i.width for i in ims); h = max(i.height for i in ims)
    o = Image.new("RGB", (w, h), (24, 16, 20)); x = 0
    for i in ims:
        o.paste(i, (x, 0)); x += i.width
    return o


# 1) vistas
pose("idle", t=0.0)
views = [lab(Image.fromarray(shot(az)).crop((0, 80, 540, 880)), name) for az, name in
         ((0, "FRENTE"), (38, "3/4"), (90, "PERFIL"), (180, "ESPALDA"))]
# 2) bocas
mouths = []
for m in ["X", "M", "E", "A", "O"]:
    pose("idle", t=0.0)
    n.face_override = lambda t, f, m=m: {"mouth": m}
    n._last_t = None; n.update(0.0)
    mouths.append(lab(face_shot(), f"BOCA {m}"))
# 3) expresiones
exprs = []
for e in ["neutral", "happy", "surprised", "angry", "sad", "skeptical"]:
    pose("idle", t=0.0, expr=e)
    exprs.append(lab(face_shot(), e.upper()))
# 4) poses
poses = []
for act, kw, az in (("explain", {}, 15), ("point", {"side": "L"}, 20), ("shrug", {}, 10),
                    ("cross_arms", {}, 20), ("wave", {"side": "R"}, 10)):
    pose(act, t=1.0, **kw)
    poses.append(lab(Image.fromarray(shot(az)).crop((0, 80, 540, 880)), act.upper()))

sheet_v = row(views)
sheet_m = row(mouths)
sheet_e = row(exprs)
sheet_p = row(poses)
Wt = max(x.width for x in (sheet_v, sheet_m, sheet_e, sheet_p))
o = Image.new("RGB", (Wt, sum(x.height for x in (sheet_v, sheet_m, sheet_e, sheet_p))), (24, 16, 20))
y = 0
for x in (sheet_v, sheet_m, sheet_e, sheet_p):
    o.paste(x, (0, y)); y += x.height
o.save(os.path.join(OUT, "narrador_hoja.jpg"), quality=90)

# 5) clip de 3 s hablando (voz en caché del vídeo 01, sin gastar créditos)
bdir = os.path.join(ROOT, "build", "01-perro-lame")
words = json.load(open(os.path.join(bdir, "words.json")))
voice = A.decode(os.path.join(bdir, "voice.wav"))
t0, dur, fps = 2.15, 3.0, 30
seg_words = [dict(w, chars=[(c, w["start"] - t0 + (w["end"] - w["start"]) * i / max(1, len(w["text"])),
                             w["start"] - t0 + (w["end"] - w["start"]) * (i + 1) / max(1, len(w["text"]))) for i, c in enumerate(w["text"])],
                  start=w["start"] - t0, end=w["end"] - t0) for w in words if t0 - 0.2 < w["start"] < t0 + dur]
clip = voice[int(t0 * A.SR):int((t0 + dur) * A.SR)]
env = A.envelope(clip)
lips = LipSync(seg_words, env)
mouth = lips.state_frames(int(dur * fps) + 2, fps)
n2 = Narrator(); n2.upload(r)
n2.timeline = [(0, "talk", {})]
n2.env_fn = lambda t: lips.level(t)
n2.face_override = lambda t, f: {"mouth": mouth[min(int(round(t * fps)), len(mouth) - 1)]} if lips.level(t) > 0.05 else None
n2.set_beats([w["start"] for w in seg_words if len(w["text"]) >= 4][::2])
VW, VH = 720, 1280
r2 = Renderer(VW, VH)
r2.add_texture("face_narr", r.textures and __import__("retro3d.textures", fromlist=["x"]).balaclava_atlas(
    n.cfg["palette"]["skin"], n.cfg["palette"]["ink"], n.cfg["palette"]["balaclava_dark"])[0], repeat=False)
n3 = Narrator(); n3.upload(r2)
n3.timeline, n3.env_fn, n3.face_override = n2.timeline, n2.env_fn, n2.face_override
n3.set_beats([b[0] for b in n2.beats])
floor2 = [Item(r2.upload(floor), np.eye(4), tex="white")]
wav = os.path.join(OUT, "clip.wav"); A.write_wav(wav, clip)
vid = os.path.join(OUT, "clip_noaudio.mp4")
ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}", "-r", str(fps),
                       "-i", "-", "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
for k in range(int(dur * fps)):
    t = k / fps
    n3.update(t)
    u = t / dur
    d = 2.9 - 0.5 * (u * u * (3 - 2 * u))
    a = math.radians(12 - 14 * u)
    P = np.array([0, 0, 1.15])
    eye = P + np.array([math.sin(a), -math.cos(a), 0.15]) * d
    r2.shadow_center = np.zeros(3); r2.shadow_radius = 4
    ff.stdin.write(r2.render(Camera(eye, P, 36), floor2 + n3.items()).tobytes())
ff.stdin.close(); ff.wait()
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                "-shortest", os.path.join(OUT, "narrador_clip_3s.mp4")], check=True)
os.remove(vid)
print("→", OUT)
