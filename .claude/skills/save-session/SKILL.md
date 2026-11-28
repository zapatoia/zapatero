---
name: save-session
description: Guarda el contexto completo de la sesión para continuar en un chat nuevo. Actualiza docs/PIPELINE_STATE.md (documento maestro), crea docs/sessions/AAAA-MM-DD-NN.md con el resumen de la sesión, comprueba que CLAUDE.md remite a PIPELINE_STATE.md, y hace commit y push. Usar cuando el usuario escriba /save-session o pida guardar el estado/contexto.
---

# /save-session — guardar el estado del proyecto

Objetivo: que un Claude **sin ningún contexto** pueda continuar el trabajo leyendo solo el repositorio.

## Pasos (en orden, sin saltarse ninguno)

1. **Reunir datos reales** (no inventar nada):
   - `git log --oneline -30`, `git tag -n`, `git status --short`, `git branch --show-current`.
   - `ls videos/ scripts/ config/ docs/ docs/sessions/`; duración de cada vídeo con `ffprobe -v error -show_entries format=duration -of csv=p=0 <mp4>` (un fichero por llamada).
   - Informes de `build/<id>/report.json`, `qa.md`, `sfx_report.md` si existen (copiar lo relevante a `docs/<id>-vK/`).
   - Repasar la conversación de esta sesión: peticiones del usuario en orden, qué se hizo, qué falló y por qué, qué quedó pendiente, qué decisiones dejó abiertas el usuario.

2. **Actualizar `docs/PIPELINE_STATE.md`** (reescribir las secciones que hayan cambiado; nunca borrar historial). Debe contener siempre estas secciones, con este orden:
   1. Cómo usar este documento (leerlo al empezar; mantenerlo al día con /save-session)
   2. Objetivo y filosofía (minimalismo, calidad ante todo, 100 % original)
   3. Estado en una frase + siguiente paso exacto
   4. Estilo visual actual (resumen de STYLE.md + decisiones clave)
   5. Narrador fijo (diseño completo, rig, bocas, expresiones, poses, dónde está definido, cómo se bloquea)
   6. Otros personajes y escenarios
   7. Arquitectura del pipeline (archivos, comandos, motor de render y por qué)
   8. Voz (voice_id, modelo, ajustes, coste, caché)
   9. Reglas: guion, sonido, cámara, textos, físicas/contactos, revisión antes de entregar
   10. Historial de cambios pedidos por el usuario (en orden, con motivo; bugs incluidos)
   11. Vídeos producidos (ruta, versión, commit, duración, tiempo de render, estado)
   12. Versiones aprobadas (tags de git) y contenido
   13. Problemas conocidos
   14. Pendiente y siguiente paso exacto
   15. Decisiones que debe tomar el usuario
   16. Índice de sesiones (enlaces a docs/sessions/)
   Escribir en español, con datos concretos (rutas, comandos, números). Sin relleno.

3. **Crear `docs/sessions/AAAA-MM-DD-NN.md`** (fecha de hoy; NN = siguiente número del día, empezando en 01) con: qué pidió el usuario, qué se hizo, qué falló (y cómo se resolvió o no), qué queda, commits de la sesión.

4. **Comprobar `CLAUDE.md`** (y que siga el aviso del comando `/loteN` → `.claude/skills/lote/SKILL.md`): debe decir al principio que al empezar una sesión hay que leer `docs/PIPELINE_STATE.md` y la última sesión, y debe incluir la regla de protección (no modificar narrador, estilo ni pipeline base sin permiso explícito; tags vK al aprobar versiones). Si falta, añadirlo.

5. **Commit y push** en la rama de trabajo actual:
   - `git add -A` (excepto `build/`, que está ignorado) y commit con mensaje `Guardar estado de sesión AAAA-MM-DD-NN` + líneas de atribución que indique el sistema.
   - `git push -u origin <rama>` (reintentar hasta 4 veces con espera si falla la red).
   - **Nunca** hacer push a `main` ni crear la pull request salvo que el usuario lo pida.

6. **Responder al usuario** con: rama en la que está todo, commit, el índice de PIPELINE_STATE.md, y el recordatorio de unir la rama a `main` (o pedir que se abra la pull request). Si algo falló (push, ffprobe, ficheros que faltan), decirlo claramente.
