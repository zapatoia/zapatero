# PIPELINE_STATE — documento maestro del proyecto

> Última actualización: 2026-11-26 (sesión `docs/sessions/2026-11-26-01.md`).
> Rama de trabajo anterior: `claude/3d-mmo-retro-video-pipeline-3ify9e`. **PR #2 fusionada en `main`** (commit de fusión `df76761`, https://github.com/zapatoia/zapatero/pull/2). **`main` es ya la rama por defecto en GitHub** (antes lo era `claude/shoe-history-vertical-video-qw2b0t`). Las sesiones nuevas parten de `main`.

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
Pipeline completo y funcionando; narrador definitivo (pasamontañas magenta) **aprobado**; vídeo **`videos/01-perro-lame-v2.mp4` entregado y pendiente de valoración**. **Siguiente paso exacto:** esperar la opinión del usuario sobre la v2 → si la aprueba, crear el tag `v2`; si pide cambios, aplicarlos y re-renderizar como `-v3`.

## 4. Estilo visual actual (resumen de `STYLE.md`; fuente de verdad en código: `retro3d/style.py`)
- Low-poly con **sombreado plano** (normales por cara) y **color por vértice uniforme** (`jitter=0`).
- **Texturas mínimas pixeladas** 16–32 px con filtro *nearest* (máx. 128 px, lo impone `Renderer.add_texture`): dos tonos en manchas grandes (hierba, tierra) o solo líneas de junta (piedra, tablas, tejas). Personajes: sin textura, salvo el camuflaje del pantalón y las caras/número en atlas pixel. **Nunca** normal maps ni PBR.
- **Luz cálida de tarde**: sol bajo 3/4 delantero-izquierdo (`LIGHT.sun_dir = (-0.62,-0.42,0.62)`), relleno hemisférico generoso (caras legibles), sombras duras (mapa de sombras 2048, PCF 4) que tiran a violeta, **contraluz cálido** (rim) en personajes e iconos.
- **Cielo** degradado suave con halo discreto; **niebla lineal** 18–70 m del color del horizonte; montañas azuladas facetadas y 5 nubes planas.
- **Post**: brillo suave, +6 % saturación, +4 % contraste, viñeta ligera.
- **Paleta mundo**: hierba `#467027/#5f8c2e/#7aa23a`, tierra `#7f5530/#a7743f/#c39257`, piedra `#686357/#8c8577/#aaa291`, madera `#7a4f2b/#9a6a3c/#b98451`, tejas `#a44c33`.
- **Subtítulos**: Montserrat Black (OFL, en `assets/fonts/`), MAYÚSCULAS, blanco con contorno marrón-negro de 10 px, palabra actual amarilla `#FFD23F`, bloques de ≤3 palabras centrados al 66,5 % de la altura; **zonas seguras**: nada en el 20 % inferior ni el 12 % derecho.
- Decisiones clave: moderngl en vez de Blender (velocidad y control del look); minimalismo; medallones para números; textos letra a letra; contraluz; dos escenarios.

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
- **Comando único**: `python make_video.py scripts/NN-tema.json [--dry|--cost|--tts|--storyboard|--preview|--contact|--from|--to|--out]`.
  - `--dry` storyboard con tiempos estimados (sin voz) · `--cost` caracteres/créditos · `--tts` genera la voz (una toma, caché) · `--storyboard` con tiempos reales · `--preview` 540×960 · `--contact` hoja por plano · `--out` ruta del MP4.
- **Flujo interno**: guion JSON → voz con timestamps (caché) → verificación/corrección del desfase de timestamps → recorte de pausas largas → director (`production.py`: anclas a palabras → planos, acciones, recursos, efectos) → render fotograma a fotograma con físicas y comprobaciones → subtítulos → mezcla de efectos → máster −14 LUFS → MP4 → `qa.md`.
- **Archivos**: `retro3d/` → `style.py` (identidad), `render.py` (moderngl), `mesh.py`, `textures.py`, `font.py` (fuente pixel 5×7 propia), `world.py`, `interior.py`, `characters/{base,narrator,dog}.py`, `props.py` (carteles, bocadillos, iconos, medallones, chispas), `camera.py`, `physics.py`, `production.py`, `voice.py`, `audio.py`, `lipsync.py`, `subtitles.py`, `anim.py`, `rig.py`, `mathutil.py`. `tools/`: `narrator_sheet.py`, `lock_narrator.py`, `preview_characters.py`, `check_physics.py`. `config/`: `voice.json`, `narrator.json`, `narrator.lock`. `scripts/01-perro-lame.json`. Salidas temporales en `build/` (ignorado por git).
- **Motor de render: moderngl + EGL + Mesa llvmpipe** (CPU, sin GPU). Medido a 1080×1920 en la fase 1: Blender Workbench ~1,1 s/fot., EEVEE por software ~60 s/fot., Cycles 16 spp ~21 s/fot., **moderngl ~0,1–0,2 s/fot.** Elegido por velocidad y porque da control total del look (niebla, cielo, *nearest*, sombreado plano). Rasterizador numpy descartado (más lento y sin ventaja). Requiere `apt-get install -y libegl1 libegl-mesa0`.
- **Dependencias**: `pip install moderngl numpy pillow scipy soundfile pyloudnorm` (+ `bpy` se instaló solo para la prueba de motores; no se usa). ffmpeg preinstalado. Fuente Montserrat copiada en `assets/fonts/`.
- **Entorno**: sin internet general (solo gestores de paquetes y `api.elevenlabs.io`).

## 8. Voz (ElevenLabs) — `config/voice.json`
- `voice_id` **`851ejYcv2BoNPjrkw93G`** (siempre; si falla o suena mal, avisar y **no** cambiarla), modelo **`eleven_v3`**, `language_code` **`"es"`**, `stability` **0.5**, endpoint `/v1/text-to-speech/{voice_id}/with-timestamps`, `output_format` `mp3_44100_128`.
- Clave **solo** de `ELEVENLABS_API_KEY` (nunca guardarla ni imprimirla).
- **Coste**: ≈ 1 crédito por carácter del texto completo (`python make_video.py <guion> --cost`). Vídeo 01: 557 caracteres ≈ 557 créditos (una sola toma, ya en caché). Prueba de voz inicial: 55 caracteres (`samples/prueba_voz.mp3`).
- **Caché**: `cache/voice/<hash>.mp3/.json` (hash de configuración + texto), versionada en git. **Cambiar el texto del guion obliga a regenerar la voz (cuesta créditos)**; cambiar planos/acciones/recursos no.
- **Una toma por vídeo**; antes, decir caracteres y créditos y esperar el OK.
- Timestamps: se verifican contra la envolvente real (correlación) y se corrigen si se desvían ≥30 ms (vídeo 01: +0,12 s, coincidencia 0,65 → 0,77); pausas > 0,42 s se acortan a 0,30 s sin regenerar (vídeo 01: 6 cortes, −1,6 s).

## 9. Reglas
- **Guion**: español de España, tono de colega, humor seco, frases cortas, **80–105 palabras**; gancho ≤3 s, bucle abierto a mitad, 3–4 razones fáciles, cierre útil; prohibido estilo ChatGPT («en el mundo actual», «descubre cómo», «sin más dilación», «es importante destacar», «te voy a contar», «en este vídeo», relleno, emojis); lo dudoso con «se cree que» y cada afirmación con confianza en `facts_to_verify.md`; cifras y siglas escritas como se pronuncian; **enseñar guion + storyboard + coste y esperar OK antes de generar la voz**.
- **Sonido**: cada efecto es un **evento puntual** (inicio, duración, motivo) ligado al guion o la animación; **nada en bucle** salvo petición explícita (ambiente solo con `"ambience_db"`); efectos suaves; **18–24 dB bajo la voz**, fundidos, atenuación extra de 6 dB al hablar; lametón máx. 2 sonidos por acción; verificación obligatoria con `sfx_report.md` y **0 sonidos sostenidos > 1 s**; máster −14 LUFS, pico ≤ −1,5 dBTP (máster propio: compresión + ganancia + limitador de pico verdadero ×4, techo −2,3 dBTP; `loudnorm` lineal de ffmpeg no llega). Sin música de terceros.
- **Cámara**: un plano por beat en el JSON con `type` (establish, orbit, crane, truck, low, push, pull), `size` (wide/medium/close), curva; barridos `whip` con desenfoque entre escenas; golpes de zoom en palabras clave; no repetir tipo seguido ni tres tamaños iguales seguidos; cambio cada 2–3 s; holgura ≥0,3 m a modelos y suelo en cada fotograma.
- **Textos**: letra a letra (~30 letras/s; subtítulos dentro del tiempo de cada palabra), subida + fundido de 0,1 s por letra, salida con fundido rápido; palabra actual resaltada.
- **Físicas/contactos**: nada atraviesa nada ni el suelo; volúmenes OBB por pieza comprobados en cada fotograma (tolerancia 2 cm); restricciones automáticas (codo hacia fuera si el antebrazo invade el cuerpo, cuello arriba si la cabeza invade las patas); pies apoyados (también sobre el cojín); contacto de lengua con objetivo real (se detiene en la superficie, 5 rayos, margen 1,2 cm, aplastamiento; la mano cede); `approach` coloca al perro frente al objetivo; anticipación y amortiguación en saltos. `python tools/check_physics.py <guion>` debe dar **0** antes de renderizar.
- **Revisión antes de entregar**: hoja con 1 fotograma por plano (`contact.jpg`), primeros planos de contactos (`contactos.jpg`), `qa.md` en verde (montaje, holgura de cámara, interpenetraciones, pies, contactos, zonas seguras, textos 3D cortados, boca, LUFS, efectos), revisión manual de fotogramas; corregir y repetir si algo falla.
- **Protección**: no modificar narrador, estilo ni pipeline base sin permiso explícito; las novedades se añaden sin romper lo existente; cada versión aprobada → tag `vK` y anotarla aquí.

## 10. Historial de cambios pedidos por el usuario (orden cronológico, sesión 2026-11-26-01)
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
7. **Sistema de sesiones** (`/save-session`, `/resume-session`, este documento, regla de protección y tags). → Esta entrada.

## 11. Vídeos producidos
| Vídeo | Ruta / commit | Contenido | Duración | Render (solo imagen) | Estado |
|---|---|---|---|---|---|
| v1 detallada | `videos/01-perro-lame.mp4` en commit `dfe7a22` (sobrescrita después) | narrador aventurero de túnica, estilo detallado | 38,65 s | 257 s (0,22 s/fot.) | sustituida por la minimalista |
| v1 minimalista | `videos/01-perro-lame.mp4` (commit `6e4e9aa`, actual en la rama) | aventurero minimalista, interior, gestos, contraluz | 38,65 s | 226 s (0,19 s/fot.) | la que el usuario llamó «primera versión» |
| **v2** | `videos/01-perro-lame-v2.mp4` (commit `face026`) | narrador del pasamontañas, cámara dinámica, físicas, textos letra a letra, sonido corregido | 38,65 s, 28,8 MB | **385 s** (0,33 s/fot.; ~7 min con mezcla y codificación) | **entregada, pendiente de valoración** |
- Informes de la v2 en `docs/01-perro-lame-v2/` (`qa.md`, `contact.jpg`, `contactos.jpg`, `sfx_report.md/.json`). Resultado: 24 planos, montaje OK, holgura cámara 0,30 m, 0 interpenetraciones, 0 pies flotando, 24 contactos, 0 subtítulos fuera de zona, 0 textos cortados, boca coherente 94,2 %, −14,0 LUFS / −2,1 dBTP, 36 efectos, 0 sostenidos.

## 12. Versiones aprobadas (tags de git)
- **Ninguna versión de vídeo aprobada explícitamente todavía; no hay tags.**
- Aprobaciones explícitas hasta ahora: guion + voz del vídeo 01 («OK A TODO»); diseño del narrador v3 («Perfecto, OK», commit `b649c5c`; después solo se retocaron tres poses por colisiones en `face026`).
- Cuando el usuario apruebe una versión: `git tag -a vK -m "<qué contiene>" <commit>` + `git push origin vK`, y añadirla a esta tabla.

| Tag | Commit | Contenido |
|---|---|---|
| — | — | — |

## 13. Problemas conocidos
- **Perro lamiéndose la pata**: la lengua toca pecho/pierna; la pata apenas se levanta → se lee peor que el lametón a la mano.
- **Plano 1 (gancho)**: el narrador queda en el borde izquierdo del encuadre.
- **Planos sin efectos** (8, 9, 17, 21, 23, 24 de la v2): podrían llevar algún paso o *whoosh* leve.
- **Render más lento** con las comprobaciones (0,33 s/fot.): la búsqueda de colisiones y el desenfoque de los barridos.
- **Sincronía labial** coherente en el 94 %: los timestamps son por letra; mejorarla requiere detectar sílabas con más precisión.
- `tools/preview_characters.py` sigue mostrando acciones antiguas (útil, pero la hoja oficial del narrador es `tools/narrator_sheet.py`).
- El cachorro conserva su acción de lamer el resto del vídeo (fuera de cuadro); el solucionador la mantiene sin coste visible.
- `CLAUDE.md` contiene algunas notas antiguas de distancias de cámara y del aventurero en secciones de formato; las reglas vigentes son las de este documento y las secciones nuevas de `CLAUDE.md`.

## 14. Pendiente y siguiente paso exacto
1. **Esperar la valoración del usuario de la v2.**
2. Si la aprueba: `git tag -a v2 -m "Vídeo 01 v2: narrador pasamontañas, cámara dinámica, físicas, textos letra a letra, sonido corregido" face026` (o el commit que indique) + push del tag; anotarlo en §12. (La rama ya está fusionada en `main`: el commit `face026` forma parte de `main`.)
3. Si pide cambios: aplicarlos sin romper lo existente, `python tools/check_physics.py scripts/01-perro-lame.json` (0), y `python make_video.py scripts/01-perro-lame.json --contact --out videos/01-perro-lame-v3.mp4`.
4. Mejoras propuestas (no hacer sin permiso): las de §13.
5. Siguiente vídeo cuando el usuario dé el tema: guion `scripts/02-…json` → `--dry` → enseñar guion + storyboard + coste → esperar OK → `--tts` → revisar → render → QA.

## 15. Decisiones que debe tomar el usuario
- ¿Aprueba la **v2**? (→ tag `v2`). ¿Quiere también un tag para la v1 minimalista (commit `6e4e9aa`)?
- ¿Aplicar las mejoras de §13 (pata del perro, encuadre del gancho, efectos en planos silenciosos, velocidad)?
- Narrador: ¿número del jersey («00» u otro / ninguno)?, ¿ropa alternativa (`outfit`) para algún vídeo?
- ¿Ambiente sonoro (viento/pájaros) en algún vídeo? (ahora desactivado por regla).
- Si los vídeos crecen: ¿Git LFS o guardarlos fuera del repo?
- Tema del **vídeo 02**.

## 16. Índice de sesiones
- [2026-11-26-01](sessions/2026-11-26-01.md) — creación del pipeline, vídeo 01 (v1 detallada, v1 minimalista, v2), narrador fijo, sistema de sesiones.
