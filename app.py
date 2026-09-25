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
from modules.filtro_observaciones import *

from spellchecker import SpellChecker
import re

spell = SpellChecker(language="es")
#vocabulario_spacy = [
#    lexema.text.lower()
#    for lexema in nlp.vocab
#    if lexema.is_alpha
#]
#spell.word_frequency.load_words(vocabulario_spacy)

app = FastAPI()

@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Servir estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/spellcheck")
async def spellcheck(data: dict):
    texto = data.get("texto", "")

    matches = []

    # ORTOGRAFÍA
    for match in re.finditer(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b", texto):
        palabra = match.group()

        if palabra.isdigit():
            continue

        palabra_lower = palabra.lower()

        # Comprobar la palabra completa
        if palabra_lower in spell.known([palabra_lower]):
            continue

        # Obtener el lema con spaCy
        doc = nlp(palabra_lower)

        if not doc:
            continue

        token = doc[0]
        lema = token.lemma_.lower()

        if token.morph.get("VerbForm") == ["Part"]:
            continue

        # Si el lema es conocido, la forma puede ser una
        # variante morfológica válida
        if lema in spell.known([lema]):
            continue

        # Si ni la palabra ni su lema son conocidos,
        # la consideramos posible error
        candidatos = spell.candidates(palabra_lower)

        if candidatos:
            matches.append({
                "offset": match.start(),
                "length": len(palabra),
                "tipo": "ortografia",
                "mensaje": f"Posible error ortográfico: {palabra}",
                "replacements": list(candidatos)
            })

    # -------------------------------------------------
    # PUNTUACIÓN
    # -------------------------------------------------

    # Espacio antes de , . ; : ! ?
    for match in re.finditer(r"\s+[,.!?;:]", texto):
        signo = match.group().strip()

        # El rango que subrayamos será solo el espacio
        offset = match.start()
        length = len(match.group()) - 1

        matches.append({
            "offset": offset,
            "length": length,
            "tipo": "puntuacion",
            "mensaje": f"No debe haber un espacio antes de «{signo}»",
            "replacements": []
        })

    # Falta de espacio después de , . ; :
    for match in re.finditer(r"[,.;:!?][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", texto):
        signo = match.group()[0]

        # No marcar signos que forman números como 3.14
        if signo == "." and match.start() > 0:
            anterior = texto[match.start() - 1]
            siguiente = match.group()[1]

            if anterior.isdigit() and siguiente.isdigit():
                continue

        matches.append({
            "offset": match.start(),
            "length": 2,
            "tipo": "puntuacion",
            "mensaje": f"Debe haber un espacio después de «{signo}»",
            "replacements": []
        })

    return {"matches": matches}


#Cuando nos pidan analizar el texto completo lo que vamos a hacer es dividir el texto en
# párrafos y hacer el análisis de cada uno de esos párrafos.
def dividir_parrafos(texto):
    return texto.split("\n")

# Nos analiza todos los índices para un párrafo dado
async def analizar_parrafo(texto, inicioParrafo, texto_completo=None):
    result = []

    evaluaciones_llm = evaluate_sentences(texto)
    evaluaciones_palabras_llm = evaluate_words(texto)

    total_oraciones = 0
    oraciones_largas = 0

    resultado_morf = await morfosintaxis_paragraph(texto, inicioParrafo, evaluaciones_llm)
    resultado_lexsem = await lexsem_paragraph(texto, inicioParrafo, evaluaciones_llm, evaluaciones_palabras_llm)
    resultado_pragdis = await pragdisc_paragraph(texto, inicioParrafo, evaluaciones_llm)
    resultado_estad = await stadistics_paragraph(texto, inicioParrafo)

    # Contar métricas
    frases = nltk.sent_tokenize(texto, language="spanish")
    total_oraciones = len(frases)

    for frase in frases:
        if oracion_larga(frase)[0]:
            oraciones_largas += 1

    result.extend(resultado_estad)
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
    fin = data["intencionalidad"]
    comentarios = await globales(texto, fin)
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
    fin = data["intencionalidad"]

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
        "comentarios": await globales(texto, fin),
    "stats": ""}
    return JSONResponse(content=resultados)


async def morfosintaxis_paragraph(texto, inicioParrafo, evaluaciones_llm=None):
    """ Dado un párrafo devuelve un resumen de dicho párrafo con los índices morfosintácticos que no cumplen las características deseadas"""
    result = []
    oraciones_llm = evaluaciones_llm.get('oracion', []) if evaluaciones_llm else []
    parrafos_llm = evaluaciones_llm.get('parrafo', []) if evaluaciones_llm else []
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
                "name": "parrafoCorto",
                "suggestion": "false"
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
                "name": "parrafoLargo",
                "suggestion": "false"
            }
            result.append(resumen)
        for ora in oraciones_llm:
            if ora["aspecto"] == "inciso":
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioParrafo + ora['inicio'],
                    "end": inicioParrafo + ora['inicio'] + len(ora['oracion']),
                    "text": "Uso de incisos o aclaraciones",
                    "type": "morfosintaxis",
                    "name": "inciso",
                    "description": ora["razonamiento"],
                    "suggestion": "false"
                }
                result.append(resumen)
            if ora["aspecto"] == "modificador":
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioParrafo + ora['inicio'],
                    "end": inicioParrafo + ora['inicio'] + len(ora['oracion']),
                    "text": "Uso de modificadores o complementos entre sujeto y verbo",
                    "type": "morfosintaxis",
                    "name": "modificador",
                    "description": ora["razonamiento"],
                    "suggestion": "false"
                }
                result.append(resumen)
            if ora["aspecto"] == "coordinada":
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioParrafo + ora['inicio'],
                    "end": inicioParrafo + ora['inicio'] + len(ora['oracion']),
                    "text": "Exceso de coordinaciones",
                    "description": f"Se debe evitar el abuso de oraciones coordinadas.",
                    "type": "morfosintaxis",
                    "name": "coordinada",
                    "suggestion": "false"
                }
                result.append(resumen)
            if ora["aspecto"] == "yuxtaposicion":
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioParrafo + ora['inicio'],
                    "end": inicioParrafo + ora['inicio'] + len(ora['oracion']),
                    "text": "Exceso de yuxtaposiciones",
                    "description": f"Se debe evitar el abuso de oraciones yuxtapuestas.",
                    "type": "morfosintaxis",
                    "name": "yuxtapuesta",
                    "suggestion": "false"
                }
                result.append(resumen)
            if ora["aspecto"] == "concordancia":
                resumen = {
                    "id": str(uuid.uuid4()),
                   "start": inicioParrafo + ora['inicio'],
                    "end": inicioParrafo + ora['inicio'] + len(ora['oracion']),
                    "text": "Falta de concordancia",
                    "description": f"No debe haber faltas de concordancia.",
                    "type": "morfosintaxis",
                    "name": "concordancia"
                }
                result.append(resumen)
            if ora["aspecto"] == "gerundio":
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioParrafo + ora['inicio'],
                    "end": inicioParrafo + ora['inicio'] + len(ora['oracion']),
                    "text": "Uso erróneo del gerundio",
                    "description": f"No debe usarse el gerundio de posterioridad.",
                    "type": "morfosintaxis",
                    "name": "gerundio"
                }
                result.append(resumen)
            if ora["aspecto"] == "negativas":
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioParrafo + ora['inicio'],
                    "end": inicioParrafo + ora['inicio'] + len(ora['oracion']),
                    "text": "Acumulación de negaciones en la oración",
                    "description": f"No deben acumularse las palabras de modalidad negativa en una misma oracion.",
                    "type": "morfosintaxis",
                    "name": "negacion"
                }
                result.append(resumen)
            if ora["aspecto"] == "relativa":
                resumen = {
                    "id": str(uuid.uuid4()),
                        "start": inicioParrafo + ora['inicio'],
                        "end": inicioParrafo + ora['inicio'] + len(ora['oracion']),
                        "text": "Oración de relativo compleja",
                        "description": f"Se debe evitar el uso de relativos complejos.",
                        "type": "morfosintaxis",
                        "name": "relativo",
                     "suggestion": "false"
                }
                result.append(resumen)
        for parraf in parrafos_llm:
            if parraf['aspecto'] == "uso_abundante_negativas":
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioParrafo,
                    "end": finParrafo,
                    "text": "Uso abundante de formulaciones negativas en el texto",
                    "description": f"No deben acumularse oraciones con varias palabras de modalidad negativa.",
                    "type": "morfosintaxis",
                    "name": "negacion"
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
                "name": "eliptico",
                "suggestion": "false"
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
                        "description": oracionLarga[1],
                        "type": "morfosintaxis",
                        "name": "oracionLarga",
                "suggestion": "false"
                    }
                    result.append(resumen)
                orden = orden_incorrecto(frase)
                if orden:
                    resumen = {
                        "id": str(uuid.uuid4()),
                        "start": inicioFrase,
                        "end": finFrase,
                        "text": "Orden sintáctico complejo",
                        "description": f"La oración no sigue el orden sintáctico adecuado, debería seguir la estructura sujeto-verbo-complementos.",
                        "type": "morfosintaxis",
                        "name": "orden",
                "suggestion": "false"
                    }
                    result.append(resumen)
                #coordinada = oracion_coordinada(frase)
                #if coordinada[0]:
                #    resumen = {
                #        "id": str(uuid.uuid4()),
                #        "start": inicioFrase,
                #        "end": finFrase,
                #        "text": "Exceso de coordinaciones",
                #        "description": f"Se debe evitar el abuso de oraciones coordinadas.",
                #        "type": "morfosintaxis",
                #        "name": "coordinada",
                #"suggestion": "false"
                #    }
                #    result.append(resumen)
                #yuxtapuesta = oracion_yuxtapuesta(frase)
                #if yuxtapuesta[0]:
                #    resumen = {
                #        "id": str(uuid.uuid4()),
                #        "start": inicioFrase,
                #        "end": finFrase,
                #        "text": "Exceso de yuxtaposiciones",
                #        "description": f"Se debe evitar el abuso de oraciones yuxtapuestas.",
                #        "type": "morfosintaxis",
                #        "name": "yuxtapuesta",
                #"suggestion": "false"
                #    }
                #    result.append(resumen)

                #tieneInciso = tiene_inciso(frase)
                #if tieneInciso:
                #    resumen = {
                #        "id": str(uuid.uuid4()),
                #        "start": inicioFrase,
                #        "end": finFrase,
                #        "text": "Uso de incisos o aclaraciones",
                #        "description": f"Se debe evitar el abuso de incisos.",
                #        "type": "morfosintaxis",
                #        "name": "inciso",
                #"suggestion": "false"
                 #   }
                    #result.append(resumen)

                #if falta_concordancia(frase):
                #    resumen = {
                #        "id": str(uuid.uuid4()),
                #       "start": inicioFrase,
                #        "end": finFrase,
                #        "text": "Falta de concordancia",
                #        "description": f"No debe haber faltas de concordancia.",
                #        "type": "morfosintaxis",
                #        "name": "concordancia"
                #    }
                    #result.append(resumen)

                #relativoLejos = relativo_lejano(frase)
                #if relativoLejos:
                #    resumen = {
                #    "id": str(uuid.uuid4()),
                #    "start": inicioFrase,
                #    "end": finFrase,
                #    "text": "Oración de relativo compleja",
                #    "description": f"Se debe evitar el uso de relativos complejos.",
                #    "type": "morfosintaxis",
                #    "name": "relativo",
                #"suggestion": "false"
                #    }
                #    result.append(resumen)

                pasiva = voz_pasiva(frase)
                if pasiva:
                    inicioPasiva, finPasiva = pasiva
                    resumen = {
                        "id": str(uuid.uuid4()),
                        "start": inicioFrase + inicioPasiva,
                        "end": inicioFrase + finPasiva,
                        "text": "Uso de voz pasiva",
                        "description": f"Se debe evitar el abuso de oraciones pasivas.",
                        "type": "morfosintaxis",
                        "name": "pasiva",
                "suggestion": "false"
                    }
                    result.append(resumen)

                noConjugados = verbos_no_conjugados(frase)
                for token in noConjugados:
                    inicio = inicioFrase + token.idx
                    fin = inicio + len(token.text)
                    resumen = {
                        "id": str(uuid.uuid4()),
                        "start": inicio,
                        "end": fin,
                        "text": "Uso de formas no personales",
                        "description": f"Se debe evitar el abuso de formas no personales.",
                        "type": "morfosintaxis",
                        "name": "nopersonal",
                        "suggestion": "false"
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


async def lexsem_paragraph(texto, inicioParrafo, evaluaciones_llm=None, evaluaciones_palabra_llm=None):
    """ Dado un párrafo devuelve un resumen de dicho párrafo con los índices léxico-semánticos que no cumplen las características deseadas"""
    result = []
    oraciones_llm = evaluaciones_llm.get('oracion', []) if evaluaciones_llm else []
    parrafos_llm = evaluaciones_llm.get('parrafo', []) if evaluaciones_llm else []
    palabras_llm = evaluaciones_palabra_llm or []

    doc  = nlp(texto)
    finParrafo = inicioParrafo + len(texto)
    elementos_complejidad = []
    for token in doc:
        if token.is_alpha and nominalizada(token.text):
            elementos_complejidad.append({
                "tipo": "nominalziacion",
                "start": token.idx,
                "end": token.idx + len(token.text),
            })

    for ora in oraciones_llm:
        if ora["aspecto"] in ("coordinada", "relativa"):
            elementos_complejidad.append({
                "tipo": ora["aspecto"],
                "start": ora['inicio'],
                "end": ora['inicio'] + len(ora['oracion'])
            })
        if ora["aspecto"] == "info_secundaria":
            elementos_complejidad.append({
                "tipo": ora["aspecto"],
                "start": ora['inicio'],
                "end": ora['inicio'] + len(ora['oracion']),
            })
        if ora["aspecto"] == "rodeos":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioParrafo + ora['inicio'],
                "end": inicioParrafo + ora['inicio'] + len(ora['oracion']),
                "text": "Uso de rodeos expresivos",
                "type": "léxico-semántico",
                "name": "rodeos",
                "description": ora["razonamiento"],
                "suggestion": "false"
            }
            result.append(resumen)
    for ora in parrafos_llm:
        if ora["aspecto"] == "perdida_referente":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioParrafo,
                "end": finParrafo,
                "text": "Pérdida del referente",
                "type": "léxico-semántico",
                "name": "referente",
                "description": ora["razonamiento"],
                "suggestion": "false"
            }
            result.append(resumen)
    for palabra_llm in palabras_llm:
        inicioPalabra = inicioParrafo + palabra_llm['inicio']
        finPalabra = inicioParrafo + palabra_llm['fin']
        aspecto = palabra_llm["aspecto"]
        palabra = palabra_llm["palabra"]
        oracion = palabra_llm["oracion"]
        inicioFrase = inicioParrafo + palabra_llm['inicioFrase']
        if aspecto=="sigla":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioPalabra,
                "end": finPalabra,
                "text": "Uso de siglas",
                "description": "Evita el uso de siglas sin descripción",
                "type": "léxico-semántico",
                "name": "siglas",
                "suggestion": "false",
                "oracion": oracion,
                "inicioFrase": inicioFrase
            }
            result.append(resumen)

        if aspecto == "lexico_poco_frecuente":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioPalabra,
                "end": finPalabra,
                "text": "Léxico poco frecuente",
                "description": "Evita el uso de léxico poco frecuente",
                "type": "léxico-semántico",
                "name": "lexFrec",
                "suggestion": "true",
                "palabra": palabra,
                "oracion": oracion,
                "inicioFrase": inicioFrase
            }
            result.append(resumen)

        if aspecto == "palabra_baul":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioPalabra,
                "end": finPalabra,
                "text": "Palabras imprecisas o palabras baúl",
                "description": "Evita el uso de palabras baúl sin significado preciso",
                "type": "léxico-semántico",
                "name": "baul",
                "suggestion": "true",
                "palabra": palabra,
                "oracion": oracion,
                "inicioFrase": inicioFrase
            }
            result.append(resumen)

        if aspecto == "extranjerismo":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioPalabra,
                "end": finPalabra,
                "text": "Presencia de extranjerismos, latinismos o arcaísmos",
                "description": "Evita el uso de extranjerismos",
                "type": "léxico-semántico",
                "name": "extranjerismo",
                "suggestion": "true",
                "palabra": palabra,
                "oracion": oracion,
                "inicioFrase": inicioFrase
            }
            result.append(resumen)

        if aspecto == "ambigua":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioPalabra,
                "end": finPalabra,
                "text": "Ambigüedad",
                "description": "Evita el uso de palabras que admiten varias interpretaciones",
                "type": "léxico-semántico",
                "name": "ambiguo",
                "suggestion": "true",
                "palabra": palabra,
                "oracion": oracion,
                "inicioFrase": inicioFrase
            }
            result.append(resumen)

        if aspecto == "elemento_valorativo":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioPalabra,
                "end": finPalabra,
                "text": "Revisar el uso de elementos valorativos",
                "description": "Evita el uso de elementos subjetivos y valorativos",
                "type": "léxico-semántico",
                "name": "elemValor",
                "suggestion": "false",
                "oracion": oracion,
                "inicioFrase": inicioFrase
            }
            result.append(resumen)

        if aspecto == "tecnicismo":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioPalabra,
                "end": finPalabra,
                "text": "Uso de tecnicismos",
                "description": "Evita el uso de términos especializados",
                "type": "léxico-semántico",
                "name": "tecnicismo",
                "suggestion": "true",
                "palabra": palabra,
                "oracion": oracion,
                "inicioFrase": inicioFrase
            }
            result.append(resumen)

        if aspecto == "coloquialismo":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioPalabra,
                "end": finPalabra,
                "text": "Revisar coloquialismos",
                "description": "Evita el uso de expresiones excesivamente informales",
                "type": "léxico-semántico",
                "name": "coloquialismo",
                "suggestion": "true",
                "palabra": palabra,
                "oracion": oracion,
                "inicioFrase": inicioFrase
            }
            result.append(resumen)

        if aspecto == "vulgarismo":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioPalabra,
                "end": finPalabra,
                "text": "Revisar vulgarismos o giros inapropiados",
                "description": "Evita el uso de expresiones vulgares o inapropiadas",
                "type": "léxico-semántico",
                "name": "vulgarismo",
                "suggestion": "true",
                "palabra": palabra,
                "oracion": oracion,
                "inicioFrase": inicioFrase
            }
            result.append(resumen)
    if len(elementos_complejidad) >= 5:
        for elemento in elementos_complejidad:
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioParrafo + elemento["start"],
                "end": inicioParrafo + elemento["end"],
                "text": "Párrafo complejo",
                "description": f"Se deben evitar párrafos demasiado complejos.",
                "type": "léxico-semántico",
                "name": "parrafoComplejo",
                    "suggestion": "false"
            }
            result.append(resumen)

    for sent in doc.sents:
        oracion = sent.text
        for match in re.finditer(r'\w+', oracion, re.UNICODE):
            palabra = match.group()
            inicioPalabra = inicioParrafo + sent.start_char + match.start()
            finPalabra = inicioParrafo + sent.start_char + match.end()

#            es_extranjerismo = extranjerismos(palabra)

#            if es_extranjerismo:
#                resumen = {
#                    "id": str(uuid.uuid4()),
#                    "start": inicioPalabra,
#                    "end": finPalabra,
#                    "text": "Extranjerismo",
#                    "description": f"Se debe evitar el abuso de extranjerismos.",
#                    "type": "léxico-semántico",
#                    "name": "extranjerismo",
#                    "suggestion": "true",
#                    "oracion": oracion,
#                    "palabra": palabra,
#                    "inicioFrase":inicioParrafo + sent.start_char
#                }
#                result.append(resumen)

#            es_baul = detectar_palabras_baul(texto, palabra)
#            if es_baul:
#                resumen = {
#                    "id": str(uuid.uuid4()),
#                    "start": inicioPalabra,
#                    "end": finPalabra,
#                    "text": "Palabras baúl",
#                    "description": f"Se debe evitar el abuso de palabra baúl.",
#                    "type": "léxico-semántico",
#                    "name": "baul",
#                "suggestion": "true",
#                    "oracion": oracion,
#                    "palabra": palabra,
#                    "inicioFrase":inicioParrafo + sent.start_char
#                }
#                result.append(resumen)
            if palabraLarga(palabra):
                resumen = {
                    "id": str(uuid.uuid4()),
                    "start": inicioPalabra,
                    "end": finPalabra,
                    "text": "Revisar uso de palabras largas o derivados",
                    "description": f"Se debe evitar el uso de palabras muy largas.",
                    "type": "léxico-semántico",
                    "name": "largas",
                "suggestion": "true",
                    "oracion": oracion,
                    "palabra": palabra,
                    "inicioFrase":inicioParrafo + sent.start_char
                }
                result.append(resumen)
#            if latinism(palabra):
#                resumen = {
#                    "id": str(uuid.uuid4()),
#                    "start": inicioPalabra,
#                    "end": finPalabra,
#                    "text": "Latinismos",
#                    "description": f"Se debe evitar el uso de latinismos.",
#                    "type": "léxico-semántico",
#                    "name": "latinismo",
#                "suggestion": "true",
#                    "oracion": oracion,
#                    "palabra": palabra,
#                    "inicioFrase":inicioParrafo + sent.start_char
#                }
#                result.append(resumen)
#            if tecnisimos(palabra):
#                resumen = {
#                    "id": str(uuid.uuid4()),
#                    "start": inicioPalabra,
#                    "end": finPalabra,
#                    "text": "Uso de tecnicismos",
#                    "description": f"Se debe evitar el uso de tecnicismos.",
#                    "type": "léxico-semántico",
#                    "name": "tecnicismo",
#                "suggestion": "true",
#                    "oracion": oracion,
#                    "palabra": palabra,
#                    "inicioFrase":inicioParrafo + sent.start_char
#                }
#                result.append(resumen)

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


async def pragdisc_paragraph(texto, inicioParrafo, evaluaciones_llm=None):
    """ Dado un párrafo devuelve un resumen de dicho párrafo con los índices pragmático-discursivos que no cumplen las características deseadas"""
    result = []
    finParrafo = inicioParrafo + len(texto)
    frases = nltk.sent_tokenize(texto, language="spanish")
    inicioFrase = inicioParrafo

    oraciones_llm = evaluaciones_llm.get('oracion', []) if evaluaciones_llm else []

    for ora in oraciones_llm:
        if ora["aspecto"] == "info_secundaria":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioParrafo + ora["inicio"],
                "end": inicioParrafo + ora["inicio"] + len(ora["oracion"]),
                "text": "Presencia de información secundaria en la oración",
                "description": ora["razonamiento"],
                "type": "pragmático-discursivo",
                "name": "secun",
                "suggestion": "false"
            }
            result.append(resumen)

        if ora["aspecto"] == "enfasis" or ora["aspecto"] == "redundancia":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioParrafo + ora["inicio"],
                "end": inicioParrafo + ora["inicio"] + len(ora["oracion"]),
                "text": "Redundancias y/o formulaciones enfáticas",
                "description": ora["razonamiento"],
                "type": "pragmático-discursivo",
                "name": "redundancias",
                "suggestion": "false"
            }
            result.append(resumen)

    cone = falta_conectores(texto)
    if cone:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": inicioParrafo + len(texto),
            "text": "Ausencia de conectores",
            "description": f"Se debe incentivar el uso de conectores.",
            "type": "pragmático-discursivo",
            "name": "conector",
            "suggestion": "false"
        }
        result.append(resumen)

    if conectores_repe(texto):
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": inicioParrafo + len(texto),
            "text": "Repetición de conector",
            "description": f"Se debe incentivar el uso de conectores variados.",
            "type": "pragmático-discursivo",
            "name": "conectorRepe",
            "suggestion": "false"
        }
        result.append(resumen)

    for frase in frases:
        finFrase = inicioFrase + len(frase)

        puntuacion = conectores_punt(frase)
        if puntuacion:
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioFrase + puntuacion[1],
                "end": inicioFrase + puntuacion[1]+len(puntuacion[2]),
                "text": "Revisar la puntuación del conector",
                "description": f"Los conectores deben ir con buena puntuación.",
                "type": "pragmático-discursivo",
                "name": "conectoresPunt",
            "suggestion": "false"
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

def legibility_paragraph(texto, inicioParrafo, evaluaciones_llm=None):
    " Dado un párrafo devuelve un resumen de dicho párrafo con los índices de legibilidad que no cumplen las características deseadas"
    result = []
    oraciones_llm = evaluaciones_llm.get('oracion', []) if evaluaciones_llm else []
    parrafos_llm = evaluaciones_llm.get('parrafo', []) if evaluaciones_llm else []
    finParrafo = inicioParrafo + len(texto)
    inicioFrase = inicioParrafo
    fernandezHuerta = indice_fernandezHuerta(texto)
    if fernandezHuerta[0]<60 and fernandezHuerta[0]!=0:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Incumplimiento de umbrales de legibilidad (índice de Fernández-Huerta)",
            "description": fernandezHuerta[1],
            "type": "legibility",
            "name": "fernandezHuerta",
                "suggestion": "false"
        }
        result.append(resumen)
    szigrisztPazos = indice_szigriszt_pazos(texto)
    if szigrisztPazos[0]<50 and szigrisztPazos!=0:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Incumplimiento de umbrales de legibilidad (índice de Szigriszt-Pazos)",
            "description": szigrisztPazos[1],
            "type": "legibility",
            "name": "szigrisztPazos",
                "suggestion": "false"
        }
        result.append(resumen)
    for ora in oraciones_llm:
        if ora['aspecto'] == "idea_principal":
            resumen = {
                "id": str(uuid.uuid4()),
                "start": inicioParrafo,
                "end": finParrafo,
                "text": "Priorizar la idea principal",
                "type": "léxico-semántico",
                "name": "rodeos",
                "description": "La idea principal del párrafo debe ir al principio del mismo.",
                "suggestion": "false"
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


async def legibility_text(texto):
    " Dado un texto devuelve un resumen de dicho texto con los índices de legibilidad que no cumplen las características deseadas"
    #data = await request.json()
    #texto = data.get("text", "")

    parrafos = dividir_parrafos(texto)
    resultados = {} # Aquí voy a almacenar todos los comentarios por parrafo
    inicioParrafo = 0
    finParrafo = inicioParrafo + len(texto)
    inicio = 0
    resultados['global'] = []
    fernandezHuerta = indice_fernandezHuerta(texto)
    if (fernandezHuerta[0] < 60 and fernandezHuerta[0]!=0):
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Incumplimiento de umbrales de legibilidad (índice de Fernández-Huerta)",
            "description": fernandezHuerta[1],
            "type": "legibility",
            "name": "fernandezHuerta",
                "suggestion": "false"
        }
        resultados['global'].append(resumen)

    szigrisztPazos = indice_szigriszt_pazos(texto)
    if (szigrisztPazos[0] < 50 and szigrisztPazos[0]!=0):
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Incumplimiento de umbrales de legibilidad (índice de Szigriszt-Pazos)",
            "description": szigrisztPazos[1],
            "type": "legibility",
            "name": "szigrisztPazos",
                "suggestion": "false"
        }
        resultados['global'].append(resumen)
    long = longitud(texto)
    if long > 2000:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": 0,
            "end": len(texto),
            "text": "Texto largo",
            "type": "legibility",
            "name": "textoLargo",
            "description": "El texto es demasiado largo",
            "suggestion": "false"
        }
        resultados['global'].append(resumen)

    # for i, parrafo in enumerate(parrafos, start=1):
    #     resultados[i] = legibility_paragraph(parrafo, inicio)
    #     inicio = inicio + len(parrafo) + 1
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
    silabas = textstat.syllable_count(texto, lang="es")
    palabras = textstat.lexicon_count(texto, removepunct=True)
    frases = textstat.sentence_count(texto)
    resumen = {
        "id": str(uuid.uuid4()),
        "start": inicioParrafo,
        "end": finParrafo,
        "text": "Estadísticas del párrafo",
        "description": f"El párrafo tiene:<br>- {caracteres} caracteres<br>- {silabas} sílabas<br>- {palabras} palabras<br>- {frases} oraciones",
        "type": "estadistica",
        "name": "estadística",
                "suggestion": "false"
    }
    result.append(resumen)
    return result


async def stadistics_text(texto):
    " Dado un texto devuelve un resumen de dicho texto con los índices estadísticos"
    result = []
    inicioParrafo = 0
    finParrafo = inicioParrafo + len(texto)

    caracteres = len(texto)
    silabas = textstat.syllable_count(texto, lang="es")
    palabras = textstat.lexicon_count(texto, removepunct=True)
    frases = textstat.sentence_count(texto)
    fernandez= str(round(fernandez_huerta(texto), 2)).replace(".", ",")
    pazos = str(round(szigriszt_pazos(texto), 2)).replace(".", ",")
    resumen = {
        "id": str(uuid.uuid4()),
        "start": inicioParrafo,
        "end": finParrafo,
        "text": "Estadísticas del texto",
        "description": f"El texto tiene:<br>- {caracteres} caracteres<br>- {silabas} sílabas<br>- {palabras} palabras<br>- {frases} frases<br><br>Test de legibilidad:<br>- Índice de Fernández-Huerta: {fernandez} (en textos dirigidos al público general se recomienda una puntuación de entre 60 y 70).<br>- Índice de Szigriszt-Pazos: {pazos} (en textos dirigidos al público general se recomienda una puntuación de entre 51 y 65).",
        "type": "estadistica",
        "name": "estadística",
                "suggestion": "false"
    }
    result.append(resumen)
    return {"global": result}

async def llm_text(texto, fin):
    """ Dado un texto devuelve un resumen de dicho texto con los índices pragmático-discursivos que no cumplen las características deseadas evaluadas por un LLM"""
    result = []
    inicioParrafo = 0
    finParrafo = inicioParrafo + len(texto)
    analisis = evaluate_text(texto, fin)
    if analisis[0]['noul']>0.5:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Falta de coherencia interna",
            "description": analisis[0]['razonamiento'],
            "type": "pragmático-discursivo",
            "name": "coherenciaInt",
                "suggestion": "false"
        }
        result.append(resumen)
    if analisis[1]['noul']>0.5:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Falta de progresión temática",
            "description": analisis[1]['razonamiento'],
            "type": "pragmático-discursivo",
            "name": "progresion",
                "suggestion": "false"
        }
        result.append(resumen)
    if analisis[2]['noul']>0.5:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Falta de conexión entre ideas",
            "description": analisis[2]['razonamiento'],
            "type": "pragmático-discursivo",
            "name": "claridad",
                "suggestion": "false"
        }
        result.append(resumen)
    if analisis[3]['se_detecta']:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Falta de coherencia externa",
            "description": analisis[3]['razonamiento'],
            "type": "pragmático-discursivo",
            "name": "coherenciaExt",
                "suggestion": "false"
        }
        result.append(resumen)
    if analisis[4]['noul']>0.5:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Posible digresión",
            "description": analisis[4]['razonamiento'],
            "type": "pragmático-discursivo",
            "name": "digresion",
                "suggestion": "false"
        }
        result.append(resumen)
    if analisis[5]['noul']>0.5:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Falta de adecuación a la finalidad comunicativa",
            "description": analisis[5]['razonamiento'],
            "type": "pragmático-discursivo",
            "name": "finalidad",
                "suggestion": "false"
        }
        result.append(resumen)
    if analisis[6]['noul']>0.5:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Falta de adecuación al destinatario",
            "description": analisis[6]['razonamiento'],
            "type": "pragmático-discursivo",
            "name": "destinatario",
            "suggestion": "false"
        }
        result.append(resumen)
    if analisis[7]['noul']>0.5:
        resumen = {
            "id": str(uuid.uuid4()),
            "start": inicioParrafo,
            "end": finParrafo,
            "text": "Incluir apartados",
            "description": analisis[7]['razonamiento'],
            "type": "pragmático-discursivo",
            "name": "apartados",
            "suggestion": "false"
        }
        result.append(resumen)

    return {"global":result}

async def globales(texto, fin):
    result = []
    estadisticas = await stadistics_text(texto)
    result.append(estadisticas)
    legibilidad = await legibility_text(texto)
    result.append(legibilidad)
    pragmaticos = await llm_text(texto, fin)
    result.append(pragmaticos)
    return result


@app.post("/generar_sugerencia")
async def generar_sugerencia(request: Request):
    try:
        data = await request.json()
        oracion = data.get("oracion")
        palabra = data.get("palabra")
        criterio = data.get("criterio")
        result = obtenerSugerencia(oracion, palabra, criterio)
        return JSONResponse({"sugerencia": result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise

@app.post("/generar_tabla")
async def generar_tabla(request: Request):
    data = await request.json()
    texto = data["texto"]

    resultado = generar_tabla_html(texto)

    return JSONResponse(content=resultado)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
