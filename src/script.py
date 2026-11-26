# Each scene: list of (display_text, spoken_text). spoken=None -> same as display.
SCENES = [
 [("Durante putos siglos, tus putos zapatos no sabían cuál era tu pie izquierdo.",None),("Sí, como lo puto oyes.",None)],
 [("Se cree que ya nos tapábamos los putos pies hace decenas de miles de años.",None),("Pieles, cuerdas… y a correr detrás del puto mamut.",None)],
 [("Las sandalias más putamente antiguas conocidas son de corteza: unos",None),("10.000","diez mil"),("putos años. Salieron de Fort Rock, en Estados Unidos.",None)],
 [("El puto zapato de cuero más putamente antiguo es de Armenia:",None),("Areni-1,","Areni uno,"),("unos",None),("5.500","cinco mil quinientos"),("putísimos años. Mejor conservado que mis putas TN, hermano.",None)],
 [("Egipcios y romanos ya iban a la puta última: sandalias para el puto día a día y botas para putamente marchar.",None)],
 [("Y lo fuerte: el izquierdo y el derecho eran iguales. Eso no cambió hasta el",None),("siglo XIX.","siglo diecinueve."),],
 [("En",None),("1839,","mil ochocientos treinta y nueve,"),("Goodyear vulcanizó la goma. Hola, suelas de goma. Adiós, resbalones.",None)],
 [("Y en",None),("1917,","mil novecientos diecisiete,"),("Converse lanzó su zapatilla de baloncesto. El resto ya lo llevas puesto. ¡Síguenos para más!",None)],
]
def spoken_scene(s): return " ".join(sp or d for d,sp in s)
FULL = " ".join(spoken_scene(s) for s in SCENES)
if __name__=="__main__":
    print(FULL); print("chars",len(FULL),"words",len(FULL.split()))
