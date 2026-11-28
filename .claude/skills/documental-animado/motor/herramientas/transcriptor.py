"""Whisper local con la misma interfaz en cualquier computadora.

· Mac con chip Apple (M1–M4): mlx-whisper (GPU), modelo whisper-large-v3-turbo.
· Windows / Linux / Mac Intel: faster-whisper (CPU o CUDA), modelo large-v3-turbo.
Variable TRANSCRIPTOR=mlx|faster fuerza uno.
Windows: CPU siempre, salvo WHISPER_CUDA=1 (con una NVIDIA sin cuBLAS/cuDNN el modelo carga en CUDA y el proceso muere al transcribir).

transcribe(audio, language=None, temperature=0.0, word_timestamps=False, condition_on_previous_text=False, initial_prompt=None)
  audio: ruta o np.float32 a 16 kHz mono. Devuelve {"text", "language", "segments": [{"text", "start", "end", "words": [{"word","start","end","probability"}]}]}
prob_idioma(x) → (p_es, [(idioma, p), ...])
"""
import os, platform
if os.name == "nt" and not os.environ.get("HF_HOME") and not os.path.expanduser("~").isascii():
    os.environ["HF_HOME"] = "C:\\hf"   # usuario de Windows con acentos o ñ: Whisper no abre el modelo desde su carpeta

import numpy as np

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")   # servidor Linux en la nube: descarga clásica por us.aws.cdn.hf.co (hosts permitidos en el entorno)   # Windows sin modo desarrollador: el aviso de symlinks del caché no es un error

REPO_MLX = "mlx-community/whisper-large-v3-turbo"
MODELO_FASTER = "large-v3-turbo"
_M = {}


def motor():
    q = os.environ.get("TRANSCRIPTOR")
    if q: return q
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        try:
            import mlx_whisper  # noqa: F401
            return "mlx"
        except ImportError:
            pass
    return "faster"


def _faster():
    if "f" not in _M:
        from faster_whisper import WhisperModel
        try:
            if platform.system() == "Windows" and os.environ.get("WHISPER_CUDA") != "1": raise RuntimeError("CPU en Windows")
            _M["f"] = WhisperModel(MODELO_FASTER, device="cuda", compute_type="float16")
        except Exception:
            _M["f"] = WhisperModel(MODELO_FASTER, device="cpu", compute_type="int8")
    return _M["f"]


def transcribe(audio, language=None, temperature=0.0, word_timestamps=False, condition_on_previous_text=False, initial_prompt=None, **_):
    if motor() == "mlx":
        import mlx_whisper
        return mlx_whisper.transcribe(audio, path_or_hf_repo=REPO_MLX, language=language, temperature=temperature, word_timestamps=word_timestamps,
                                      condition_on_previous_text=condition_on_previous_text, initial_prompt=initial_prompt)
    m = _faster()
    if isinstance(audio, (str, os.PathLike)):                     # algunas versiones de PyAV no aceptan la ruta (metadata_errors): se decodifica con ffmpeg
        import subprocess
        audio = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                                             capture_output=True, check=True).stdout, np.float32)
    if isinstance(audio, np.ndarray): audio = audio.astype(np.float32)
    segs, info = m.transcribe(audio, language=language, temperature=temperature, word_timestamps=word_timestamps, beam_size=5,
                              condition_on_previous_text=condition_on_previous_text, initial_prompt=initial_prompt, vad_filter=False)
    out = []
    for s in segs:
        ws = [dict(word=w.word, start=float(w.start), end=float(w.end), probability=float(w.probability)) for w in (s.words or [])]
        out.append(dict(text=s.text, start=float(s.start), end=float(s.end), words=ws, avg_logprob=float(s.avg_logprob)))   # verificar_es lo lee (mlx ya lo trae)
    return dict(text="".join(s["text"] for s in out), language=info.language, segments=out)


def prob_idioma(x):
    """x = np.float32 16 kHz mono."""
    if motor() == "mlx":
        import mlx.core as mx
        from mlx_whisper.transcribe import ModelHolder
        from mlx_whisper.audio import log_mel_spectrogram, pad_or_trim, N_SAMPLES, N_FRAMES
        if "m" not in _M: _M["m"] = ModelHolder.get_model(REPO_MLX, mx.float16)
        m = _M["m"]; mel = log_mel_spectrogram(x, n_mels=m.dims.n_mels, padding=N_SAMPLES)
        seg = pad_or_trim(mel, N_FRAMES, axis=-2).astype(mx.float16); _, probs = m.detect_language(seg)
    else:
        m = _faster()
        try:
            _, _, todas = m.detect_language(x.astype(np.float32))
            probs = dict(todas)
        except Exception:
            _, info = m.transcribe(x.astype(np.float32), language=None, beam_size=1)
            probs = dict(info.all_language_probs or [(info.language, info.language_probability)])
    top = sorted(probs.items(), key=lambda kv: -kv[1])[:3]
    return float(probs.get("es", 0.0)), [(k, round(float(v), 3)) for k, v in top]
