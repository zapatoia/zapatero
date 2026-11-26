# STYLE.md — Estética «MMO retro low-poly 2003»

Fuente de verdad en código: `retro3d/style.py` (paleta, luz, cielo, niebla, render, subtítulos).
Todo es **original**: ningún nombre, logo, modelo, personaje, música ni UI de juegos existentes.

## Principios (versión MINIMALISTA, v2)
0. **Menos es más.** Cada elemento debe ganarse su sitio: silueta clara, pocas piezas, superficies limpias, un acento de color por personaje. Si algo no se lee en un móvil a 1 m, sobra.
1. **Polígonos visibles, no realismo.** Sombreado plano por cara (normales planas) y **color por vértice uniforme** (sin variación por cara: `jitter=0` por defecto).
2. **Texturas mínimas y pixeladas** (16–32 px, *nearest*): dos tonos en manchas grandes y poco contraste (hierba, tierra), o solo líneas de junta (piedra, tablas, tejas). Personajes sin textura: solo color por vértice. Nunca normal maps ni PBR. `Renderer.add_texture` rechaza > 128 px.
3. **Formas simples**: cajas con poco bisel, copas de árbol de 10–14 puntos, rocas de 10, montañas de 10. Sin piezas decorativas pequeñas.
4. **Luz cálida de tarde:** sol bajo en 3/4 delantero-izquierdo, relleno hemisférico generoso (caras siempre legibles), sombras duras que tiran a violeta. **Contraluz cálido** (`rim_col`) en el borde de personajes e iconos.
5. **Cielo y niebla:** degradado suave cenit→horizonte con un halo discreto; niebla lineal 18–70 m del color del horizonte. Montañas azuladas y 5 nubes planas.
6. **Post:** brillo suave, +6 % saturación, +4 % contraste y viñeta ligera.

## Paleta (terrosa saturada)
| Uso | Colores |
|---|---|
| Hierba | `#467027` `#5f8c2e` `#7aa23a` |
| Tierra / camino | `#7f5530` `#a7743f` `#c39257` |
| Piedra | `#686357` `#8c8577` `#aaa291` + musgo `#5f8a2c` |
| Madera | `#7a4f2b` `#9a6a3c` `#b98451`; tejas `#a44c33` |
| Follaje | `#2d5c22` `#3f7a2a` `#5e9a2f`; pinos `#2f5e3a` `#3f7546` |
| Narrador | túnica `#2f8072`, ribete `#e0a83a`, bufanda `#c4512e`, cuero `#7b4a28`, piel `#f0b98a`, pelo `#7a3b1e` |
| Perro | pelo `#d0913f`, crema `#f2dcb0`, orejas `#8a4f22`, nariz `#2a1d17`, lengua `#ee6f86`, collar `#c43b3b` |
| UI en el mundo | papel `#fbf1d8`, tinta `#2a1a10`, oro `#f2b632`, rojo aviso `#d8312b` |

## Narrador (fijo; ver config/narrator.json)
Pasamontañas magenta #D61F8C que solo deja ver ojos y boca, cruz pequeña blanca en la frente; jersey streetwear negro con franjas blancas y «00»; pantalón militar ancho de camuflaje (oliva, oliva oscuro, caqui); cinturón negro con plata y oro; cadena fina de plata; zapatillas blancas de suela gruesa. La silueta (pasamontañas + jersey + zapatillas) debe leerse a la primera. Colores planos, casi sin detalle.

## Personajes
- **Proporciones achaparradas:** cabeza ≈ 30 % de la altura, manos en bloque (manopla + pulgar), piernas cortas, botas grandes.
- **Rig rígido por segmentos** (cadera, torso, cabeza, brazo, antebrazo, mano, muslo, espinilla) — como los modelos de la época.
- **Caras mínimas pintadas en textura** (atlas 128 px, un solo tono oscuro, sin brillos, cejas, nariz ni rubor): 5 ojos (óvalo, medio, cerrado, feliz ^, sorpresa) y 5 bocas (X media sonrisa, M, E, A, O).
- **Presupuesto:** 300–1.500 triángulos por personaje (narrador 576, perro 554).
- **Movimiento secundario** con muelles amortiguados (`anim.Spring`): orejas y cola del perro, cola de la bufanda.

## Escenarios
- **Claro** (`retro3d/world.py`): hierba en mosaico y camino de tierra mezclado por vértice, cabaña de piedra y madera, muro de piedra, vallas, farol, árboles y pinos simples, pocas rocas y matojos, montañas y nubes.
- **Casa** (`retro3d/interior.py`, en `ORIGIN`): interior de la cabaña con frente abierto a cámara: suelo de tablas, zócalo de piedra, ventana con luz de día, chimenea con fuego que parpadea, alfombra, cojín del perro, mesa, taburete, estante. Luz propia (`LIGHT_INTERIOR`): ventana cálida, sin niebla.

## Cámara dinámica
Nunca un vídeo entero en plano fijo y cercano. Cada beat define su plano: situación lejana y picada con empuje rápido (easeInOut fuerte), órbita (media o completa), grúa que sube o baja, travelling lateral, contrapicado para el énfasis, empuje y alejamiento; **barrido rápido con desenfoque de movimiento** entre escenas; **golpes de zoom cortos** en palabras clave. Alterna general/medio/primer plano, sin repetir tipo seguido, cambio claro cada 2–3 s. La cámara nunca atraviesa modelos ni el suelo (holgura ≥ 0,3 m comprobada en cada fotograma). Formato vertical: a 2,5 m solo caben ±0,5 m en horizontal; los planos se diseñan para ello. La cámara nunca entra en un modelo (`Production._avoid`).

## Recursos explicativos 3D (`retro3d/props.py`)
Siluetas limpias de uno o dos tonos: carteles lisos con texto pixel, bocadillos (papel claro, borde oscuro), corazón y gota extruidos sin bisel, «?» en vóxeles, aviso (disco rojo con cruz blanca), patatas fritas, **números en medallón** (disco oscuro con cifra dorada gruesa), chispas. Entran con **easeOutBack** (rebote) y salen con easeInBack; flotan y oscilan. Los números/iconos clave pueden anclarse al encuadre (`"screen": [x, y, profundidad]`) para garantizar que se ven en vertical.

## Animación
easeOutBack, easeInOut, anticipación (recoger antes de lanzar), rebote/aplastamiento al aterrizar. Nada quieto más de 1,5 s: respiración, microbalanceo, parpadeo (al final de cada frase + aleatorio cada 2–4 s), deriva de cámara. **Gestos de énfasis**: en las palabras acentuadas (picos de energía de la voz) el narrador asiente, golpea con las manos, levanta una mano o ladea la cabeza con ojos abiertos (variado, con anticipación). Las acciones arrancan 0,2 s antes de su palabra.

## Textos animados
Letra a letra (≈30 letras/s; en subtítulos, dentro del tiempo de cada palabra), cada letra sube unos píxeles y se funde en 0,1 s; salida con fundido rápido. Nada extravagante.

## Subtítulos
Montserrat Black (OFL, incluida en `assets/fonts/`), MAYÚSCULAS, bloques de ≤3 palabras, palabra actual en amarillo `#FFD23F` con rebote sutil, texto blanco con contorno marrón-negro de 10 px, sin sombra. Centro vertical al 66,5 % de la altura. **Zonas seguras:** nada en el 20 % inferior ni en el 12 % derecho (se verifica en cada fotograma).
