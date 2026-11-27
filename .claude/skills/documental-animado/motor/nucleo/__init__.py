"""Núcleo de reels animados. Ver LEEME.md. voz.py y comparar.py se ejecutan como scripts."""
from .tiempo import *            # noqa: F401,F403
from .tiempo import W, H, FPS, LineaTiempo, CURVAS, tabla, pop
from .texto import fuente, texto, ancho, color, partir_lineas, tipo
from .lienzo import (Lienzo, transf, capa, relleno, trazo, brillo, rr, rrc, ruta, sombra_contacto, sombra_suave, degradado_lineal, degradado_radial,
                     cargar_imagen, imagen_de)
from .compositor import (tramar, hex_rgb, fondo_degradado, mascara_vineta, capsula_brillo, glow_aditivo, bloom, reflejo, textura_ruido, aplicar_textura, grano,
                         BufferFloat, Camara2D)
from .subtitulos import (bloques_de, bloques_auto, FraseFija, PalabraSeleccion, PalabraPorPalabra, Paginas, KaraokeCondensada, TituloFijo)
from .dibujo import Dibujo, trim, parcial
from .audio import RelojMusical, midi, acorde
from .estilo import Estilo, principal, EXPORTS, MV
from . import ui
