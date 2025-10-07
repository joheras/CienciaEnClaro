import nltk
import uuid
from ollama import chat
from ollama import ChatResponse

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

    palabras = [w for w in nltk.word_tokenize(frase, language = "spanish") if w.isalpha()]

    if (len(palabras) > 30):
        comment_id = str(uuid.uuid4())  # ID único
        start = pos
        end = pos + len(frase)
        generar = generate_prompt(frase)
        response: ChatResponse = chat(model="nichonauta/pepita-2-2b-it-v5", messages=[
            {
                'role': 'user',
                'content': generar,
            },
        ])
        sugerencia = response.message.content
        result.append({"id": comment_id, "start": start, "end": end, "text": "Frase demasiado larga",
                       "description": "Una frase debe contener menos de 30 palabras (palabras actuales: " + str(
                           len(palabras)) + ")",
                       "suggestion": sugerencia,
                       "type": "longitud"})
    elif (len(palabras)>20):
        comment_id = str(uuid.uuid4())  # ID único
        start = pos
        end = pos + len(frase)
        generar = generate_prompt(frase)
        #response: ChatResponse = chat(model="gemma3:27b", messages=[
        #response: ChatResponse = chat(model="llama2", messages=[
        #response: ChatResponse = chat(model="mistral", messages=[
        #response: ChatResponse = chat(model="jobautomation/OpenEuroLLM-Spanish", messages=[
        response: ChatResponse = chat(model="nichonauta/pepita-2-2b-it-v5", messages=[
            {
                'role': 'user',
                'content': generar,
            },
        ])
        sugerencia = response.message.content
        result.append({"id": comment_id, "start": start, "end": end, "text": "Frase demasiado larga",
                       "description": "Es recomendable que una frase contenga menos de 20 palabras (palabras actuales: " + str(
                           len(palabras)) + ")",
                       "suggestion": sugerencia,
                       "type": "longitud"})
    else:
        end = pos + len(frase)


    return result, end

def generate_prompt(frase): # Función para, dada una frase, generar una versión más corta de esta por medio de LLMs
    instruction = f"""Eres un experto en recortar las frases manteniendo el significado en español. 
    Una frase debería tener siempre menos de 20 palabras, o 30 como mucho.
    Para mantener el significado completo, puedes generar más de una frase si lo necesitas.
    Añade únicamente la frase recortada, nada más. No des varias opciones.
    Lo que devuelvas tiene que estar en castellano y debe ser únicamente la frase recortada.
    Frase a recortar: {frase}
    """
    return instruction