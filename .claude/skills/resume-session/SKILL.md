---
name: resume-session
description: Retoma el proyecto en un chat nuevo. Lee CLAUDE.md, docs/PIPELINE_STATE.md, la última sesión de docs/sessions/ y el git log reciente, y responde con un resumen breve (dónde estamos, qué quedó pendiente, siguiente paso propuesto) SIN hacer ningún cambio. Usar cuando el usuario escriba /resume-session o pida retomar/ponerse al día.
---

# /resume-session — retomar el contexto (solo lectura)

**No modificar nada** (ni ficheros, ni git, ni renders, ni llamadas a ElevenLabs) hasta que el usuario lo diga.

## Pasos

1. Leer completos, en este orden:
   - `CLAUDE.md`
   - `docs/PIPELINE_STATE.md`
   - la última sesión: el fichero más reciente de `docs/sessions/` (orden alfabético = cronológico, `AAAA-MM-DD-NN.md`)
2. Ejecutar (solo lectura): `git branch --show-current`, `git status --short`, `git log --oneline -15`, `git tag -n`.
3. Formato activo = documentales 9:16 (ver `CLAUDE.md`): comprobar en silencio `[ -x ~/.venvs/documental-animado/bin/python ] && echo kit-listo`; si no está, decir en el resumen que antes del próximo vídeo hay que correr `bash .claude/skills/documental-animado/instalar/instalar_linux.sh` (2–3 min) y leer `.claude/skills/documental-animado/SKILL.md`. Solo si el usuario pide el formato 3D archivado:
   comprobar en silencio que el entorno está listo (sin instalar nada todavía): `python3 -c "import moderngl, numpy, PIL, scipy, soundfile, pyloudnorm"` y `[ -n "$ELEVENLABS_API_KEY" ] && echo clave-presente` (no imprimir la clave). Si falta algo, mencionarlo en el resumen con el comando de instalación de CLAUDE.md, pero no ejecutarlo.
3b. **Automatización diaria:** leer `docs/AUTOMATIZACION.md` → «Estado». Si la tarea `trig_01LnEdK2H5uTmnoDDv9AAi9z` sigue pausada o
   pendiente de activar, comprobarlo con `get_trigger` (solo lectura) y **recordárselo al usuario en el resumen, lo primero**: «la tarea diaria
   está pausada; ¿la activo? (antes: el conector de Metricool añadido en claude.ai y la PR fusionada)». No activarla sin que el usuario lo diga.
3c. **Mejoras pendientes que el usuario pidió recordar** (`docs/PIPELINE_STATE.md` §15, «Recordar al usuario»): mencionarlas en una línea al
   final del resumen mientras sigan pendientes: (1) limpieza de MP4 con una rama aparte que se vacía cada mes (necesita su permiso; urgente
   antes de ~febrero 2027, cuando el repo pase de ~4–5 GB); (2) clave de ElevenLabs con permiso de leer el saldo (la crea él en 1 minuto).
4. Responder en español, breve (máx. ~15 líneas):
   - **Dónde estamos**: versión actual, último vídeo, rama y si hay cambios sin commit.
   - **Pendiente**: lo que quedó abierto, incluidas las decisiones que tocan al usuario.
   - **Siguiente paso propuesto**: uno, concreto.
   - Recordar en una línea que para pedir varios vídeos basta con `/loteN (títulos/hooks)` (skill `.claude/skills/lote/SKILL.md`).
   - Terminar preguntando qué quiere hacer. No empezar ningún trabajo por iniciativa propia.
