"""Identidad visual «retro MMO low-poly 2003». Única fuente de verdad del estilo.

Cualquier vídeo nuevo debe usar estas constantes. Ver STYLE.md.
"""

# Paleta terrosa saturada ----------------------------------------------------
PAL = {
    # mundo
    "grass_a": "#5f8c2e", "grass_b": "#467027", "grass_c": "#7aa23a",
    "dirt_a": "#a7743f", "dirt_b": "#7f5530", "dirt_c": "#c39257",
    "stone_a": "#8c8577", "stone_b": "#686357", "stone_c": "#aaa291",
    "moss": "#5f8a2c",
    "bark": "#6b4528", "bark_dark": "#4a2e1b",
    "leaf_a": "#3f7a2a", "leaf_b": "#5e9a2f", "leaf_c": "#2d5c22",
    "pine_a": "#2f5e3a", "pine_b": "#3f7546",
    "wood_a": "#9a6a3c", "wood_b": "#7a4f2b", "wood_c": "#b98451",
    "roof_a": "#a44c33", "roof_b": "#7c3a27",
    "thatch": "#c49a4a",
    "window": "#ffcf6b",
    "mountain": "#6a76a6",
    "flower_r": "#e0503a", "flower_y": "#f2c43a", "flower_w": "#f4ead2", "flower_p": "#b066c9",
    # narrador: aventurero de túnica verde azulada y bufanda teja
    "skin": "#f0b98a", "skin_shade": "#d99a6c",
    "hair": "#7a3b1e", "hair_light": "#9c5229",
    "tunic": "#2f8072", "tunic_dark": "#235f55", "tunic_trim": "#e0a83a",
    "scarf": "#c4512e", "scarf_dark": "#9c3d22",
    "leather": "#7b4a28", "leather_dark": "#5a341c",
    "metal": "#a9aeb3", "metal_dark": "#7b8188",
    "pants": "#5b4a3a", "boot": "#4e2f1b",
    "buckle": "#f0c64a",
    # perro: canela con pecho crema y orejas tostadas
    "fur": "#d0913f", "fur_dark": "#a86a2a", "fur_light": "#f2dcb0",
    "ear": "#8a4f22", "nose": "#2a1d17", "tongue": "#ee6f86", "tongue_dark": "#c94a63",
    "collar": "#c43b3b", "tag": "#f0c64a",
    # cachorro y madre (variantes)
    "pup_fur": "#e6c38c", "pup_dark": "#c49a5c",
    "mom_fur": "#9d7a5a", "mom_dark": "#76583e", "mom_light": "#e4d3b8",
    # recursos explicativos
    "heart": "#e8344e", "heart_dark": "#a81f35",
    "salt": "#cfeaff", "salt_dark": "#6fa2d6",
    "gold": "#f2b632", "gold_dark": "#b07a18",
    "warn_red": "#d8312b", "warn_white": "#f6f1e4",
    "question": "#ffd43b", "question_dark": "#c28f12",
    "ui_ink": "#2a1a10", "ui_paper": "#fbf1d8", "ui_paper_dark": "#e3cf9f",
}

# Iluminación de tarde ---------------------------------------------------------
LIGHT = {
    "sun_dir": (-0.62, -0.42, 0.62),  # hacia la luz: sol bajo de tarde, 3/4 delantero izquierdo
    "sun_col": (1.08, 0.86, 0.62),    # cálido
    "sky_ambient": (0.50, 0.58, 0.78),  # relleno frío desde arriba
    "ground_ambient": (0.46, 0.36, 0.22),  # rebote terroso
    "shadow_tint": (0.62, 0.55, 0.78),  # las sombras tiran a violeta, nunca a negro
    "shadow_strength": 0.62,
}

SKY = {
    "zenith": (0.30, 0.47, 0.78),
    "mid": (0.58, 0.70, 0.88),
    "horizon": (0.99, 0.80, 0.58),
    "sun_glow": (1.0, 0.86, 0.55),
}

FOG = {
    "start": 18.0,
    "end": 70.0,
    "color": (0.93, 0.80, 0.64),  # igual que el horizonte para fundirse con el cielo
    "max": 0.92,
}

RENDER = {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "msaa": 4,
    "shadow_size": 2048,
    "tex_max": 128,   # ninguna textura supera 128 px
}

# Subtítulos y zonas seguras ------------------------------------------------------
SAFE = {
    "bottom": 0.20,   # nada en el 20 % inferior
    "right": 0.12,    # nada en el 12 % derecho
    "top": 0.08,
    "left": 0.05,
}
SUBS = {
    "font": "assets/fonts/Montserrat-Black.ttf",
    "size": 92,
    "fill": (255, 255, 255),
    "highlight": (255, 210, 63),
    "stroke": (24, 14, 8),
    "stroke_w": 11,
    "center_y": 0.665,   # centro vertical del bloque (por encima del 20 % inferior)
    "max_words": 3,
    "max_width": 0.78,   # fracción de la zona segura
}
