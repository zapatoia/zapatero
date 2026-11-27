# ¿Y si cayeras por un agujero que atraviesa la Tierra? (segundo a segundo)

Saltas en Madrid y sales en Nueva Zelanda: 38 minutos de caída sin aire. Pasas la mina más honda, el pozo de Kola,
el manto, el núcleo de hierro líquido y el centro a casi 36.000 km/h… hasta que entra el aire.

## Cómo se calculó la caída
Túnel recto Madrid → antípoda, sin aire ni rozamiento, con la densidad real de la Tierra por capas (modelo PREM de
Dziewonski y Anderson, 1981). Integración numérica propia (`escenas_tierra.py → estado()`): centro a los 19 min 5 s
(35.700 km/h) y salida a los 38 min 11 s, igual que el resultado publicado por Klotz (2015).
Tiempos usados: 10 s → 0,5 km y 354 km/h · 28 s → 3,9 km y 990 km/h · 50 s → 12 km · 1 min 30 s → 40 km (fin de la
corteza continental) · 5 min → 444 km · 12 min 43 s → 2.890 km (núcleo) · 17 min → 5.140 km (núcleo interno) ·
19 min 5 s → centro · 38 min 11 s → Nueva Zelanda. Periodo de ida y vuelta: 76 min («cada hora y cuarto»).
Con aire: velocidad terminal de un paracaidista ≈ 200 km/h → solo los 6.371 km al centro llevan más de 30 h (y el aire
más denso en el fondo frena aún más); el rozamiento amortigua el vaivén y acabas parado en el centro.

## Fuentes
- Klotz (2015), «The gravity tunnel in a non-uniform Earth», American Journal of Physics: 38 min 11 s. https://arxiv.org/abs/1308.1342 · https://phys.org/news/2015-03-fall-hole-earth.html
- Gravity train (uniforme ≈ 42 min, periodo, recorrido): https://en.wikipedia.org/wiki/Gravity_train
- Antípoda de Madrid ≈ 40,4° S 176,3° E, junto a Weber (Nueva Zelanda): https://en.wikipedia.org/wiki/Weber,_New_Zealand · https://www.geodatos.net/en/antipodes/spain/madrid
- Pozo superprofundo de Kola: 12.262 m (1989), empezado en 1970, unos 180 °C en el fondo: https://en.wikipedia.org/wiki/Kola_Superdeep_Borehole · https://www.guinnessworldrecords.com/world-records/66177-deepest-penetration-into-the-earths-crust
- Mina de Mponeng (Sudáfrica), la más profunda, unos 4 km: https://en.wikipedia.org/wiki/Mponeng_Gold_Mine · https://www.guinnessworldrecords.com/world-records/66169-deepest-mine
- Núcleo interno: radio ≈ 1.220 km (Plutón ≈ 1.190 km), ≈ 5.700 K, como la superficie del Sol: https://en.wikipedia.org/wiki/Earth%27s_inner_core · https://www.smithsonianmag.com/smart-news/the-center-of-the-earth-is-as-hot-as-the-sun-43631207
- Núcleo externo de hierro líquido y geodinamo (campo magnético): https://en.wikipedia.org/wiki/Earth%27s_outer_core
- Gravedad máxima en el límite manto–núcleo (≈ 10,7 m/s², +9 %), modelo PREM: https://en.wikipedia.org/wiki/Gravity_of_Earth#Depth
- Manto: roca sólida que fluye muy despacio, más de 1.000 °C: https://en.wikipedia.org/wiki/Earth%27s_mantle
- Corteza continental ≈ 30–50 km; en proporción, más fina que la piel de una manzana: https://en.wikipedia.org/wiki/Continental_crust
- Nueva Zelanda: 23,6 millones de ovejas y 5,3 millones de personas (Stats NZ, 2024): https://www.ctvnews.ca/world/article/yes-new-zealand-still-has-more-sheep-than-people-but-humans-are-catching-up/
- Velocidad terminal de un paracaidista ≈ 200 km/h: https://en.wikipedia.org/wiki/Terminal_velocity
