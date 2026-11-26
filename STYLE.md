# STYLE — El zapato que explica cosas

Referencia: dibujos de tarjetas de seguridad de avión, minimalistas, con identidad marcada, en versión oscura.
El código que aplica este estilo está en `studio/style.py` (paleta, trazos, easing, pictogramas),
`studio/shoe.py` (personaje) y `studio/scenes.py` (escenas). Si cambias algo aquí, cámbialo allí.

## Formato
- 1080x1920, 30 fps, MP4 (H.264 + AAC), audio normalizado a -14 LUFS (pico -1,5 dBTP).
- Zonas seguras: nada en el 20 % inferior (y > 1536) ni en el 12 % derecho (x > 950).
  Centro óptico del área segura: x = 510. Contenido en y 250–1200; subtítulos centrados en y ≈ 1370.

## Paleta (colores planos, sin degradados)
| Uso | Color |
|---|---|
| Fondo azul noche | `#0E1A2B` (+ cuadrícula crema al 4,5 % y cruces al 9 %, con parallax) |
| Trazo y texto | crema `#F3EBDD` |
| Acentos (máx. 2 por escena) | naranja `#FF7A1A`, amarillo `#FFC93C`; a veces menta `#4FD1A5` o rojo aviso `#FF4D4D` |
| Paneles | `#16263D` (tarjetas), sombra plana `#0A1422` |
| Zapato | cuero `#8A4B2A`, suela/sombra `#5E2F18`, lengüeta `#B7774C`, brillo `#E9C9A4` |
| Cara | ojos `#FFFDF6`, pupilas/boca `#08111D`, lengua `#E2574C` |

## Trazo y formas
- Trazo uniforme, grueso y redondeado: 11 px (7 px detalle), extremos y uniones redondos.
- Formas geométricas simples, esquinas redondeadas (radio 22–34 px).
- Lenguaje: pictogramas de línea, flechas con punta redonda, números grandes en círculos,
  triángulos de aviso, recuadros numerados, barras y porcentajes animados, siluetas de personas sin
  rasgos, objetos reducidos a lo esencial (móvil, banco, documento, lupa, cartera, reloj de arena…).

## Tipografía
- Inter Display Black para cifras, titulares y subtítulos (mayúsculas). Bold/SemiBold para textos secundarios.

## Personaje (el narrador)
- Zapato oxford de cuero, de perfil, con la puntera a la derecha. Sin nombre, sin marca.
- Contorno crema, relleno marrón cálido, brillo plano claro en puntera y talón, cordones con lazada,
  lengüeta que asoma, pespunte discontinuo en la suela.
- Ojos grandes redondos blancos con pupilas (los dos visibles, solapados), cejas de dos trazos
  expresivas, boca grande en la puntera con lengua visible al hablar.
- Sin piernas: salta sobre la suela. Brazos finos crema con manitas simples que salen de detrás
  del cuerpo (puntera y talón), aparecen y desaparecen.
- Rig: squash & stretch, inclinaciones, parpadeo cada 2–4 s, 5 bocas (X reposo, M labios
  apretados, E ancha con dientes, A abierta con lengua, O redonda), 3 poses de brazos
  (`point`, `open`, `raise`) + `none`, 7 emociones (neutral, happy, skeptic, worried, serious,
  surprised, smug), respiración y movimiento secundario en lengüeta y cordones.
- Dos tamaños: protagonista (escena `shoe`, escala 1,06) y mini (esquina inferior izquierda de las
  infografías, escala 0,46, señalando el contenido).

## Animación
- Curvas: easeOutBack para entradas, easeInOut para movimientos, anticipación y rebote.
- Nada estático más de 1,5 s; cambio visual cada 2–3 s.
- Cámara: zoom lento por escena (+4 %), golpe de zoom en palabras enfatizadas, deriva suave,
  parallax en el fondo. Transiciones: deslizamiento, zoom o subida (con whoosh); entre dos escenas
  del zapato, el zapato da un saltito y cambia el atrezo.
- Alternar escenas del zapato e infografías.

## Subtítulos
- Grandes (96 px, mínimo 68), centrados, en mayúsculas, palabra a palabra.
- Palabra actual en naranja (amarillo si está enfatizada), resto crema, contorno azul noche de 22 px.
- Bloques de ≤ 3 palabras / ≤ 16 caracteres, cortan en pausas.
- Último segundo: «Información, no consejo financiero.» en pequeño.

## Sonido
- Voz: ElevenLabs, Tony (ver `config/voice.json`).
- Efectos generados por código a volumen bajo: whoosh, pop, ding, tick, thud, sello. Sin música de terceros.
