"""ElevenLabs con timestamps y caché en disco.

La clave se lee SOLO de la variable de entorno (nunca se guarda ni se imprime).
La caché se indexa por hash de (configuración + texto): pedir dos veces el
mismo texto no gasta créditos.
"""
import base64
import hashlib
import json
import os
import ssl
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "voice")


def load_config(path=None):
    with open(path or os.path.join(ROOT, "config", "voice.json")) as f:
        return json.load(f)


def cache_key(text, cfg):
    payload = {k: cfg[k] for k in ("voice_id", "model_id", "language_code", "voice_settings", "output_format")}
    payload["text"] = text
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]


def cached(text, cfg):
    k = cache_key(text, cfg)
    mp3 = os.path.join(CACHE, k + ".mp3")
    js = os.path.join(CACHE, k + ".json")
    return (mp3, js) if os.path.exists(mp3) and os.path.exists(js) else None


def estimate(text):
    """Caracteres que se facturan (≈ 1 crédito por carácter en eleven_v3)."""
    return len(text)


def synthesize(text, cfg=None, allow_api=True):
    """Devuelve (ruta_mp3, alineación dict). Usa la caché si existe."""
    cfg = cfg or load_config()
    hit = cached(text, cfg)
    if hit:
        with open(hit[1]) as f:
            return hit[0], json.load(f)["alignment"]
    if not allow_api:
        raise RuntimeError("Audio no cacheado y API desactivada")
    key = os.environ.get(cfg.get("api_key_env", "ELEVENLABS_API_KEY"))
    if not key:
        raise RuntimeError("Falta ELEVENLABS_API_KEY en el entorno")
    url = cfg["endpoint"].format(voice_id=cfg["voice_id"]) + "?output_format=" + cfg["output_format"]
    body = json.dumps({"text": text, "model_id": cfg["model_id"], "language_code": cfg["language_code"],
                       "voice_settings": cfg["voice_settings"]}).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    ctx = ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or None)
    try:
        with urllib.request.urlopen(req, timeout=300, context=ctx) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"ElevenLabs HTTP {e.code}: {e.read()[:300]!r}") from None
    os.makedirs(CACHE, exist_ok=True)
    k = cache_key(text, cfg)
    mp3 = os.path.join(CACHE, k + ".mp3")
    with open(mp3, "wb") as f:
        f.write(base64.b64decode(data["audio_base64"]))
    with open(os.path.join(CACHE, k + ".json"), "w") as f:
        json.dump({"text": text, "alignment": data["alignment"],
                   "normalized_alignment": data.get("normalized_alignment")}, f, ensure_ascii=False)
    return mp3, data["alignment"]
