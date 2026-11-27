"""Cadena de locutor (EQ + de-esser + compresión) que se aplica a la voz sintética. La lee nucleo/voz.py."""

CADENA_EQ = (
    "equalizer=f=120:t=q:w=0.9:g=1.5,"
    "equalizer=f=250:t=q:w=1.1:g=-3,"
    "equalizer=f=600:t=q:w=1.4:g=-1.5,"
    "equalizer=f=3500:t=q:w=1.0:g=3.5,"
    "highshelf=f=9000:g=3,"
    "deesser=i=0.45:m=0.5:f=0.5,"
    "acompressor=threshold=-26dB:ratio=2.5:attack=25:release=250:makeup=2dB,"   # nivelador lento
    "acompressor=threshold=-18dB:ratio=4:attack=3:release=60:makeup=3dB,"        # densidad
    "alimiter=limit=0.89:attack=2:release=40,"
    "loudnorm=I=-16:TP=-1.5:LRA=6"
)
