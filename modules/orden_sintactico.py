import nltk
import spacy
import uuid
nltk.download('punkt_tab')



def analisis_orden_sintactico(frase, pos_inicial):
    nlp = spacy.load("es_core_news_sm")  # Modelo en español


    pos = pos_inicial
    result = []

    doc = nlp(frase)

    sujeto = [t for t in doc if t.dep_ in ("nsubj", "nsubj_pass")]
    verbo = [t for t in doc if t.dep_ == "ROOT" and t.pos_ == "VERB"]
    objeto = [t for t in doc if t.dep_ in ("obj", "iobj")]

    if sujeto and verbo and objeto:
        if not(sujeto[0].i < verbo[0].i < objeto[0].i):
            comment_id = str(uuid.uuid4())  # ID único
            start = pos
            end = pos + len(frase)
            result.append({"id": comment_id, "start": start, "end": end, "text": "Orden sintáctico incorrecto",
                           "description": "La oración no sigue el orden natural del español (sujeto + verbo + complementos)",
                           "suggestion": "Recorta la frase",
                           "type": "orden-sintáctico",
                           "original": frase,
                           "error": "orden"})

    else:
        end = pos + len(frase)

    return result

