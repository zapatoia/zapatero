# ESTILO PREMIUM — carpeta del estilo (léela entera antes de hacer un vídeo premium)

Cuando el usuario diga **«estilo premium»**, el vídeo se hace con esta carpeta. Es un estilo VIVO: cada vídeo añade piezas y reglas.
No dependas solo de lo que hay: si el tema pide algo nuevo (un icono, una escena, un movimiento), créalo aquí siguiendo las mismas reglas
de estética y apúntalo en el catálogo de abajo. Nunca rompas lo existente (opciones nuevas, no cambios de comportamiento).

## Qué es (estética obligatoria)
Mundo 3D continuo, oscuro y dorado: tarjetas y placas de **cristal** flotando en el espacio, **cámara que vuela** entre ellas con desenfoque
de movimiento, **profundidad de campo**, **reflejo** en un suelo con rejilla dorada, **partículas** bokeh, **halo** dorado, **barrido de luz**,
**rótulo-karaoke** arriba (palabra actual blanca con brillo, las dichas en gris), **viñeta + aberración cromática + grano**.
Paleta: fondo `#06080D` → `#151B2C`; oro `#E8B04A` / `#FFD98A`; texto blanco y gris `#7D8597`. Colores propios solo dentro de los iconos.
9:16 1080×1920 a 60 fps; zonas seguras de TikTok (nada importante a la derecha de x=950 ni abajo de y=1536).

## Archivos
```
motor.py            guion.json → vídeo (escenas, cámara, rótulo, SFX, render, audio, QA)
escena3d.py         núcleo 3D: Camara (lookAt + roll), Plano (imagen en el mundo), profundidad de campo, suelo, partículas, posproceso
piezas/iconos.py    ICONOS vectoriales con volumen y animación
piezas/tarjetas.py  texturas: tarjeta (cifra), placa_titulo, placa_contador (fichas)
piezas/camaras.py   CAMARAS: movimientos dentro de cada escena
prueba.py, prueba2.py   pruebas mudas históricas (referencia visual)
```

## Uso (flujo de un vídeo premium)
```
PY=~/.venvs/documental-animado/bin/python; P=.claude/skills/documental-animado/motor/variantes
$PY $P/premium/motor.py documentales/NN-tema escenas          # escenas y segundos
$PY $P/premium/motor.py documentales/NN-tema prueba 0.5 3 6   # cuadros sueltos (sin voz: tiempos inventados)
$PY $P/vertical/voz_eleven.py documentales/NN-tema            # voz (una toma; pedir OK de créditos al usuario)
$PY $P/premium/motor.py documentales/NN-tema render --procesos 4
$PY $P/vertical/outro.py documentales/NN-tema                 # outro de compartir (obligatoria) → final/NN-tema-v2.mp4
```
`guion.json`: como los documentales (`lineas[]` con `texto`, `tts`, y `escena` en la línea que abre escena) + `"estilo": "premium"` + `outro`.

## CATÁLOGO (ampliar con cada vídeo)
### Escenas (`escena.tipo`)
| tipo | qué hace | campos |
|---|---|---|
| `titulo` | placa de cristal con icono y texto grande con relieve dorado | `texto`, `icono`, `sub`, `vel_reloj` |
| `tarjeta` | tarjeta con icono, cifra que rueda al decirla, unidad | `titulo`, `icono`, `valor`, `dec`, `prefijo`, `sufijo`, `unidad`, `word`, `extra: "ecg"` |
| `comparar` | 2–3 tarjetas en fila, la cámara las recorre | `tarjetas: [ {…tarjeta…} ]`, `sep` |
| `contador` | cifra enorme en fichas que ruedan + enjambre de iconos 3D | `titulo`, `valor`, `unidad`, `word`, `icono`, `enjambre`, `dur` |
| `apilado` | las tarjetas anteriores se tumban y apilan en capas con etiquetas de línea guía | `max`, `sep_capas` |
Todas aceptan `cam` (ver cámaras) y `dist` (distancia de cámara).

### Cámaras (`escena.cam`) — dentro de cada escena
`entrada` (desde muy lejos, empuje que frena: gancho) · `acercar` (empuje lento con giro) · `orbita` (gira −28°→+22°) ·
`lateral` (travelling para comparar) · `grua` (sube y revela) · `picado` (desde arriba bajando).
Por defecto: titulo→entrada, tarjeta→acercar/orbita alternas, comparar→lateral, contador→acercar, apilado→grua.

### Transiciones
Entre escenas, la cámara **vuela** de una estación a la siguiente (0,6 s, curva exponencial, arco hacia arriba, giro) con **desenfoque de
movimiento real** (4 subcuadros). Las estaciones están separadas en diagonal (`PASO` en motor.py): la siguiente se ve al fondo, desenfocada.

### Textos
Rótulo-karaoke arriba (y≈300): trozos equilibrados de ≤ 4 palabras; cada palabra entra al decirla (resorte + desenfoque); la actual en
blanco con brillo dorado, las dichas en gris. Etiquetas con línea guía y punto dorado (apilado). Cifras con desenfoque vertical al rodar.

### Iconos (`piezas/iconos.py`)
`corazon` (late a `lpm`) · `pulmones` (respiran) · `ojo` (parpadea) · `gota` (se llena con el contador) · `reloj` (aguja que barre) ·
`globulo` (glóbulo rojo) · `aire` (corrientes que fluyen).

### Efectos de sonido (automáticos)
whoosh en cada vuelo de cámara · golpe al aparecer el título · pop + tics al rodar cada cifra · destello al apilar.

## Reglas aprendidas (historial de correcciones del usuario; obligatorias)
- (27 nov 2026) El usuario quiere este estilo «casi 3D», con muy buenos movimientos de cámara y efectos; lo plano «tipo diapositiva» no vale.
- (27 nov 2026) Outro de compartir en todos los vídeos.
- (27 nov 2026, opinión del usuario sobre el vídeo 07 — descartado, «olvida este vídeo»):
  - Había **desenfoques innecesarios**: la profundidad de campo y el desenfoque de movimiento solo donde aporten (vuelos rápidos, fondo lejano);
    el protagonista y los textos SIEMPRE nítidos. Revisar cuadro a cuadro que nada importante salga borroso.
  - Había **cortes de audio**: no recortar ni empalmar la voz de forma que se note (los `silencio` insertados y los recortes deben sonar
    naturales; escuchar/medir cada empalme). Revisar también que los SFX no corten ni se pisen.
  - **Cifras que ruedan → sonido de rodillo** («tictictic») continuo durante todo el rodaje, que acelera/frena con la cifra y para al fijarse.
  - **Las tarjetas de cristal 3D (y el apilado en capas) son UN recurso más, no el vídeo entero.** Úsalas cuando haya que explicar algo
    en bloques; el resto del vídeo debe variar: escenas distintas según el tema (objetos/ilustraciones en 3D, mapas, líneas de tiempo,
    escenarios, comparativas visuales, tipografía grande en el espacio, etc.). Ser flexible y crear recursos nuevos para cada tema.
  - En general, «un largo etcétera de cosas mal»: antes de entregar, revisión mucho más estricta (cuadro a cuadro en transiciones,
    audio escuchado en los empalmes) y pedir al usuario sus correcciones concretas para añadirlas aquí.
- Ritmo sin prisas, explicaciones sencillas, voz fija del usuario, datos verificados con fuente (reglas generales de SKILL.md §7).

## Reglas técnicas (rendimiento; aprendidas en el vídeo 07)
- Dentro de un dibujo escalado (iconos con `c.scale(s)`), el desenfoque de una capa se multiplica por la escala: usa `capa_px()` de
  `piezas/iconos.py` (convierte píxeles de pantalla a unidades locales). Un blur sin convertir llegó a 4.000 px y hacía cada cuadro 10× más lento.
- Nunca `saveLayer(None, …)` con desenfoque sobre la pantalla entera por cada elemento: acota la capa a su caja.
- Texturas por piezas cacheadas (`tarjetas._cache`): fondo fijo + icono a 20 fps + cifra por texto. Iconos repetidos (enjambres): sprite único.
- El grano de película hace que a crf 16 un vídeo de 35 s pese ~195 MB (GitHub no admite > 100 MB): `motor.py render` lo recomprime solo a crf 23 (~18 MB). La outro se pega después sobre ese archivo.
- Objetivo: ≤ 0,4 s por cuadro (×4 en los vuelos con desenfoque de movimiento). Mídelo con unos cuadros antes del render completo.

## Límites conocidos
Sin objetos fotorrealistas (todo vectorial con volumen). Sin modelos 3D complejos. Render ≈ 1,5–2× más lento que el documental normal.

## Historial de vídeos premium
- `documentales/_pruebas/premium/prueba-premium.mp4` (prueba 1, plana) · `prueba-premium-2.mp4` (prueba 2, «Tu cuerpo en un minuto», 8 s).
- `documentales/07-cuerpo-un-minuto` — primer vídeo completo con el motor (33 s + outro; render 4,4 min con 4 procesos). Descartado por el usuario (ver reglas aprendidas); sirve solo como referencia de lo que NO debe repetirse.
