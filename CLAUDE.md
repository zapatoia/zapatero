# CLAUDE.md — Pipeline de vídeos 3D «MMO retro low-poly» para TikTok/Reels

> **AL EMPEZAR CUALQUIER SESIÓN:** lee `docs/PIPELINE_STATE.md` (estado, historial y siguiente paso) y la última sesión de `docs/sessions/`, o usa `/resume-session`. No cambies nada hasta que el usuario lo pida. Al terminar o si se acaba el contexto: `/save-session`.

> **FORMATO ACTIVO (desde 2026-11-27, decisión del usuario): DOCUMENTALES ANIMADOS VERTICALES 9:16** con mapas, cifras y la voz del usuario. Se piden con «hazme un documental animado sobre…». Todo está en `.claude/skills/documental-animado/SKILL.md` (§0 instalación en Linux con `instalar/instalar_linux.sh`, §7 reglas del usuario: obligatorias) y en `docs/PIPELINE_STATE.md` §7b; los proyectos van en `documentales/NN-tema/`.
> **COMANDO /loteN (desde 2026-11-28, decisión del usuario):** si el usuario escribe `/lote5 (título/hook 1) … (título/hook 5)` (o `/lote N …`, cualquier N), ejecuta TAL CUAL `.claude/skills/lote/SKILL.md`: su prompt original completo (N vídeos estrictamente uno a uno, pipeline entero y QA propio en cada uno, mismo esfuerzo que un vídeo suelto, informe final). Hay atajos `/lote2` … `/lote10`; para N > 10, usa el mismo skill con ese N. Sin preguntar nada.
> **DISTRIBUCIÓN (desde 2026-11-28, decisión del usuario):** publicar/programar en Instagram Reels, YouTube Shorts y TikTok mediante el conector de **Metricool** (huecos 15:30 y 20:30 Europe/Madrid, siguientes libres). Plan, estado y reglas en `docs/DISTRIBUCION.md`: léelo antes de programar nada. Skill `/distribuir`; los textos (estilo «🤯 TÍTULO + emoji», 5 hashtags) **no necesitan el OK del usuario**: se programan y se informa después.
> **«HAZ N VÍDEOS Y DISTRIBÚYELOS» (desde 2026-11-28, decisión del usuario):** sin títulos → `/ideas N` (`.claude/skills/ideas/SKILL.md`: competidores de Instagram en Metricool (fuente principal), tu canal y web; datos refrescados en cada ronda → ≥80 ideas → filtro y puntuación → N elegidas) → `/lote N` → `/distribuir`. Todo sin preguntar. Banco de ideas: `ideas/banco.json`.
> **DURACIÓN (desde 2026-11-28):** los documentales duran entre **45 s y 1:30** según la idea (no siempre ~1:30): ver `.claude/skills/lote/SKILL.md`.
> **«Estilo premium»** (2.5D/3D oscuro + dorado, cámara que vuela): ver `.claude/skills/documental-animado/ESTILO-PREMIUM.md`.
> **El pipeline 3D de este documento (narrador, perro, `make_video.py`, `retro3d/`, `videos/`) queda ARCHIVADO**: no se usa ni se modifica salvo que el usuario lo pida expresamente. Todo lo que sigue en este archivo se refiere a ese formato archivado.

## REGLAS DE PROTECCIÓN (permanentes)
- **No modificar el narrador, el estilo ni el pipeline base sin permiso explícito del usuario.** El narrador (`config/narrator.json` + `retro3d/characters/narrator.py` + `config/narrator.lock`), el estilo (`STYLE.md`, `retro3d/style.py`) y el pipeline base (`make_video.py`, `retro3d/`) solo cambian si el usuario lo pide.
- **Las novedades se añaden sin romper lo existente**: nuevas acciones, escenarios, recursos o tipos de plano como opciones adicionales; los guiones y vídeos anteriores deben seguir renderizando igual.
- **Versiones**: cada vez que el usuario apruebe una versión, crear un tag de git anotado (`v1`, `v2`, …) en el commit correspondiente, hacer push del tag y apuntarlo en `docs/PIPELINE_STATE.md` (§12). Las versiones nuevas de un vídeo se guardan como `videos/NN-tema-vK.mp4` sin borrar las anteriores.
- Skills del proyecto: `.claude/skills/save-session/SKILL.md` y `.claude/skills/resume-session/SKILL.md`.

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
  world.py               escenario «claro» (camino, cabaña, muro, árboles…) + altura/zona
  interior.py            escenario «casa» (interior de la cabaña) con su propia luz
  characters/            narrator.py (NARRADOR FIJO), dog.py (+ base.py: acciones, capas, muelles, caras)
  camera.py              repertorio de planos (establish/orbit/crane/truck/low/push/pull), barridos, zooms, validación
  physics.py             volúmenes de colisión, interpenetraciones, apoyo en suelo, contacto lengua→superficie
  props.py               carteles, bocadillos, iconos, números en vóxeles, chispas
  production.py          director: anclas a palabras → planos, acciones, recursos, sfx
  voice.py audio.py      ElevenLabs con caché; alineación, pausas, sfx, mezcla, LUFS
  lipsync.py subtitles.py
scripts/NN-tema.json     guiones
config/voice.json        configuración de voz (fija)
config/narrator.json     DEFINICIÓN ÚNICA del narrador (medidas, colores, rig, caras, poses, ropa) + narrator.lock
cache/voice/             audio cacheado (se versiona: nunca repetir llamadas)
tools/preview_characters.py   hojas de revisión (5 poses + 3 s de animación)
tools/narrator_sheet.py  hoja de diseño del narrador + clip de 3 s; tools/lock_narrator.py fija su huella
tools/check_physics.py   comprobación rápida de interpenetraciones sin renderizar
videos/NN-tema.mp4       entregables
STYLE.md facts_to_verify.md
```

## Entorno y render
- Sin internet general: solo gestores de paquetes y `api.elevenlabs.io`. Todo se modela y renderiza por código; nada de assets descargados.
- Dependencias: `pip install moderngl numpy pillow scipy soundfile pyloudnorm`, `apt-get install -y libegl1 libegl-mesa0 fonts-montserrat` (la fuente ya está copiada en `assets/fonts/`). ffmpeg viene instalado.
- **Motor elegido: moderngl + EGL/Mesa llvmpipe** (medido a 1080x1920): ~0,1–0,2 s/fotograma frente a ~1,1 s Blender Workbench, ~60 s EEVEE por software y ~21 s Cycles 16 spp. Además da control total del look (niebla, cielo, *nearest*, sombreado plano).
- Salida: 1080x1920, 30 fps, H.264 (crf 19) + AAC 192k, audio a **-16 LUFS, pico ≤ -1,5 dBTP** (aprobado por el usuario en la v5: con esta voz, -14 LUFS obliga a ~9 dB de limitador y suena saturado). Usar en los guiones `"master": "clean2", "lufs": -16` (voz procesada sola: expansor de silencios, nivelador, compresor de picos limitado a 6 dB, limitador; luego efectos y música; limitador final suave). Verificado con `ebur128` sobre el MP4 final. Los guiones antiguos sin `master` siguen con el máster clásico a -14.

## Flujo de trabajo para un vídeo nuevo
1. **Guion** en `scripts/NN-tema.json` (copiar la estructura de `01-perro-lame.json`).
2. `python make_video.py scripts/NN.json --dry` → storyboard con tiempos estimados en `build/NN/storyboard.jpg`. Revisa TÚ los fotogramas (texto cortado, iconos fuera de cuadro, cámara dentro de modelos, planos aburridos) y corrige.
3. **Enseña al usuario el guion + storyboard + coste (`--cost`) y ESPERA su OK.**
4. `python make_video.py scripts/NN.json --tts` → **una sola toma**, se cachea.
5. `python make_video.py scripts/NN.json --storyboard` (con tiempos reales) → revisar.
6. `python make_video.py scripts/NN.json --preview --contact` (540x960, rápido) → revisar `build/NN/contact.jpg`, labios, cortes.
7. `python tools/check_physics.py scripts/NN.json` → **0 interpenetraciones** y `python tools/shot_frames.py scripts/NN.json` → **0 avisos de encuadre** antes de renderizar.
8. `python make_video.py scripts/NN.json --contact` → final en `videos/NN-tema.mp4` (o `--out videos/NN-tema-vK.mp4` para versiones, sin borrar las anteriores). Genera en `build/NN/`: `qa.md`, `contact.jpg` (1 fotograma por plano), `contactos.jpg` (primeros planos de cada contacto), `sfx_report.md` (lista de efectos y energía por plano).
9. **Revisión antes de entregar (obligatoria)**: hoja por plano (texto cortado, cámara dentro de modelos, modelos que se atraviesan, pies flotando, planos repetidos, boca desincronizada, zonas seguras), `qa.md` todo en verde, -16 LUFS (pico ≤ -1,5 dBTP). Si algo falla, corregir y repetir. Entregar con la lista de efectos de sonido, el tiempo de render y mejoras.

## Formato del guion JSON
- `scenes`: `["claro", "casa"]` (añadir `"casa"` para construir el interior).
- `cast`: personajes con `type` (`narrator`/`dog`), `pos` [x,y], `yaw`, y para perros `variant` (`default`, `pup`, `mom`), `size`, `head_scale`.
- Coordenadas en otra zona: añade el nombre al final de la lista: `"place": [x, y, yaw, "casa"]`, `"sub": [x, y, z, "casa"]`, `"pos": [x, y, "casa"]`. La luz cambia sola según la zona del sujeto del plano. Narrador en casa (-0,4, 0,6), perro (0,64, 0,58); cojín del perro (0,95, 1,45).
- `segments[]`: `text` (lo que se dice y se subtitula, **cifras y siglas escritas como se pronuncian**), `shots`, `acts`, `props`, `sfx`.
- Anclas `at`/`until`: índice de palabra del segmento, palabra («sal»), `"start"`, `"end"`, `"next"`, o `[ancla, segundos]`.
- Plano (uno por beat): `type` (`establish` situación lejana y picada → empuje rápido, `orbit` con `deg` 180/360, `crane` con `rise` ±, `truck` travelling con `move`, `low` contrapicado, `push`, `pull`), `size` (`wide`/`medium`/`close`), `sub` (`narr`, `dog`, `two`, `mom+pup`, parte del cuerpo `"narr.hand_L"` o punto [x,y,z]), `az`, `el`, `dist`/`h` opcionales, `ease`, `transition: "whip"` (barrido con desenfoque de movimiento; úsalo al cambiar de escena), `zoom` (anclas de golpe de zoom). En el segmento, `zooms`: palabras clave con golpe de zoom.
- **Reglas de cámara (se validan solas)**: no repetir tipo dos veces seguidas, no tres tamaños iguales seguidos, cambio de plano/movimiento claro cada 2–3 s (0,8–3,4 s por plano), holgura mínima 0,3 m a modelos y suelo en cada fotograma (la cámara se empuja fuera de obstáculos, personajes y paredes del interior).
- **Opciones globales del guion (desde la v3 del vídeo 01; recomendadas en vídeos nuevos)**: `"master": "clean"` (máster sin saturación: nivelador lento + compresor de picos + limitador con anticipación y curvas suaves; sin la opción se usa el máster antiguo), `"icon_style": "world"` (**preferido por el usuario desde la v4**: iconos integrados en la escena, iluminados, con sombra real y de contacto, anclados al mundo con `anchor`/`off`, no a la pantalla; iconos nuevos: `lollipop`), `"icon_style": "glow"` (iconos dibujados encima de la escena con contorno de pegatina, halo de su color que late y destello en anillo al aparecer; patatas fritas mejoradas), `"cam_smooth": 0.18` (la cámara sigue al sujeto con muelle amortiguado y absorbe los empujones anti-colisión: sin tirones). Los números (`num:N`) van con `screen: [0, 0.72, 1.6]`, `size 0.42`, por encima de la cabeza.
- **Revisión de encuadres**: `python tools/shot_frames.py scripts/NN.json` → `build/NN/shots.jpg` (inicio/mitad/final de cada plano) y `framing.md` (cabezas cortadas, recursos fuera de cuadro o tapando caras). Debe dar **0 avisos**.
- `emph`: lista opcional de palabras del segmento que deben llevar gesto de énfasis (además de las detectadas en la voz).
- Las acciones empiezan 0,2 s antes de su palabra (`delay` para cambiarlo); los `place` ocurren exactamente en el corte. Plano medio narrador ≈ dist 2,7–3,2; primer plano ≈ 2,0–2,4 (h 1,32). Perro: dist 2,1–2,6.
- Acciones narrador: `idle talk explain point(side) shrug lean_in laugh offer_hand(side) look_down wave walk`. Perro: `idle wag sit head_tilt jump lick(up,reach,rate) lick_paw calm nuzzle walk`. `place: [x,y,yaw]` recoloca en el corte.
- Recursos: `icon` (`heart drop salt question exclaim warn fries tongue num:N text:…`), `bubble` (texto pixel), `sign` (cartel; textos cortos ≤11 letras por línea), `sparkles`. `anchor`+`off`/`node`, `pos`, o `screen: [x,y,prof]` (anclado al encuadre, recomendado para números).
- Lametón: narrador con `offer_hand side L` y perro con `lick` + `"target": {"who": "narr", "node": "hand_L"}, "approach": true, "yaw": -1.15` → el perro se coloca solo frente a la mano en el corte y la lengua se detiene en la superficie. Para encuadrarlo, plano lateral con `sub: "narr.hand_L"`.

## Estilo
Ver **STYLE.md** (y `retro3d/style.py`). **Dirección actual: MINIMALISTA** (petición del usuario): caras de un solo tono sin nariz ni rubor, personajes con pocas piezas y color plano, texturas de dos tonos, escenario despejado, iconos de silueta limpia. Resumen: low-poly 300–1.500 tris por personaje, sombreado plano / color por vértice, texturas 32–128 px sin filtrar, sin normal maps ni PBR; personajes achaparrados con caras pintadas intercambiables; hierba en mosaico, camino de tierra, árboles low-poly, rocas facetadas, cabaña y muro de piedra, cielo degradado con niebla; luz cálida de tarde y sombras simples; cámara MMO en 3ª persona ligeramente picada con cambios cada 2–3 s; carteles, bocadillos, iconos y números con rebote.

## Personajes
### REGLA: narrador fijo y reutilizable
- **Hay UN narrador, el mismo en todos los vídeos.** Se define una sola vez en `config/narrator.json` + `retro3d/characters/narrator.py`. **Ningún vídeo puede modificarlo**: los guiones solo eligen acciones/poses, expresión (`expr`: neutral, happy, surprised, angry, sad, skeptical), ropa alternativa (`outfit`, solo si el usuario la pide y existe en el JSON) y planos.
- `config/narrator.lock` guarda la huella del JSON; si no coincide, el pipeline se niega a renderizar. Solo se cambia por petición explícita del usuario y luego `python tools/lock_narrator.py`.
1. **Narrador** (sin nombre, ~1.150 tris): persona con **pasamontañas magenta #D61F8C** (franja abierta para los ojos con cejas/párpados, abertura ovalada para la boca, cruz cristiana pequeña blanca en la frente), **jersey streetwear** oversize negro (cuello en V, franjas blancas en mangas y bajo, número «00»), **pantalón militar** ancho de camuflaje con bolsillos cargo, **cinturón** negro con hebilla de plata y toques de oro, **cadena fina de plata**, **zapatillas** blancas de suela gruesa crema y talonera negra (sin logotipos), piel clara. Cara: 6 expresiones × 3 párpados, 5 bocas. Poses: explicar, señalar, encogerse, brazos cruzados, saludo, hablar, confidencia, reír, ofrecer la mano, mirar abajo, caminar. Idle con respiración y cambio de peso; parpadeo cada 2–4 s y al final de frase; gestos de énfasis.
2. **Perro** (554 tris): canela con hocico crema, orejas caídas tostadas con muelle, cola de 3 segmentos con muelle, collar rojo, mandíbula y lengua articuladas. Variantes `pup` y `mom`.
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
- **Sonido (regla fija)**: cada efecto es un **evento puntual** (inicio + duración) ligado a un momento del guion o de la animación; **ningún efecto en bucle** salvo petición explícita (el ambiente solo con `"ambience_db"` en el guion). Efectos suaves (pop corto, whoosh leve, pasos ligeros, lametón blando), **18–24 dB por debajo de la voz**, con fundidos de entrada/salida y atenuación extra de 6 dB mientras se habla. Lametón: máximo 2 sonidos por acción (`lick_sfx`). Verificación obligatoria: `sfx_report.md` (tiempo, tipo, nivel, motivo; energía por plano) y **0 sonidos sostenidos > 1 s**. **Sin música de terceros.** Música de fondo: solo la original generada por código (`retro3d/music.py`), con `"music": {"style": "aldea", "db": -19, "duck_db": -5}` (aprobada en la v5). Para rehacer solo el audio de un vídeo ya renderizado: `--reuse-video build/<id>/video.mp4`.
- **Textos animados**: subtítulos palabra a palabra escritos **letra a letra dentro del tiempo de cada palabra** (≤30 letras/s, cada letra sube unos píxeles y se funde en 0,1 s), palabra actual resaltada; bocadillos y carteles letra a letra a 30 letras/s; salida de todos los textos con **fundido rápido** (0,12–0,15 s). Nada en el 20 % inferior ni el 12 % derecho.
- **Físicas y contactos (regla fija)**: ningún modelo atraviesa a otro ni el suelo. Volúmenes de colisión por pieza (OBB) comprobados en cada fotograma (tolerancia 2 cm); restricciones automáticas (codo hacia fuera si el antebrazo invade el cuerpo, cuello arriba si la cabeza invade las patas); pies apoyados en el suelo (también en el cojín del interior), salvo en el aire; contactos con objetivo real: la lengua apunta a la superficie y se detiene en ella (5 rayos, margen 1,2 cm, ligero aplastamiento), la mano cede un poco; anticipación antes de saltar y amortiguación al caer. Si `check_physics.py` o `qa.md` muestran penetraciones, **corregir antes de entregar**.

## Proceso por fases
No avanzar si una fase falla; explicar qué falla y proponer alternativa. Revisar siempre fotogramas antes de entregar.

## Git
Trabajar en la rama indicada por la sesión. `build/` está ignorado; `cache/voice/` y `videos/` sí se versionan.
Peso: con el estilo minimalista un vídeo de ~40 s ocupa ~25–30 MB (crf 19). Las versiones nuevas se suben como `-vK` sin borrar las anteriores. Si algún MP4 supera 50 MB, considerar Git LFS (`git lfs` está instalado) o subir los vídeos fuera del repo.
