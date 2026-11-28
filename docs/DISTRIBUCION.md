# DISTRIBUCIÓN — publicación automática de los vídeos (Metricool)

> Creado en la sesión 2026-11-28-03. **Estado (sesión 2026-11-28-04): §5 APLICADO** (`config/redes.json`, `publicaciones/calendario.json`, skill `/distribuir`, líneas en `documental-animado` y `lote`). Primera distribución real: documental 21.
> Nada de esto toca el motor de vídeo, el estilo ni los comandos de producción: es una capa nueva encima.

## 1. Objetivo del usuario
- Flujo ideal: «genera un lote de N vídeos de estas ideas/hooks **y distribúyelos**» → cada vídeo sale con título, textos y hashtags →
  se programan en **Instagram Reels, YouTube Shorts y TikTok** (TikTok: el usuario quiere incluirlo «si se puede»; si da problemas,
  se queda manual) → **2 al día: 10:30 y 18:30, hora de Madrid** → siempre en los **siguientes huecos libres**, sin solapes ni duplicados,
  acumulándose en el tiempo (20 vídeos = 10 días de calendario) → Claude comprueba que han quedado programados y da el calendario + errores.
- Restricciones: todo desde el **iPad** (sin ordenador, sin servidores, sin Docker); nada de pago adicional salvo lo ya decidido.

## 2. Decisión tomada (y por qué)
- **Metricool, plan Starter (de pago, ya contratado por el usuario)**. El plan gratuito solo publica 20 posts/mes (≈5–10 días a nuestro
  ritmo de ~120–180 posts/mes). Alternativa gratuita estudiada y descartada por el usuario: Buffer free (10 programados por canal a la vez →
  solo 5 días por delante, cola a rellenar con una tarea diaria). APIs directas de YouTube/Instagram: descartadas (Google Cloud + app de Meta
  + tokens + cron: demasiado complejo desde iPad; Instagram no programa por API).
- **Puente de los vídeos: el repositorio es PÚBLICO** (`zapatoia/zapatero`, comprobado con la API de búsqueda: `"visibility":"public"`).
  Cada MP4 con commit + push tiene URL directa `https://raw.githubusercontent.com/zapatoia/zapatero/<commit>/documentales/NN-tema/final/NN-tema.mp4`
  → Metricool la descarga (`media` acepta «public URLs to image or video files»). Sin Drive ni Dropbox. Usar el **hash del commit** en la URL
  (no el nombre de la rama: las ramas se borran tras el merge). Límite de GitHub: 100 MB por fichero (los MP4 rondan 20–60 MB).
  Consecuencia aceptable: quien tenga el enlace puede ver el vídeo antes de su hora (ya pasaba: el repo es público).

## 3. Conexión verificada (2026-11-28, solo lectura)
- Conector **«Metricool Social Media Management»** conectado por el usuario en claude.ai/customize/connectors. Tools en la sesión:
  `mcp__Metricool_Social_Media_Management__*` (si una sesión nueva no las ve, buscarlas con ToolSearch «metricool»).
- `getBrandSettings` → **marca `blogId` = `8415557`**, zona horaria **`Europe/Madrid`**, redes: Instagram `telocuentobro`,
  TikTok `telocuentobroo`, YouTube canal `UCw097QIiqRhLlX5ZycZ5RTw`.
- `getScheduledPosts` (28-11-2026 → 28-02-2027): **vacío** (ninguna publicación programada todavía).
- Desde el contenedor NO hay red a metricool.com (DNS bloqueado), pero da igual: el conector lo llama la infraestructura de Claude.

## 3b. Huecos ya ocupados A MANO por el usuario (dato del 2026-11-28; NO salen en `getScheduledPosts`)
El usuario programó vídeos directamente desde las apps de cada red, así que Metricool no los ve. Hay que contarlos como ocupados:
| Red | Cubierto hasta (incluido) | Primer hueco libre |
|---|---|---|
| Instagram | 2-dic-2026 15:30 | **2-dic-2026 20:30** |
| YouTube | 2-dic-2026 15:30 | **2-dic-2026 20:30** |
| TikTok | 2-dic-2026 20:30 | **3-dic-2026 15:30** (el usuario escribió «a las 3 del día 3» = turno de tarde, 15:30) |
- Al crear `publicaciones/calendario.json`, sembrarlo con estos «ocupado_manual» para que nunca se programe antes.
- Cada red lleva su propio cursor de huecos (TikTok va un turno por detrás de IG/YouTube). **Confirmado por el usuario (28-11-04): no hace falta alinearlas**;
  cada red avanza por su cursor en `publicaciones/calendario.json → redes.<red>.siguiente_libre`.
- Antes de distribuir, preguntar siempre si ha programado algo más a mano desde la última vez.

## 4. Qué permite el conector (leído de sus definiciones)
- `getBrandSettings`, `getScheduledPosts(brandId, fromDate, toDate, timezone)` (solo los aún no publicados), `createScheduledPost(blogId, date, info)`,
  `updateScheduledPost(id, uuid, blogId, info)` (sobrescribe todo; cambia el `id`, el `uuid` se mantiene; hay que mandar el contenido completo),
  `createScheduledPostForReview` / `sendScheduledPostForReview` (flujo de aprobación; no lo usamos), `getBestTimeToPostByNetwork`, analítica.
- **NO hay herramienta para BORRAR** publicaciones: borrar = el usuario en la app/web de Metricool (o mover con `update`). Por eso hay que
  hacer las pruebas con cuidado (ver §7).
- `info` (JSON en texto). Campos que usaremos:
  - `providers`: `[{"network":"instagram"}]` / `youtube` / `tiktok`.
  - `publicationDate`: `{"dateTime":"2026-12-01T15:30:00","timezone":"Europe/Madrid"}` (la hora de Madrid con cambio de hora lo resuelve Metricool).
  - `text`: texto del post (una sola por post → **un post por red y vídeo**, así cada red lleva su texto y los errores quedan aislados).
  - `media`: `["https://raw.githubusercontent.com/…/NN.mp4"]`. Portada opcional: `videoCoverMilliseconds` (fotograma) o `videoThumbnailUrl` (jpg/png).
  - `autoPublish: true` (publica solo; `false` = aviso al móvil para publicar a mano). `draft: false`.
  - `instagramData`: `{"type":"REEL","showReelOnFeed":true,"isAiGenerated":<decidir>}`.
  - `youtubeData`: `{"title":"…","type":"short","privacy":"public","madeForKids":false,"category":"EDUCATION","tags":[…],"isAiGeneratedContent":<decidir>}`.
  - `tiktokData`: `{"privacyOption":"PUBLIC_TO_EVERYONE","title":"…","autoAddMusic":false,"isAigc":<decidir>}`.
  - `date` (parámetro aparte, ISO con desfase, p. ej. `2026-12-01T15:30:00+01:00`); no puede estar en el pasado.
  - La respuesta trae `plannerUrl` de cada post (dárselo al usuario).
- TikTok (ayuda de Metricool): autopublicación de 3 s a 10 min; **sin saltos de línea** en el texto; sin efectos/stickers/ubicación/dúos;
  música solo Top 100 en cuentas Business (no la necesitamos: audio propio). Si un post no sale a su hora no se reactiva: duplicar.

## 5. Cambios mínimos propuestos en la pipeline (PENDIENTES DE APLICAR; explicados al usuario)
1. **`config/redes.json`** (nuevo): base fija de hashtags de descubrimiento por red, límites y valores por defecto. Propuesta:
   - TikTok: `#parati #fyp #foryou #foryoupage` + 2–3 temáticos.
   - Instagram: `#parati #fyp` + 3 temáticos (≤5 en total, por prudencia: Instagram limita/penaliza los bloques largos).
   - YouTube: `#shorts` + `#parati` + 1–2 temáticos (en la descripción; YouTube muestra los 3 primeros), y `tags` del vídeo con 5–8 palabras clave.
2. **`documentales/NN-tema/publicacion.json`** (nuevo, uno por vídeo), generado en el mismo paso que `descripcion.md`:
   ```json
   {"video": "final/NN-tema.mp4", "titulo": "…",
    "instagram": {"texto": "gancho + 1–2 frases + pregunta\n\n#… #…"},
    "youtube":   {"titulo": "≤100 car. (ideal ≤60)", "texto": "2–3 frases + #shorts #…", "tags": ["…"], "categoria": "EDUCATION"},
    "tiktok":    {"texto": "una sola línea con #parati #fyp #foryou #foryoupage #…"},
    "hashtags_tema": ["#…"], "portada_ms": 1500}
   ```
   **ESTILO FIJADO POR EL USUARIO (28-11-04, con capturas de sus TikTok; manda sobre lo de abajo):** texto corto = «🤯 TÍTULO EN MAYÚSCULAS + emoji del tema» y
   **5 hashtags como máximo en todas las redes** (Instagram no deja más): `#SabiasQue #curiosidades #parati #fyp` + 1 del tema (en YouTube `#shorts` en lugar de `#fyp`).
   Sin párrafos ni preguntas al público. Ejemplos y plantilla en `config/redes.json → formato_texto`.
   Reglas del título: ligado al contenido, curiosidad sin clickbait falso, estilo de colega del canal, variar la fórmula entre vídeos
   (pregunta / afirmación sorprendente / «qué pasaría si» / cifra), nada de «descubre», «increíble», emojis en cadena. Hashtags temáticos
   elegidos por el contenido de ESE vídeo (historia, ciencia, cuerpo humano, tecnología…), sin rellenos ni repetir el bloque del anterior.
3. **`.claude/skills/documental-animado/SKILL.md`**: una línea en el paso de cierre: «generar `publicacion.json` (ver `docs/DISTRIBUCION.md` §5)».
   **`.claude/skills/lote/SKILL.md`**: una línea: cada vídeo del lote incluye su `publicacion.json`; si el usuario dice «y distribúyelos», al final `/distribuir`.
4. **`publicaciones/calendario.json`** (nuevo): registro de huecos ya usados (fecha, hora, vídeo, red, `id`/`uuid`/`plannerUrl` de Metricool, estado).
   Evita duplicados aunque se cierre la sesión.
5. **Skill nuevo `.claude/skills/distribuir/SKILL.md`** (`/distribuir [vídeos]`):
   1. Leer `calendario.json` + `getScheduledPosts` (próximos 90 días) → huecos ocupados.
   2. Calcular los siguientes huecos libres (10:30 y 18:30 Europe/Madrid; el primero al menos 60 min en el futuro), en el orden del lote.
   3. Comprobar que cada MP4 está commiteado y empujado y que su URL raw responde 200 (desde el contenedor sí hay red a raw.githubusercontent.com: probado 200 el 28-11).
   4. Por vídeo y red: `createScheduledPost` → guardar `id/uuid/plannerUrl` en `calendario.json` (commit + push).
   5. Verificar con `getScheduledPosts` que están todos (red, hora, texto, medio) → informe: tabla del calendario + errores + enlaces.
   - Vídeos ya distribuidos (en `calendario.json`) no se repiten salvo petición expresa.

## 6. Decisiones del usuario
- **Textos sin OK previo** (2026-11-28-04, «total confianza, los entendiste bien»): títulos, textos y hashtags se generan con su estilo y se programan sin enseñárselos antes; se informan en el informe final.
- **Declaración de IA: SÍ en las tres redes** (decidido 2026-11-28-04): `isAiGenerated`, `isAiGeneratedContent`, `isAigc` = true.
- **Redes no alineadas**: cada una en su siguiente hueco libre (decidido 2026-11-28-04).

Pendientes:
- TikTok automático o manual tras la prueba.
- ¿Qué vídeos ya hechos (01–20) se publican primero? ¿Alguno ya está subido a mano en alguna red (para no duplicar)?
- ¿Avisar a los suscriptores de YouTube en cada Short? (por defecto sí).

## 7. Plan paso a paso (uno cada vez, verificando)
1. ✅ Investigar y elegir plataforma → Metricool Starter.
2. ✅ Conectar Metricool a Claude (usuario) y comprobar marca/redes (solo lectura).
3. ✅ (28-11-04) Aplicar los cambios del §5 (config, plantilla `publicacion.json`, líneas en SKILL.md, skill `distribuir`) con el OK del usuario,
   y generar el `publicacion.json` de un vídeo ya hecho para que el usuario revise título y hashtags.
4. ✅ (28-11-04) Sustituida por la distribución real del documental 21 (el usuario dio el OK a los textos): 3 posts creados y verificados con `getScheduledPosts`; Metricool descarga el MP4 de la URL raw (aunque GitHub lo sirve como `application/octet-stream`) y lo aloja en static.metricool.com. Pendiente: confirmar que se publican solos a su hora. Antes:
   **Prueba real controlada** con ese vídeo: un post de YouTube con `privacy: "private"` (o el que elija el usuario) en un hueco cercano →
   comprobar en `getScheduledPosts` y en la app de Metricool que el vídeo se ha descargado bien desde la URL raw y que el tipo es Short/Reel.
   Ojo: no se puede borrar por el conector; el usuario lo borra en Metricool si hace falta.
5. Prueba en las 3 redes con un vídeo real en un hueco de verdad (15:30 o 20:30).
6. Distribuir los vídeos ya producidos (decide el usuario cuáles y en qué orden).
7. Uso normal: «/loteN … y distribúyelos».
