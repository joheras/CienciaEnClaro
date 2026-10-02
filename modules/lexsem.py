from modules.auxiliares_lexsem import *
from modules.auxiliares_morfosintaxis import *
import spacy

nlp = spacy.load("es_core_news_sm")

def lematizar(palabra):
    return nlp(palabra)[0].lemma_

listaExtranjerismos = listExtranjerismos()
listaBaul = listBaul()

def extranjerismos(palabra):
    """
    Dada una palabra, devuelve True si se considera extranjerismo y False si no.
    Se consideran extranjerismos aquellas palabras que devuelve la función "listExtranjerismos()"
    """
    pal = lematizar(palabra)
    if pal in listaExtranjerismos:
        return True
    else:
        return False

def detectar_palabras_baul(texto, pal):
    tokens = tokenizar(texto)
    palabra = lematizar(pal)
    if palabra in listaBaul:
        match = re.search(rf"\b{re.escape(pal)}\b", texto, re.IGNORECASE)
        if match:
            start = match.start()
            end = match.end()
            # heurística: solo si NO está matizada
            if not tiene_complemento(texto, end):
                return True
    return False

#def parrafoComplejo(texto):
#    puntuacion = 0
#    doc = nlp(texto)
#    oraciones = [sent.text for sent in doc.sents]
#    for oracion in oraciones:
#        if coordinada(oracion, 0):
#            puntuacion +=1
#        #if filtrarInciso(oracion):
#        #    puntuacion +=1
#        if relativo(oracion):
#            puntuacion +=1

#    for token in doc:
#        if token.is_alpha and nominalizada(token.text):
#            puntuacion += 1

#    return puntuacion >= 5

def palabraLarga(palabra):
    return largas(palabra)

def latinism(palabra):
    return latin(palabra)

def tecnisimos(palabra):
    return tecnico(palabra)

def sigla(texto):
    siglas = []
    palabras = re.findall(
        r'\b[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+(?:-[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+)*\b',
        texto
    )
    for palabra in palabras:
        letras = ''.join(c for c in palabra if c.isalpha())

        if (
                len(letras) >= 2
                and letras.isupper()
        ):
            siglas.append(palabra)

    siglas_con_puntos = re.findall(
        r'\b(?:[A-ZÁÉÍÓÚÜÑ]\.\s*){2,}',
        texto
    )

    for sigla in siglas_con_puntos:
        sigla = sigla.strip()
        if sigla not in siglas:
            siglas.append(sigla)

    return siglas