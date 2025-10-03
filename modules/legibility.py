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

    if indice<30:
        result.append({"id": comment_id, "start": start, "end": end, "text": "Contenido poco legible",
                       "description": "Es un texto muy difícil. Un texto legible dentro de la divulgación científica debería extraer una puntuación de entre 60 y 70 (puntuación actual:  " + str(
                           indice) + ")",
                       "suggestion": "",
                       "type": "legibilidad"})
    elif indice < 50:
        result.append({"id": comment_id, "start": start, "end": end, "text": "Contenido poco legible",
                       "description": "Es un texto difícil. Un texto legible dentro de la divulgación científica debería extraer una puntuación de entre 60 y 70 (puntuación actual:  " + str(
                           indice) + ")",
                       "suggestion": "",
                       "type": "legibilidad"})
    elif indice<60:
        result.append({"id": comment_id, "start": start, "end": end, "text": "Contenido poco legible",
                   "description": "Es un texto algo difícil. Un texto legible dentro de la divulgación científica debería extraer una puntuación de entre 60 y 70 (puntuación actual:  " + str(
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
def palabra_en_txt(palabra, archivo): # Me devuelve true si la palabra está en el archivo, false si no
    with open("mazyvan/"+archivo, "r", encoding="utf-8") as f:
        contenido = f.read().splitlines()
    return palabra in contenido

def palabraComplejas(palabra, pos_inicial):
    # Lista de palabras comunes sacadas de: https://github.com/mazyvan/most-common-spanish-words/
    pos = pos_inicial
    result = []
    comment_id = str(uuid.uuid4)  # ID único
    start = pos
    end = pos + len(palabra)

    archivos = ["most-common-spanish-words.txt", "most-common-spanish-words-v2.txt", "most-common-spanish-words-v3.txt",
                "most-common-spanish-words-v4.txt", "most-common-spanish-words-v5.txt"]

    esta = False
    for archivo in archivos:
        if palabra_en_txt(palabra, archivo):
            esta = True
    if esta == False and textstat.is_difficult_word(palabra):
        result.append({"id": comment_id, "start": start, "end": end, "text": "Palabra complicada",
                       "description": "La palabra " + palabra + " es complicada.",
                       "suggestion": "",
                       "type": "legibilidad"})
    return result, end


"""
    if textstat.is_difficult_word(palabra):
        result.append({"id": comment_id, "start": start, "end": end, "text": "Palabra complicada",
                       "description": "La palabra " + palabra + " es complicada." ,
                       "suggestion": "",
                       "type": "legibilidad"})

    return result, end
"""