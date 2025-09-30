import textstat
import uuid
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

"""
def longFrases_promedio(text):
    parrafos = text.split('\n') # Partimos la frase e

    pos = 0
    result = []
    for parrafo in parrafos:
"""