import nltk
import uuid

def analisis_longitud_parrafo(parrafo, pos_inicial):

    pos = pos_inicial
    result = []


    if len(parrafo) == 0:
        pos = pos + 2
        return result, pos

    else:
        frases = nltk.sent_tokenize(parrafo)

        if(len(frases) == 1):
            comment_id = str(uuid.uuid4())  # ID único
            start = pos
            end = pos + len(parrafo)
            result.append({"id": comment_id, "start": start, "end": end, "text": "Parrafo demasiado corto",
                           "description": "Un párrafo debería contener entre 2 y 5 frases", "suggestion": "",
                           "type": "longitud"})

        elif(len(frases) > 5):
            comment_id = str(uuid.uuid4())  # ID único
            start = pos
            end = pos + len(parrafo)
            result.append({"id": comment_id, "start": start, "end": end, "text": "Parrafo demasiado largo",
                           "description": "Un párrafo debería contener entre 2 y 5 frases", "suggestion": "",
                           "type": "longitud"})

        else:
            end = pos + len(parrafo)
    return result, end

def analisis_longitud_frase(frase, pos_inicial):
    result = []
    pos = pos_inicial
    palabras = [w for w in nltk.word_tokenize(frase) if w.isalpha()]
    if (len(palabras) > 20):
        comment_id = str(uuid.uuid4())  # ID único
        start = pos
        end = pos + len(frase)
        result.append({"id": comment_id, "start": start, "end": end, "text": "Frase demasiado larga",
                       "description": "Una frase debería contener menos de 20 palabras (palabras actuales: " + str(
                           len(palabras)) + ")",
                       "suggestion": "Recorta la frase",
                       "type": "longitud"})
    else:
        end = pos + len(frase)

    return result, end
