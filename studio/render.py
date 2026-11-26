"""Montaje: guion → voz → escenas → cámara/transiciones → subtítulos → MP4."""
from __future__ import annotations

import json
import math
import multiprocessing as mp
import os
import random
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import skia

from . import sfx as SFX
from . import style as S
from .captions import Captions, draw_disclaimer
from .scenes import HERO_SCENES, SCENES, Ctx
from .shoe import ShoeAnimator
from .style import C, FPS, H, W, clamp, ease_in_out, ease_out, ease_out_back, prog
from .timeline import Envelope, LipSync, apply_alignment, parse_beats, refine_alignment
from .voice import decode_audio, estimate, load_config, synthesize

ROOT = Path(__file__).resolve().parent.parent
LEAD = 0.20     # silencio antes de la voz
TAIL = 1.35     # tiempo tras la última palabra (cierre + aviso legal)
TRANS = 0.40    # duración de transición entre escenas


@dataclass
class Scene:
    index: int
    type: str
    params: dict
    start: float
    end: float
    words: list = field(default_factory=list)
    first_hero: bool = False

    @property
    def dur(self):
        return self.end - self.start

    @property
    def hero(self):
        return self.type in HERO_SCENES


def new_surface():
    info = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    return skia.Surface.MakeRaster(info)


class Video:
    def __init__(self, script_path, allow_api=True, dry=False):
        self.script_path = Path(script_path)
        self.script = json.loads(self.script_path.read_text(encoding="utf-8"))
        self.slug = self.script.get("slug", self.script_path.stem)
        self.voice_text, self.beats, self.words = parse_beats(self.script["beats"])
        self.cfg = load_config()
        self.dry = dry
        if dry:   # previsualización sin voz: tiempos estimados y audio sintético
            align, self.pcm = fake_voice(self.voice_text)
            self.mp3 = None
            self.audio_dur = len(self.pcm) / SFX.SR
        else:
            self.mp3, meta = synthesize(self.voice_text, self.cfg, allow_api=allow_api)
            self.pcm = decode_audio(self.mp3, SFX.SR)
            self.audio_dur = len(self.pcm) / SFX.SR
            align = refine_alignment(meta["alignment"], self.pcm, SFX.SR)
        apply_alignment(self.words, self.beats, align, self.audio_dur)
        # desplazar todo por LEAD
        for w in self.words:
            w.start += LEAD
            w.end += LEAD
        for i, b in enumerate(self.beats):
            b.start = 0.0 if i == 0 else b.start + LEAD
        self.speech_end = self.words[-1].end
        self.duration = round((self.speech_end + TAIL) * FPS) / FPS
        for i, b in enumerate(self.beats):
            b.end = self.beats[i + 1].start if i + 1 < len(self.beats) else self.duration
        shifted = dict(align)
        shifted["character_start_times_seconds"] = [x + LEAD for x in align["character_start_times_seconds"]]
        shifted["character_end_times_seconds"] = [x + LEAD for x in align["character_end_times_seconds"]]
        self.envelope = Envelope(self.pcm, SFX.SR, offset=LEAD)
        self.lip = LipSync(shifted, self.envelope, self.duration + 0.5)
        # escenas
        self.scenes = []
        seen_hero = False
        for b in self.beats:
            sc = dict(b.scene)
            if sc.get("continue") and self.scenes:
                prev = self.scenes[-1]
                prev.end = b.end
                prev.words = prev.words + b.words
                continue
            typ = sc.pop("type", "shoe")
            s = Scene(len(self.scenes), typ, sc, b.start, b.end, list(b.words))
            if s.hero and not seen_hero:
                s.first_hero = True
                seen_hero = True
            self.scenes.append(s)
        self.animator = ShoeAnimator(seed=self.script.get("seed", 11), visemes=self.lip,
                                     events=self._shoe_events(), energy=self.envelope,
                                     base_emotion="neutral")
        self.captions = Captions(self.words, self.duration)
        self.sfx_cues = self._sfx_cues()
        self.canvas = None
        self.surface = None

    # ------------------------------------------------------------ personaje
    def _shoe_events(self):
        ev = []
        rnd = random.Random(5)
        arm_cycle = ["open", "point", "raise", "open"]
        hero_count = 0
        for i, s in enumerate(self.scenes):
            prev = self.scenes[i - 1] if i else None
            p = s.params
            emo = p.get("emotion", "neutral")
            ev.append(dict(t=s.start, kind="emotion", name=emo))
            if s.hero:
                if prev is None or not prev.hero:
                    ev.append(dict(t=s.start, kind="land", height=1000))
                    arm_t = s.start + 0.45
                else:
                    ev.append(dict(t=s.start, kind="hop", height=55, spin=rnd.choice([-5, 5])))
                    arm_t = s.start + 0.15
                arms = p.get("arms", arm_cycle[hero_count % len(arm_cycle)])
                hero_count += 1
                far = p.get("arms_far", "open" if arms == "open" else "none")
                ev.append(dict(t=arm_t, kind="arms", near=arms, far=far,
                               angle=p.get("point_angle", -55)))
                ev.append(dict(t=s.start, kind="look", x=p.get("look_x", 0.45),
                               y=p.get("look_y", -0.15 if p.get("prop") else 0.05)))
                if s.dur > 2.0:
                    nxt = self.scenes[i + 1] if i + 1 < len(self.scenes) else None
                    if not (nxt and nxt.hero):
                        ev.append(dict(t=s.end - 0.3, kind="arms", near="none", far="none"))
            else:
                ev.append(dict(t=s.start, kind="arms", near=p.get("mini_arms", "point"),
                               far="none", angle=p.get("mini_angle", -58)))
                ev.append(dict(t=s.start, kind="look", x=0.6, y=-0.55))
            # gestos dentro de la escena: inicio de cada frase y palabras enfatizadas
            for j, w in enumerate(s.words):
                prevw = s.words[j - 1] if j else None
                if prevw is not None and prevw.sentence_end:
                    kind = rnd.choice(["tilt", "nod", "hop"] if s.hero else ["tilt", "nod"])
                    if kind == "tilt":
                        ev.append(dict(t=w.start - 0.05, kind="tilt", angle=rnd.choice([-7, 6, -5]),
                                       hold=0.7))
                    elif kind == "hop":
                        ev.append(dict(t=w.start - 0.1, kind="hop", height=40))
                    else:
                        ev.append(dict(t=w.start - 0.05, kind="nod"))
                if w.emph:
                    ev.append(dict(t=w.start - 0.05, kind="brow"))
                    if s.hero:
                        ev.append(dict(t=w.start - 0.08, kind="tilt", angle=-6, hold=0.35))
        # mirar a cámara/abajo de vez en cuando para que los ojos vivan
        return ev

    # ------------------------------------------------------------ sonido
    def _sfx_cues(self):
        cues = []
        for i, s in enumerate(self.scenes):
            prev = self.scenes[i - 1] if i else None
            if prev is not None and not (prev.hero and s.hero):
                cues.append(dict(t=s.start - 0.16, kind="whoosh", var=i))
            if s.hero and (prev is None or not prev.hero):
                cues.append(dict(t=s.start + 0.33, kind="thud"))
            if not s.hero:
                cues.append(dict(t=s.start + 0.12, kind="pop", var=i))
            p = s.params
            if s.type == "big_number":
                t0 = s.start + _local_at(s, p.get("at"), 0.05)
                cd = p.get("count_dur", 0.9)
                k = 0.0
                while k < cd:
                    cues.append(dict(t=t0 + k, kind="tick"))
                    k += 0.07 + k * 0.08
                cues.append(dict(t=t0 + cd, kind="ding"))
            if s.type == "stamp" or (p.get("prop") or {}).get("kind") == "stamp":
                at = p.get("at") if s.type == "stamp" else p["prop"].get("at")
                cues.append(dict(t=s.start + _local_at(s, at, 0.15) + 0.3, kind="stamp"))
            if s.type in ("checklist", "updown", "timeline", "search", "flow"):
                for key in ("items", "rows", "points", "results", "nodes"):
                    for j, it in enumerate(p.get(key, [])):
                        if it.get("at"):
                            cues.append(dict(t=s.start + _local_at(s, it["at"], 0), kind="pop", var=j))
            if s.type == "outro":
                cues.append(dict(t=s.start + 0.5, kind="ding"))
            if (p.get("prop") or {}).get("kind") in ("icon", "sign", "bubble", "icons"):
                cues.append(dict(t=s.start + _local_at(s, p["prop"].get("at"), 0.12), kind="pop", var=i))
        return cues

    # ------------------------------------------------------------ cámara
    def camera(self, t, s):
        u = clamp((t - s.start) / max(0.1, s.dur))
        zoom = 1.0 + 0.04 * ease_in_out(u)
        for w in s.words:
            if w.emph and w.start - 0.05 <= t:
                dt = t - (w.start - 0.05)
                zoom += 0.045 * (1 - math.exp(-22 * dt)) * math.exp(-3.2 * dt)
        cam_x = 14 * math.sin(t * 0.55) + (s.index % 2 * 2 - 1) * 10 * ease_in_out(u)
        cam_y = 10 * math.sin(t * 0.41 + 1)
        return zoom, cam_x, cam_y

    def scene_at(self, t):
        for s in self.scenes:
            if s.start <= t < s.end:
                return s
        return self.scenes[-1]

    def draw_scene(self, s, t, dx=0.0, dy=0.0, zoom_extra=1.0, alpha=1.0, skip_shoe=False):
        c = self.canvas
        zoom, cx, cy = self.camera(t, s)
        zoom *= zoom_extra
        if alpha < 0.999:
            c.saveLayerAlpha(None, int(255 * clamp(alpha)))
        else:
            c.save()
        c.translate(W / 2 + dx - cx * 0.35, 760 + dy - cy * 0.35)
        c.scale(zoom, zoom)
        c.translate(-W / 2, -760)
        ctx = Ctx(self, s, t - s.start, s.start)
        if skip_shoe:
            ctx.shoe = lambda *a, **k: None
            ctx.mini_shoe = lambda *a, **k: None
        SCENES[s.type](c, ctx)
        c.restore()

    def render_frame(self, f):
        if self.surface is None:
            self.surface = new_surface()
            self.canvas = self.surface.getCanvas()
        t = f / FPS
        c = self.canvas
        s = self.scene_at(t)
        zoom, cam_x, cam_y = self.camera(t, s)
        S.draw_background(c, cam_x, cam_y, t)
        # ¿estamos en una transición?
        drawn = False
        i = s.index
        nxt = self.scenes[i + 1] if i + 1 < len(self.scenes) else None
        prv = self.scenes[i - 1] if i > 0 else None
        for a, b in ((prv, s), (s, nxt)):
            if a is None or b is None:
                continue
            tb = b.start
            t0 = tb - TRANS * 0.35
            if not (t0 <= t < t0 + TRANS):
                continue
            u = (t - t0) / TRANS
            if a.hero and b.hero:
                # el zapato sigue (da un saltito); el atrezo viejo se encoge y se va
                if t < tb:
                    self.draw_scene(a, t)
                else:
                    fade = 1 - (t - tb) / 0.18
                    if fade > 0:
                        self.draw_scene(a, t, alpha=fade, zoom_extra=0.92 + 0.08 * fade,
                                        skip_shoe=True)
                    self.draw_scene(b, t)
                drawn = True
            elif b.hero:
                # la infografía sale deslizándose; el zapato cae desde arriba
                e = ease_in_out(u)
                self.draw_scene(a, t, dx=-W * 1.05 * e, alpha=1 - 0.3 * e)
                if t >= tb:
                    self.draw_scene(b, t)
                drawn = True
            else:
                style = ("slide", "zoom", "slide_up")[b.index % 3]
                e = ease_in_out(u)
                if style == "zoom":
                    self.draw_scene(a, t, zoom_extra=1 + 0.35 * e, alpha=1 - e)
                    k = ease_out_back(clamp((u - 0.2) / 0.8), 1.4)
                    if u > 0.2:
                        self.draw_scene(b, t, zoom_extra=0.75 + 0.25 * k, alpha=clamp((u - 0.2) * 3))
                elif style == "slide_up":
                    self.draw_scene(a, t, dy=-H * 0.6 * e, alpha=1 - e)
                    self.draw_scene(b, t, dy=H * 0.6 * (1 - ease_out_back(u, 1.0)), alpha=clamp(u * 2.5))
                else:
                    d = 1 if b.index % 2 else -1
                    self.draw_scene(a, t, dx=-d * W * 1.05 * e)
                    self.draw_scene(b, t, dx=d * W * 1.05 * (1 - ease_out_back(u, 0.9)))
                drawn = True
            break
        if not drawn:
            self.draw_scene(s, t)
        # capa fija: subtítulos y aviso legal
        self.captions.draw(c, t)
        draw_disclaimer(c, t, self.duration)
        return self.surface.makeImageSnapshot()

    # ------------------------------------------------------------ salida
    def frame_count(self):
        return int(round(self.duration * FPS))

    def build_audio(self, workdir):
        sfx = SFX.render_sfx(self.sfx_cues, self.duration)
        mixed = SFX.mix(self.pcm, LEAD, sfx, self.duration)
        wav = Path(workdir) / "mix.wav"
        SFX.write_wav(wav, mixed)
        return wav


def fake_voice(text):
    """Alineamiento estimado (~14 caracteres/s) y audio sintético para --dry."""
    chars, st, en = [], [], []
    t = 0.0
    for ch in text:
        d = {" ": 0.035, ",": 0.2, ".": 0.45, "?": 0.45, "!": 0.4, ":": 0.25, "…": 0.4}.get(ch, 0.047)
        chars.append(ch)
        st.append(t)
        en.append(t + d)
        t += d
    sr = SFX.SR
    n = int((t + 0.2) * sr)
    pcm = np.zeros(n, dtype=np.float32)
    rng = np.random.default_rng(1)
    for ch, a, b in zip(chars, st, en):
        if ch.isalpha():
            i, j = int(a * sr), int(b * sr)
            amp = 0.3 if ch.lower() in "aeiouáéíóú" else 0.12
            pcm[i:j] = rng.standard_normal(j - i).astype(np.float32) * amp
    return {"characters": chars, "character_start_times_seconds": st,
            "character_end_times_seconds": en}, pcm


def _local_at(s, word, default):
    if word is None:
        return default
    key = str(word).lower().strip("*¿?¡!.,:;")
    for w in s.words:
        d = w.display.lower().strip("¿?¡!.,:;«»\"")
        if d.startswith(key):
            return w.start - s.start
    return default


# ---------------------------------------------------------------- render paralelo
_VIDEO: Video | None = None


def _render_chunk(args):
    a, b, path = args
    v = _VIDEO
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
         "-pix_fmt", "yuv420p", "-threads", "2", "-g", "60", str(path)],
        stdin=subprocess.PIPE)
    for f in range(a, b):
        img = v.render_frame(f)
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    return path


def render_video(video: Video, out_path, workers=None, log=print):
    global _VIDEO
    _VIDEO = video
    out_path = Path(out_path)
    work = ROOT / "build" / video.slug
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    n = video.frame_count()
    workers = workers or max(1, min(4, os.cpu_count() or 1))
    bounds = np.linspace(0, n, workers + 1).astype(int)
    jobs = [(int(bounds[i]), int(bounds[i + 1]), work / f"part{i:02d}.mp4") for i in range(workers)]
    t0 = time.time()
    with mp.get_context("fork").Pool(workers) as pool:
        parts = pool.map(_render_chunk, jobs)
    t_frames = time.time() - t0
    log(f"  fotogramas: {n} en {t_frames:.1f} s ({n / t_frames:.1f} fps)")
    lst = work / "parts.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    wav = video.build_audio(work)
    af = SFX.loudnorm_filter(wav)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", af,
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                    "-movflags", "+faststart", "-shortest", str(out_path)], check=True)
    return time.time() - t0


def render_stills(video: Video, times, out_dir, sheet=None, cols=4, scale=0.25):
    from PIL import Image
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ims = []
    for t in times:
        f = min(video.frame_count() - 1, int(round(t * FPS)))
        img = video.render_frame(f)
        arr = img.toarray(colorType=skia.kRGBA_8888_ColorType)[:, :, :3]
        im = Image.fromarray(arr)
        im.save(out_dir / f"{video.slug}_{t:06.2f}.png")
        ims.append(im)
    if sheet and ims:
        w, h = int(W * scale), int(H * scale)
        rows = math.ceil(len(ims) / cols)
        out = Image.new("RGB", (w * cols, h * rows), (14, 26, 43))
        from PIL import ImageDraw
        d = ImageDraw.Draw(out)
        for i, (im, t) in enumerate(zip(ims, times)):
            x, y = (i % cols) * w, (i // cols) * h
            out.paste(im.resize((w, h), Image.LANCZOS), (x, y))
            d.rectangle([x, y, x + 64, y + 22], fill=(0, 0, 0))
            d.text((x + 4, y + 4), f"{t:.2f}s", fill=(255, 255, 0))
        out.save(sheet)
    return ims
