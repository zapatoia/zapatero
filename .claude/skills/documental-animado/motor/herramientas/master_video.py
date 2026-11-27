"""Master final del audio de un MP4 exportado por el motor: −11 LUFS integrados y pico real ≤ −1 dBTP MEDIDO DESPUÉS DEL AAC.

  python3 herramientas/master_video.py exports/x-render.mp4 exports/x.mp4 [--lufs -11] [--tp -1.0] [--recorte 62.97]

El video se copia tal cual (sin recodificar). El audio: ganancia → limitador sobremuestreado ×4 (atrapa los picos entre
muestras) → AAC 320k → se decodifica y se mide; si el AAC sube el pico por encima del techo, se baja el techo y se repite.
--recorte corta el video en ese segundo (regla: termina ≤ 0.3 s después de la última palabra, sin outro).
"""
import os, re, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ffruta import ffmpeg   # también deja la salida en UTF-8 (Windows: el «→» del reporte)
FF = ffmpeg()


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0: raise RuntimeError(r.stderr[-1500:])
    return r.stderr


def medir(f):
    m = run([FF, '-hide_banner', '-i', f, '-map', '0:a:0', '-af', 'ebur128=peak=true', '-f', 'null', '-'])
    return float(m.split('I:')[-1].split('LUFS')[0]), float(m.split('Peak:')[-1].split('dBFS')[0])


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    o = {k: float(v) for k, v in re.findall(r'--(\w+)[= ]([-\d.]+)', ' '.join(sys.argv[1:]))}
    src, dst = a[0], a[1]; L, TP = o.get('lufs', -11.0), o.get('tp', -1.0); cut = o.get('recorte')
    tmp = tempfile.mkdtemp(prefix='master-')
    wav = os.path.join(tmp, 'mezcla.wav'); run([FF, '-v', 'error', '-y', '-i', src, '-vn', '-ac', '2', '-ar', '48000', '-c:a', 'pcm_f32le'] + (['-t', f'{cut:.3f}'] if cut else []) + [wav])
    l0, p0 = medir(wav); g = L - l0; techo = 0.86
    for intento in range(8):
        mw = os.path.join(tmp, 'master.wav')
        for _ in range(3):
            run([FF, '-v', 'error', '-y', '-i', wav, '-af', f'volume={g:.2f}dB,aresample=192000,alimiter=limit={techo}:attack=0.8:release=80:level=false,aresample=48000', '-c:a', 'pcm_f32le', mw])
            lu, _ = medir(mw)
            if abs(lu - L) < .2: break
            g += L - lu
        run([FF, '-v', 'error', '-y', '-i', src, '-i', mw, '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart', '-shortest'] + (['-t', f'{cut:.3f}'] if cut else []) + [dst])
        lu, tp = medir(dst)
        print(f'intento {intento + 1}: {lu:.1f} LUFS · pico real tras AAC {tp:.1f} dBTP (techo {techo:.2f})')
        if tp <= TP and abs(lu - L) <= .5: break
        if tp > TP: techo *= 10 ** ((TP - tp - .15) / 20)
        else: g += L - lu
    print(f'listo: {dst} · antes {l0:.1f} LUFS / {p0:.1f} dBTP → {lu:.1f} LUFS / {tp:.1f} dBTP')


if __name__ == '__main__':
    main()
