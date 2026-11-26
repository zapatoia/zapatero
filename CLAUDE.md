# CLAUDE.md — Pipeline de vídeos 3D «MMO retro low-poly» para TikTok/Reels

Este repositorio produce vídeos verticales explicativos (30–40 s) con estética de MMO
low-poly de principios de los 2000, **100 % originales** y generados por código.
El usuario pide vídeos nuevos en el chat; sigue este documento al pie de la letra.

> El código antiguo de `src/` y `zapato_historia_vertical.mp4` es de un intento previo.
> **No se reutiliza** (ni código, ni personajes, ni estilo).

## Estructura
```
make_video.py            comando único (guion JSON → MP4)
retro3d/                 motor y librería de estilo
  style.py               paleta, luz, cielo, niebla, render, subtítulos  ← identidad visual
  render.py              renderizador moderngl (EGL, llvmpipe), sombras, cielo, niebla, post
  mesh.py textures.py    geometría low-poly y texturas pixel procedurales (≤128 px)
  font.py                fuente pixel 5x7 propia (carteles, bocadillos, vóxeles)
  world.py               escenario reutilizable (claro, camino, cabaña, muro, árboles…)
  characters/            narrator.py, dog.py (+ base.py: acciones, capas, muelles, caras)
  props.py               carteles, bocadillos, iconos, números en vóxeles, chispas
  production.py          director: anclas a palabras → planos, acciones, recursos, sfx
  voice.py audio.py      ElevenLabs con caché; alineación, pausas, sfx, mezcla, LUFS
  lipsync.py subtitles.py
scripts/NN-tema.json     guiones
config/voice.json        configuración de voz (fija)
cache/voice/             audio cacheado (se versiona: nunca repetir llamadas)
tools/preview_characters.py   hojas de revisión (5 poses + 3 s de animación)
videos/NN-tema.mp4       entregables
STYLE.md facts_to_verify.md
```

## Entorno y render
- Sin internet general: solo gestores de paquetes y `api.elevenlabs.io`. Todo se modela y renderiza por código; nada de assets descargados.
- Dependencias: `pip install moderngl numpy pillow scipy soundfile pyloudnorm`, `apt-get install -y libegl1 libegl-mesa0 fonts-montserrat` (la fuente ya está copiada en `assets/fonts/`). ffmpeg viene instalado.
- **Motor elegido: moderngl + EGL/Mesa llvmpipe** (medido a 1080x1920): ~0,1–0,2 s/fotograma frente a ~1,1 s Blender Workbench, ~60 s EEVEE por software y ~21 s Cycles 16 spp. Además da control total del look (niebla, cielo, *nearest*, sombreado plano).
- Salida: 1080x1920, 30 fps, H.264 (crf 19) + AAC 192k, audio a **-14 LUFS, pico ≤ -1,5 dBTP** (loudnorm en dos pasadas) verificado con `ebur128` sobre el MP4 final.

## Flujo de trabajo para un vídeo nuevo
1. **Guion** en `scripts/NN-tema.json` (copiar la estructura de `01-perro-lame.json`).
2. `python make_video.py scripts/NN.json --dry` → storyboard con tiempos estimados en `build/NN/storyboard.jpg`. Revisa TÚ los fotogramas (texto cortado, iconos fuera de cuadro, cámara dentro de modelos, planos aburridos) y corrige.
3. **Enseña al usuario el guion + storyboard + coste (`--cost`) y ESPERA su OK.**
4. `python make_video.py scripts/NN.json --tts` → **una sola toma**, se cachea.
5. `python make_video.py scripts/NN.json --storyboard` (con tiempos reales) → revisar.
6. `python make_video.py scripts/NN.json --preview --contact` (540x960, rápido) → revisar `build/NN/contact.jpg`, labios, cortes.
7. `python make_video.py scripts/NN.json --contact` → final en `videos/NN-tema.mp4`. Comprobar LUFS/dBTP y el informe `build/NN/report.json`.
8. Revisar fotogramas clave del MP4 final, subirlo al repo (`git add -f` no hace falta: `videos/` está versionado) y contar tiempo de render y mejoras.

## Formato del guion JSON
- `cast`: personajes con `type` (`narrator`/`dog`), `pos` [x,y], `yaw`, y para perros `variant` (`default`, `pup`, `mom`), `size`, `head_scale`.
- `segments[]`: `text` (lo que se dice y se subtitula, **cifras y siglas escritas como se pronuncian**), `shots`, `acts`, `props`, `sfx`.
- Anclas `at`/`until`: índice de palabra del segmento, palabra («sal»), `"start"`, `"end"`, `"next"`, o `[ancla, segundos]`.
- Plano: `sub` (`narr`, `dog`, `two`, `mom+pup`, o punto [x,y,z]), `h`, `dist`/`az`/`el` como [inicio, fin], `fov`, `lift`, `ease`. Plano medio narrador ≈ dist 2,7–3,2; primer plano ≈ 2,0–2,4 (h 1,32). Perro: dist 2,1–2,6.
- Acciones narrador: `idle talk explain point(side) shrug lean_in laugh offer_hand(side) look_down wave walk`. Perro: `idle wag sit head_tilt jump lick(up,reach,rate) lick_paw calm nuzzle walk`. `place: [x,y,yaw]` recoloca en el corte.
- Recursos: `icon` (`heart drop salt question exclaim warn fries tongue num:N text:…`), `bubble` (texto pixel), `sign` (cartel; textos cortos ≤11 letras por línea), `sparkles`. `anchor`+`off`/`node`, `pos`, o `screen: [x,y,prof]` (anclado al encuadre, recomendado para números).
- Para que el perro lama la mano del narrador: narrador en (0, 0,8) yaw 0,15 con `offer_hand side L`, perro en (1,04, 0,78) yaw -1,15 con `lick up 0.55`. Recalcular si cambian.

## Estilo
Ver **STYLE.md** (y `retro3d/style.py`). Resumen: low-poly 300–1.500 tris por personaje, sombreado plano / color por vértice, texturas 32–128 px sin filtrar, sin normal maps ni PBR; personajes achaparrados con caras pintadas intercambiables; hierba en mosaico, camino de tierra, árboles low-poly, rocas facetadas, cabaña y muro de piedra, cielo degradado con niebla; luz cálida de tarde y sombras simples; cámara MMO en 3ª persona ligeramente picada con cambios cada 2–3 s; carteles, bocadillos, iconos y números con rebote.

## Personajes
1. **Narrador** (sin nombre): aventurero achaparrado de túnica verde azulada con ribete ocre, bufanda teja con cola que se mueve, bandolera y zurrón, hombrera metálica solo en el hombro izquierdo, brazaletes y botas con vuelta, pelo castaño rojizo en mechones. 5 bocas para labios, parpadeo cada 2–4 s, respiración.
2. **Perro**: canela con pecho, hocico y patas crema, orejas caídas tostadas con muelle, cola de 3 segmentos con muelle, collar rojo con chapa, mandíbula y lengua articuladas. Variantes `pup` y `mom`.
Revisar con `python tools/preview_characters.py` → `build/characters/*.jpg`.

## Voz (ElevenLabs) — reglas fijas
- `ELEVENLABS_API_KEY` solo del entorno; **no guardarla ni imprimirla nunca**.
- Voz **voice_id 851ejYcv2BoNPjrkw93G, siempre**. Si falla o suena mal en español, avisar al usuario y **no cambiar de voz por cuenta propia**.
- Modelo `eleven_v3`, `language_code "es"`, `stability 0.5`, endpoint `/v1/text-to-speech/{voice_id}/with-timestamps` (en `config/voice.json`).
- Antes de generar: decir caracteres y créditos estimados (≈1 crédito/carácter, `--cost`). **Una toma por vídeo.** La caché evita repetir llamadas.
- Los timestamps se verifican contra la envolvente real (desfase por correlación) y se corrigen si se desvían ≥30 ms. Las pausas > 0,42 s se acortan a 0,30 s en el audio (sin regenerar) y se remapean los timestamps.

## Guion — reglas
- Español de España, tono de colega, directo, humor seco, frases cortas, **80–105 palabras** (30–40 s).
- Hook ≤3 s, bucle abierto a mitad, 3–4 razones fáciles, cierre útil.
- Prohibido estilo ChatGPT: «en el mundo actual», «descubre cómo», «sin más dilación», «es importante destacar», «te voy a contar», «en este vídeo», relleno, emojis.
- Nada dudoso como hecho: «se cree que», y cada afirmación con confianza en `facts_to_verify.md`.
- **Enseñar guion + storyboard y esperar OK antes de generar la voz.**

## Animación, sonido y subtítulos
- easeOutBack/easeInOut, anticipación y rebote. Nada estático > 1,5 s; cambio visual cada 2–3 s. Alternar narrador a cámara con el perro demostrando.
- Labios: forma por letra de los timestamps × apertura por envolvente, retención mínima 2 fotogramas, adelanto de 35 ms.
- SFX generados por código a volumen bajo (pop, ding, blip, pasos, lametón, boing, golpe) + ambiente de viento y pájaros sintéticos. **Sin música de terceros.**
- Subtítulos grandes, centrados, palabra a palabra con la actual resaltada; nada en el 20 % inferior ni el 12 % derecho.

## Proceso por fases
No avanzar si una fase falla; explicar qué falla y proponer alternativa. Revisar siempre fotogramas antes de entregar.

## Git
Trabajar en la rama indicada por la sesión. `build/` está ignorado; `cache/voice/` y `videos/` sí se versionan.
