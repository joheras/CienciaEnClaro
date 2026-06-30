import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio

import dspy

# Importamos los módulos
from modules.morfosintaxis import *
from modules.lexsem import *
from modules.legibility import *
from modules.models import *
from modules.pragdisc import *
from modules.observaciones_llm import *



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
async def analizar_parrafo(texto, inicioParrafo, texto_completo=None):
    result = []
    total_oraciones = 0
    oraciones_largas = 0

    resultado_morf = await morfosintaxis_paragraph(texto, inicioParrafo)
    resultado_lexsem = await lexsem_paragraph(texto, inicioParrafo)
    resultado_pragdis = await pragdisc_paragraph(texto, inicioParrafo)

    # Contar métricas
    frases = nltk.sent_tokenize(texto, language="spanish")
    total_oraciones = len(frases)

    for frase in frases:
        if oracion_larga(frase)[0]:
            oraciones_largas += 1

    result.extend(resultado_morf)
    result.extend(resultado_lexsem)
    result.extend(resultado_pragdis)
    errores_por_tipo = {}
    for item in resultado_morf:
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

@app.post("/analyse_document")
async def analyse_document(request: Request):
    data = await request.json()
    texto = data['texto']
    comentarios = await globales(texto)
    return JSONResponse(content={
        "comentarios_globales": comentarios
    })

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
    resultados["global"] = {
        #"comentarios": await stadistics_text(texto),
        "comentarios": await globales(texto),
    "stats": ""}
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
                "text": "Párrafo-oración",
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
        eliptico = sujeto_eliptico(texto)
        if eliptico:
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioParrafo,
                "end": finParrafo,
                "text": "Sujeto elíptico reiterado",
                "description": f"El párrafo contiene varias oraciones seguidas con sujeto elíptico.",
                "type": "morfosintaxis",
                "name": "eliptico"
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
                        "text": "Exceso de coordinaciones",
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
                        "text": "Exceso de yuxtaposiciones",
                        "description": f"Se debe evitar el abuso de oraciones yuxtapuestas.",
                        "type": "morfosintaxis",
                        "name": "yuxtapuesta"
                    }
                    result.append(resumen)

                tieneInciso = tiene_inciso(frase)
                if tieneInciso:
                    resumen = {
                        "id": str(uuid.uuid4()),
                        "start": inicioFrase,
                        "end": finFrase,
                        "text": "Uso de incisos o aclaraciones",
                        "description": f"Se debe evitar el abuso de incisos.",
                        "type": "morfosintaxis",
                        "name": "inciso"
                    }
                    #result.append(resumen)

                if falta_concordancia(frase):
                    resumen = {
                        "id": str(uuid.uuid4()),
                        "start": inicioFrase,
                        "end": finFrase,
                        "text": "Falta de concordancia",
                        "description": f"No debe haber faltas de concordancia.",
                        "type": "morfosintaxis",
                        "name": "concordancia"
                    }
                    #result.append(resumen)

                relativoLejos = relativo_lejano(frase)
                if relativoLejos:
                    resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioFrase,
                    "end": finFrase,
                    "text": "Oración de relativo compleja",
                    "description": f"Se debe evitar el uso de relativos complejos.",
                    "type": "morfosintaxis",
                    "name": "relativo"
                    }
                    result.append(resumen)

                pasiva = voz_pasiva(frase)
                if pasiva:
                    resumen = {
                        "id": str(uuid.uuid4()),
                        "start": inicioFrase,
                        "end": finFrase,
                        "text": "Uso de voz pasiva",
                        "description": f"Se debe evitar el abuso de oraciones pasivas.",
                        "type": "morfosintaxis",
                        "name": "pasiva"
                    }
                    result.append(resumen)

                noConjugados = verbos_no_conjugados(frase)
                if noConjugados:
                    resumen = {
                        "id": str(uuid.uuid4()),
                        "start": inicioFrase,
                        "end": finFrase,
                        "text": "Uso de formas no personales",
                        "description": f"Se debe evitar el abuso de formas no personales.",
                        "type": "morfosintaxis",
                        "name": "nopersonal"
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

async def lexsem_paragraph(texto, inicioParrafo):
    """ Dado un párrafo devuelve un resumen de dicho párrafo con los índices léxico-semánticos que no cumplen las características deseadas"""
    result = []
    finParrafo = inicioParrafo + len(texto)
    if parrafoComplejo(texto):
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Párrafo complejo",
            "description": f"Se deben evitar párrafos demasiado complejos.",
            "type": "léxico-semántico",
            "name": "parrafoComplejo"
        }
        result.append(resumen)
    if texto != '\n' and texto!='':
        for match in re.finditer(r'\w+', texto, re.UNICODE):
            palabra = match.group()
            inicioPalabra = inicioParrafo + match.start()
            finPalabra = inicioParrafo + match.end()

            es_extranjerismo = extranjerismos(palabra)

            if es_extranjerismo:
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioPalabra,
                    "end": finPalabra,
                    "text": "Extranjerismo",
                    "description": f"Se debe evitar el abuso de extranjerismos.",
                    "type": "léxico-semántico",
                    "name": "extranjerismo"
                }
                result.append(resumen)

            es_baul = detectar_palabras_baul(texto, palabra)
            if es_baul:
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioPalabra,
                    "end": finPalabra,
                    "text": "Baul",
                    "description": f"Se debe evitar el abuso de palabra baúl.",
                    "type": "léxico-semántico",
                    "name": "baul"
                }
                result.append(resumen)
            if palabraLarga(palabra):
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioPalabra,
                    "end": finPalabra,
                    "text": "Revisar uso de palabras largas o derivados",
                    "description": f"Se debe evitar el uso de palabras muy largas.",
                    "type": "léxico-semántico",
                    "name": "largas"
                }
                result.append(resumen)
            if latinism(palabra):
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioPalabra,
                    "end": finPalabra,
                    "text": "Latinismos",
                    "description": f"Se debe evitar el uso de latinismos.",
                    "type": "léxico-semántico",
                    "name": "latinismo"
                }
                result.append(resumen)
            if tecnisimos(palabra):
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioPalabra,
                    "end": finPalabra,
                    "text": "Uso de tecnicismos",
                    "description": f"Se debe evitar el uso de tecnicismos.",
                    "type": "léxico-semántico",
                    "name": "tecnicismo"
                }
                result.append(resumen)

    return result

async def lexsem_text(request: Request):
    """ Dado un texto devuelve un resumen de dicho texto con los índices léxico-semánticos que no cumplen las características deseadas"""
    data = await request.json()
    texto = data.get("text", "")

    parrafos = dividir_parrafos(texto)
    resultados = {} # Aquí voy a almacenar todos los comentarios por parrafo

    inicio = 0
    for i, parrafo in enumerate(parrafos, start=1):
        resultados[i] = lexsem_paragraph(parrafo, inicio)
        inicio = inicio + len(parrafo) + 1
    return resultados


async def pragdisc_paragraph(texto, inicioParrafo):
    """ Dado un párrafo devuelve un resumen de dicho párrafo con los índices pragmático-discursivos que no cumplen las características deseadas"""
    result = []
    finParrafo = inicioParrafo + len(texto)
    frases = nltk.sent_tokenize(texto, language="spanish")
    inicioFrase = inicioParrafo

    CHUNK_SIZE = 2  # Procesamos 5 frases por vez
    for i in range(0, len(frases), CHUNK_SIZE):
        chunk = frases[i:i + CHUNK_SIZE]
        for frase in chunk:
            finFrase = inicioFrase + len(frase)
            cone = falta_conectores(frase)
            if cone:
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioFrase,
                    "end": finFrase,
                    "text": "Ausencia de conectores",
                    "description": f"Se debe incentivar el uso de conectores.",
                    "type": "pragmático-discursivo",
                    "name": "conector"
                }
                result.append(resumen)

            if conectores_repe(frase):
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioFrase,
                    "end": finFrase,
                    "text": "Repetición de conector",
                    "description": f"Se debe incentivar el uso de conectores variados.",
                    "type": "pragmático-discursivo",
                    "name": "conectorRepe"
                }
                result.append(resumen)

            puntuacion = conectores_punt(frase)
            if puntuacion[0]:
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioFrase + puntuacion[1],
                    "end": inicioFrase + puntuacion[1]+len(puntuacion[2]),
                    "text": "Revisar la puntuación de conector",
                    "description": f"Los conectores deben ir con buena puntuación.",
                    "type": "pragmático-discursivo",
                    "name": "conectoresPunt"
                }
                result.append(resumen)
            inicioFrase = finFrase + 1

    return result

async def pragdisc_text(request: Request):
    """ Dado un texto devuelve un resumen de dicho texto con los índices pragmático-discursivos que no cumplen las características deseadas"""
    data = await request.json()
    texto = data.get("text", "")

    parrafos = dividir_parrafos(texto)
    resultados = {} # Aquí voy a almacenar todos los comentarios por parrafo

    inicio = 0
    for i, parrafo in enumerate(parrafos, start=1):
        resultados[i] = pragdisc_paragraph(parrafo, inicio)
        inicio = inicio + len(parrafo) + 1
    return resultados

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
            "text": "Incumplimiento de umbrales de legibilidad",
            "description": fernandezHuerta[1],
            "type": "legibility",
            "name": "fernandezHuerta"
        }
        result.append(resumen)
        """
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
        """

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


async def stadistics_paragraph(texto, inicioParrafo):
    # Dado un párrafo devuelve un resumen de dicho párrafo con los índices estadísticos
    result = []
    finParrafo = inicioParrafo + len(texto)

    caracteres = len(texto)
    resumen = {
        "id": str(uuid.uuid4()),
        "start": inicioParrafo,
        "end": finParrafo,
        "text": "Número de caracteres",
        "description": f"El texto tiene {caracteres} caracteres.",
        "type": "estadistica",
        "name": "caracteres"
    }
    result.append(resumen)
    silabas = textstat.syllable_count(texto, lang="es")
    resumen = {
        "id": str(uuid.uuid4()),
        "start": inicioParrafo,
        "end": finParrafo,
        "text": "Número de sílabas",
        "description": f"El texto tiene {silabas} sílabas.",
        "type": "estadistica",
        "name": "silabas"
    }
    result.append(resumen)
    palabras = textstat.lexicon_count(texto, removepunct=True)
    resumen = {
        "id": str(uuid.uuid4()),
        "start": inicioParrafo,
        "end": finParrafo,
        "text": "Número de palabras",
        "description": f"El texto tiene {palabras} palabras.",
        "type": "estadistica",
        "name": "palabras"
    }
    result.append(resumen)
    frases = textstat.sentence_count(texto)
    resumen = {
        "id": str(uuid.uuid4()),
        "start": inicioParrafo,
        "end": finParrafo,
        "text": "Número de frases",
        "description": f"El texto tiene {frases} frases.",
        "type": "estadistica",
        "name": "frases"
    }
    result.append(resumen)
    return result


async def stadistics_text(texto):
    " Dado un texto devuelve un resumen de dicho texto con los índices estadísticos"
    result = []
    inicioParrafo = 0
    finParrafo = inicioParrafo + len(texto)

    caracteres = len(texto)
    resumen = {
        "id": str(uuid.uuid4()),
        "start": inicioParrafo,
        "end": finParrafo,
        "text": "Número de caracteres",
        "description": f"El texto tiene {caracteres} caracteres.",
        "type": "estadistica",
        "name": "caracteres"
    }
    result.append(resumen)
    silabas = textstat.syllable_count(texto, lang="es")
    resumen = {
        "id": str(uuid.uuid4()),
        "start": inicioParrafo,
        "end": finParrafo,
        "text": "Número de sílabas",
        "description": f"El texto tiene {silabas} sílabas.",
        "type": "estadistica",
        "name": "silabas"
    }
    result.append(resumen)
    palabras = textstat.lexicon_count(texto, removepunct=True)
    resumen = {
        "id": str(uuid.uuid4()),
        "start": inicioParrafo,
        "end": finParrafo,
        "text": "Número de palabras",
        "description": f"El texto tiene {palabras} palabras.",
        "type": "estadistica",
        "name": "palabras"
    }
    result.append(resumen)
    frases = textstat.sentence_count(texto)
    resumen = {
        "id": str(uuid.uuid4()),
        "start": inicioParrafo,
        "end": finParrafo,
        "text": "Número de frases",
        "description": f"El texto tiene {frases} frases.",
        "type": "estadistica",
        "name": "frases"
    }
    result.append(resumen)
    return result

async def llm_text(texto):
    """ Dado un texto devuelve un resumen de dicho texto con los índices pragmático-discursivos que no cumplen las características deseadas evaluadas por un LLM"""
    result = []
    inicioParrafo = 0
    finParrafo = inicioParrafo + len(texto)
    analisis = evaluate_text(texto)
    if analisis[0]['se_detecta']:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Falta de coherencia interna",
            "description": f"El texto tiene contradicciones internas.",
            "type": "pragmático-discursivo",
            "name": "coherenciaInt"
        }
        result.append(resumen)
    if analisis[1]['se_detecta']:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Falta de progresión temática",
            "description": f"Existe un salto abrupto en la progresión temática.",
            "type": "pragmático-discursivo",
            "name": "progresion"
        }
        result.append(resumen)
    if analisis[2]['se_detecta']:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Falta de claridad entre ideas",
            "description": f"Las ideas entre cada párrafo no están bien estructuradas.",
            "type": "pragmático-discursivo",
            "name": "claridad"
        }
        result.append(resumen)
    if analisis[3]['se_detecta']:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Falta de coherencia externa",
            "description": "La organización global no se ajusta a la estructura de un texto divulgativo coherente..",
            "type": "pragmático-discursivo",
            "name": "coherenciaExt"
        }
        result.append(resumen)
    if analisis[4]['se_detecta']:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Posible digresión",
            "description": "Hay ideas que se alejan del tema principal.",
            "type": "pragmático-discursivo",
            "name": "digresion"
        }
        result.append(resumen)
    return result

async def globales(texto):
    result = []
    #estadisticas = await stadistics_text(texto)
    #result.append(estadisticas)
    pragmaticos = await llm_text(texto)
    result.append(pragmaticos)
    return result


@app.post("/generar_sugerencia")
async def generar_sugerencia(request: Request):
    data = await request.json()
    comment = data.get("comment")
    result = obtenerSugerencia(comment)
    return JSONResponse({"sugerencia": result})

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
