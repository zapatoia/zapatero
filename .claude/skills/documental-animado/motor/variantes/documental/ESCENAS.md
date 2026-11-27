# Escenas del motor documental (referencia)

En `guion.json` cada línea es una frase; `"escena"` lleva uno de estos objetos (los campos de cada tipo).
Lo que dice «frase/phrase» aquí = una línea de `guion.json`. `step` = en qué línea de la escena aparece (0 = la primera).
Las escenas `motion` traen animaciones hechas (algunas con textos por defecto genéricos): da SIEMPRE sus textos.

```
TIPOS DE ESCENA
- title:    { "type":"title", "kicker":"TEXTO PEQUEÑO", "text":"Título grande", "sub":"opcional", "logo":true }  (logo:true = logo del tema encima)
- date:     { "type":"date", "text":"SIGLO XIV a. C.", "sub":"opcional" }
- map:      { "type":"map", "title":"opcional", "bounds":[[lonOeste,latSur],[lonEste,latNorte]], "highlight":["Panama","Colombia"],
              "points":[{"name":"Colón","lon":-79.9,"lat":9.36,"pos":"r|l|t|b","step":0}], "routes":[{"from":"Colón","to":"Balboa","step":1,"dashed":false}], "zoom":0.07 }
              (highlight usa nombres de país en inglés de Natural Earth)
- chart:    { "type":"chart", "title":"...", "data":[[2017,8.1],[2018,11.2]], "prefix":"$", "suffix":" mil M", "decimals":1,
              "marks":[{"x":2018,"label":"opcional","step":1}], "band":{"from":2019,"to":2020,"label":"Pandemia","step":0}, "source":"Fuente: ..." }
- bars:     { "type":"bars", "title":"...", "items":[{"label":"España","value":12,"highlight":true}], "suffix":" %", "source":"..." }
- stat:     { "type":"stat", "kicker":"opcional", "value":1650, "prefix":"$", "suffix":" millones", "decimals":0, "label":"Qué significa" }
- donut:    { "type":"donut", "title":"opcional", "value":55, "label":"para el creador", "rest":"45 % para YouTube" }
- list:     { "type":"list", "title":"...", "items":["uno", {"text":"dos","step":1}] }
- timeline: { "type":"timeline", "title":"...", "events":[{"date":"2005","label":"Fundación","step":0,"highlight":false}] }
- flow:     { "type":"flow", "title":"...", "nodes":[{"label":"Anunciante","sub":"paga"},{"label":"YouTube"}], "arrows":["texto flecha 1"] }
- doc:      { "type":"doc", "source":"Fuente del documento", "text":"Cita del documento", "note":"opcional" }
- quote:    { "type":"quote", "text":"Frase potente", "author":"opcional" }
- photo:    { "type":"photo", "src":"fotos/x.jpg", "style":"full|framed|archive", "move":"in|out|left|right|up|down|none",
              "focus":[0.5,0.3], "amount":0.12, "filter":"bw|sepia|warm|cold|archive", "place":"LUGAR · AÑO",
              "name":"Nombre", "role":"Cofundador", "label":"texto a mano (framed)", "credit":"opcional (si no, sale de fotos/creditos.json)" }
              (retrato vertical + "name" = foto a la izquierda y nombre grande a la derecha; fotos pequeñas = estilo archivo)
- compare:  { "type":"compare", "title":"...", "left":{"label":"CPM","value":10,"prefix":"$","decimals":0,"sub":"lo que paga el anunciante"},
              "right":{"label":"RPM","value":4,"prefix":"$","sub":"lo que ganas tú","step":1}, "highlight":"right", "vs":"vs", "note":"opcional" }
- list:     items pueden llevar "icon":"check" o "icon":"x" (✓ / ✕)
- people:   { "type":"people", "title":"Los fundadores", "items":[{"src":"fotos/a.jpg","name":"Nombre","role":"Diseño","focus":[0.5,0.3],"step":0}] }
FOTOS DE FONDO (cualquier escena): "bg":"fotos/x.jpg", "bgBright":0.4, "bgMove":"in|out|left|right", "bgFocus":[0.5,0.5]
- motion:   { "type":"motion", "anim":"<preset>", ...textos opcionales }  animación que ilustra lo que dice la voz. Presets:
              upload (subir un video falla) · growth {value,label} · scale {left,right} (balanza) · admachine · tovideo (anuncio web → video)
              monetize (¿? → $) · owned {left,right} · streams {items[]} · fans {bubbles[]} · price {left,tag} · rpmcpm {cut1,cut2,note}
              calc {lines[]} · unlock {label,rings:[[nombre,0-1]]} · payment {left,right,day} · leak (errores que cuestan) · ready {name,items[],badge}
              subscribe {name,handle,button,done,hint}  (CTA de suscripción con clic y campanita)
  Úsalas en lugar de títulos de solo texto: cada frase debe verse, no leerse.
TRANSICIONES (en la escena que entra): "transition":"fade|dip|liquid|shapes|slide|zoom|blur|wipe|flash|leak|cut"
  Por defecto: fade entre escenas y dip (fundido a negro) al empezar cada bloque. Tema: "film":true (grano, parpadeo, polvo),
  "drift":0.035 (acercamiento lento), "letterbox":true (franjas de cine).
FOTOS: van en <proyecto>/fotos/. Solo fotos con licencia libre (Wikimedia Commons, dominio público) o propias; anota autor y licencia en fotos/creditos.json
  ({"fotos/x.jpg": {"credit": "Autor · CC BY-SA 4.0"}}): el crédito sale chico abajo a la derecha.
MOTOR v2.0 · ESTILO C (por defecto; "engine":"v1" reproduce el estilo anterior)
- Tema: guion.json → "tema": "editorial" (azul, por defecto) o "club" (negro/dorado). "surfaces":["dark","light","blue","clay"] limita las superficies;
  cada escena puede pedir "surface":"light|blue|dark|clay" (clay = acento terracota/dorado). Nunca dos superficies iguales seguidas.
- Sincronía palabra por palabra: palabras.json del proyecto (lo hace voz.py; motor.py lo pasa solo).
  Con palabras, cada frase puede ser un tramo corto (2–5 palabras) y cambiar de escena cada 1.5–3 s; el texto debe coincidir con la voz.
- Tipografía cinética (estilo B): en cada frase "key":"palabra" o "keys":["uno","*dos"] (con * = serif cursiva); contexto chico + clave
  grande en acento, palabra por palabra con la voz. "cap":false la apaga (úsalo cuando la escena ya muestra ese texto: date, stat, title).
- Escenas nuevas/ampliadas: map {"from":bounds,"bounds":bounds,"flyAt","flyDur","cams":[{"at"|"step","bounds"}],"highlight":[...],"lights":[[lon,lat]...],
  "areas":[{"coords":[[lon,lat]...],"at","lossWord":"palabra","label"}],"labels":[{"text","lon","lat","word"}]} · date {"year","from","travel","chip"}
  · timeline {"events":[{"date","label"}],"travel","span":{"value","suffix"}} · stat {"ring":true,"photo":"fotos/x.jpg"} · gallery {"items":[fotos]}
  · photo {"style":"full|card","subject":[x,y,rx,ry] (sujeto 2.5D),"rings":[x,y],"date":1910} · motion "texcoco" (lago con ciudad-isla: lakeLabel, cityLabel, kicker) | "cielo" (constelaciones) · "counter":{value,from,suffix,label} en cualquier escena.
- Cualquier tiempo de elemento puede ir pegado a una palabra: "word":"cayó".
- Transiciones v2: whip | card | zoom | mask | swipe | cut (las de v1 se traducen solas).
- Mezcla v2: la hace el núcleo: guion.json → "musica" opcional; master −14 LUFS.
```
