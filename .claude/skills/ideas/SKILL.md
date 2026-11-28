---
name: ideas
description: Genera muchísimas ideas de vídeo a partir de señales virales (estadísticas propias y de competidores en Metricool, Shorts en español más vistos de YouTube, tendencias y efemérides de la web) y las filtra a fondo hasta quedarse con las N mejores, cada una con gancho y concepto listos para producir. Usar cuando el usuario pida «haz N vídeos (y distribúyelos)» SIN dar títulos, «/ideas N», «dame ideas», «busca ideas virales».
---

# /ideas N — de cero a N conceptos ganadores (pedido del usuario, 28 nov 2026)

**Uso habitual:** el usuario escribe «haz 6 vídeos y distribúyelos». Entonces:
`/ideas 6` (este skill, sin preguntar nada) → `/lote 6` con los 6 títulos/ganchos elegidos (`.claude/skills/lote/SKILL.md`, tal cual) →
`/distribuir` (`.claude/skills/distribuir/SKILL.md`, sin pedir OK a los textos) → informe final. **No se pregunta nada en ningún paso.**
Si solo pide ideas («dame ideas», «/ideas 10»), se entrega la lista de elegidas + reserva y se para.

Archivos:
- `ideas/banco.json` — hechas (no repetir), reserva (ideas buenas sin usar), descartadas, **rendimiento** real por vídeo, **vetos**, historial de rondas.
- `ideas/rondas/AAAA-MM-DD-HHMM.md` — la ronda completa: señales, las ~80 ideas, filtro, puntuaciones, top 15 investigado, elegidas y por qué.
- `ideas/fuentes/` — datos crudos (p. ej. `yt-AAAA-MM-DD.json` de `tools/ideas/yt_shorts.py`).

## Fase 0 · Contexto (2 min)
- Leer `ideas/banco.json` entero (hechas, reserva, vetos, rendimiento) y `documental-animado/SKILL.md` §7 (tono: pocas cifras, conceptos
  animados, gancho con acción, nada político salvo petición, explicaciones para un niño de 12 años).
- Mirar la fecha de publicación prevista (siguientes huecos en `publicaciones/calendario.json`): efemérides y temporada de ESA semana.

## Fase 1 · Señales (qué está funcionando)
1. **Tu canal (Metricool, `getAnalyticsDataByMetrics`, brandId 8415557, últimos 60 días):**
   - TikTok: `TKPO02` fecha, `TKPO05` texto, `TKPO07` vistas, `TKPO08` likes, `TKPO10` compartidos, `TKPO13` % vídeo completo, `TKPO15` tiempo medio.
   - Instagram Reels: `IGRE02`, `IGRE03`, `IGRE23` vistas, `IGRE12` guardados, `IGRE21` compartidos, `IGRE27` retención, `IGRE30` % que salta en 3 s.
   - YouTube: `YTVP02`, `YTVP17` título, `YTVP06` vistas, `YTVP08` duración media vista, `YTVP12` compartidos.
   Volcar en `banco.json → rendimiento` (por nº de vídeo: casar por texto/título y fecha). Calcular por categoría y por fórmula la media de
   vistas, compartidos+guardados por 1.000 vistas, retención y salto en 3 s. **Esto pesa más que cualquier tendencia externa** en cuanto haya ≥ 6
   vídeos con ≥ 72 h publicados. Un gancho con salto en 3 s alto = fórmula de gancho a evitar.
2. **Competidores (Metricool):** Reels de competidores IG `IGCR01,IGCR03,IGCR04,IGCR05,IGCR07,IGCR08,IGCR09` y vídeos de competidores YouTube
   `YTCV03,YTCV04,YTCV06,YTCV07,YTCV08,YTCV09` (últimos 30 días). Si vienen vacíos, el usuario no ha añadido competidores en Metricool
   (sección Competidores): decirlo UNA vez en el informe, sin bloquear. Ordenar por interacciones/likes y quedarse con los 20 mejores TEMAS.
3. **Shorts de YouTube en español:** `python3 tools/ideas/yt_shorts.py --dias 10 --top 40` (y otra pasada `--region MX` si hace falta más
   volumen). Si sale «falta la clave», seguir sin esta fuente y decirlo en el informe (la clave va como Network secret de youtube.googleapis.com,
   cabecera `X-Goog-Api-Key`, añadida por el usuario en los ajustes del entorno desde claude.ai/code en el navegador).
   Leer los títulos con más **vistas/día**: extraer el TEMA y el ÁNGULO (no el guion).
4. **Web (WebSearch, 4–6 búsquedas en paralelo, modo standard):** tendencias de la semana en TikTok/Reels España de curiosidades y ciencia,
   preguntas muy buscadas («por qué…», «qué pasa si…»), efemérides y temporada de la semana de publicación, noticias curiosas recientes de
   ciencia/espacio/naturaleza (no tragedias), y «datos curiosos» de un tema que esté sonando.

## Fase 2 · Generar MUCHAS ideas (≥ 80)
Mezclar señales con fórmulas probadas. Cada idea en una línea: `título/gancho · fórmula · categoría · señal que la respalda`.
Fórmulas: «¿Qué pasaría si…?» · «¿Por qué…?» (cuerpo, cosas cotidianas) · mito → «No funciona» · cifra/afirmación que choca («Si tienes 20 años…»)
· historia oculta de un objeto cotidiano · escala imposible (comparar tamaños/tiempos) · reto/juego de 30 s · «tu cuerpo hace esto sin que lo sepas»
· «esto lo haces mal» · origen de una palabra/costumbre · lo que pasa segundo a segundo / hora a hora · «la verdad sobre…».
Al menos: 25 de señales externas (competidores/Shorts/web), 15 inspiradas en lo que mejor ha funcionado en el canal, 40 propias.

## Fase 3 · Filtro duro (fuera sin puntuar)
Fuera si: choca con un **veto** de `banco.json`; repite tema o ángulo de una **hecha** (o de otra idea de la misma ronda); no se puede
verificar con fuentes fiables; necesita fotos/vídeo reales, logos o personas reales para entenderse; es demasiado nicho (no le importa a
alguien de 15 a 45 años en España); no da para 60–90 s; el gancho no se puede decir en ≤ 8 palabras. Apuntar cada descarte con su motivo.

## Fase 4 · Puntuación (1–5 por criterio, con peso)
| Criterio | Peso |
|---|---|
| Gancho en 3 s (¿te para el dedo? ¿hay acción o pregunta que te toca a ti?) | ×3 |
| Hueco de curiosidad (necesitas saber la respuesta) | ×2 |
| Universal (le pasa / le importa a casi todo el mundo) | ×2 |
| Señal viral externa (competidores, Shorts con muchas vistas/día, tendencia de la semana) | ×2 |
| Encaje con lo que funciona en TU canal (categoría/fórmula con buen rendimiento) | ×2 |
| Animable literal con el kit (objetos y conceptos que se dibujan; protagonista, mano, ojo, mapas…) | ×2 |
| Giro o remate final (cierre que vuelve al gancho) | ×1 |
| Datos sólidos y fáciles (2–3 cifras con fuente) | ×1 |
| Compartible («pásaselo a…» tiene destinatario claro) | ×1 |
Máximo 80. Ordenar y quedarse con el **top 15**.

## Fase 5 · Investigación del top 15
Por cada una: 1–2 WebSearch para confirmar que el dato central es cierto y tiene fuente (si no, fuera); 3 ganchos alternativos (pregunta,
afirmación, acción) y elegir el mejor; esqueleto en 5 tiempos (gancho → contexto → 2–3 «razones»/pasos → giro → cierre que vuelve al gancho);
escena de gancho con acción concreta («la mano estampa…», «el mundo se da la vuelta…»); destinatario del «Pásaselo a…»; riesgos.
Repuntuar con lo aprendido.

## Fase 6 · Elegir N con variedad
Las N de más puntuación, con estas condiciones: nunca dos de la misma categoría seguidas; máximo 2 de la misma fórmula por lote; al menos 1
de señal externa fuerte y 1 de lo que mejor funciona en el canal; alternar ligeras («por qué te pasa…») y de «guau» (escala, qué pasaría si).
Orden del lote = orden de publicación: la más fuerte primero.
Guardar: `ideas/rondas/…md` completo; en `banco.json` → `rondas` (fecha, N, elegidas), `reserva` (las del top 15 no elegidas, con su ficha y
puntuación: se reaprovechan en la siguiente ronda tras recomprobar), `descartadas` (resumen). Commit + push.

## Fase 7 · Pasar al lote
Para cada elegida, el título/gancho que recibe `/lote` incluye la ficha: `TÍTULO — gancho: «…»; escena de gancho: …; esqueleto: …; datos y
fuentes: …; cierre: …; outro: «Pásaselo a…»`. El lote decide el resto con su pipeline completo. Al terminar cada vídeo, mover la idea de
«elegida» a `hechas` (con nº, ruta y, tras distribuir, fechas de publicación).

## Informe (al final del lote, no antes)
Tabla de las N elegidas (puntuación, señal que la respalda, por qué), 5 mejores de la reserva, qué fuentes funcionaron (Metricool propio /
competidores / Shorts / web) y qué faltó (clave de YouTube, competidores sin añadir…).

## Reglas
- Nunca copiar un vídeo ajeno: de lo viral se toma el TEMA y el ÁNGULO; guion, datos, dibujo y sonido son propios (§7 del kit).
- Nada de scraping de TikTok/Instagram: solo datos oficiales (Metricool, API de YouTube) y búsqueda web.
- No preguntar nada al usuario durante la ronda: decide tú con la rúbrica.
