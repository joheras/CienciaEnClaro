import textstat
import uuid
import nltk
#nltk.download('omw-1.4')
#nltk.download('wordnet')
from nltk.corpus import wordnet as wn
from nltk.tokenize import sent_tokenize, word_tokenize
import pyphen
import textstat
from ollama import chat
from ollama import ChatResponse

textstat.set_lang(lang="es")

def fernandezHuerta(texto):
    pos = 0
    result = []
    comment_id = str(uuid.uuid4())  # ID único
    start = pos
    end = pos #+ len(texto)

    indice = textstat.fernandez_huerta(texto)
    indice = round(indice, 2)

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
    end = pos #+ len(text)


    numPal = textstat.lexicon_count(text, removepunct=True)
    numFrases = textstat.sentence_count(text)
    promedio = numPal / numFrases
    promedio = round(promedio, 2)

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
    end = pos #+ len(text)

    numPal = textstat.lexicon_count(text, removepunct=True)
    numSilabas = textstat.syllable_count(text, lang="es")
    promedio = numSilabas/numPal
    promedio = round(promedio, 2)

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
def palabrasComunes(archivos): # Me devuelve true si la palabra está en el archivo, false si no
    contenido = set()
    todas = set()

    for archivo in archivos:
        with open("mazyvan/" + archivo, "r", encoding="utf-8") as f:
            contenido.update(f.read().splitlines())
            for cont in contenido:
                todas.update(cont.split('|'))
    return todas

archivos = ["most-common-spanish-words.txt", "most-common-spanish-words-v2.txt", "most-common-spanish-words-v3.txt",
                "most-common-spanish-words-v4.txt", "most-common-spanish-words-v5.txt"]
contenido = palabrasComunes(archivos)
for con in contenido:
   con.split('|')
aparecen = set()


def palabraComplejas(frase, palabra, pos_inicial):
    # Lista de palabras comunes sacadas de: https://github.com/mazyvan/most-common-spanish-words/
    pos = pos_inicial
    result = []
    comment_id = str(uuid.uuid4)  # ID único
    start = pos
    end = pos + len(palabra)

    esta = False
    if palabra in aparecen:
        esta = True
    elif textstat.syllable_count(palabra, lang="es")<2:
        esta = True
        aparecen.add(palabra)
    elif palabra in contenido:
        esta = True
        aparecen.add(palabra)
    elif not textstat.is_difficult_word(palabra):
        esta = True
        aparecen.add(palabra)



    if esta == False:
        # sinonimos = obtenerSinonimos(palabra)
        # sinonimos_filtrados = [s for s in sinonimos if s.lower()!=palabra.lower()]
        sinonimo = obtenerSinonimo(frase, palabra)
        if sinonimo.lower() != palabra.lower():
            result.append({"id": comment_id, "start": start, "end": end, "text": "Palabra complicada",
                           "description": "La palabra " + palabra + " es complicada.",
                           "suggestion": sinonimo,
                           "type": "legibilidad"})
        else:
            result.append({"id": comment_id, "start": start, "end": end, "text": "Palabra complicada",
                           "description": "La palabra " + palabra + " es complicada.",
                           "suggestion": "",
                           "type": "legibilidad"})
    return result, end

def obtenerSinonimo(frase, palabra):
    instruccion = f"""
    En el siguiente texto: '{frase}'
    Dame un sinónimo más simple y natural en español para la palabra '{palabra}',
    manteniendo el mismo sentido.
    Devuelve solo el sinónimo, sin explicaciones.
    """

    response: ChatResponse = chat(model = "nichonauta/pepita-2-2b-it-v5", messages=[
    #response: ChatResponse = chat(model="jobautomation/OpenEuroLLM-Spanish", messages=[
        {
            'role': 'user',
            'content': instruccion,
        },
    ])
    sugerencia = response.message.content
    return sugerencia

"""
def obtenerSinonimos(palabra):
    sinonimos = set()
    for synset in wn.synsets(palabra, lang='spa'):
        for lemma in synset.lemmas('spa'):
            sinonimos.add(lemma.name().replace('_', ' '))
    return list(sinonimos)
"""


"""
    if textstat.is_difficult_word(palabra):
        result.append({"id": comment_id, "start": start, "end": end, "text": "Palabra complicada",
                       "description": "La palabra " + palabra + " es complicada." ,
                       "suggestion": "",
                       "type": "legibilidad"})

    return result, end
"""