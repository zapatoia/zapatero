---
name: ideas
description: Genera muchísimas ideas de vídeo a partir de señales virales (competidores de Instagram en Metricool —la fuente principal—, estadísticas propias de Metricool, tendencias y efemérides de la web) y las filtra a fondo hasta quedarse con las N mejores, cada una con gancho y concepto listos para producir. Usar cuando el usuario pida «haz N vídeos (y distribúyelos)» SIN dar títulos, «/ideas N», «dame ideas», «busca ideas virales».
---

# /ideas N — de cero a N conceptos ganadores (pedido del usuario, 28 nov 2026)

**Uso habitual:** el usuario escribe «haz 6 vídeos y distribúyelos». Entonces:
`/ideas 6` (este skill, sin preguntar nada) → `/lote 6` con los 6 títulos/ganchos elegidos (`.claude/skills/lote/SKILL.md`, tal cual) →
`/distribuir` (`.claude/skills/distribuir/SKILL.md`, sin pedir OK a los textos) → informe final. **No se pregunta nada en ningún paso.**
Si solo pide ideas («dame ideas», «/ideas 10»), se entrega la lista de elegidas + reserva y se para.

Archivos:
- `ideas/banco.json` — hechas (no repetir), reserva (ideas buenas sin usar), descartadas, **rendimiento** real por vídeo, **vetos**, historial de rondas.
- `ideas/rondas/AAAA-MM-DD-HHMM.md` — la ronda completa: señales, las ~80 ideas, filtro, puntuaciones, top 15 investigado, elegidas y por qué.
- `ideas/fuentes/` — instantáneas con fecha de cada ronda: `competidores-AAAA-MM-DD.md` (top de competidores) y `canal-AAAA-MM-DD.md` (tus vídeos).

## Fase 0 · Contexto SIEMPRE ACTUALIZADO (pedido del usuario: nada de datos estáticos)
Cada ronda reconstruye el estado; lo guardado en `banco.json` es solo el historial, nunca se da por actual:
- **Vídeos hechos**: volver a listar `documentales/[0-9]*/guion.json` (título) y añadir a `banco.json → hechas` los que falten (nº, título,
  categoría, fórmula, ruta). Así cuentan también los vídeos hechos fuera del flujo de ideas.
- **Publicados**: leer `publicaciones/calendario.json → publicaciones` y casar cada vídeo con sus fechas por red.
- Leer `ideas/banco.json` (reserva, descartadas, vetos) y `documental-animado/SKILL.md` §7 (tono: pocas cifras, conceptos animados, gancho
  con acción, nada político salvo petición, explicaciones para un niño de 12 años).
- Fecha de publicación prevista (siguientes huecos en `calendario.json`): efemérides y temporada de ESA semana.

## Fase 1 · Señales (se piden de nuevo en cada ronda)
1. **Competidores de Instagram (Metricool) — LA FUENTE PRINCIPAL (decisión del usuario).** Últimos 30 días, por tramos de 3–4 días porque
   el volumen es grande (~800 Reels/mes; una sola llamada de 30 días pasa de 100.000 tokens y la rechaza):
   - pasada A, ligera, para todo el mes: `IGCR01` cuenta, `IGCR05` fecha, `IGCR09` interacciones (tramos de 7 días);
   - calcular la **mediana de interacciones de cada cuenta** y el **«veces su media»** de cada Reel (interacciones ÷ mediana de su cuenta);
   - pasada B, con texto, solo en los tramos donde caen los ~30 Reels con más «veces su media» y más interacciones absolutas:
     `IGCR01, IGCR09, IGCR03` (y `IGCR04` url si hace falta), tramos de 2–3 días.
   - Descartar los Reels promocionales («comenta X», «link en mi perfil», venta de cursos o herramientas) y los de temas que chocan con los vetos.
   - De cada Reel ganador sacar: TEMA, ÁNGULO y FÓRMULA DEL GANCHO (nunca el guion). Agrupar por patrones («¿haces X? lo haces mal», mito
     corregido, cuerpo/sueño cotidiano, reto de números…) y ver qué patrón tiene más «veces su media».
   - Guardar el top 30 en `ideas/fuentes/competidores-AAAA-MM-DD.md` (tabla cuenta · fecha · interacciones · veces su media · tema · patrón).
   - Si un tema ganador ya es un vídeo nuestro (p. ej. la barba del 17 hizo 48 k en un competidor), es una confirmación: subir el peso de esa
     categoría y fórmula, no repetir el tema.
   - Competidores de YouTube (`YTCV03,YTCV04,YTCV06,YTCV07`): solo si el usuario los añade en Metricool; hoy no hay.
2. **Tu canal (Metricool, últimos 90 días, SIEMPRE de nuevo):**
   - TikTok: `TKPO02` fecha, `TKPO05` texto, `TKPO07` vistas, `TKPO08` likes, `TKPO10` compartidos, `TKPO13` % vídeo completo, `TKPO15` tiempo medio.
   - Instagram Reels: `IGRE02`, `IGRE03`, `IGRE23` vistas, `IGRE12` guardados, `IGRE21` compartidos, `IGRE27` retención, `IGRE30` % que salta en 3 s.
   - YouTube: `YTVP02`, `YTVP17` título, `YTVP06` vistas, `YTVP08` duración media vista, `YTVP12` compartidos.
   Casar cada post con su vídeo (texto/título y fecha; los del flujo nuevo, por `calendario.json`) y **sobrescribir** `banco.json → rendimiento`
   con los valores de hoy (`_actualizado` = fecha). Guardar la tabla en `ideas/fuentes/canal-AAAA-MM-DD.md`. Medias por categoría y fórmula:
   vistas, (compartidos+guardados)/1.000 vistas, retención, salto en 3 s. Pesa cada vez más a medida que hay vídeos con ≥ 72 h publicados;
   un gancho con salto en 3 s alto = fórmula de gancho a evitar.
3. **Web (WebSearch, 3–5 búsquedas en paralelo, modo standard):** efemérides y temporada de la semana de publicación, preguntas «por qué» muy
   buscadas, noticias curiosas recientes de ciencia/espacio/naturaleza (no tragedias).

## Fase 1b · Aprender de TUS resultados (`ideas/aprendizaje.json`)
- Con la tabla del canal de la Fase 1, para cada vídeo con ≥ 72 h publicado: puntuación de éxito = media normalizada (frente a la mediana de tus
  vídeos) de vistas, (compartidos+guardados)/1.000 vistas, retención IG (`IGRE27`), % vídeo completo TikTok (`TKPO13`) y, en negativo, salto en 3 s
  (`IGRE30`). Agrupar por categoría, fórmula, tipo de gancho (pregunta / afirmación / acción / reto) y duración (45–60 / 60–75 / 75–90 s).
- Con ≥ 3 vídeos en un grupo: multiplicador = clamp(éxito medio del grupo, 0,6, 1,5); con menos, 1,0. Guardar en `aprendizaje.json` con fecha.
- **Los lunes** (o si han pasado ≥ 7 días desde `historial_semanal[-1]`): análisis a fondo de la semana → 3–5 conclusiones concretas («los ganchos
  de acción retienen un 20 % más», «lo de cuerpo funciona, lo de mapas no») en `conclusiones` e `historial_semanal`, y un párrafo en el informe.
- En la Fase 4, el criterio «Encaje con tu canal» = nota base × multiplicador de su categoría × el de su fórmula (máx. 5).

## Fase 1c · Fichas de éxito → biblioteca (`ideas/biblioteca_exito.json`) (pedido del usuario, 28-nov)
Para los **10 Reels de competidores con más «veces su media»** (sin promocionales), una ficha cada uno:
`cuenta · fecha · interacciones · veces su media · tema · gancho literal (1.ª frase del texto) · por qué engancha · estructura deducida
(p. ej. situación frustrante → misterio → culpable inesperado → consejo) · formato deducido (duración aprox., explicación / reto / lista / historia)
· motivo del éxito (universal, sorpresa, utilidad, emoción, compartible con destinatario…) · patrón reutilizable (frase general, p. ej.
«situación cotidiana frustrante con culpable inesperado») · qué es dato y qué es deducido` (Metricool solo da texto e interacciones: el vídeo no se ve).
- Añadirlas a `biblioteca_exito.json → fichas` (acumulativo, sin duplicar el mismo Reel) y recalcular `patrones`: cada patrón reutilizable con
  cuántas fichas lo respaldan y su «veces su media» medio. La biblioteca crece ronda a ronda: es la memoria de **por qué** funciona en tu nicho.

## Fase 2 · Generar MUCHAS ideas (≥ 80)
Mezclar señales con fórmulas probadas. **Cada idea nace como MINI CONCEPTO** (no solo título): `gancho · situación · estructura (3–5 pasos)
· giro final · patrón de éxito de la biblioteca en el que se apoya · categoría · señal`. Inspirarse en los **patrones** (el porqué), no en el tema
del Reel: de «situación cotidiana frustrante con culpable inesperado» pueden salir ideas nuevas propias (la cola del súper más lenta…).
Fórmulas: «¿Qué pasaría si…?» · «¿Por qué…?» (cuerpo, cosas cotidianas) · mito → «No funciona» · cifra/afirmación que choca («Si tienes 20 años…»)
· historia oculta de un objeto cotidiano · escala imposible (comparar tamaños/tiempos) · reto/juego de 30 s · «tu cuerpo hace esto sin que lo sepas»
· «esto lo haces mal» · origen de una palabra/costumbre · lo que pasa segundo a segundo / hora a hora · «la verdad sobre…».
**Series (pedido del usuario, 28-nov):** proponer también 3–5 ideas de SERIE (un tema que da para 2–3 partes con gancho propio cada una,
p. ej. «Tu cuerpo mientras duermes · parte 1/3: los primeros 10 minutos»). Reglas: como mucho UNA serie activa (`banco.json → series`);
si se elige, la parte 1 entra en este lote y las siguientes quedan reservadas como prioridad de las próximas rondas (una por ronda, para que
salgan en días seguidos); cada parte acaba con «parte 2 mañana» y su título lleva «(1/3)»; cada parte se entiende sola.
Al menos: 35 de competidores de Instagram (temas y patrones ganadores, adaptados a nuestro estilo y a España), 10 de la web,
15 inspiradas en lo que mejor ha funcionado en el canal, 20 propias.

## Fase 3 · Filtro duro (fuera sin puntuar)
Fuera si: choca con un **veto** de `banco.json`; repite tema o ángulo de una **hecha** (o de otra idea de la misma ronda); no se puede
verificar con fuentes fiables; necesita fotos/vídeo reales, logos o personas reales para entenderse; es demasiado nicho (no le importa a
alguien de 15 a 45 años en España); no da para 60–90 s; el gancho no se puede decir en ≤ 8 palabras. Apuntar cada descarte con su motivo.

## Fase 4 · Puntuación (1–5 por criterio, con peso)
| Criterio | Peso |
|---|---|
| Gancho en 3 s (¿te para el dedo? ¿hay acción o pregunta que te toca a ti?) | ×3 |
| **Concepto completo**: la estructura mantiene hasta el final y el giro sorprende (se puntúa el concepto entero, no el título) | **×2** |
| **Patrón de éxito**: se apoya en un patrón de la biblioteca con buen «veces su media» | **×2** |
| Hueco de curiosidad (necesitas saber la respuesta) | ×2 |
| Universal (le pasa / le importa a casi todo el mundo) | ×2 |
| **Señal de competidores de Instagram** (tema o patrón con muchas «veces su media») | **×3** |
| Otra señal externa (web, efeméride, tendencia de la semana) | ×1 |
| Encaje con lo que funciona en TU canal (categoría/fórmula con buen rendimiento) | ×2 |
| Animable literal con el kit (objetos y conceptos que se dibujan; protagonista, mano, ojo, mapas…) | ×2 |
| Giro o remate final (cierre que vuelve al gancho) | ×1 |
| Datos sólidos y fáciles (2–3 cifras con fuente) | ×1 |
| Compartible («pásaselo a…» tiene destinatario claro) | ×1 |
Máximo 110. Se puntúa el **concepto entero**: un gancho bueno con desarrollo flojo pierde puntos. Ordenar y quedarse con el **top 15**.

## Fase 5 · Investigación del top 15
Por cada una: 1–2 WebSearch para confirmar que el dato central es cierto y tiene fuente (si no, fuera); 3 ganchos alternativos (pregunta,
afirmación, acción) y elegir el mejor; esqueleto en 5 tiempos (gancho → contexto → 2–3 «razones»/pasos → giro → cierre que vuelve al gancho);
escena de gancho con acción concreta («la mano estampa…», «el mundo se da la vuelta…»); destinatario del «Pásaselo a…»; riesgos; **duración propuesta** (45–60 / 60–75 / 75–90 s según lo que dé la idea, sin rellenar).
Repuntuar con lo aprendido.

## Fase 6 · Elegir N con variedad
Las N de más puntuación, con estas condiciones: nunca dos de la misma categoría seguidas; máximo 2 de la misma fórmula por lote; al menos la
mitad respaldadas por competidores de Instagram y 1 por lo que mejor funciona en el canal; alternar ligeras («por qué te pasa…») y de «guau» (escala, qué pasaría si).
Orden del lote = orden de publicación: la más fuerte primero.
Guardar: `ideas/rondas/…md` completo; en `banco.json` → `rondas` (fecha, N, elegidas), `reserva` (las del top 15 no elegidas, con su ficha y
puntuación: se reaprovechan en la siguiente ronda tras recomprobar), `descartadas` (resumen). Commit + push.

## Fase 7 · Pasar al lote
La ficha de cada elegida incluye el patrón de éxito y la ficha de competidor en la que se apoya, para que el guion use esa estructura.
Para cada elegida, el título/gancho que recibe `/lote` incluye la ficha: `TÍTULO — gancho: «…»; escena de gancho: …; esqueleto: …; datos y
fuentes: …; cierre: …; outro: «Pásaselo a…»`. El lote decide el resto con su pipeline completo. Al terminar cada vídeo, mover la idea de
«elegida» a `hechas` (con nº, ruta y, tras distribuir, fechas de publicación).

## Informe (al final del lote, no antes)
Tabla de las N elegidas (puntuación, señal que la respalda —Reel de competidor y sus «veces su media»—, por qué), 5 mejores de la reserva,
resumen de tu canal (qué vídeo va mejor y peor) y qué faltó.

## Reglas
- Nunca copiar un vídeo ajeno: de lo viral se toma el TEMA y el ÁNGULO; guion, datos, dibujo y sonido son propios (§7 del kit).
- Nada de scraping de TikTok/Instagram: solo datos de Metricool y búsqueda web. (La API de YouTube se descartó: el usuario lo cubre con competidores.)
- No preguntar nada al usuario durante la ronda: decide tú con la rúbrica.
