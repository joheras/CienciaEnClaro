import textstat
import uuid
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import pyphen
import textstat

textstat.set_lang(lang="es")

def fernandezHuerta(texto):
    pos = 0
    result = []
    comment_id = str(uuid.uuid4())  # ID único
    start = pos
    end = pos + len(texto)

    indice = textstat.fernandez_huerta(texto)
    if indice<60:
        result.append({"id": comment_id, "start": start, "end": end, "text": "Contenido poco legible",
                   "description": "Un texto legible dentro de la divulgación científica debería extraer una puntuación de entre 60 y 70 (puntuación actual:  " + str(
                       indice) + ")",
                   "suggestion": "",
                   "type": "legibilidad"})
    return result


def longFrases_promedio(text):
    pos = 0
    result = []
    comment_id = str(uuid.uuid4) # ID único
    start =  pos
    end = pos + len(text)


    numPal = textstat.lexicon_count(text, removepunct=True)
    numFrases = textstat.sentence_count(text)
    promedio = numPal / numFrases

    result.append({"id": comment_id, "start": start, "end": end, "text": "Longitud promedio de frases",
                   "description": "Las oraciones deben tener menos de 30 palabras, a ser posible no más de 20. La longitud promedio de las frases actuales es de  " + str(
                       promedio),
                   "suggestion": "",
                   "type": "legibilidad"})

    return result
"""
    frases = nltk.sent_tokenize(text, language = "spanish")
    frases = [frase.strip() for frase in frases if frase.strip()] # Eliminar frases vacías
    totalPalabras = 0

    for frase in frases:
        palabras = [w for w in word_tokenize(frase, language="spanish") if w.isalpha()]
        totalPalabras += len(palabras)

    promedio = totalPalabras/len(frases) if frases else 0
    """


def silabasPalabra(text):
    pos = 0
    result = []
    comment_id = str(uuid.uuid4)  # ID único
    start = pos
    end = pos + len(text)

    numPal = textstat.lexicon_count(text, removepunct=True)
    numSilabas = textstat.syllable_count(text, lang="es")
    promedio = numSilabas/numPal

    result.append({"id": comment_id, "start": start, "end": end, "text": "Media de sílabas por palabra",
                   "description": "La media de sílabas por palabra actual es de:  " + str(
                       promedio),
                   "suggestion": "",
                   "type": "legibilidad"})
    return result

"""
a = pyphen.Pyphen(lang='es')
    palabras = [w for w in text.split() if w.isalpha()]

    silabas = sum(len(a.inserted(palabra).split("-")) for palabra in palabras)
    promedio = silabas/len(palabras) if palabras else 0
    """

def palabraComplejas(palabra, pos_inicial):
    pos = pos_inicial
    result = []
    comment_id = str(uuid.uuid4)  # ID único
    start = pos
    end = pos + len(palabra)

    if textstat.is_difficult_word(palabra):
        result.append({"id": comment_id, "start": start, "end": end, "text": "Palabra complicada",
                       "description": "La palabra " + palabra + " es complicada." ,
                       "suggestion": "",
                       "type": "legibilidad"})

    return result, end