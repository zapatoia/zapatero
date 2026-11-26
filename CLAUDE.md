# Estudio de reels — el zapato que explica cosas

Estudio reutilizable para producir reels verticales. El narrador es un ZAPATO DE VESTIR (oxford) que
habla: sin nombre, sin marca. NO es una cuenta sobre zapatos: el zapato explica cosas random.
Todos los vídeos tienen exactamente el mismo personaje y estilo. La calidad es lo más importante.

## Pedir un vídeo nuevo (flujo de trabajo)
1. El usuario da un tema. Escribe el guion en `scripts/NN-tema.json` (formato abajo).
2. `python make_video.py scripts/NN-tema.json --check` → reglas, nº de palabras, caracteres y créditos.
3. `python make_video.py scripts/NN-tema.json --dry --contact` → storyboard sin gastar créditos
   (`build/<slug>_dry_contact.png`); revísalo abriendo la imagen.
4. **Muestra el guion al usuario y espera su OK.** Dile caracteres y coste estimado en créditos.
5. `python make_video.py scripts/NN-tema.json --yes` → voz (una sola toma, queda en caché) + render.
6. `python make_video.py scripts/NN-tema.json --contact` → revisa fotogramas clave (texto cortado,
   boca desincronizada, solapamientos, escenas aburridas). Corrige y vuelve a renderizar (la voz no se repite).
7. Sube el MP4 a `videos/` y haz commit. Informa del tiempo de render.

Instalación en un entorno nuevo: `bash setup.sh` (instala `libegl1`, skia-python, numpy, pillow, requests).

## Voz (ElevenLabs)
- Clave en la variable de entorno `ELEVENLABS_API_KEY`. Nunca guardarla en archivos ni imprimirla.
- Voz **Tony**, voice_id `851ejYcv2BoNPjrkw93G`. Úsala SIEMPRE. Si falla o suena mal en español,
  avisa al usuario y NO cambies de voz por tu cuenta.
- Modelo `eleven_v3` (el más expresivo, probado con esta voz), `language_code: es`, stability 0.5,
  endpoint `/with-timestamps`. Configuración en `config/voice.json`. Coste ≈ 1 crédito/carácter.
- Los timestamps de v3 son aproximados: `refine_alignment` los corrige con DTW contra el audio.
- Una toma por vídeo: el audio queda en `build/voice_cache/` (clave = texto + ajustes).
- Antes de generar, dile al usuario los caracteres y el coste estimado en créditos.
- Escribe números, siglas y cifras en forma hablada: `{82 %|ochenta y dos por ciento}`,
  `{CNMV|ce ene eme uve}`, `{CFDs|ce efe des}`, `{UE|u e}`, `{DAC8|dac ocho}`.

## Guiones — reglas
- Español de España, tono de colega, directo, humor seco y algo de mala leche simpática; frases cortas.
- 85–115 palabras (30–45 s). Ritmo rápido, sin alargarse (~650-700 caracteres hablados ≈ 38-40 s).
- Estructura: hook de máximo 3 s que haga pensar «esto me importa» → bucle abierto a mitad →
  dato final concreto y útil → coletilla.
- **Coletilla del zapato (siempre la misma): «Pisa con cabeza.»**
  (alternativas descartadas: «Te lo ha dicho un zapato. Tú verás.» / «Pies en el suelo, cartera en el bolsillo.»)
- Que suene a zapato narrando, como máximo UN chiste de zapatos por vídeo (la coletilla no cuenta).
- Prohibido: «en el mundo actual», «descubre cómo», «sin más dilación», «es importante destacar»,
  «revolucionario», «desbloquea», «te voy a contar», «en este vídeo», frases de relleno, emojis.
  Nada de promesas de dinero fácil, rentabilidades garantizadas ni «hazte rico». No recomendar
  brokers, criptos ni activos concretos.
- Cifras: solo de datos verificados. Si añades otra, apúntala en `facts_to_verify.md` con tu nivel
  de confianza. Si dudas, suaviza con «se cree que».
- Los temas financieros acaban con el aviso en pantalla «Información, no consejo financiero.» (automático).

## Formato del guion (`scripts/*.json`)
```json
{
  "slug": "04-tema", "title": "…", "catchphrase": "Pisa con cabeza", "seed": 44,
  "beats": [
    {"text": "Frase con *énfasis* y {82 %|ochenta y dos por ciento}.",
     "scene": {"type": "shoe", "emotion": "serious", "arms": "raise",
               "accent": "orange", "accent2": "yellow",
               "prop": {"kind": "icon", "name": "phone", "badge": "excl", "at": "palabra"}}},
    {"text": "Siguiente frase…", "scene": {"continue": true}}
  ]
}
```
- `*palabra*` → énfasis (subtítulo amarillo, golpe de cámara, cejas). `{mostrado|hablado}` → subtítulo ≠ voz.
- `"at": "palabra"` sincroniza una aparición con la palabra dicha dentro del beat.
- `{"continue": true}` alarga la escena anterior con este beat.
- Un beat ≈ 2–4 s. Alterna escenas del zapato con infografías. Dos acentos por escena.
- Escenas (`studio/scenes.py`): `shoe` (prop: `icon`, `icons`, `sign`, `bubble`, `stamp`), `big_number`,
  `people`, `bars`, `lever`, `updown`, `warning`, `timeline`, `checklist` (`numbers|flags|checks`),
  `flow`, `network`, `threshold`, `search`, `stamp`, `outro`.
- Emociones: neutral, happy, skeptic, worried, serious, surprised, smug. Brazos: point, open, raise, none.
- Iconos: bank, calendar, cash, chart, crown, doc, exchange, eye, gift, globe, hourglass, lock,
  magnifier, megaphone, phone, shield, wallet. Badges: check, cross, excl, clock o un carácter.

## Estilo
Ver `STYLE.md` (resumen: fondo #0E1A2B con cuadrícula sutil, trazo crema #F3EBDD grueso y redondeado,
colores planos, acentos naranja #FF7A1A / amarillo #FFC93C, a veces menta #4FD1A5 / rojo #FF4D4D;
estética de tarjeta de seguridad de avión). Subtítulos grandes palabra a palabra; nada en el 20 % inferior
ni en el 12 % derecho. Efectos de sonido generados por código, sin música de terceros.

## Arquitectura
- `make_video.py` — comando único.
- `studio/style.py` — paleta, trazos, tipografía, easing, fondo, pictogramas.
- `studio/shoe.py` — rig del zapato + `ShoeAnimator` (determinista, renderizable en paralelo).
- `studio/timeline.py` — sintaxis del guion, tiempos de palabras, refinado DTW, visemas, envolvente.
- `studio/scenes.py` — escenas. `studio/captions.py` — subtítulos y aviso.
- `studio/sfx.py` — efectos sintetizados, mezcla, loudnorm. `studio/voice.py` — ElevenLabs + caché.
- `studio/render.py` — cámara, transiciones, eventos del personaje, render paralelo (4 procesos → ffmpeg).
- Render: skia-python (motor de Chrome) → frames RGBA → ffmpeg libx264 CRF 17 → concat + AAC 192k.

## Reglas de git
- Trabaja en la rama indicada por la sesión. No subas `build/` (caché y temporales; está en .gitignore).
