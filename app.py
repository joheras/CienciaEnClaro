import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio

# Importamos los módulos
from modules.morfosintaxis import *
from modules.legibility import *
from modules.models import *

app = FastAPI()

@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Servir estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")


#Cuando nos pidan analizar el texto completo lo que vamos a hacer es dividir el texto en
# párrafos y hacer el análisis de cada uno de esos párrafos.
def dividir_parrafos(texto):
    return texto.split("\n")


# Nos analiza todos los índices para un párrafo dado
async def analizar_parrafo(texto, inicioParrafo):
    result = []
    total_oraciones = 0
    oraciones_largas = 0

    resultado = await morfosintaxis_paragraph(texto, inicioParrafo)

    # Contar métricas
    frases = nltk.sent_tokenize(texto, language="Spanish")
    total_oraciones = len(frases)

    for frase in frases:
        if oracion_larga(frase)[0]:
            oraciones_largas += 1

    result.extend(resultado)
    errores_por_tipo = {}
    for item in resultado:
        tipo = item["name"]
        if tipo not in errores_por_tipo:
            errores_por_tipo[tipo] = set()
        errores_por_tipo[tipo].add(item["start"]) # Para saber qué oracion es

    porcentajes = {}
    for tipo, errores in errores_por_tipo.items():
        if total_oraciones > 0:
            porcentajes[tipo] = round((len(errores) / total_oraciones) * 100, 1)
        else:
            porcentajes[tipo] = 0
    #result.extend(legibility_paragraph(texto, inicioParrafo))
    return {
        "comentarios": result,
        "stats": {
            "total_oraciones": total_oraciones,
            "porcentajes": porcentajes
        }
    }

@app.post("/analyse_paragraph")
async def analyse_paragraph(request: Request):
    """ Dado un párrafo devuelve un resumen de dicho párrafo con los índices que no cumplen las características deseadas"""
    data = await request.json()
    texto = data['parrafo']
    inicioParrafo = data['start']
    result = await analizar_parrafo(texto, inicioParrafo)
    return JSONResponse(content=result)


# Nos analiza todos los índices para todo el texto
@app.post("/analyse_text")
async def analyse_text(request: Request):
    """ Dado un texto devuelve un resumen de dicho texto con los índices que no cumplen las características deseadas"""
    data = await request.json()
    texto = data.get("text", "")

    parrafos = dividir_parrafos(texto)
    resultados = {} # Aquí voy a almacenar todos los comentarios por parrafo

    inicio = 0
    for i, parrafo in enumerate(parrafos, start=1):
        data_parrafo = await analizar_parrafo(parrafo, inicio)
        resultados[i] = {
            "comentarios": data_parrafo["comentarios"],
            "stats": data_parrafo["stats"]
        }
        inicio = inicio + len(parrafo) + 1 # +1 por el salto de línea
    return JSONResponse(content=resultados)


async def morfosintaxis_paragraph(texto, inicioParrafo):
    """ Dado un párrafo devuelve un resumen de dicho párrafo con los índices morfosintácticos que no cumplen las características deseadas"""
    result = []
    if texto != '\n' and texto!='':
        finParrafo = inicioParrafo + len(texto)
        inicioFrase = inicioParrafo

        parrafoCorto = parrafo_corto(texto)
        if parrafoCorto[0]:
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioParrafo,
                "end": finParrafo,
                "text": "Párrafo corto",
                "description": f"El párrafo es demasiado corto, debería tener mínimo dos oraciones y tiene {parrafoCorto[1]}.",
                "type": "morfosintaxis",
                "name": "parrafoCorto"
            }
            result.append(resumen)
        parrafoLargo = parrafo_largo(texto)
        if parrafoLargo[0]:
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioParrafo,
                "end": finParrafo,
                "text": "Párrafo largo",
                "description": f"El párrafo es demasiado largo, debería tener máximo cinco oraciones y tiene {parrafoLargo[1]}.",
                "type": "morfosintaxis",
                "name": "parrafoLargo"
            }
            result.append(resumen)

        frases = nltk.sent_tokenize(texto, language="spanish")

        CHUNK_SIZE = 2 # Procesamos 5 frases por vez
        for i in range(0, len(frases), CHUNK_SIZE):
            chunk = frases[i:i+CHUNK_SIZE]
            for frase in chunk:
                finFrase = inicioFrase + len(frase)
                oracionLarga = oracion_larga(frase)
                if oracionLarga[0]:
                    resumen = {
                        "id": str(uuid.uuid4()),
                        "start": inicioFrase,
                        "end": finFrase,
                        "text": "Oración larga",
                        "description": f"La oración es demasiado larga, debería tener máximo 20 palabras y tiene {oracionLarga[1]}.",
                        "type": "morfosintaxis",
                        "name": "oracionLarga"
                    }
                    result.append(resumen)
                orden = orden_incorrecto(frase)
                if orden:
                    resumen = {
                        "id": str(uuid.uuid4()),
                        "start": inicioFrase,
                        "end": finFrase,
                        "text": "Orden sintáctico incorrecto",
                        "description": f"La oración no sigue el orden sintáctico adecuado, debería seguir la estructura sujeto-verbo-complementos.",
                        "type": "morfosintaxis",
                        "name": "orden"
                    }
                    result.append(resumen)
                coordinada = oracion_coordinada(frase)
                if coordinada[0]:
                    resumen = {
                        "id": str(uuid.uuid4()),
                        "start": inicioFrase,
                        "end": finFrase,
                        "text": "Oración coordinada",
                        "description": f"Se debe evitar el abuso de oraciones coordinadas.",
                        "type": "morfosintaxis",
                        "name": "coordinada",
                    }
                    result.append(resumen)
                yuxtapuesta = oracion_yuxtapuesta(frase)
                if yuxtapuesta[0]:
                    resumen = {
                        "id": str(uuid.uuid4()),
                        "start": inicioFrase,
                        "end": finFrase,
                        "text": "Oración yuxtapuesta",
                        "description": f"Se debe evitar el abuso de oraciones yuxtapuestas.",
                        "type": "morfosintaxis",
                        "name": "yuxtapuesta"
                    }
                    result.append(resumen)

                inicioFrase = finFrase + 1  # Para seguir en la siguiente frase

    return result


async def morfosintaxis_text(request: Request):
    """ Dado un texto devuelve un resumen de dicho texto con los índices morfosintácticos que no cumplen las características deseadas"""
    data = await request.json()
    texto = data.get("text", "")

    parrafos = dividir_parrafos(texto)
    resultados = {} # Aquí voy a almacenar todos los comentarios por parrafo

    inicio = 0
    for i, parrafo in enumerate(parrafos, start=1):
        resultados[i] = morfosintaxis_paragraph(parrafo, inicio)
        inicio = inicio + len(parrafo) + 1
    return resultados

"""
def legibility_paragraph(texto, inicioParrafo):
    " Dado un párrafo devuelve un resumen de dicho párrafo con los índices de legibilidad que no cumplen las características deseadas"
    result = []
    finParrafo = inicioParrafo + len(texto)
    inicioFrase = inicioParrafo
    fernandezHuerta = indice_fernandezHuerta(texto)
    if fernandezHuerta[0]<60:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Fernández-Huerta",
            "description": fernandezHuerta[1],
            "type": "legibility",
            "name": "fernandezHuerta"
        }
        result.append(resumen)
    frases = nltk.sent_tokenize(texto, language="spanish")
    for frase in frases:
        finFrase = inicioFrase + len(frase)
        palabrasFrase = media_palabras_frases(frase)
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioFrase,
            "end": finFrase,
            "text": "Media palabras-frase",
            "description": f"El párrafo contiene una media de {palabrasFrase} palabras por frase",
            "type": "legibility",
            "name": "palabrasFrase"
        }
        result.append(resumen)
        silabasPalabra = media_silabas_palabras(frase)
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioFrase,
            "end": finFrase,
            "text": "Media sílabas-palabra",
            "description": f"El párrafo contiene una media de {silabasPalabra} sílabas por palabra",
            "type": "legibility",
            "name": "silabasPalabra"
        }
        result.append(resumen)

    return result


async def legibility_text(request: Request):
    " Dado un texto devuelve un resumen de dicho texto con los índices de legibilidad que no cumplen las características deseadas"
    data = await request.json()
    texto = data.get("text", "")

    parrafos = dividir_parrafos(texto)
    resultados = {} # Aquí voy a almacenar todos los comentarios por parrafo

    inicio = 0
    for i, parrafo in enumerate(parrafos, start=1):
        resultados[i] = legibility_paragraph(parrafo, inicio)
        inicio = inicio + len(parrafo) + 1
    return resultados
"""
@app.post("/resumen")
async def summary(request: Request):
    data = await request.json()
    data = data['text']
    caracteres = len(data)
    silabas = textstat.syllable_count(data, lang="es")
    palabras = textstat.lexicon_count(data, removepunct=True)
    frases = textstat.sentence_count(data)

    texto = "Número de caracteres: " + str(caracteres)
    texto = texto + '\n' + 'Número de sílabas: ' + str(silabas)
    texto = texto + '\n' + 'Número de palabras: ' + str(palabras)
    texto = texto + '\n' + 'Número de frases: ' + str(frases)
    texto = texto + '\n' + 'Media de caracteres por palabra: ' + str(round(caracteres / palabras, 2))
    texto = texto + '\n' + 'Media de sílabas por palabra: ' + str(round(silabas / palabras, 2))
    texto = texto + '\n' + 'Media de palabras por frase: ' + str(round(palabras / frases, 2))
    texto = texto + '\n' + "Índice de Fernández-Huerta: " + str(round(textstat.fernandez_huerta(data), 2))

    return JSONResponse(content=texto)

@app.post("/generar_sugerencia")
async def generar_sugerencia(request: Request):
    data = await request.json()
    comment = data.get("comment")
    result = obtenerSugerencia(comment)
    return JSONResponse({"sugerencia": result})

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)