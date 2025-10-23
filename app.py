import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from modules.longitud import analisis_longitud_frase, sugerenciaFrase
from modules.longitud import analisis_longitud_parrafo
from modules.orden_sintactico import analisis_orden_sintactico
from modules.legibility import fernandezHuerta, longFrases_promedio, silabasPalabra, obtenerSinonimo, palabraComplejas
import nltk
import textstat

import time

app = FastAPI()

# Servir estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/analyze")
async def analyze(request: Request):
    data = await request.json()
    print(data)
    text = data.get("text", "")

    # Ejemplo: contar palabras
    word_count = len(text.split())

    return JSONResponse({"result": f"El texto tiene {word_count} palabras."})

@app.post("/add-hola")
async def add_hola(request: Request):
    data = await request.json()
    text = data.get("text", "")
    modified_text = "Hola desde FastAPI " + text
    return JSONResponse({"modified_text": modified_text})

@app.post("/analyse_text")
async def analyse_text(request: Request):
    """
    Añade un comentario a la primera línea del texto y devuelve:
    - text: el texto original
    - comment_text: el comentario
    - comment_id: un identificador único
    """

    inicio = time.time()

    data = await request.json()
    text = data.get("text", "")

    # 1. Análisis a nivel de texto
    # 1.1 Fernández-Huerta
    #result = fernandezHuerta(text)
    # 1.2 longitud promedio de frases
    #result.extend(longFrases_promedio(text))
    # 1.3 promedio de sílabas por palabra
    #result.extend(silabasPalabra(text))
    result = []
    # 2. Análisis a nivel de párrafo
    parrafos = text.split("\n")
    pos = 0 # Posición de los párrafos
    for parrafo in parrafos:
        pos2 = pos
        # 2.1 Longitud de párrafos
        res_parrafo, pos = analisis_longitud_parrafo(parrafo, pos)
        result.extend(res_parrafo)

        # 3. Análisis a nivel de frase
        frases = nltk.sent_tokenize(parrafo, language = "spanish")
        for frase in frases:
            posFrases = pos2
            # 3.1 Longitud de frases
            res_frase, pos2 = analisis_longitud_frase(frase, posFrases)
            result.extend(res_frase)
            pos2 = pos2 + 1

            # 3.2 Orden sintáctico
            res_orden_sintactico = analisis_orden_sintactico(frase, posFrases)
            result.extend(res_orden_sintactico)


            # 4. Análisis a nivel de palabra
            palabras = [w for w in nltk.word_tokenize(frase, language="spanish") if w.isalpha()]
            posPalabras = posFrases
            while not text[posPalabras:posPalabras + 1].isalpha():
                posPalabras = posPalabras + 1  # para contar uno por cada caracter no alfanumérico

            for pal in palabras:
                while not text[posPalabras:posPalabras+1].isalpha():
                    posPalabras = posPalabras + 1 # para contar uno por cada caracter no alfanumérico

                res_palabra, posPalabras = palabraComplejas(frase, pal, posPalabras)
                result.extend(res_palabra)




    final = time.time()
    print(final-inicio)
    return JSONResponse(
        content = result

    #     {
    #     "id": comment_id,
    #     "start": start,
    #     "end": end,
    #     "text": "comentario fastapi",
    #     "suggestion":"prueba",
    #     "original": texto marcado
    # }
    )

@app.post("/generar_sugerencia")
async def generar_sugerencia(request: Request):
    data = await request.json()
    if data['comment']['error'] == "longFrase":
        result = sugerenciaFrase(data['comment'])
    elif data['comment']['error'] == 'sinonimo':
        result = obtenerSinonimo(data['comment']['original'][0], data['comment']['original'][1])
    return JSONResponse({"sugerencia": result})

@app.post("/resumen")
async def resumen(request: Request):
    data = await request.json()
    data = data['text']
    caracteres = len(data)
    silabas = textstat.syllable_count(data, lang="es")
    palabras = textstat.lexicon_count(data, removepunct=True)
    frases = textstat.sentence_count(data)


    texto = "Número de caracteres: " + str(caracteres)
    texto = texto + '\n' + 'Número de sílabas: ' + str(silabas)
    texto = texto + '\n' + 'Número de palabras: '+ str(palabras)
    texto = texto + '\n' + 'Número de frases: ' + str(frases)
    texto = texto + '\n' + 'Media de caracteres por palabra: ' + str(round(caracteres/palabras, 2))
    texto = texto + '\n' + 'Media de sílabas por palabra: ' + str(round(silabas/palabras, 2))
    texto = texto + '\n' + 'Media de palabras por frase: ' + str(round(palabras/frases, 2))
    texto = texto + '\n' + "Índice de Fernández-Huerta: " + str(round(textstat.fernandez_huerta(data), 2))

    return JSONResponse(
        content = texto)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
