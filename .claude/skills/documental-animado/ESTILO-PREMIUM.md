# ESTILO PREMIUM (catalogado a petición del usuario, 27 nov 2026)

Cuando el usuario diga **«quiero el estilo premium»** (o «estilo premium», «como la prueba premium»), el vídeo se hace con ESTE estilo.
No tiene por qué salir un móvil: lo que define el estilo es la estética, el 2.5D/3D y la cámara.

## Referencias
- Prueba aprobada como dirección: `documentales/_pruebas/premium/prueba-premium-2.mp4` («Tu cuerpo en un minuto»: tarjetas de cristal en 3D,
  cámara que vuela, apilado final en capas). Código: `motor/variantes/premium/prueba2.py` + motor `motor/variantes/premium/escena3d.py`.
- Primera prueba (más plana, solo como historial): `documentales/_pruebas/premium/prueba-premium.mp4` (`prueba.py`): móvil que se abre en capas,
  contador de fichas, línea de tiempo «detrás de las cámaras» con fotogramas, onda de voz y palabras con su segundo.
- Inspiración del usuario: reel oscuro con capas de cristal en perspectiva, contador «5,8 M», línea de tiempo con fotogramas/voz/palabras, teclado 3D.
  Solo se toma la técnica; nada de copiar textos, marcas ni personajes.

## Qué lo define (obligatorio)
- **Paleta:** negro azulado `#06080D` con degradado radial `#151B2C`; acento **dorado** `#E8B04A` / `#FFD98A`; texto blanco y gris `#8C93A6`.
  Colores propios de cada objeto (rojo del corazón, azul, verde) solo dentro de los iconos, con volumen.
- **Espacio 3D real** (`escena3d.py`): planos con textura colocados en el mundo (x, y, z, rotación), cámara con mirada (`Camara(ojo, mira, roll)`),
  orden por profundidad, perspectiva de verdad. Nada de diapositivas planas.
- **Cámara con movimientos de cine:** acercamiento lento, giro rápido (barrido) entre objetos con **desenfoque de movimiento** (subcuadros),
  grúa que sube para revelar, ligera inclinación (roll). Cambios cada 2–3 s; nunca quieta.
- **Profundidad de campo:** lo que no está a la distancia de foco se desenfoca según su profundidad; partículas doradas tipo bokeh en 3D.
- **Cristal:** tarjetas con degradado oscuro semitransparente, borde fino blanco, línea de brillo arriba, rejilla sutil, **barrido de luz** diagonal.
- **Suelo:** rejilla dorada en perspectiva que se funde a lo lejos + **reflejo** tenue de los objetos.
- **Halos** dorados detrás del protagonista; iconos vectoriales con degradado, brillo especular y halo de su color.
- **Cifras** grandes que ruedan (odómetro con desenfoque) y etiquetas con **línea guía** y punto dorado (estilo plano técnico / explosionado).
- **Revelado en capas:** los elementos terminan apilados como capas de cristal separadas en profundidad (vista explosionada).
- **Rótulo arriba** (y≈300): contexto en gris fino + palabra clave en blanco grueso, entrando con resorte y desenfoque; sale con fundido.
- **Posproceso:** viñeta, aberración cromática leve en los bordes, grano fino.
- Formato 9:16 1080×1920 a 60 fps; zonas seguras de TikTok (nada importante a la derecha de x=950 ni abajo de y=1536).

## Límites conocidos (decírselo al usuario si hace falta)
- Sin objetos fotorrealistas (dedos, bolígrafos con materiales reales): todo es vectorial con degradados y brillos.
- Sin modelos 3D complejos que giren 360°: planos y objetos sencillos en el espacio.
- Render más lento que el documental normal (≈1–2 min por cada 8 s con desenfoque de movimiento).

## Cómo se hace un vídeo premium (mientras no exista la variante completa)
1. Guion, voz (ElevenLabs, voz del usuario) y outro como en el resto de vídeos (SKILL.md §7).
2. Escena 3D con `escena3d.py`: lista de `Plano`s (texturas dibujadas con skia por frase), fotogramas clave de cámara ligados a las palabras
   (`palabras.json`), rótulos con la voz.
3. Revisar fotogramas sueltos antes del render completo; después hoja de cuadros, QA de audio (−14 LUFS) y outro.
Pendiente: convertirlo en variante con escenas pedidas desde `guion.json` (como `variantes/vertical`).
