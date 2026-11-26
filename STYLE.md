# STYLE.md — Estética «MMO retro low-poly 2003»

Fuente de verdad en código: `retro3d/style.py` (paleta, luz, cielo, niebla, render, subtítulos).
Todo es **original**: ningún nombre, logo, modelo, personaje, música ni UI de juegos existentes.

## Principios
1. **Polígonos visibles, no realismo.** Sombreado plano por cara (normales planas), color por vértice con ligera variación por cara (`jitter`) que da aspecto «pintado a mano».
2. **Texturas pequeñas y pixeladas** (32–128 px, filtro *nearest*, sin mipmaps): hierba, tierra, piedra, tablones, corteza, tejas, tela, cuero, metal, pelo. Las de detalle son grises y se multiplican por el color del vértice. Nunca normal maps ni PBR. `Renderer.add_texture` rechaza texturas > 128 px.
3. **Formas facetadas por envolvente convexa** (`mesh.hull`, `mesh.box(bevel=…)`, `mesh.blob`): cabezas biseladas, rocas, copas de árbol, montañas.
4. **Luz cálida de tarde:** sol bajo en 3/4 delantero-izquierdo (`LIGHT.sun_dir`), color ámbar; relleno hemisférico (cielo azul arriba, rebote terroso abajo); sombras duras del sol con PCF mínimo, que tiran a violeta (nunca negras).
5. **Cielo y niebla:** degradado cenit→horizonte con halo del sol y bandas de 64 niveles; niebla lineal 18–70 m del color del horizonte (más cálida hacia el sol). Montañas lejanas facetadas que la niebla vuelve azuladas, nubes planas.
6. **Post:** brillo suave de zonas claras, +6 % saturación, +4 % contraste y viñeta. Sin desenfoques ni profundidad de campo.

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

## Personajes
- **Proporciones achaparradas:** cabeza ≈ 30 % de la altura, manos en bloque (manopla + pulgar), piernas cortas, botas grandes.
- **Rig rígido por segmentos** (cadera, torso, cabeza, brazo, antebrazo, mano, muslo, espinilla) — como los modelos de la época.
- **Caras pintadas en textura** (atlas 128 px): 5 estados de ojos (abierto, medio, cerrado, feliz ^^, sorpresa) y 5 bocas (X cerrada, M entreabierta, E ancha, A abierta, O redonda). Ojos «chibi» sin esclerótica: óvalo oscuro con brillo.
- **Presupuesto:** 300–1.500 triángulos por personaje (narrador 1.416, perro 1.342).
- **Movimiento secundario** con muelles amortiguados (`anim.Spring`): orejas y cola del perro, cola de la bufanda.

## Escenario base (`retro3d/world.py`)
Claro de bosque: terreno con hierba en mosaico y camino de tierra mezclado por vértice (splatting clásico), cabaña de piedra y madera con ventana iluminada, muro de piedra con musgo, vallas, farol, barril y cajas, árboles redondos y pinos de pocos polígonos, rocas facetadas, matojos y flores con recorte alfa, montañas y nubes lejanas. Zona de actuación despejada alrededor del origen.

## Cámara
Tercera persona tipo MMO, **ligeramente picada** (elevación 8–32°), siempre en movimiento suave (órbita, empuje o alejamiento con `easeInOut` + deriva mínima). **Cambio de plano cada 2–3 s.** Formato vertical: a 2,5 m solo caben ±0,5 m en horizontal; los planos se diseñan para ello. La cámara nunca entra en un modelo (`Production._avoid`).

## Recursos explicativos 3D (`retro3d/props.py`)
Carteles de madera con texto pixel tallado, bocadillos pixel (papel crema, borde oscuro), iconos low-poly (corazón, gota de sal, cristales de sal, «?» en vóxeles, cruz de aviso, patatas fritas, lengua), números en vóxeles dorados, chispas. Entran con **easeOutBack** (rebote) y salen con easeInBack; flotan y oscilan. Los números/iconos clave pueden anclarse al encuadre (`"screen": [x, y, profundidad]`) para garantizar que se ven en vertical.

## Animación
easeOutBack, easeInOut, anticipación (recoger antes de lanzar), rebote/aplastamiento al aterrizar. Nada quieto más de 1,5 s: respiración, microbalanceo, parpadeo cada 2–4 s, deriva de cámara.

## Subtítulos
Montserrat Black (OFL, incluida en `assets/fonts/`), MAYÚSCULAS, bloques de ≤3 palabras, palabra actual en amarillo `#FFD23F` con rebote, texto blanco con contorno marrón-negro de 11 px y sombra. Centro vertical al 66,5 % de la altura. **Zonas seguras:** nada en el 20 % inferior ni en el 12 % derecho (se verifica en cada fotograma).
