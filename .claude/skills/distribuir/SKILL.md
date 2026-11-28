---
name: distribuir
description: Programa vídeos ya terminados en Instagram Reels, YouTube Shorts y TikTok con el conector de Metricool, en los siguientes huecos libres (15:30 y 20:30 Europe/Madrid) de cada red. Usar cuando el usuario escriba /distribuir, pida «distribúyelo/distribúyelos», «prográmalo en redes» o un lote «y distribúyelos».
---

# /distribuir [vídeos] — programar en redes (Metricool)

Plan completo y lo verificado del conector: `docs/DISTRIBUCION.md` (léelo antes). Base fija: `config/redes.json`.
Registro de huecos: `publicaciones/calendario.json` (fuente de verdad junto con `getScheduledPosts`).

## Antes de programar
- **SIN PEDIR OK (decisión del usuario, 2026-11-28: «total confianza»):** los títulos, textos y hashtags NO se enseñan antes ni esperan aprobación.
  Se generan con su estilo (`config/redes.json → formato_texto`: «🤯 TÍTULO EN MAYÚSCULAS + emoji del tema», 5 hashtags máx.) y se programan directamente.
  Se informan DESPUÉS, en el informe final.
- Cada vídeo debe tener `documentales/NN-tema/publicacion.json` y su MP4 final (`final/NN-tema-v2.mp4`) con commit **empujado**. Si falta el
  `publicacion.json`, generarlo (formato en `docs/DISTRIBUCION.md` §5) y seguir.
- No preguntar por huecos manuales: se usa el cursor de `calendario.json`. Si el usuario dice que ha programado algo a mano, apuntarlo en
  `calendario.json → ocupado_manual` y mover el cursor de esa red.
- Las tools son `mcp__Metricool_Social_Media_Management__*` (si no se ven, ToolSearch «metricool»).

## Pasos
1. **Ocupado** = `calendario.json` (cursor `siguiente_libre` por red + `publicaciones`) ∪ `getScheduledPosts(brandId 8415557, hoy → +90 días, Europe/Madrid)`.
2. **Huecos**: para cada red por separado, desde su `siguiente_libre`, los huecos 15:30 / 20:30 que no estén ocupados y que caigan ≥ 60 min
   en el futuro; se asignan en el orden de los vídeos. Las redes NO tienen por qué ir alineadas (cada una con su cursor).
3. **Medio**: URL `https://raw.githubusercontent.com/zapatoia/zapatero/<hash del commit>/<ruta del mp4>` (hash, nunca rama). Comprobar con
   `curl -sI` que responde 200 y que el `Content-Length` coincide con el fichero local.
4. **Un post por vídeo y red** con `createScheduledPost(blogId=8415557, date=<ISO con desfase>, info=<JSON>)`:
   - comunes: `providers:[{"network":…}]`, `publicationDate:{"dateTime":"AAAA-MM-DDTHH:MM:00","timezone":"Europe/Madrid"}`, `text`, `media:[url]`,
     `autoPublish:true`, `draft:false`, `videoCoverMilliseconds` = `portada_ms`.
   - instagram: `instagramData:{"type":"REEL","showReelOnFeed":true,"isAiGenerated":true}`.
   - youtube: `youtubeData:{"title","type":"short","privacy":"public","madeForKids":false,"category":"EDUCATION","tags":[…],"isAiGeneratedContent":true}`.
   - tiktok: texto en UNA línea (sin saltos), `tiktokData:{"privacyOption":"PUBLIC_TO_EVERYONE","title","autoAddMusic":false,"isAigc":true}`.
   - Declaración de IA en las tres redes (decisión del usuario, 2026-11-28).
5. Tras cada post creado: añadir a `calendario.json → publicaciones` {video, red, fecha, id, uuid, plannerUrl, estado:"programado"} y avanzar el
   `siguiente_libre` de esa red. Si un post falla, apuntarlo con `estado:"error"` y el mensaje, y no mover el cursor.
6. **Verificar** con `getScheduledPosts` que cada post está (red, hora, texto, medio). Commit + push de `calendario.json`.
7. **Informe**: tabla vídeo × red con fecha/hora y enlace del planner, errores y siguiente hueco libre de cada red.

## Reglas
- Nunca repetir un vídeo ya presente en `calendario.json → publicaciones` para la misma red, salvo petición expresa.
- El conector **no puede borrar**: si algo sale mal, `updateScheduledPost` (con el contenido completo) o pedir al usuario que lo borre en Metricool.
- Los textos no necesitan el OK del usuario (decisión del 2026-11-28). Sí se le informa al terminar.
