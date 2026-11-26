# PIPELINE_STATE — documento maestro del proyecto

> Última actualización: 2026-11-26 (sesión `docs/sessions/2026-11-26-02.md`).
> Rama de trabajo de la sesión 02: `claude/hopeful-einstein-ix8p37` (sin fusionar en `main`; pedir PR al usuario si la quiere). Rama de la sesión 01: `claude/3d-mmo-retro-video-pipeline-3ify9e`. **PR #2 fusionada en `main`** (commit de fusión `df76761`, https://github.com/zapatoia/zapatero/pull/2). **`main` es ya la rama por defecto en GitHub** (antes lo era `claude/shoe-history-vertical-video-qw2b0t`). Las sesiones nuevas parten de `main`.

## 1. Cómo usar este documento
- **Al empezar cualquier sesión**: leer `CLAUDE.md`, este documento y la última sesión de `docs/sessions/` (o usar `/resume-session`). No cambiar nada hasta que el usuario lo pida.
- **Al terminar o cuando se acabe el contexto**: `/save-session` actualiza este documento, crea el resumen de la sesión y hace commit + push.
- Las reglas operativas detalladas están en `CLAUDE.md`; el estilo, en `STYLE.md`. Aquí está el **estado**, el **porqué** de cada decisión y el **historial**.

## 2. Objetivo y filosofía
- Pipeline **reutilizable** que produce vídeos verticales explicativos de **30–40 s** para TikTok/Reels (1080×1920, 30 fps) con estética de **MMO low-poly de principios de los 2000**, **100 % original** (nada de nombres, logos, modelos, personajes, música ni UI de juegos existentes) y generado **íntegramente por código** (sin assets descargados).
- El usuario pide vídeos nuevos en el chat; Claude los produce siguiendo `CLAUDE.md`.
- **Calidad ante todo**: los intentos previos del usuario (fuera de este pipeline) «quedaron básicos y cutres». Se revisan fotogramas a mano y con comprobaciones automáticas antes de entregar.
- **Minimalismo** (petición explícita del usuario tras la v1): pocas piezas, colores planos, casi sin detalles; la silueta tiene que leerse a la primera.
- Trabajo **por fases**; no se avanza si una falla, y en las fases marcadas se espera el OK del usuario.
- Código antiguo **no reutilizable**: `src/` y `zapato_historia_vertical.mp4` (rama `claude/shoe-history-vertical-video-qw2b0t`) son de un intento anterior y no se tocan.

## 3. Estado en una frase
Pipeline completo y funcionando; narrador definitivo **aprobado**; **vídeo 01 aprobado en su v5** (`videos/01-perro-lame-v5.mp4`, tag `v5`, −16 LUFS, música original) — el usuario lo va a subir a TikTok. Avisó de que en los próximos vídeos querrá cambiar **muchas cosas de la animación**. **Siguiente paso exacto:** esperar el tema del vídeo 02 o la lista de cambios de animación; no tocar nada hasta entonces.

## 4. Estilo visual actual (resumen de `STYLE.md`; fuente de verdad en código: `retro3d/style.py`)
- Low-poly con **sombreado plano** (normales por cara) y **color por vértice uniforme** (`jitter=0`).
- **Texturas mínimas pixeladas** 16–32 px con filtro *nearest* (máx. 128 px, lo impone `Renderer.add_texture`): dos tonos en manchas grandes (hierba, tierra) o solo líneas de junta (piedra, tablas, tejas). Personajes: sin textura, salvo el camuflaje del pantalón y las caras/número en atlas pixel. **Nunca** normal maps ni PBR.
- **Luz cálida de tarde**: sol bajo 3/4 delantero-izquierdo (`LIGHT.sun_dir = (-0.62,-0.42,0.62)`), relleno hemisférico generoso (caras legibles), sombras duras (mapa de sombras 2048, PCF 4) que tiran a violeta, **contraluz cálido** (rim) en personajes e iconos.
- **Cielo** degradado suave con halo discreto; **niebla lineal** 18–70 m del color del horizonte; montañas azuladas facetadas y 5 nubes planas.
- **Post**: brillo suave, +6 % saturación, +4 % contraste, viñeta ligera.
- **Paleta mundo**: hierba `#467027/#5f8c2e/#7aa23a`, tierra `#7f5530/#a7743f/#c39257`, piedra `#686357/#8c8577/#aaa291`, madera `#7a4f2b/#9a6a3c/#b98451`, tejas `#a44c33`.
- **Subtítulos**: Montserrat Black (OFL, en `assets/fonts/`), MAYÚSCULAS, blanco con contorno marrón-negro de 10 px, palabra actual amarilla `#FFD23F`, bloques de ≤3 palabras centrados al 66,5 % de la altura; **zonas seguras**: nada en el 20 % inferior ni el 12 % derecho.
- **Iconos (desde la v4, preferido por el usuario)**: `"icon_style": "world"` → objetos de la escena: los ilumina la luz del plano, proyectan sombra real y una sombra de contacto suave en el suelo, los tapan los personajes, brillo propio que late y anillo de destello al aparecer; anclados al mundo (`anchor`+`off`/`node`), no a la pantalla. El estilo `glow` (pegatina encima de todo, v3) quedó descartado por «pegote». Iconos: heart, drop, salt, question, exclaim, warn, fries, lollipop (chupachups sin marca), tongue, num:N, text:….
- Decisiones clave: moderngl en vez de Blender (velocidad y control del look); minimalismo; medallones para números; textos letra a letra; contraluz; dos escenarios; iconos integrados en la escena.

## 5. Narrador fijo (aprobado por el usuario el 2026-11-26: «Perfecto, OK»)
- **Definido una sola vez** en `config/narrator.json` (medidas, paleta, ropa, rig, caras, poses) + `retro3d/characters/narrator.py` (construcción y animación). Huella SHA-256 en `config/narrator.lock` (actual: `6ec52617807948fe…`); si no coincide, el pipeline **se niega a renderizar**. Solo se modifica con permiso explícito del usuario y luego `python tools/lock_narrator.py`.
- **Diseño** (≈1.156 triángulos):
  - **Pasamontañas magenta `#D61F8C`** (borde `#B0166F`) que cubre cabeza y cuello; deja ver solo una **franja de ojos** (piel, con cejas y párpados) y una **abertura ovalada para la boca**; **cruz cristiana pequeña blanca** (`#F4F2EC`) centrada arriba en la frente (geometría: dos barras). Cabeza 0,54×0,50×0,56 m, bisel 0,07, ligeramente estrechada arriba.
  - **Piel clara** `#F2D6C3` (ojos, boca, antebrazos, manos).
  - **Jersey streetwear** oversize negro `#1D1E24`: cuello en V fino, mangas cortas anchas con franja blanca, doble franja blanca en el bajo, número **«00»** pequeño delante y grande detrás (textura pixel).
  - **Pantalón militar** ancho de **camuflaje** (textura 32 px de 3 tonos: `#6B7350`, `#474E33`, `#9C8D62`) con **bolsillos cargo con solapa** en cada muslo.
  - **Cinturón** negro con **hebilla de plata** (`#CDD2D8`), **dos remaches y puntera de oro** (`#E3B53C`).
  - **Cadena fina de plata** (`#B4BAC2`): eslabones por detrás del cuello y caída en U sobre el pecho.
  - **Zapatillas** de silueta tipo «Air Force» **sin logotipos**: blancas `#F4F3EE`, suela gruesa crema `#E8E2D2`, talonera negra a juego con el jersey.
- **Rig** por segmentos rígidos: root → hips → torso → head; brazos `arm_R/L` → `fore_*` → `hand_*`; piernas `thigh_*` → `shin_*`. Lado «R» = −X; el personaje mira a −Y.
- **Cara** (atlas 128 px, `textures.balaclava_atlas`): **6 expresiones** (neutral, happy, surprised, angry, sad, skeptical) × **3 párpados** (open, half, closed); **5 bocas** para la sincronía labial (X cerrada con media sonrisa, M entreabierta, E ancha, A abierta, O redonda) dentro de la abertura.
- **Poses** (en el JSON, convención «hacia fuera positivo», L espejada): idle, talk, explain, point, shrug, cross_arms (antebrazos apilados delante del pecho; con brazos tan cortos no llegan a cruzar del todo), wave, lean_in (confidencia; mano junto a la mejilla, calculada numéricamente sin colisiones), offer_hand, laugh, look_down; más walk procedural.
- **Vida**: respiración, cambio de peso de pie cada ~4,5 s (ciclo de 9 s, rodilla de la pierna libre doblada), parpadeo cada 2–4 s y al final de cada frase, **gestos de énfasis** en palabras acentuadas (picos de energía de la voz): asentir, golpe de manos, levantar una mano, ladear la cabeza con ojos de sorpresa, con anticipación.
- Hoja de diseño y clip: `docs/narrador/narrador_hoja.jpg`, `docs/narrador/narrador_clip_3s.mp4` (regenerar con `python tools/narrator_sheet.py`).
- Historia del diseño: v1 aventurero de túnica (descartado) → minimalista con túnica (descartado) → **pasamontañas magenta + sudadera** (boceto) → **pasamontañas + jersey + militar + cinturón + cadena + zapatillas blancas, piel clara, cruz** (aprobado).

## 6. Otros personajes y escenarios
- **Perro** (`retro3d/characters/dog.py`, ~550 tris): canela con hocico crema, orejas caídas con muelle, cola de 3 segmentos con muelle, collar rojo, mandíbula y lengua articuladas. Variantes `pup` (cachorro crema, cabeza grande) y `mom` (madre marrón). Acciones: idle, wag (con jadeo), sit, head_tilt, jump (**uno solo** con anticipación y aplastamiento), lick (con objetivo), lick_paw, calm, nuzzle, walk.
- **Escenario «claro»** (`retro3d/world.py`): terreno con hierba y camino de tierra mezclados por vértice, cabaña de piedra y madera, muro de piedra, vallas, farol, árboles y pinos simples, rocas, matojos, montañas, nubes.
- **Escenario «casa»** (`retro3d/interior.py`, en `ORIGIN=(0,-400,0)`): interior de la cabaña con frente abierto a cámara; suelo de tablas, zócalo de piedra, ventana con luz de día, chimenea con fuego que parpadea, alfombra, **cojín del perro (superficie pisable a 0,14 m)**, mesa, taburete, estante. Luz propia (`LIGHT_INTERIOR`), sin niebla. La luz cambia sola según la zona del sujeto del plano.

## 7. Arquitectura del pipeline
- **Comando único**: `python make_video.py scripts/NN-tema.json [--dry|--cost|--tts|--storyboard|--preview|--contact|--from|--to|--out|--reuse-video]`. `--reuse-video build/<id>/video.mp4` rehace solo el audio sobre imágenes ya renderizadas (~30 s).
- **Opciones globales del guion** (usar en vídeos nuevos): `"master": "clean2", "lufs": -16`, `"music": {"style": "aldea", "db": -19, "duck_db": -5}`, `"icon_style": "world"`, `"cam_smooth": 0.18`. Sin ellas, los guiones antiguos renderizan como antes.
  - `--dry` storyboard con tiempos estimados (sin voz) · `--cost` caracteres/créditos · `--tts` genera la voz (una toma, caché) · `--storyboard` con tiempos reales · `--preview` 540×960 · `--contact` hoja por plano · `--out` ruta del MP4.
- **Flujo interno**: guion JSON → voz con timestamps (caché) → verificación/corrección del desfase de timestamps → recorte de pausas largas → director (`production.py`: anclas a palabras → planos, acciones, recursos, efectos) → render fotograma a fotograma con físicas y comprobaciones → subtítulos → voz procesada sola (`voice_chain`) → mezcla de efectos y música → bus final (limitador suave) a −16 LUFS → MP4 → `qa.md`.
- **Archivos**: `retro3d/` → `style.py` (identidad), `render.py` (moderngl), `mesh.py`, `textures.py`, `font.py` (fuente pixel 5×7 propia), `world.py`, `interior.py`, `characters/{base,narrator,dog}.py`, `props.py` (carteles, bocadillos, iconos, medallones, chispas), `camera.py`, `physics.py`, `production.py`, `voice.py`, `audio.py` (másteres `classic`, `clean`, `clean2`), `music.py` (música original por código), `lipsync.py`, `subtitles.py`, `anim.py`, `rig.py`, `mathutil.py`. `tools/`: `narrator_sheet.py`, `lock_narrator.py`, `preview_characters.py`, `check_physics.py`, `shot_frames.py` (inicio/mitad/final de cada plano + avisos de encuadre; `--dry` sin voz). `config/`: `voice.json`, `narrator.json`, `narrator.lock`. `scripts/01-perro-lame*.json` (v1–v2 en el original; `-v3`, `-v4`, `-v5`). Salidas temporales en `build/` (ignorado por git).
- **Motor de render: moderngl + EGL + Mesa llvmpipe** (CPU, sin GPU). Medido a 1080×1920 en la fase 1: Blender Workbench ~1,1 s/fot., EEVEE por software ~60 s/fot., Cycles 16 spp ~21 s/fot., **moderngl ~0,1–0,2 s/fot.** Elegido por velocidad y porque da control total del look (niebla, cielo, *nearest*, sombreado plano). Rasterizador numpy descartado (más lento y sin ventaja). Requiere `apt-get install -y libegl1 libegl-mesa0`.
- **Dependencias**: `pip install moderngl numpy pillow scipy soundfile pyloudnorm` (+ `bpy` se instaló solo para la prueba de motores; no se usa). ffmpeg preinstalado. Fuente Montserrat copiada en `assets/fonts/`.
- **Entorno**: sin internet general (solo gestores de paquetes y `api.elevenlabs.io`).

## 8. Voz (ElevenLabs) — `config/voice.json`
- `voice_id` **`851ejYcv2BoNPjrkw93G`** (siempre; si falla o suena mal, avisar y **no** cambiarla), modelo **`eleven_v3`**, `language_code` **`"es"`**, `stability` **0.5**, endpoint `/v1/text-to-speech/{voice_id}/with-timestamps`, `output_format` `mp3_44100_128`.
- Clave **solo** de `ELEVENLABS_API_KEY` (nunca guardarla ni imprimirla).
- **Coste**: ≈ 1 crédito por carácter del texto completo (`python make_video.py <guion> --cost`). Vídeo 01: 557 caracteres (guion original, v1–v3) + 588 caracteres (guion del usuario, v4–v5), una toma cada uno, ya en caché. Prueba de voz inicial: 55 caracteres (`samples/prueba_voz.mp3`).
- **Caché**: `cache/voice/<hash>.mp3/.json` (hash de configuración + texto), versionada en git. **Cambiar el texto del guion obliga a regenerar la voz (cuesta créditos)**; cambiar planos/acciones/recursos no.
- **Una toma por vídeo**; antes, decir caracteres y créditos y esperar el OK.
- Timestamps: se verifican contra la envolvente real (correlación) y se corrigen si se desvían ≥30 ms (vídeo 01: +0,12 s, coincidencia 0,65 → 0,77); pausas > 0,42 s se acortan a 0,30 s sin regenerar (vídeo 01: 6 cortes, −1,6 s).

## 9. Reglas
- **Guion**: español de España, tono de colega, humor seco, frases cortas, **80–105 palabras**; gancho ≤3 s, bucle abierto a mitad, 3–4 razones fáciles, cierre útil; prohibido estilo ChatGPT («en el mundo actual», «descubre cómo», «sin más dilación», «es importante destacar», «te voy a contar», «en este vídeo», relleno, emojis); lo dudoso con «se cree que» y cada afirmación con confianza en `facts_to_verify.md`; cifras y siglas escritas como se pronuncian; **enseñar guion + storyboard + coste y esperar OK antes de generar la voz**.
- **Sonido**: cada efecto es un **evento puntual** (inicio, duración, motivo) ligado al guion o la animación; **nada en bucle** salvo petición explícita (ambiente solo con `"ambience_db"`); efectos suaves; **18–24 dB bajo la voz**, fundidos, atenuación extra de 6 dB al hablar; lametón máx. 2 sonidos por acción; verificación obligatoria con `sfx_report.md` y **0 sonidos sostenidos > 1 s**; **−16 LUFS, pico ≤ −1,5 dBTP** (aprobado por el usuario en la v5; con esta voz, PLR 18,6 dB, −14 LUFS exige ~9 dB de limitador y suena saturado) con `master: clean2`. Música de fondo: solo la original de `retro3d/music.py`, −19 dB bajo la voz y −5 dB extra al hablar. Sin música de terceros.
- **Encuadres**: `python tools/shot_frames.py <guion>` → **0 avisos** (cabezas cortadas, recursos fuera de cuadro, en el 6 % superior o tapando caras) antes de renderizar.
- **Cámara**: un plano por beat en el JSON con `type` (establish, orbit, crane, truck, low, push, pull), `size` (wide/medium/close), curva; barridos `whip` con desenfoque entre escenas; golpes de zoom en palabras clave; no repetir tipo seguido ni tres tamaños iguales seguidos; cambio cada 2–3 s; holgura ≥0,3 m a modelos y suelo en cada fotograma.
- **Textos**: letra a letra (~30 letras/s; subtítulos dentro del tiempo de cada palabra), subida + fundido de 0,1 s por letra, salida con fundido rápido; palabra actual resaltada.
- **Físicas/contactos**: nada atraviesa nada ni el suelo; volúmenes OBB por pieza comprobados en cada fotograma (tolerancia 2 cm); restricciones automáticas (codo hacia fuera si el antebrazo invade el cuerpo, cuello arriba si la cabeza invade las patas); pies apoyados (también sobre el cojín); contacto de lengua con objetivo real (se detiene en la superficie, 5 rayos, margen 1,2 cm, aplastamiento; la mano cede); `approach` coloca al perro frente al objetivo; anticipación y amortiguación en saltos. `python tools/check_physics.py <guion>` debe dar **0** antes de renderizar.
- **Revisión antes de entregar**: hoja con 1 fotograma por plano (`contact.jpg`), primeros planos de contactos (`contactos.jpg`), `qa.md` en verde (montaje, holgura de cámara, interpenetraciones, pies, contactos, zonas seguras, textos 3D cortados, boca, LUFS, efectos), revisión manual de fotogramas; corregir y repetir si algo falla.
- **Protección**: no modificar narrador, estilo ni pipeline base sin permiso explícito; las novedades se añaden sin romper lo existente; cada versión aprobada → tag `vK` y anotarla aquí.

## 10. Historial de cambios pedidos por el usuario (orden cronológico; sesiones 2026-11-26-01 y -02)
1. **Encargo inicial**: pipeline desde cero, estilo MMO retro low-poly, narrador aventurero + perro creados por código, voz ElevenLabs, subtítulos, 1080×1920 −14 LUFS; vídeo de prueba «¿Por qué tu perro te lame?». → Fases 1–4 hechas; motor moderngl elegido tras medir.
2. **«OK A TODO»** (guion, voz y gasto de ~557 créditos) → voz generada; vídeo v1 (aventurero de túnica, estilo detallado). Correcciones propias: números de vóxeles finos → medallones; desfase de timestamps +0,12 s; `loudnorm` no llegaba a −14 LUFS → máster propio; MP4 de 80 MB → crf 19.
3. **«Más minimalista aún» + todas las mejoras propuestas** → caras de un tono, menos piezas, texturas de 2 tonos, escenario despejado; gestos de énfasis; interior de la cabaña; contraluz; zoom de golpe en el gancho; peso 59 → 25 MB.
4. **Narrador fijo y reutilizable (prioridad máxima)**: persona con pasamontañas magenta `#D61F8C`, streetwear, rig con expresiones y bocas; bocetos y parar hasta el OK. → `config/narrator.json` + lock; hoja y clip. Fallos propios corregidos antes de enseñar: brazos cruzados con las manos dentro del torso, saludo con el antebrazo hacia abajo (signo), primeros planos demasiado cerca, cabeza demasiado cúbica.
5. **Cambios al narrador**: piel más clara, cruz cristiana pequeña arriba en el pasamontañas, pantalón más ancho estilo militar, cinturón con plata y oro, cadena fina de plata, zapatillas tipo Air Force del color que mejor combine, jersey streetwear en lugar de sudadera. → Hecho (cadena primero se leía como una «V» gruesa; corregida).
6. **«Perfecto, OK, prosigue con todo»** (fases 2–6):
   - **Bug: el lametón sonaba todo el rato** → causa: un lametón cada ⅓ s durante toda la acción de lamer y lamerse la pata (varios segundos) + viento de fondo continuo. Solución: eventos puntuales, máx. 2 lametones por acción, sin ambiente, niveles relativos a la voz, atenuación al hablar, informe.
   - **Cámara dinámica**: repertorio de planos, barridos con desenfoque, zooms, validación y colisión.
   - **Bug: la lengua/hocico atravesaba la mano** → causa: animación «a ojo» y perro mal colocado (la mano quedaba 44 cm detrás del hocico en la v1; luego, la mano «cedía» después de calcular la lengua). Solución: contacto con objetivo (la lengua se detiene en la superficie), aproximación automática del perro, la mano cede antes, 5 rayos por el ancho de la lengua, resolución durante el fundido entre acciones.
   - Otras interpenetraciones encontradas por el verificador (166 fotogramas): antebrazo/mano dentro del torso en la pose de confidencia y al explicar; manga contra el pasamontañas al encogerse; brazo que señalaba dentro de la cabeza del perro; lengua dentro del pecho al lamerse la pata; cabeza del perro apoyada en su pecho (por diseño → par adyacente). Todas corregidas → **0**.
   - Textos letra a letra con fundido; revisión automática; vídeo v2 con todo.
7. **Sesión 2026-11-26-02 — feedback de la v2**: audio saturado; símbolos sin brillo ni contorno; revisar físicas/movimientos de cámara; mejorar todo lo posible. → Causas y soluciones:
   - **Saturación**: el máster antiguo bajaba la ganancia en escalones instantáneos de 2 ms acumulados en 12 pasadas (hasta 12 dB; 10 % de la modulación de ganancia por encima de 40 Hz). Nuevo `audio.master_clean` (paso alto 70 Hz, de-esser, nivelador RMS lento, compresor de picos con anticipación 10 ms, limitador con rampa coseno): limitador ≤2,8 dB, modulación audible −13 dB. Opción `"master": "clean"`.
   - **Símbolos**: `"icon_style": "glow"` → se dibujan encima de la escena, contorno de pegatina (blanco + tinta) en posproceso, halo de su color que late, anillo de destello al aparecer; patatas fritas rehechas.
   - **Cámara**: medición por fotograma: el gancho se acercaba a 61 m/s, los planos que siguen a la mano o al perro copiaban cada sacudida (17–19 m/s²) y el empujón anti-pared daba un salto de 190 m/s². Solución: `"cam_smooth": 0.18` (muelle crítico para sujeto y cámara, se reinicia en cada corte) y acercamientos más cortos.
   - **Encuadres**: nueva `tools/shot_frames.py` (inicio/mitad/final de cada plano + avisos de cabezas cortadas, recursos fuera de cuadro o tapando caras): 20 avisos → 0. Corregidos gancho, lametones (planos 4 y 13), patatas sobre la cabeza, medallones cortados por el golpe de zoom, generales del interior y final, cartel del veterinario.
8. **v4 (misma sesión)**: mantener la v3 salvo los iconos → integrados en la escena: `"icon_style": "world"` (iluminados por la luz del plano, proyectan sombra, sombra de contacto en el suelo, los tapan los personajes, brillo propio que late y anillo al aparecer; anclados al mundo, no a la pantalla). Guion nuevo del usuario (112 palabras, por encima de la regla de 80–105, aceptado por el usuario): voz regenerada (588 créditos). Icono nuevo `lollipop` (chupachups sin marca). Corregido un fallo antiguo: los corazones de «te ríes» terminaban antes de empezar (el ancla «ha» coincidía con «te ha»). `tools/shot_frames.py --dry` y aviso de recursos en el 6 % superior (interfaz de TikTok).
9. **v5 (misma sesión)**: «se escucha un ruido de fondo en la voz» + «música de fondo bastante baja, sin copyright, te doy libertad». Causa del ruido: el máster `clean` de la v3/v4 tenía un compresor de picos de umbral fijo que el bucle de ganancia perseguía (+38 dB de ganancia, 25 dB de compresión): silencios de −68 a −40 dBFS. Solución `"master": "clean2"`: la voz se procesa sola (expansor que baja los silencios, nivelador, compresor de picos limitado a 6 dB, limitador), luego efectos y música, y un limitador final suave (≤0,5 dB). Ruido en silencios −71 dBFS. Medido: con esta voz (PLR 18,6 dB), −14 LUFS a ≤−2 dBTP exige ~9 dB de limitador o un recortador (armónicos −13 dB) → se propone −16 LUFS (limitador 2,1 dB); a −14 el pico tras AAC fue −1,4 dBTP (fuera de regla). Música: `retro3d/music.py` (100 BPM, Fa mayor, bajo, colchón, arpegio de pulso, campanita, batería ligera con swing; sin melodía en la banda de la voz), −19 dB bajo la voz y −5 dB extra al hablar (opción `"music"`). Nueva opción `--reuse-video` para rehacer solo el audio.
10. **Aprobación**: «Me quedo con la primera [−16 LUFS], ya está, este TikTok lo subiré» → tag `v5` en `978dfcd`; regla de −16 LUFS y música anotadas en `CLAUDE.md`. Aviso: en los próximos vídeos querrá cambiar muchas cosas de la animación.
11. **Sistema de sesiones** (`/save-session`, `/resume-session`, este documento, regla de protección y tags). → Esta entrada.

## 11. Vídeos producidos
| Vídeo | Ruta / commit | Contenido | Duración | Render (solo imagen) | Estado |
|---|---|---|---|---|---|
| v1 detallada | `videos/01-perro-lame.mp4` en commit `dfe7a22` (sobrescrita después) | narrador aventurero de túnica, estilo detallado | 38,65 s | 257 s (0,22 s/fot.) | sustituida por la minimalista |
| v1 minimalista | `videos/01-perro-lame.mp4` (commit `6e4e9aa`, actual en la rama) | aventurero minimalista, interior, gestos, contraluz | 38,65 s | 226 s (0,19 s/fot.) | la que el usuario llamó «primera versión» |
| v2 | `videos/01-perro-lame-v2.mp4` (commit `face026`) | narrador del pasamontañas, cámara dinámica, físicas, textos letra a letra, sonido corregido | 38,65 s, 28,8 MB | 385 s (0,33 s/fot.) | usuario: audio «saturado», símbolos «aparecen y ya está» → v3 |
| v3 | `videos/01-perro-lame-v3.mp4` (guion `scripts/01-perro-lame-v3.json`) | máster limpio, iconos con halo/contorno/destello, cámara amortiguada, encuadres corregidos | 38,65 s, 30,4 MB | 375 s (0,32 s/fot.) | base de la v4 |
| v4 | `videos/01-perro-lame-v4.mp4` (guion `scripts/01-perro-lame-v4.json`, voz nueva 588 caracteres) | guion nuevo del usuario, iconos integrados en la escena (`icon_style: world`), chupachups, bocadillos «¡DAME LA PUTA COMIDA!» y «¡ESTO MOLA!» | 37,75 s, 29,2 MB | 274 s (0,24 s/fot.) | usuario: ruido de fondo en la voz → v5 |
| **v5** | `videos/01-perro-lame-v5.mp4` (commit `978dfcd`, guion `scripts/01-perro-lame-v5.json`; imágenes de la v4 con `--reuse-video`) | máster `clean2` sin ruido de fondo, −16 LUFS / −1,7 dBTP; música original «aldea» generada por código | 37,75 s | solo audio (~30 s) | **APROBADA (tag `v5`)**, el usuario la sube a TikTok |
- Informes: `docs/01-perro-lame-v3/`, `-v4/` (qa, contact, contactos, sfx, framing) y `-v5/` (qa de audio, sfx).
- Informes de la v2 en `docs/01-perro-lame-v2/` (`qa.md`, `contact.jpg`, `contactos.jpg`, `sfx_report.md/.json`). Resultado: 24 planos, montaje OK, holgura cámara 0,30 m, 0 interpenetraciones, 0 pies flotando, 24 contactos, 0 subtítulos fuera de zona, 0 textos cortados, boca coherente 94,2 %, −14,0 LUFS / −2,1 dBTP, 36 efectos, 0 sostenidos.

## 12. Versiones aprobadas (tags de git)
- Aprobaciones explícitas: guion + voz del vídeo 01 original («OK A TODO»); diseño del narrador v3 («Perfecto, OK», `b649c5c`); **vídeo 01 v5** («Me quedo con la primera, ya está»).
- Al aprobar una versión: `git tag -a vK -m "<qué contiene>" <commit>` + `git push origin vK`, y anotarla aquí.

| Tag | Commit | Contenido |
|---|---|---|
| `v5` | `978dfcd` | Vídeo 01 «¿Por qué tu perro te lame?» v5: guion del usuario (v4), iconos integrados en la escena con sombras, chupachups, bocadillos nuevos, cámara amortiguada, voz sin ruido (máster `clean2`, −16 LUFS) y música original «aldea». |

## 13. Problemas conocidos
- **El usuario quiere cambiar muchas cosas de la animación** en los próximos vídeos (aún no ha dicho cuáles).
- **Perro lamiéndose la pata**: la lengua toca pecho/pierna; la pata apenas se levanta → se lee peor que el lametón a la mano.
- **Sincronía labial** coherente en el 92 % (v4/v5; 94 % con la voz anterior): timestamps por letra; mejorarla requiere detectar sílabas.
- **Planos sin efectos** (varios planos): podrían llevar un paso o *whoosh* leve.
- **Plano 9**: asoma un trozo del perro en la esquina inferior derecha.
- El comprobador de textos 3D (`qa.md`) mide la caja del bocadillo; los iconos se comprueban con `tools/shot_frames.py` (3 fotogramas por plano, no todos).
- El máster `clean` (v3/v4) tiene el fallo del bucle de ganancia (voz aplastada, ruido +30 dB): no usarlo; usar `clean2`.
- `tools/preview_characters.py` muestra acciones antiguas (la hoja oficial del narrador es `tools/narrator_sheet.py`).
- `CLAUDE.md` conserva notas antiguas de distancias de cámara y del aventurero en secciones de formato; las reglas vigentes son las de este documento.

## 14. Pendiente y siguiente paso exacto
1. **Esperar al usuario**: tema del vídeo 02 y/o lista de cambios de animación. No tocar nada antes.
2. Vídeo nuevo: copiar `scripts/01-perro-lame-v5.json` (trae `master: clean2`, `lufs: -16`, `music`, `icon_style: world`, `cam_smooth`) → guion `scripts/02-…json` → `--dry` + `tools/shot_frames.py --dry` → enseñar guion + storyboard + coste → esperar OK → `--tts` → `tools/shot_frames.py` (0 avisos) + `tools/check_physics.py` (0) → `--contact` → QA.
3. Cambios de animación que toquen el narrador, el estilo o el pipeline base: solo con permiso explícito y sin romper lo anterior (opciones nuevas en el guion).
4. Unir la rama `claude/hopeful-einstein-ix8p37` a `main` cuando el usuario lo pida (PR).
5. Mejoras opcionales: las de §13.

## 15. Decisiones que debe tomar el usuario
- Qué cambios de animación quiere para los próximos vídeos.
- Tema del **vídeo 02**.
- ¿Abrir PR de `claude/hopeful-einstein-ix8p37` a `main`?
- ¿Aplicar las mejoras de §13 (pata del perro, efectos en planos silenciosos, sincronía labial)?
- ¿Estilo de música distinto para otros vídeos (ahora solo «aldea»)?
- Narrador: ¿número del jersey («00»)?, ¿ropa alternativa (`outfit`)?
- Si los vídeos crecen: ¿Git LFS o guardarlos fuera del repo? (5 MP4 de ~25–30 MB en `videos/`).

## 16. Índice de sesiones
- [2026-11-26-01](sessions/2026-11-26-01.md) — creación del pipeline, vídeo 01 (v1 detallada, v1 minimalista, v2), narrador fijo, sistema de sesiones.
- [2026-11-26-02](sessions/2026-11-26-02.md) — vídeo 01 v3 (audio, iconos con brillo, cámara, encuadres), v4 (guion del usuario, iconos integrados), v5 (voz sin ruido, −16 LUFS, música original); **v5 aprobada (tag `v5`)**.
