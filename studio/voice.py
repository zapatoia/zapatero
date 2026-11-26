"""Voz con ElevenLabs (endpoint con timestamps) + caché local.

La clave se lee SOLO de la variable de entorno ELEVENLABS_API_KEY.
Nunca se escribe en disco ni se imprime.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import requests

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "voice.json"
CACHE = ROOT / "build" / "voice_cache"


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def estimate(text: str, cfg: dict | None = None) -> tuple[int, float]:
    cfg = cfg or load_config()
    n = len(text)
    return n, n * cfg.get("credits_per_char", 1.0)


def _key(text, cfg):
    blob = json.dumps({"t": text, "v": cfg["voice_id"], "m": cfg["model_id"],
                       "s": cfg["voice_settings"], "seed": cfg.get("seed"),
                       "f": cfg["output_format"]}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def cached(text: str, cfg: dict | None = None):
    cfg = cfg or load_config()
    k = _key(text, cfg)
    mp3, js = CACHE / f"{k}.mp3", CACHE / f"{k}.json"
    if mp3.exists() and js.exists():
        return mp3, json.loads(js.read_text(encoding="utf-8"))
    return None


def synthesize(text: str, cfg: dict | None = None, allow_api=True):
    """Devuelve (ruta_mp3, alignment). Usa caché si existe: una toma por texto."""
    cfg = cfg or load_config()
    hit = cached(text, cfg)
    if hit:
        return hit
    if not allow_api:
        raise RuntimeError("No hay audio en caché y la llamada a la API no está permitida.")
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("Falta la variable de entorno ELEVENLABS_API_KEY.")
    CACHE.mkdir(parents=True, exist_ok=True)
    url = cfg["endpoint"].format(voice_id=cfg["voice_id"])
    body = {
        "text": text,
        "model_id": cfg["model_id"],
        "language_code": cfg.get("language_code", "es"),
        "voice_settings": cfg["voice_settings"],
    }
    if cfg.get("seed") is not None:
        body["seed"] = cfg["seed"]
    r = requests.post(url, params={"output_format": cfg["output_format"]},
                      headers={"xi-api-key": key}, json=body, timeout=300)
    if not r.ok:
        # nunca mostramos cabeceras (contienen la clave)
        raise RuntimeError(f"ElevenLabs respondió {r.status_code}: {r.text[:300]}")
    d = r.json()
    k = _key(text, cfg)
    mp3 = CACHE / f"{k}.mp3"
    mp3.write_bytes(base64.b64decode(d["audio_base64"]))
    align = d.get("alignment") or d.get("normalized_alignment")
    meta = {"text": text, "model_id": cfg["model_id"], "voice_id": cfg["voice_id"],
            "alignment": align, "normalized_alignment": d.get("normalized_alignment")}
    (CACHE / f"{k}.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return mp3, meta


def decode_audio(path, sr=48000) -> np.ndarray:
    """Decodifica a float32 mono a `sr` Hz con ffmpeg."""
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr),
         "-f", "f32le", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()
