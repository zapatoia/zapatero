---
name: lote
description: Produce un LOTE de N documentales verticales completos, estrictamente uno detrás de otro y con el pipeline entero cada uno. Usar cuando el usuario escriba /loteN (p. ej. /lote4, /lote5) o /lote N seguido de los títulos/hooks de cada vídeo, o pida «un lote de N vídeos».
---

# /loteN — lote de N vídeos (pedido del usuario, 28 nov 2026)

**Uso:** `/lote5 (título/hook 1) (título/hook 2) … (título/hook 5)` — o `/lote 5 …`, o los títulos en líneas/numerados.
N = el número pegado a «lote». Los títulos/hooks van entre paréntesis, numerados o uno por línea.

**Sin títulos («haz N vídeos», «haz N vídeos y distribúyelos»):** primero `/ideas N` (`.claude/skills/ideas/SKILL.md`, sin preguntar nada)
y usar sus N elegidas (con su ficha) como títulos/hooks de este lote; al acabar cada vídeo, pasar la idea a `ideas/banco.json → hechas`.

**DURACIÓN VARIABLE (decisión del usuario, 2026-11-28; manda sobre el «~1:30» del prompt original del lote):** cada vídeo dura entre **45 s y 1:30**
según lo que pida la idea: un dato o mito con una sola explicación → 45–60 s (~100–140 palabras); explicación con 2–3 pasos → 60–75 s
(~140–175); progresión o historia con varios hitos → 75–90 s (~175–215). Se decide en el guion (o en la ficha de `/ideas`) y se dice en el informe.
Nunca se rellena para llegar a una duración: si la idea da para 50 s, son 50 s.

**Qué hacer:** ejecutar **tal cual** el prompt de abajo (el que el usuario escribió para el primer lote, documentales 17–20, sesión
2026-11-28-02), sustituyendo «4» por N y la lista de vídeos por los títulos/hooks que ha dado. **No preguntar nada**: el OK de la voz
y del gasto viene implícito (regla de oro del kit). Formato activo: documentales animados verticales 9:16 (`.claude/skills/documental-animado/SKILL.md`,
§7 obligatorio). Si falta el kit en el contenedor: `bash .claude/skills/documental-animado/instalar/instalar_linux.sh`.

**Cómo se hizo el primer lote (la referencia de calidad; repetir igual):**
1. Antes del vídeo 1: leer `CLAUDE.md`, `docs/PIPELINE_STATE.md`, la última sesión, `documental-animado/SKILL.md` entero (§7) y un módulo de
   escenas reciente (p. ej. `escenas_zurdo.py`, `escenas_vida.py`) para el nivel visual. Crear una tarea por vídeo (TaskCreate) y marcarlas en orden.
2. Por CADA vídeo, en `documentales/NN-tema/` (NN = siguiente número libre):
   datos verificados con WebSearch (fuentes en `guion.json → fuentes` y `descripcion.md`; lo dudoso como «se cree» / «es una teoría») →
   guion (~2,2–2,5 palabras/s; duración VARIABLE 45 s–1:30 según la idea, ver arriba; gancho con acción, cierre que vuelve al gancho con remate) →
   **módulo de escenas NUEVO** `escenas_<tema>.py` (7–8 tipos de escena dibujados a medida, conceptos animados al decirlos, SFX propios, enganchado
   al final de `motor.py`) → `motor.py <proy> escenas` y `prueba` sin voz, revisar y corregir → `voz_eleven.py <proy>` (una toma) → comprobar anclas con
   `palabras.json` → `prueba` con tiempos reales en todos los momentos clave y corregir (huecos vacíos de 2–3 s, pastillas que se pisan, cosas en
   y<150 o tapando la franja de texto, texto ilegible) → `render --procesos 4` → QA (`qa_aceptadas` solo con medida) → hoja completa + recortes a tamaño
   real (`ffmpeg -ss T … crop`) → corregir y volver a renderizar → `outro.py <proy>` → medir LUFS del `-v2.mp4` → `descripcion.md` → regla nueva en
   `SKILL.md` §7 → commit + push → `SendUserFile` del `-v2.mp4` con «Vídeo k/N terminado» → solo entonces el siguiente.
   Cada vídeo del lote incluye su `publicacion.json` (junto a `descripcion.md`; ver `docs/DISTRIBUCION.md` §5).
3. Al acabar los N: informe final (tabla con número, título, duración con y sin outro, ruta, estado de QA; errores corregidos; pendientes;
   confirmación de secuencialidad y de pipeline completo; coste de voz; fuentes) y `/save-session`. Si el usuario dijo «y distribúyelos», ejecutar `/distribuir` directamente (sin enseñar los textos ni esperar OK: decisión del usuario del 2026-11-28) y añadir al informe la tabla de publicaciones (`.claude/skills/distribuir/SKILL.md`).

---

## PROMPT ORIGINAL DEL USUARIO (ejecutarlo tal cual, con N y los títulos nuevos)

PRODUCCIÓN DE LOTE DE VÍDEOS — PIPELINE COMPLETO

Quiero que fabriques un lote de N vídeos completos utilizando mi pipeline habitual de producción.

1. VÍDEOS QUE QUIERO PRODUCIR

Fabricar los siguientes N vídeos, estos son los titulos/hooks:
	(los títulos/hooks que haya escrito el usuario tras /loteN, en su orden)

Duración objetivo de cada vídeo: aproximadamente 1 minuto y 30 segundos, salvo que el tema, la narrativa o los criterios definidos en mi pipeline justifiquen razonablemente otra duración.

⸻

2. INSTRUCCIÓN CRÍTICA: PRODUCCIÓN ESTRICTAMENTE SECUENCIAL

Quiero que fabriques los vídeos ESTRICTAMENTE UNO A UNO, en orden.

El orden de ejecución debe ser:
	•	Primero: vídeo 1. Completar absolutamente todo su proceso de fabricación.
	•	Segundo: vídeo 2. Comenzar únicamente cuando el vídeo 1 esté completamente terminado.
	•	(y así sucesivamente hasta el vídeo N, cada uno solo cuando el anterior esté completamente terminado.)

NO fabriques los vídeos simultáneamente.
NO paralelices la fabricación de vídeos.
NO empieces a generar escenas, assets, animaciones, audio ni renders de un vídeo mientras todavía estés fabricando otro.
NO repartas el esfuerzo, el tiempo, los recursos, la atención ni la capacidad de trabajo entre los vídeos.
Cada vídeo debe completar su pipeline íntegro e independiente antes de comenzar el siguiente.
Quiero una ejecución secuencial real, no simplemente una planificación secuencial con producción paralela.

⸻

3. CALIDAD Y ESFUERZO: NO REDUCIR EN ABSOLUTO

Esta es la instrucción más importante de toda la solicitud.

Quiero que cada vídeo del lote reciba EXACTAMENTE el mismo nivel de esfuerzo creativo, profundidad, atención al detalle, calidad, rigor, desarrollo, trabajo de animación, recursos, tiempo de producción y control de calidad que recibiría si te hubiera pedido fabricar ese vídeo individualmente en una sesión independiente.

El hecho de que te solicite varios vídeos en una misma petición NO debe provocar ninguna reducción en la calidad de ninguno de ellos.

No quiero que aceleres artificialmente el proceso.
No quiero que simplifiques el pipeline.
No quiero que recortes pasos.
No quiero que reduzcas la complejidad de las escenas.
No quiero que reduzcas la cantidad, calidad o detalle de las animaciones.
No quiero que simplifiques guiones, narración, efectos, composición, recursos visuales ni transiciones para terminar el lote antes.
No quiero que los últimos vídeos reciban menos atención que el primero.
No quiero que el esfuerzo se distribuya entre los vídeos.
Quiero que cada vídeo reciba individualmente el 100% del esfuerzo que aplicarías a un vídeo solicitado de forma aislada.

Presupuesto de trabajo y tiempo

Utiliza como referencia el tiempo, el nivel de trabajo y el presupuesto de ejecución habituales de mi pipeline para fabricar UN vídeo individual.

Si normalmente fabricar un vídeo implica aproximadamente 30 minutos de trabajo, quiero que dediques aproximadamente ese mismo nivel de trabajo a cada uno de los vídeos, por lo que la producción total debería representar aproximadamente N veces el trabajo habitual de un vídeo individual.

Si mi pipeline habitualmente requiere más tiempo, pasos, iteraciones, generación, renderizado o revisiones para producir un vídeo de calidad, respeta ese proceso para cada vídeo.

No interpretes esta solicitud como una petición de producir N vídeos en el tiempo habitual de uno.
Interpreta esta solicitud como la producción de N vídeos completos, con el esfuerzo individual habitual aplicado N veces.
No utilices el hecho de estar trabajando en lote como justificación para economizar trabajo creativo o técnico.
El objetivo es producir N vídeos de la misma calidad que N vídeos fabricados individualmente, no N vídeos más rápidos o simplificados.

⸻

4. CONTEXTO, DOCUMENTACIÓN Y APRENDIZAJES PREVIOS

Antes de empezar el vídeo 1:
	•	Lee íntegramente el archivo maestro que define mi pipeline.
	•	Revisa las instrucciones, documentación, estándares y especificaciones relevantes.
	•	Revisa los aprendizajes, decisiones, mejoras y patrones de calidad documentados en sesiones anteriores.
	•	Inspecciona los assets, herramientas, recursos, animaciones, scripts, plantillas y componentes existentes que sean relevantes.
	•	Comprende cómo se fabricaron mis vídeos anteriores y qué mejoras se han incorporado al pipeline.
	•	Utiliza los aprendizajes previos para mantener y mejorar la calidad de todos los vídeos.

No inventes ni sustituyas los estándares establecidos en el archivo maestro.
El archivo maestro y las instrucciones consolidadas del pipeline tienen prioridad sobre cualquier supuesto genérico sobre cómo fabricar vídeos.
Si existen contradicciones entre documentación, identifica la instrucción más reciente o la que esté establecida como autoridad en mi pipeline.
No repitas innecesariamente operaciones de preparación que ya estén resueltas y disponibles, pero tampoco omitas procesos que sean necesarios para la calidad individual de cada vídeo.

⸻

5. FABRICACIÓN COMPLETA DE CADA VÍDEO

Para cada uno de los vídeos, ejecuta el pipeline completo, siguiendo las instrucciones y estándares de mi sistema.
Cada vídeo debe ser tratado como un proyecto independiente.

Esto incluye, según corresponda a mi pipeline:
	•	Análisis y desarrollo del tema.
	•	Investigación y verificación de datos.
	•	Desarrollo del concepto creativo.
	•	Creación de un hook potente.
	•	Guion completo y optimizado para retención.
	•	Desarrollo de la narrativa.
	•	Estructuración de escenas.
	•	Diseño visual.
	•	Creación y selección de assets.
	•	Animaciones.
	•	Narración y audio.
	•	Efectos de sonido.
	•	Música, cuando corresponda.
	•	Sincronización de elementos.
	•	Composición.
	•	Transiciones.
	•	Textos y subtítulos, cuando corresponda.
	•	Renderizado.
	•	Inspección del resultado.
	•	Corrección de errores.
	•	Renderizado final corregido.
	•	Verificación de los archivos finales.

Estos pasos son orientativos y complementarios: no sustituyen, simplifican ni modifican los pasos específicos que ya existan en mi pipeline.
Mantén el nivel de originalidad, creatividad, profundidad y detalle que utilizas habitualmente.
No reutilices mecánicamente estructuras narrativas, guiones, escenas o composiciones entre vídeos cuando eso perjudique su calidad u originalidad.
Reutiliza herramientas, componentes o assets existentes únicamente cuando sea apropiado y compatible con los estándares de calidad.

⸻

6. CONTROL DE CALIDAD INDIVIDUAL Y OBLIGATORIO

Cada vídeo debe pasar su propia revisión completa antes de comenzar la fabricación del siguiente.
No consideres un vídeo terminado simplemente porque su render haya finalizado.

Comprueba individualmente:
	•	Que el vídeo se renderiza y reproduce correctamente.
	•	Que la duración es adecuada.
	•	Que el guion y la narración están completos.
	•	Que el audio funciona correctamente.
	•	Que las escenas están completas.
	•	Que las animaciones funcionan.
	•	Que no hay errores visuales.
	•	Que no hay elementos inesperados, escenas vacías o assets faltantes.
	•	Que los textos, subtítulos y elementos visuales son correctos.
	•	Que la sincronización es adecuada.
	•	Que el resultado mantiene la calidad habitual de mi pipeline.

Si detectas errores, corrígelos y vuelve a revisar el resultado.
Si una comprobación requiere reproducir, inspeccionar o renderizar de nuevo el vídeo, hazlo.
No sacrifiques la revisión por completar el lote rápidamente.

Criterio de finalización

Un vídeo únicamente se considerará terminado cuando:
	1.	Su fabricación completa haya finalizado.
	2.	El render final esté generado.
	3.	Las comprobaciones de calidad hayan concluido.
	4.	Los problemas detectados hayan sido corregidos o claramente documentados.
	5.	Los archivos finales estén organizados y disponibles.

Únicamente después de cumplir estos requisitos podrás comenzar el siguiente vídeo del lote.

⸻

7. ORGANIZACIÓN Y SEGURIDAD DEL PIPELINE

Mantén la organización de archivos, carpetas, assets, proyectos, renders, temporales y resultados conforme a la estructura existente de mi pipeline.
Evita sobrescribir accidentalmente archivos de vídeos anteriores.
Mantén los proyectos separados y correctamente identificados.
No modifiques ni elimines recursos preexistentes que no sean necesarios para la fabricación de estos vídeos.
No alteres la configuración global de mi pipeline salvo que sea necesario y esté justificado.
Si una tarea falla, intenta resolverla siguiendo el procedimiento habitual de mi pipeline antes de continuar.
Si se produce un error que impide completar un vídeo correctamente, no lo marques como terminado ni avances silenciosamente dejando una producción incompleta. Intenta solucionar el error y, si no puedes, documenta claramente el bloqueo.

⸻

8. ORDEN DE EJECUCIÓN

Ejecuta la producción en este orden exacto, para k = 1 … N:

VÍDEO k
Comienza únicamente cuando el vídeo k−1 esté completamente finalizado (el 1, de inmediato).
Fabricación completa.
Renderizado.
Control de calidad.
Correcciones.
Verificación.
Confirmación de finalización.

No alteres este orden.

⸻

9. ENTREGA FINAL

Cuando hayas terminado todos los vídeos, presenta un informe final con:
	•	Número y título de cada vídeo.
	•	Duración real de cada vídeo.
	•	Ubicación de los renders finales.
	•	Ubicación de los proyectos y archivos relevantes.
	•	Estado de las verificaciones de calidad de cada vídeo.
	•	Errores encontrados y corregidos.
	•	Problemas que hayan quedado pendientes.
	•	Confirmación de que los vídeos se han fabricado secuencialmente.
	•	Confirmación de que cada vídeo ha recibido su pipeline individual completo.

No entregues únicamente guiones, ideas, planificación, assets parciales o renders preliminares.
El objetivo de esta solicitud es obtener N VÍDEOS COMPLETOS, TERMINADOS, RENDERIZADOS Y VERIFICADOS.

Empieza revisando mi archivo maestro y la documentación de mi pipeline. Después comienza la fabricación del vídeo 1 y continúa secuencialmente hasta completar todos los vídeos.

Puedes añadir y mejorar cosas que no habían antes para estos vídeos, según veas si mejora.
