---
name: documental-animado
description: Hace videos HORIZONTALES de YouTube (1920×1080) 100 % animados por código en el formato «Documental animado» — mapas con vuelo de cámara, fechas que ruedan, cifras con odómetro, barras, listas, flujos y fotos 2.5D — con la voz del usuario (ElevenLabs) sincronizada palabra por palabra y tipografía cinética. Usar cuando el usuario pida «documental animado», «video de historia/geografía con mapas», «video horizontal animado con mapas y cifras», «estilo documental».
---

# Documental animado · video horizontal animado por código

Haces el video COMPLETO y lo entregas: guion → voz → animación → render → QA → video final abierto. No entregues planes ni partes.
Un video a la vez, con el tema y la voz del usuario. Nada de producción masiva ni de automatizar canales: el usuario crea su propio contenido.

Este formato se construyó con correcciones reales sobre videos terminados. **Cada regla de abajo es obligatoria**: existe porque algo salió
mal antes. Si el usuario te corrige algo nuevo, agrégalo a la sección 7 en el mismo turno.

**Regla de oro: una vez que empiezas, no le preguntas nada al usuario** ni le pides que confirme o elija: tú decides todo
(variante, guion, escenas, música, reintentos, gasto de voz) y sigues hasta entregar el video. La única pregunta es la de la voz (§ 0), una sola vez.

## Mapa de la skill
```
SKILL.md · INSTALAR.md · requirements.txt · perfil.ejemplo.json · env.ejemplo
motor/nucleo/                    voz (ElevenLabs + Whisper), mezcla, master, QA, fuentes libres (no lo cambies salvo para arreglar un error)
motor/herramientas/              ElevenLabs, verificación con Whisper, master de audio
motor/variantes/documental/      el motor: motor.py (línea de comandos) + motor.html y lib/*.js (el dibujo) + vendor/ (mapa del mundo, d3)
motor/variantes/documental/ESCENAS.md   todos los tipos de escena con sus campos
motor/marca/                     aquí van los PNG oficiales de logos y el logo propio del usuario, si los da (el kit no trae ninguno)
ejemplos/canal-de-panama/        guion.json de ejemplo (fecha → mapa → cifra → flujo), con fuentes
```
Llama `<SKILL>` a la carpeta de este archivo, `PY` al Python del entorno (ver INSTALAR.md: Mac `~/.venvs/documental-animado/bin/python` o donde el
usuario prefiera, anotado en perfil.json → `python`; Windows `"$HOME/.venvs/documental-animado/Scripts/python.exe"`, porque Claude Code usa Git Bash) y `<motor>` a
`<SKILL>/motor/variantes/documental/motor.py`. Si copias el motor fuera de la skill y no la instalaste en `~/.claude/skills/documental-animado`, define `KIT_MOTOR=<SKILL>/motor`.

## 0 · Primera vez (una sola vez por computadora)
> **Servidor Linux de Claude Code en la nube (repo zapatero):** el contenedor se borra entre sesiones. Si falta `~/.venvs/documental-animado`, corre `bash .claude/skills/documental-animado/instalar/instalar_linux.sh` (2–3 min). La clave de ElevenLabs ya está en la variable de entorno `ELEVENLABS_API_KEY`. Huggingface está bloqueado: el modelo de Whisper no se puede bajar; para las marcas por palabra usar los timestamps/forced-alignment de ElevenLabs.

1. **Instala** con un solo comando (córrelo en segundo plano: la primera vez tarda 10–30 min; se puede repetir y sigue donde se quedó):
   Mac `bash "<SKILL>/instalar/instalar.sh"` · Windows `powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL>\instalar\instalar.ps1"`.
   Instala Python 3.12 y las librerías (con uv: sin contraseña ni administrador), el navegador sin ventana de Playwright, el modelo de Whisper, deja `perfil.json`
   con valores por defecto y hace una prueba sin voz. Al final dice «LISTO», la ruta de `PY` y la de la prueba: mírala.
   Si falla, lee el error y el registro que indica, arréglalo tú y vuelve a correrlo. `INSTALAR.md` explica lo mismo a mano, solo por si hace falta.
   **Nunca le pidas al usuario que instale, copie, edite archivos o escriba comandos: todo lo haces tú.**
2. **Perfil:** no preguntes nada. `perfil.json` ya queda con valores por defecto (sin firma, sin avatar, sin música, es-MX).
   Si el usuario te da su @, su foto o su música, guárdalos ahí.
3. **Voz — la única pregunta, una sola vez** (si `PY "<SKILL>/instalar/voz_ia.py" --estado` ya dice qué eligió, no preguntes):
   «¿Quieres que tus videos lleven voz con IA de ElevenLabs?»
   - **Sí:** pídele su API key (elevenlabs.io → Developers → API Keys → crear) y, cuando la pegue, `PY "<SKILL>/instalar/voz_ia.py" --clave <la clave>`.
     La valida, la guarda solo en su computadora (en todas sus skills de video), elige su voz (la suya clonada si tiene; si no, una de
     ElevenLabs) y dice su saldo. **Nunca repitas la clave ni la copies a otro lado.** Otra voz: `--voz "<nombre>"` (`--voces` las lista).
   - **No:** `PY "<SKILL>/instalar/voz_ia.py" --sin-ia`. Cada video lleva **su voz grabada**: con el guion listo, dáselo para que lo lea de
     corrido en una nota de voz del celular y pídele el archivo; luego `PY "<SKILL>/instalar/voz_propia.py" <proyecto> <archivo>`
     deja `voz.wav` y `palabras.json` (no gasta). Si dijo algo distinto, cambia el `texto` de esa línea a lo que dijo y vuelve a correrlo.

No vuelvas a preguntar lo que ya está en `perfil.json`.

## 1 · Flujo por cada video (en orden, sin saltarte nada)
1. **Proyecto:** crea una carpeta para el video (p. ej. `videos/<tema-corto>/`) FUERA de la skill y copia ahí `ejemplos/canal-de-panama/` como punto de partida.
2. **Guion** (fórmula en § 3). **Investiga y verifica cada dato, fecha, cifra y lugar** en fuentes reales y guarda las URL en `descripcion.md`
   y en `guion.json → fuentes`. Si un dato no tiene fuente, quítalo. Enséñale el guion en pocas líneas y sigue sin esperar su aprobación (decide tú).
3. **Escenas** (§ 4): en `guion.json`, cada línea es una frase corta (2–6 palabras) y la que abre escena lleva `"escena"`. `PY <motor> <proyecto> escenas`
   lista cada escena con su segundo de entrada.
4. **Prueba visual sin voz (gratis):** sin `palabras.json` el motor inventa tiempos de palabra, así que ya ves la animación:
   `PY <motor> <proyecto> prueba 0.5 2 4 6 …` → `revision/prueba.jpg` (3 por fila). Corrige lo que se vea mal ANTES de pagar la voz.
5. **Voz:** `PY <SKILL>/motor/nucleo/voz.py <proyecto> saldo` → que quepa en su saldo; genera sin pedir permiso y al entregar di cuánto costó.
   **Con su voz grabada** (eligió no usar IA, § 0): en lugar de esto, `PY <SKILL>/instalar/voz_propia.py <proyecto> <archivo>` (no gasta).
   Luego `PY <SKILL>/motor/nucleo/voz.py <proyecto>` (una sola toma corrida, verificación literal, marcas por palabra → `voz.wav`, `palabras.json`).
   Si algo falla, lee POR QUÉ (`audio/corrida/verificacion.json`, `voz-verificacion.json`) antes de pagar otro intento (§ 5).
6. **Revisa con la voz real:** `prueba` en los momentos clave y `secuencia <t> 12` en cada transición (12 cuadros seguidos). Revisa tú cada imagen (§ 6).
7. **Render:** `PY <motor> <proyecto> render` (2 procesos por defecto, cada uno con su navegador; con 8 GB de RAM usa `--procesos 1`; `--fps 30`
   para una versión rápida). Hace mezcla, master a −14 LUFS y ≤ −1 dBTP, hoja de cuadros y QA. El video queda en `<proyecto>/final/<proyecto>.mp4`.
8. **QA:** `qa.json` debe decir `ok: true`. Abre `final/<proyecto>-hoja.jpg` y míralo completo con tus ojos.
9. **Entrega:** abre el video (`open` en Mac, `start` en Windows) y di en pocas líneas qué hiciste, qué revisar y la descripción con fuentes.

Comandos del motor:
```
PY <motor> <proyecto> prueba 0.5 3.2 8.1      → revision/prueba.jpg (cuadros sueltos)
PY <motor> <proyecto> secuencia 7.9 12        → revision/seq-7.9.jpg (12 cuadros seguidos: para revisar movimiento y transiciones)
PY <motor> <proyecto> escenas                 → escenas con su segundo, transición y superficie
PY <motor> <proyecto> render [--procesos 2] [--fps 60]  → final/<proyecto>.mp4 + -hoja.jpg + qa.json
PY <motor> <proyecto> audio | qa              → solo remezcla | solo QA
PY <motor> <proyecto> demo 0 8 [salida.mp4]   → clip mudo de 8 s con loop (para mostrar el estilo)
```

## 2 · El estilo (especificación medida)
**Formato:** 1920×1080 **horizontal**, 60 fps (30 con `--fps 30`), H.264. Voz desde el cuadro 0. Duración típica 45–90 s; una prueba corta
(≤ 20 s) = 35–55 palabras y 4–6 escenas. Termina ≤ 0.4 s después de la última palabra: sin outro, sin fundido a negro.
**Look «editorial»** (por defecto, `guion.json → "tema": "editorial"`): limpio y premium; acento `#2F6BFF` sobre claro y `#5C96FF` sobre oscuro.
Tema `"club"` opcional: negro / carbón / dorado `#E2B34D`.
**Superficies por escena, nunca dos iguales seguidas** (`"surface"` en la escena, o las elige el motor): `light` (blanco → azul suave), `blue`
(azul intenso), `dark` (azul noche con rejilla en perspectiva y partículas), `clay` (terracota/dorado, para lo antiguo o cálido). Las fotos a sangre no cuentan.
**Fuentes** (libres, vienen en el kit): Inter (contexto Semibold, cifras y claves Bold) + Instrument Serif cursiva para claves emotivas (`"*palabra"`).
Vidrio esmerilado en píldoras, rótulos y tarjetas; sombras suaves en dos capas; halos sin quemar; destello que solo toca lo pintado; dither contra bandas.

**Tipografía cinética (la voz manda):** en la franja baja, contexto **46 px** + UNA clave **124 px** (serif cursiva 133) centrados en x=960, base de
la clave en y=958. Los gráficos viven entre y≈100 y 790. Cada palabra entra cuando se dice (opacidad en 4 cuadros + subida con resorte); la clave
con resorte pesado, escala 0.94 → 1 y halo de acento en superficies oscuras. Por línea: `"key": "Panamá"` o `"keys": ["mayas", "*estrellas"]`;
`"cap": false` cuando la escena ya muestra ese texto (date, stat, title). El texto sale 3 cuadros antes del siguiente y antes de la transición: nunca se enciman.

**Curvas y tiempos:** resortes de forma cerrada (snappy/default/heavy) y `easeOutBack` 1.2–1.4 en barras y filas; escalonado 35–120 ms; opacidad
en ≤ 4 cuadros (el movimiento hace la entrada). Cámara: `easeInOutExpo` en vuelos de mapa (zoom en escala logarítmica) y transiciones;
deriva lenta + empuje con resorte en cada frase (nada quieto > 3 s). Contadores: odómetro mecánico con desenfoque vertical según la velocidad.
**Ritmo:** primeros 5 s con un cambio cada ~1.5 s; después cada 1.5–3 s.

**Transiciones (todas con desenfoque de movimiento):** `whip` (barrido) · `card` (la escena nueva sube como tarjeta) · `zoom` (pasa de largo hacia la
cámara) · `mask` (revelado circular con anillo) · `swipe` (panel diagonal, cambio de bloque) · `cut`. Por defecto rotan sin repetirse.
Mapas: desenfoque real por acumulación de subcuadros cuando la cámara vuela rápido.

**Escenas** (campos completos en `ESCENAS.md`): map (vuelo entre encuadres, país que se dibuja y se enciende, `areas`, rutas con cometa, puntos con
pulso, `lights`) · date (regla de años que corre, año que rueda) · timeline · stat (odómetro, anillo) · bars · chart (línea con cometa) · donut ·
photo / image (Ken Burns con paralaje 2.5D, `full` o `card`, `hud`) · people · gallery · quote / title · list (✓/✕ que se trazan) · flow (nodos y
conectores con partículas) · doc (hoja con marcador) · compare · motion (animaciones hechas; dales siempre sus textos).
Cualquier elemento puede pegarse a una palabra: `"word": "cayó"`. Cualquier escena acepta `"counter": {...}` y `"bg": "fotos/x.jpg"`.

**Audio:** voz al frente; whooshes solo en transiciones que caen en huecos de voz (≤ 1 cada 3.5 s; los coloca el motor; `"sfx": false` los apaga);
música opcional muy baja (`guion.json → "musica"`, del usuario y con derechos). Master −14 LUFS / ≤ −1 dBTP (lo hace el núcleo).

## 3 · Guion (fórmula)
45–90 s (o lo que pida el usuario). Narrador de documental: frases cortas, concretas, con fecha, lugar o cifra en cada una.
1. **Gancho 0–5 s:** la fecha o la cifra que sorprende, con un cambio de escena cada ~1.5 s.
2. **Contexto:** dónde (mapa) y cuándo (date / timeline).
3. **Desarrollo:** un dato por escena (stat, bars, chart, compare, list, flow); cada sustantivo importante aparece cuando se nombra.
4. **Cierre:** el dato que lo resume o la consecuencia; sin pedir suscripción ni outro.
Cada línea de `guion.json` lleva `texto` (lo que se ve y lo que la voz dice, con ortografía real) y `tts` (§ 5). Las líneas juntas forman
UNA toma corrida: el texto de todas las líneas, en orden, es exactamente lo que dice la voz.

## 4 · Cómo se hace un tema nuevo
1. Copia el ejemplo al proyecto y reescribe `guion.json` (aquí todo es datos, no código).
2. Haz la tabla frase → escena → clave. Una escena por concepto; la que abre escena lleva `"escena"`, las siguientes la continúan (y avanzan un `step`).
3. Mapas: `bounds` = [[lon oeste, lat sur], [lon este, lat norte]] del encuadre final y `from` del inicial; `highlight` con el nombre del país en
   inglés de Natural Earth ("Panama", "Mexico", "Spain"); verifica las coordenadas de cada punto.
4. Fotos (opcionales): solo libres o propias, en `<proyecto>/fotos/`, con crédito en `fotos/creditos.json`. El motor avisa si falta una.
5. Alterna superficies y transiciones; revisa con `escenas`, `prueba` y `secuencia` antes de la voz.
6. Si necesitas un tipo de escena que no existe, cópialo de uno parecido en `lib/v2.js` (objeto `SC`) dentro de tu copia del motor; nunca dibujes logos.

## 5 · Voz (ElevenLabs)
- Modelo `eleven_v4`, `language_code: "es"`, stability 0.5, similarity 0.85 (lo fija `motor/nucleo/voz.py`). La voz es la del usuario (`perfil.json → voz_id`).
- **Una sola voz = TOMA CORRIDA:** todo el guion en una sola petición (`voz.py` lo hace por defecto). Nunca pegues líneas sueltas ni uses `next_text`.
- `tts` por línea: base natural y etiquetas solo en momentos clave: `[curious]`, `[warm]`, `[playful]`, `[firm]`, `[short pause]`. **Una emoción por frase.**
  Pausas: o `[short pause]` o puntos suspensivos en todo el guion, **nunca las dos** (`voz.py` corta antes de gastar si las mezclas).
- En `tts` las cifras van en palabras y las marcas como se pronuncian («Yutub», «Clod»…); `texto` conserva la ortografía real.
- **Tope: 2,500 caracteres por video**, reintentos incluidos. Antes de generar, `saldo` (que quepa). No pidas permiso: al entregar, di cuánto costó.
- **Una sola toma por defecto:** `voz.py` genera UNA vez (`--intentos 1`). Solo tras leer por qué falló, `--intentos 2` (decídelo tú; una vez por video). Tope propio del video en `guion.json → "tope_caracteres"` (p. ej. 350 para una prueba).
- El saldo de ElevenLabs tarda unos minutos en actualizarse; el gasto real queda en `audio/eleven_gasto.json`.
- **Antes de pagar un reintento, lee por qué falló.** Lo que no cuesta: `armar`, `verificar`, `recorte_ini` (quita un silencio o un «Eh» real
  antes de la primera palabra) y `toma` (elige una toma ya pagada). Whisper duda con cifras: si la pasada literal coincide y solo fallan
  numerales, la línea PASA.
- **No regeneres una voz que el usuario ya aprobó.** Si cambias el guion después, avisa cuánto cuesta rehacerla.
- **Nunca recortes la voz a mano.** `recortar()` solo acorta pausas > 0.8 s dentro del silencio real; el final conserva toda la cola natural.

## 6 · QA y revisión con tus ojos
El QA del motor (`qa.json`) exige: voz en el cuadro 0 · pausas ≤ 0.8 s · cierre ≤ 0.6 s tras el final COMPLETO de la última palabra ·
ninguna palabra cortada (`palabras_completas`) · pasada literal del `voz.wav` final contra el guion (`literal_final`; lee `aceptadas`) ·
zona segura · −14 LUFS / ≤ −1 dBTP · vetos de texto. Si algo falla: arréglalo, no lo ignores. Si decides aceptar una alerta (p. ej. Whisper
oye mal una palabra que sí está bien dicha), mídela, escríbelo y díselo al usuario.

**Revisión visual obligatoria** (hoja de cuadros completa + `prueba` en cada momento clave). Pregúntate en cada cuadro:
- ¿Lo que se ve representa LITERALMENTE lo que se dice en ese momento? ¿Se entiende sin sonido?
- ¿Hay una sola idea en pantalla? ¿Algo de la escena anterior sigue estorbando?
- ¿Algo se encima (texto sobre texto, objeto sobre subtítulo, píldora sobre el protagonista)?
- ¿El protagonista llena la franja de gráficos (y≈100–790) y está al centro? ¿La tipografía cinética (y≈850–990) se lee y no choca con el gráfico?
- ¿Se ve con volumen y textura, o plano como clip-art?
Corrige y vuelve a revisar hasta que todo pase.

- **Falso positivo:** si mides que una falla no es real (p. ej. un final carrasposo que baja poco a poco), anótalo en `guion.json → "qa_aceptadas": {"palabras_completas": "medido: cola baja a −60 dB antes de la siguiente palabra"}` y dile al usuario cuál aceptaste y por qué. Nunca lo uses para tapar un corte real.

## 7 · Reglas que salieron de correcciones reales (obligatorias)
**Del usuario (27 nov 2026)**
- Voz: SIEMPRE su voz favorita de ElevenLabs, voice_id `851ejYcv2BoNPjrkw93G` (ya en `perfil.json → voz_id`). No cambiarla por cuenta propia.
- Clave: la de su cuenta, en la variable de entorno `ELEVENLABS_API_KEY` de este servidor. No guardarla en archivos ni mostrarla. Es una clave restringida (sin permiso de leer voces, modelos ni saldo): `voz_ia.py` y `voz.py … saldo` dan 401; se ignora y se genera directamente; el coste se estima ≈1 crédito por carácter.

**Vertical 9:16 (TikTok / Reels / Shorts), pedido del usuario 27 nov 2026**
- Si pide «9:16», «vertical» o «formato TikTok», usa `motor/variantes/vertical/motor.py` (skia sobre el núcleo, 1080×1920, 60 fps) con los mismos comandos (`escenas`, `prueba`, `secuencia`, `render`, `qa`). Escenas: `map` (mapa en metros con cámara, anillos de radio, bola de fuego, pines), `radio` (suelo 2.5D con personas a escala), `stat` (cifra con odómetro + objeto), `artico` (globo + año). Ejemplo completo: `documentales/01-bombas-madrid/guion.json` del repo.
- Voz para el vertical: `motor/variantes/vertical/voz_eleven.py <proyecto>` (una toma, marcas de ElevenLabs, pausas reales dejadas en 0,28 s, `tempo` opcional en guion.json). `armar` rehace sin gastar.
- Zonas seguras de TikTok: nada abajo de y=1536 ni a la derecha de x=950; tipografía en y 1268–1460, centro de gráficos x=520.
- Duración 30–45 s: si la toma sale larga, primero recorta pausas (`pausa`) y luego `tempo` ≤ 1,05; nunca regeneres la voz por eso.
- La clave grande va al FINAL de la frase (si va en medio, el contexto chico se lee raro: «Bola de de 180»). Reordena la frase antes de generar la voz.
- Mapas de Madrid sin internet: npm `madrid-atlas` (secciones censales) + `es-atlas` (municipios/provincias), pasados a UTM 30N con pyproj (ver `documentales/01-bombas-madrid/datos/`).

**Correcciones del usuario sobre el vídeo 01 (27 nov 2026)**
- **Ritmo sin prisas:** el 01 se sintió apresurado. Escribe unas 2,1–2,3 palabras por segundo de duración pedida (60 s ≈ 125–135 palabras), deja las pausas naturales (`pausa` ≈ 0,45 s, sin `tempo`) y escenas de 2,5–4 s con su respiro.
- **Efectos de sonido suaves siempre:** whoosh leve en las transiciones y detallitos (pop al aparecer un pin o una etiqueta, tic en los contadores, golpe sordo en los momentos fuertes), bajos (−26 a −32 dB aprox.) y colocados en el hueco justo antes de la palabra, nunca encima.

**Corrección del usuario sobre el vídeo 02 (27 nov 2026)**
- **Explicaciones sencillas, para todos los públicos:** palabras de todos los días, una idea por frase, nada de tecnicismos (o explicados con una comparación cotidiana), datos redondos cuando el exacto no aporta, y que un niño de 12 años lo entienda a la primera.

**Del usuario (27 nov 2026, vídeos de juego)**
- **Outro en TODOS los vídeos:** al final, outro corta de compartir con `motor/variantes/vertical/outro.py <proyecto>` (guion.json → `outro`: texto tipo «Pásaselo a…» relacionado con el vídeo, `tts`, `key`). Se pega sin volver a renderizar el vídeo; la entrega es `final/<proyecto>-v2.mp4`.
- **Juegos verticales:** escenas `bolas` (sigue la pelota: silueta de neón, niveles, `ciclo` de colores, respuesta fija) y `penalti` (pausa cuando el portero se tire: cronómetro, escala de reacción, rondas con `espera`, `amagos`). En los juegos la cámara no se mueve y las esperas son silencios reales: `lineas[].silencio` (s) en guion.json (voz_eleven.py los inserta; el QA de pausas se acepta con esa razón).
- Ganchos de juego: retadores y cortos, sin datos científicos si el usuario no los pide.

**Del usuario (27 nov 2026, documental 08)**
- **Más detalle en los efectos de sonido, sin pasarse:** cada cosa que se mueve suena (rodillo de tics que frenan + «clac» al rodar cifras y años: `"rodillo": true` en stat/fecha; nota por generación en `arbol`; barrido en barras; campana, destello, mensaje). Los tics del rodillo pueden ir bajo la voz (son muy suaves); el resto, en los huecos.
- **Vídeos a partir del guion de un reel:** se toma solo el texto (gancho y partes) y se anima con el kit vertical; nada del estilo de la referencia. Escena `arbol` (`motor/variantes/vertical/escena_arbol.py`) para árboles genealógicos.

**Del usuario (27 nov 2026, tras el documental 09): efectos un poco más altos**
- Volumen de los SFX **+4 dB sobre el nivel anterior** (ya es el valor por defecto en `motor.py` y `outro.py`; `guion.json → "sfx_db"` lo cambia por vídeo). La voz no se toca.
- Para retocar solo el audio de un vídeo ya hecho, sin renderizar la imagen: `motor.py <proy> audio` y luego `outro.py <proy> --solo-audio` (reutiliza la animación de la outro).

**Del usuario (27 nov 2026, documental 09): «con cada generación, mejoremos»**
- Cada vídeo nuevo debe superar al anterior en algo visual y en algo de audio, y decirlo al entregar. Escenas de objetos cotidianos en `escenas_cotidianas.py`: `ojo`, `reloj` (24 h), `bateria`, `digital` (despertador de 7 segmentos, `tachar_word`). Las escenas nuevas van en módulos aparte con su `efectos_<tipo>` y se enganchan solas.
- Nada quieto: cada escena lleva micro-movimiento propio (parpadeo, estrellas que titilan, ola y burbujas, pantalla que se desplaza, chispas).

**Documental 10 (27 nov 2026), mejoras que quedan como regla**
- Cada transición suena según su tipo (`SFX_TRANS`: whip→whoosh, zoom→zum, mask→barrido, card→desliz); `"sfx_trans": false` vuelve al whoosh único.
- En juegos de tiempo, el silencio es de verdad: nada rítmico mientras el jugador cuenta (solo pitido de salida y golpe al parar); `lineas[].cap_dur` quita el subtítulo para que no tape el juego.
- Cronómetros de juego cuentan en tiempo real desde el final de la palabra (`inicio_fin`), para que el reto sea justo.
- Nada de cifras no verificadas aunque salgan en la referencia: se cuenta sin el número.

**Corrección del usuario sobre el documental 10 (cifra que se salía del cronómetro y «30» duplicado en la barra)**
- La hoja de cuadros es demasiado pequeña para ver fallos finos. Antes de entregar, revisa a tamaño real (recorte a 50 %, `ffmpeg -ss T -i final.mp4 -vf crop=…`) un cuadro de CADA tipo de escena en su peor momento: la cifra más larga, la etiqueta más ancha, todos los bocadillos a la vez.
- Ningún texto puede salirse de su contenedor: las cifras se ajustan al ancho útil (`maxw`) midiendo el caso más ancho («88,8»), no el actual.
- Nunca dibujes dos veces la misma etiqueta: si una marca se resalta (el 30 en verde), se quita de la serie normal.

**Del usuario (27 nov 2026, documental 11 «¿Qué te pasa si vuelve a ganar el PSOE?»)**
- **Vídeos de opinión / política con idea del usuario:** el gancho es una pregunta que te toca a ti; la estructura que funciona es «lo que prometieron (cita literal del documento, con página) → lo que pasó (dato de hoy que rueda)» y luego «qué te toca a ti» por perfiles (si alquilas, si trabajas, si tienes hijos…). Cierre neutro y útil («decides tú»), sin pedir el voto.
- **Nombre de un partido o marca:** escribir su nombre con nuestra tipografía sobre su color SÍ se puede (p. ej. «PSOE» en blanco sobre rojo); lo prohibido es redibujar su logo con código.
- **Programas y documentos:** se citan del PDF original (el usuario lo pasa si la red no llega); lo que dice la prensa y no está en el documento se descarta. «Me he leído…» solo si de verdad se ha leído (el PDF de otro año no vale para el de ahora: avisar).
- **Causas judiciales de terceros:** se pueden mencionar con su estado procesal exacto y verificado (condenado / condenado en primera instancia / pendiente de juicio) y, si existe, el dato que equilibra (p. ej. «la Fiscalía pide absolverla»). Nada en instrucción presentado como hecho.
- Escenas en `escenas_politica.py`: `urna`, `programa`, `cita`, `nomina`, `expedientes`, `promesas`; superficie nueva `rojo`.

**Del usuario (27 nov 2026, tras el 11 y para el 12 «¿Y si desaparecieran los mosquitos?»)**
- **El tono habitual NO es el político:** el 11 tenía demasiados datos y era muy serio. Lo normal: pocas cifras (2–3 por vídeo) y que los CONCEPTOS que dice el narrador se animen literalmente (si dice «se los comen», un pez se las come; si dice «cambian de ruta», los renos se dan la vuelta; si dice «desaparecieran», una mano lo estampa).
- **Gancho visual con acción en la palabra clave** (la mano que estampa al mosquito justo en «desaparecieran») y **cierre que vuelve al gancho** con un remate de humor.
- Personaje protagonista ilustrado y GRANDE (≥ 50 % del ancho), reutilizado en todas las escenas; nada pequeño arriba con media franja vacía.
- Al dibujar un golpe: polvo y estrella DETRÁS de la mano, rótulo de cómic («¡PLAF!») ENCIMA y sin pisar otros elementos.
- Anclas: `"él"` se normaliza a `"el"` y casa con el artículo; usa `"palabra#n"` cuando una palabra corta se repite.
- `outro.py` saca el último cuadro con `-sseof -0.3` (el audio puede durar unos ms más que el vídeo).
- Escenas en `escenas_mosquito.py`: `mosquito`, `ranking`, `contagio`, `zumbido`, `estanque`, `tundra`, `orquidea`, `red`, `especies`, `selectivo`.

**Documental 13 (27 nov 2026, «¿Qué pasaría si dejases de dormir a propósito?»): mejoras que quedan como recurso**
- **Hilo conductor visible**: un HUD fijo que avanza escena a escena (aquí «HORAS DESPIERTO») une el vídeo; campo `hud` {desde, hasta, word, dur}.
- **Que el propio vídeo viva el concepto** (microsueño = pantalla en negro con glitch). **PÁRPADOS EN PANTALLA: DESCARTADOS por el usuario** (no le gustan; `capa_hud` ya no los dibuja).
- Gancho con acción física de cómic en la palabra clave (palillos ¡CLAC! en «a propósito») y cierre que lo deshace (se caen y se duerme).
- Escenas en `escenas_sueno.py`: `insomne`, `calendario`, `conducir`, `neuronas`, `limpieza`, `alucina`, `recuerdos`, `dormir`, `capitulo`.

**Corrección del usuario sobre el 13 (v2): «más centrado en el hora a hora»**
- Si el tema es una progresión (horas, días, años, grados…), el NARRADOR dice cada hito en voz («Hora 16…», «Hora 24…») y cada hito es una escena que abre
  como capítulo: el contador sale grande en el centro sobre un velo, rueda hasta el nuevo valor y vuela a su sitio (`hud.capitulo`). Más hitos y más concretos
  (qué pasa exactamente en cada uno), no un resumen.
- Siempre más detalle visual y de sonido que la versión anterior (el 13 v2 pasó de 108 a 156 efectos): cada cosa que aparece o cambia, suena.

**Corrección del usuario sobre el 13 v2: el velo oscuro de la entrada de capítulo**
- El velo/borrón que tapa la escena mientras el contador sale grande NO le gusta: entra y sale de golpe, sin transición de desenfocado a enfocado. Regla general:
  **ningún desenfoque, velo ni oscurecido de fondo si no tiene una transición suave y bien hecha (entrada y salida graduales, con desenfoque real que se va
  enfocando). Si no se puede hacer bien, no se pone.** Para los capítulos: o un desenfoque real animado (blur que baja de N px a 0 con easing), o nada.

**Estilo premium (catalogado a petición del usuario, 27 nov 2026)**
- Si el usuario pide **«estilo premium»**, lee `motor/variantes/premium/LEEME.md` (carpeta del estilo: motor, piezas, catálogo, reglas) y sigue `ESTILO-PREMIUM.md` (2.5D/3D oscuro + dorado, cámara que vuela, cristal, profundidad de campo,
  reflejo, partículas, revelado en capas). Motor: `motor/variantes/premium/escena3d.py`; referencia: `documentales/_pruebas/premium/prueba-premium-2.mp4`.

**Del formato**
1. Sincronía palabra por palabra: el texto de las líneas debe ser IDÉNTICO a lo que dice la voz y en el mismo orden; nunca muevas una palabra
   de lugar después de generar la voz (rompe la sincronía de las escenas siguientes).
2. Una escena cada 1.5–3 s; en los primeros 5 s, cada ~1.5 s. Nada quieto más de 3 s.
3. Nunca dos superficies iguales seguidas ni la misma transición dos veces seguidas.
4. Tipografía cinética debajo de los gráficos (franja y≈850–990): contexto chico + UNA clave; `"cap": false` cuando la escena ya muestra ese texto.
5. Sin outro ni fundido a negro: corta ≤ 0.4 s después de la última palabra.
6. Fotos con licencia y crédito; nada de fotos de marcas ajenas ni de personas privadas. Sin fotos, las escenas de datos y mapas bastan.
7. Mapas y fechas verificados: país, coordenadas y año salen de una fuente con URL.
8. Decimales en la voz: si se puede, dilos sin «punto» («veintisiete metros y medio»). Whisper escribe «27.5» en cifra y la pasada literal
   marca «falta punto» (prueba real); si la toma está bien dicha, mídelo y anótalo en `qa_aceptadas` con la razón, no pagues otra toma.
9. «se abrió», «la hora»: la sinalefa junta dos palabras en un tramo de voz continua y el QA puede marcar «se dura 0.9 s». Mide la voz continua
   (`voz-verificacion.json`): si no hay corte ni vocal estirada, es falso positivo medido (prueba real: 0.48 s en «se‿abrió»).

**Generales**
**Escenas y encuadre**
1. **Una escena por concepto.** Las escenas no se mezclan: deja en pantalla SOLO lo que se está explicando; lo de la escena anterior sale antes de que entre lo nuevo.
2. **El mundo es el del tema.** No metas objetos o lugares que no aporten a la explicación (un decorado bonito que no se explica distrae).
3. **Lo que se ve representa lo que se dice**, al cuadro: cada sustantivo importante aparece cuando se nombra (0–6 cuadros después).
4. **Encuadre:** el protagonista ocupa 60–75 % del ancho de la franja de gráficos; lo importante al centro; nada pegado a los bordes ni abajo de y=1020 (barra de YouTube).
5. **Nada encimado y espacios parejos:** zonas fijas por elemento; titulares y subtítulos sin huecos de palabras que aún no salen.
6. **Entradas suaves** con desenfoque de movimiento; sin rebotes duros ni sacudidas largas.
7. **Formas con forma:** nada distorsionado ni piezas que se meten unas en otras; si un objeto atraviesa a otro, corrígelo.
8. **Logos:** nunca dibujados con código. Si hace falta uno, PNG oficial que dé el usuario; si no, no se pone.
9. **Cero texto escrito dentro del código** que dependa del tema: todo va en `guion.json`.

19. **Nivel del ejemplo, no menos (prueba real: un tema nuevo salió más plano que el original).** Cada objeto protagonista se arma con
    VARIAS piezas (cuerpo, borde, tapa, asa, detalle), cada pieza con degradado de dos tonos, reflejo especular suave, sombra de contacto
    en el piso y una textura sutil del material (grano, poros, vetas). El fondo nunca es liso: degradado + viñeta + bokeh o partículas lentas.
20. Antes de la voz, compara tu `prueba` lado a lado con el mismo momento del ejemplo de la variante (`ejemplos/<variante>`): si el tuyo
    se ve más plano, más chico o más vacío, agrega piezas y textura hasta igualarlo.

**Voz y audio**
10. Toma corrida, emoción con etiquetas, pausas naturales ≤ 0.8 s, sin silencios muertos, sin ecos ni palabras incompletas.
11. Ninguna palabra se corta, ni al inicio ni al final; el video termina ≤ 0.6 s después del final real de la última palabra. Sin outro.
12. Sin música por defecto; SFX mínimos y nunca sobre palabras: colócalos en el hueco ANTES de la palabra ancla o en una pausa, nunca en `F[palabra]`. Nada de ruidos constantes de fondo.

**Contenido**
13. Datos verificados con fuente (URL en `descripcion.md`); sin cifras inventadas.
14. Guion propio del usuario: nunca copies textos, personajes, marcas ni nombres de cuentas de videos de referencia; se toma solo la técnica.
15. Un video a la vez. Nada de producción masiva ni de canales automatizados.

**Proceso**
16. Mira tú cada imagen de prueba antes de seguir; nunca entregues sin revisar la hoja completa.
17. Antes de gastar voz: guion revisado por ti + que quepa en el saldo; al entregar, di cuánto costó (sin pedir permiso antes).
18. Si el usuario corrige algo, aplícalo y agrégalo aquí como regla nueva, para que no se repita.

## 8 · Trampas que lo abaratan
1. Escenas de solo texto (title/quote) seguidas: cada frase debe VERSE (mapa, cifra, objeto), no leerse.
2. Escenas largas sin cambio (> 3 s) o la misma superficie dos veces seguidas → se siente presentación de diapositivas.
3. Claves que no son la palabra importante, o contexto de más de 4 palabras → la tipografía se vuelve subtítulo.
4. Datos redondeados o inventados para que «se vean bien» → pierde credibilidad; usa el dato exacto de la fuente.
5. Música alta o whooshes encima de palabras → tapa la voz.
