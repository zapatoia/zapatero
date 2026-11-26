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
3. Comprobar en silencio que el entorno está listo (sin instalar nada todavía): `python3 -c "import moderngl, numpy, PIL, scipy, soundfile, pyloudnorm"` y `[ -n "$ELEVENLABS_API_KEY" ] && echo clave-presente` (no imprimir la clave). Si falta algo, mencionarlo en el resumen con el comando de instalación de CLAUDE.md, pero no ejecutarlo.
4. Responder en español, breve (máx. ~15 líneas):
   - **Dónde estamos**: versión actual, último vídeo, rama y si hay cambios sin commit.
   - **Pendiente**: lo que quedó abierto, incluidas las decisiones que tocan al usuario.
   - **Siguiente paso propuesto**: uno, concreto.
   - Terminar preguntando qué quiere hacer. No empezar ningún trabajo por iniciativa propia.
