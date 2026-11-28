# AUTOMATIZACIÓN DIARIA — «haz 2 vídeos y distribúyelos» cada mañana

> Creada el 2026-11-28 a petición del usuario. La lanza una **tarea programada de Claude en la nube** cada día a las **07:47 (Europe/Madrid)**,
> en una sesión nueva. **Nadie supervisa en directo**: sigue esto al pie de la letra y **no preguntes nada**.

## Estado
- Tarea programada `trig_01LnEdK2H5uTmnoDDv9AAi9z` («Vídeos diarios: 2 vídeos + distribución»), cron `CRON_TZ=Europe/Madrid 47 7 * * *`,
  sesión nueva en cada disparo, aviso push. **Creada PAUSADA el 2026-11-28** (el usuario estaba al 89 % de su uso hasta el martes 1-dic 07:00).
- **Antes de activarla:** (1) fusionar la PR #12 (Whisper, duración variable, este archivo); (2) ✅ conector de Metricool añadido por el usuario el 28-nov (comprobado con `get_trigger`); (3) activarla (o pedírselo a Claude: `update_trigger enabled=true`) para que la primera ejecución sea el martes 1-dic a las 07:47.

## Permiso del usuario (2026-11-28)
- Al terminar, **fusionar el trabajo en `main` y hacer push a `main`** directamente (sin pull request). Si el push se rechaza: `git fetch origin main`,
  `git merge --no-edit origin/main`, resolver y volver a empujar. Nunca reescribir historia ni forzar.

## Pasos
0. **Preparar:** repo `zapatoia/zapatero` en `main` actualizado (`git fetch origin main && git checkout main && git pull`). Kit:
   `bash .claude/skills/documental-animado/instalar/instalar_linux.sh`. Leer `CLAUDE.md`, `.claude/skills/ideas/SKILL.md`, `lote/SKILL.md`,
   `distribuir/SKILL.md`, `documental-animado/SKILL.md` (§0, §7) y, de `docs/PIPELINE_STATE.md`, solo §3 (primeras entradas) y §14 (primera).
   No leer el historial antiguo completo (ahorra uso).
1. **Topes de seguridad (antes de gastar nada):**
   - **Metricool:** si las herramientas `mcp__Metricool_Social_Media_Management__*` no están (ToolSearch «metricool»), no producir nada: informe
     «la tarea no tiene el conector de Metricool» y fin (sin él no hay ideas ni distribución).
   - **ElevenLabs:** `publicaciones/creditos_eleven.json` lleva la cuenta (plan Creator 100.000/mes). Estimar ~1.400 créditos por vídeo (menos si es
     corto). Si `restantes_estimados` < 3.000 → no generar voz ni programar; informe «sin créditos» y fin. Si en un vídeo la API responde
     «quota_exceeded», parar igual. Tras cada voz, restar los caracteres reales (`audio/eleven_gasto.json`).
   - **Cola llena:** si en `publicaciones/calendario.json` el `siguiente_libre` de las tres redes está a más de 6 días vista, hacer 0 vídeos hoy
     (informe «cola llena»); si está a 4–6 días, hacer 1.
2. **Ideas:** `/ideas 2` (competidores de Instagram en Metricool + tu canal + web, datos frescos), duración variable 45 s–1:30 según la idea.
3. **Producción:** `/lote 2` con esas ideas, pipeline completo. **Control de voz obligatorio:** tras `voz_eleven.py`, `PY motor/nucleo/voz.py <proy> verificar`
   (Whisper). Cada falla real (palabra cambiada/comida, baja confianza confirmada al medir, vocal estirada, pausa rara): regrabar SOLO esa frase y
   encajarla (método del documental 16, `documentales/16-partida-unica/audio/parche_l1.py`), máximo 2 intentos por vídeo; si sigue mal, ese vídeo
   **no se programa** (queda en el repo marcado «pendiente de revisión»). QA (`qa.json`) en verde con aceptadas medidas; si no, no se programa.
4. **Distribuir:** `/distribuir` con los vídeos que pasaron (textos con el estilo del usuario, sin pedir OK; Instagram, YouTube y TikTok en los
   siguientes huecos de cada red; verificar con `getScheduledPosts`; actualizar `calendario.json`).
5. **Guardar:** `/save-session` breve (sesión `docs/sessions/AAAA-MM-DD-NN.md`) + log del día `docs/automatizacion/AAAA-MM-DD.md` (ideas elegidas y por
   qué, duración, créditos gastados y restantes, posts con fecha/hora y enlace del planner, avisos de Whisper y cómo se resolvieron, errores).
   Commit y **push a `main`**.
6. Incluir en el log y en el mensaje, si es lunes, las conclusiones semanales de `ideas/aprendizaje.json`.
7. **Mensaje final** (llega al usuario como notificación): 5–8 líneas: los 2 títulos, cuándo sale cada uno por red, créditos restantes estimados,
   y cualquier vídeo que no se programó y por qué.

## Si algo falla
No inventar resultados. Dejar lo hecho guardado, apuntar el error en el log del día y empujar a `main` igualmente. Al día siguiente se sigue normal.
