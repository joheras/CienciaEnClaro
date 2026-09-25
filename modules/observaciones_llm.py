#!/usr/bin/env python
# coding: utf-8

# In[1]:

import json
from json_repair import repair_json
import dspy
import re

#lm = dspy.LM('ollama_chat/gemma4:12b', api_base='http://localhost:11434', think=False)

lm = dspy.LM('ollama_chat/gemma4:12b', api_base='http://ollama:11434',think=False)
dspy.configure(lm=lm)


def get_aspectos(fin):
    if isinstance(fin, list):
        fin = ", ".join(fin)

    return {
        "coherencia_interna": """
Detecta falta de coherencia interna si hay contradicciones o incompatibilidades lógicas, reiteraciones innecesarias o saltos informativos sin relación clara con el contenido previo que dificultan la comprensión global.
""",

        "progresion_tematica": """
Detecta falta de progresión temática si las ideas no avanzan de forma ordenada: hay cambios bruscos de tema, información sin conexión con lo anterior o ausencia de relaciones lógicas. Cada idea debería ampliar, complementar o desarrollar la información previa.
""",

        "claridad_ideas": """
Detecta falta de claridad entre ideas si sus relaciones no son evidentes para el lector. Puede deberse a ausencia o uso inadecuado de conectores o marcadores, o a relaciones no explícitas de causa-efecto, secuencia temporal, contraste, ejemplificación o adición.
""",

        "coherencia_externa": """
Detecta falta de coherencia externa si la organización global no se ajusta a la estructura esperada de un texto divulgativo: introducción, desarrollo y conclusión no se distinguen claramente, falta alguna de estas partes o su organización dificulta comprender el propósito general.
""",

        "posible_disgresion": """
Detecta posible digresión si se incorpora información, comentarios o desarrollos que se alejan del tema principal sin contribuir claramente a su explicación o desarrollo. Incluye ideas secundarias, ejemplos o detalles que interrumpen el hilo y desvían la atención. Márcala cuando una parte significativa del contenido no guarde relación directa con el tema central o propósito comunicativo.
""",

        "finalidad_comunicativa": f"""
Detecta falta de adecuación a la finalidad comunicativa cuando el contenido, la organización o el tono no contribuyen al propósito principal de {fin}, o cuando el texto se desvía de él, incorpora recursos que no lo favorecen o desarrolla el tema de forma incompatible con dicho propósito.
""",

        "destinatario": """
Detecta falta de adecuación al destinatario si el nivel de lenguaje, los conocimientos previos, la cantidad de información o la forma de explicar los contenidos no se ajustan a un adulto que ha finalizado la ESO.
""",

        "apartados": """
Marca true si el texto contiene varias partes o bloques temáticos claramente diferenciados y sería recomendable dividirlos mediante títulos o encabezados para facilitar la comprensión de la estructura, localizar información o seguir la explicación. En caso contrario, marca false.
"""
    }

def get_aspectos_parrafo():
    return {
        "perdida_referente": """
Detecta pérdida de referente cuando no se puede identificar claramente a qué persona, objeto, concepto o entidad se refiere una expresión posterior del párrafo. Puede ocurrir si un pronombre, demostrativo o expresión nominal no tiene un antecedente claro, si hay varios antecedentes posibles o si la referencia no puede relacionarse fácilmente con la información previa.
""",

        "uso_abundante_negativas": """
Detecta uso abundante de formulaciones negativas solo si se cumplen ambas condiciones:
1. Al menos dos oraciones del párrafo contienen una acumulación de elementos o expresiones de modalidad negativa. 
2. La repetición de estas formulaciones tiene una presencia relevante en el párrafo.

No lo detectes por varias negaciones aisladas ni por una negación normal en una sola oración.
""",

        "idea_principal": """
Detecta presentación tardía de la idea principal cuando el mensaje central del párrafo aparece después de una parte significativa de información secundaria, contextual o explicativa, de modo que el lector debe avanzar bastante para identificarlo.

Marca false si la idea principal aparece al comienzo y las oraciones posteriores la desarrollan, explican, justifican o amplían.
"""
    }

def get_aspectos_oracion():
    return {
        "inciso": """
        Detecta un inciso cuando una construcción interrumpe la estructura principal de la oración para añadir información adicional, aclaratoria o secundaria. Puede aparecer entre comas, paréntesis, rayas u otros signos equivalentes.

        No consideres incisos las comas que separan elementos de una enumeración ni las que forman parte de la estructura sintáctica normal.
        """,

        "modificador": """
        Detecta un modificador o complemento entre el sujeto y su verbo principal cuando una información adicional interrumpe su relación directa.

        Solo debe detectarse si está realmente entre el sujeto y el verbo principal. No consideres modificaciones que formen parte del propio sujeto ni complementos posteriores al verbo.
        """,

        "coordinada": """
        Detecta si la oración contiene tres o más proposiciones coordinadas.

        Una proposición coordinada está al mismo nivel sintáctico que otra y se une a ella mediante un nexo coordinante explícito, como "y", "e", "ni", "o", "u", "pero", "sino", etc.

        Solo cuenta la coordinación cuando el nexo une proposiciones u oraciones, no palabras o grupos de palabras.
        """,

        "yuxtaposicion": """
        Detecta si la oración contiene tres o más proposiciones yuxtapuestas.

        Una proposición yuxtapuesta está al mismo nivel sintáctico que otra y se relaciona con ella sin nexo coordinante explícito, únicamente mediante un signo de puntuación, como coma, punto y coma o dos puntos.

        Solo cuenta la yuxtaposición cuando el signo separa dos proposiciones u oraciones del mismo nivel sintáctico.
        """,

        "relativa": """
        Detecta si existe una oración de relativo compleja por su estructura o por la distancia entre la relativa y su antecedente.

        Es compleja si cumple al menos una de estas condiciones:
        1. Relativos encapsulados: una oración de relativo aparece dentro de otra oración de relativo.
        2. Relativo alejado de su antecedente: existe una cantidad considerable de material entre ambos, especialmente otras proposiciones, incisos u otros elementos que dificulten identificar el referente.
        """,

        "concordancia": """
        Detecta errores gramaticales reales de concordancia dentro de la oración.

        No marques construcciones gramaticalmente correctas aunque sean menos habituales o complejas.
        """,

        "gerundio": """
        Detecta un uso erróneo del gerundio cuando expresa una acción posterior a la principal. Normativamente, el gerundio debe expresar normalmente una acción simultánea o anterior, no posterior.

        Presta especial atención a estructuras donde primero ocurre la acción del verbo principal y después la expresada por el gerundio.
        """,

        "redundancia": """
        Detecta redundancia cuando se repite innecesariamente una misma información, idea o significado mediante palabras o expresiones que no aportan contenido nuevo.

        Solo debe detectarse cuando la repetición sea innecesaria.
        """,

        "enfasis": """
        Detecta una formulación enfática cuando contiene expresiones intensificadoras, reiterativas o enfáticas innecesarias que pueden hacer el mensaje más complejo o menos directo.

        Solo debe detectarse cuando el énfasis sea innecesario para transmitir el significado.
        """,

        "rodeos": """
        Detecta un rodeo expresivo cuando una idea puede expresarse de forma más directa, sencilla y concisa mediante un verbo simple, pero se usa una construcción más larga o perifrástica que añade complejidad innecesaria.

        Debe poder sustituirse la expresión nominal o construcción equivalente por un verbo simple sin cambiar significativamente el significado.
        """,

        "negativas": """
        Detecta si la oración contiene dos o más elementos de negación combinados en la misma estructura.

        Cuenta como elementos negativos:
        1. Partículas, pronombres o determinantes negativos explícitos ("no", "jamás", "ningún", etc.).
        2. Palabras o expresiones con significado negativo ("infrecuente", "desleal", "imposible", etc.).
        """,

        "info_secundaria": """
        Detecta información secundaria cuando la oración contiene contenido adicional no necesario para comprender la idea principal, introducido como información complementaria, aclaratoria o accesoria.

        Debe detectarse cuando una idea principal claramente identificable se combina con uno o varios datos secundarios que pueden dificultar innecesariamente la comprensión.
        """
    }

def get_aspectos_palabra():
    return {
        "sigla": """
        Detecta una sigla cuando la palabra o secuencia está formada por las iniciales de varias palabras y funciona como denominación abreviada (p. ej., OMS, ONU, UE, ADN).

        Solo debe detectarse si es realmente una sigla y su significado no está explicado ni puede conocerse por el contexto. Si aparece acompañada de su denominación completa o de una explicación suficiente, no la marques.

        No marques como siglas las palabras comunes escritas completamente en mayúsculas.
        """,

        "lexico_poco_frecuente": """
        Detecta léxico poco frecuente cuando la palabra es poco habitual en el uso general del español y puede resultar desconocida para una parte importante de los lectores.

        Valora su frecuencia de uso general, no solo que sea larga, culta o especializada. No marques automáticamente los tecnicismos, que tienen una categoría específica.
        """,

        "palabra_baul": """
        Detecta una palabra baúl cuando su significado es excesivamente general o impreciso y sustituye a una expresión más concreta que transmitiría la información con mayor precisión.

        Debe resultar demasiado inespecífica en el contexto concreto.
        """,

        "extranjerismo": """
        Detecta un extranjerismo cuando la palabra procede de otra lengua y se utiliza en español manteniendo una forma o uso propio de la lengua de origen.

        Solo debe detectarse cuando sea realmente un extranjerismo en el contexto analizado.
        """,

        "ambigua": """
        Detecta ambigüedad léxica cuando la palabra admite interpretaciones relevantes distintas en el contexto y su significado no puede determinarse con suficiente claridad.

        No marques una palabra solo porque tenga varios significados en el diccionario: la ambigüedad debe afectar al texto concreto.
        """,

        "elemento_valorativo": """
        Detecta un elemento valorativo cuando la palabra expresa una valoración, juicio, opinión o apreciación subjetiva sobre una persona, objeto, situación o hecho.
        """,

        "tecnicismo": """
        Detecta un tecnicismo cuando la palabra pertenece específicamente al vocabulario especializado de un ámbito científico, técnico, profesional o académico y puede resultar poco familiar para lectores no especializados.

        Solo debe detectarse cuando tenga un uso especializado en el contexto.
        """,

        "coloquialismo": """
        Detecta un coloquialismo cuando la palabra o expresión pertenece principalmente al registro coloquial o informal y puede resultar inadecuada en un texto divulgativo dirigido a un público general.

        No marques palabras de uso general solo porque también puedan aparecer en conversaciones informales.
        """,

        "vulgarismo": """
        Detecta un vulgarismo cuando la palabra presenta una forma o uso incorrecto o no normativo en el español estándar.

        Solo debe detectarse ante un uso realmente no normativo. No marques variantes regionales ni formas coloquiales que sean correctas.
        """
    }


# aspectos_seleccionados = [
#     "coherencia_interna",
#     "progresion_tematica",
#     "claridad_ideas",
#     "coherencia_externa",
#     "posible_disgresion",
#     "finalidad_comunicativa"
# ]


class EvaluarTexto(dspy.Signature):
    texto = dspy.InputField()

    aspectos = dspy.InputField(
        desc="Lista de aspectos a evaluar con nombre y descripción"
    )

    resultado_json = dspy.OutputField(
        desc="""
        JSON con formato:
        [
          {
            "aspecto": "...",
            "se_detecta": true,
            "razonamiento": "..."
          }
        ]
        """
    )


evaluador = dspy.Predict(EvaluarTexto)


class EvaluarParrafo(dspy.Signature):
    parrafo = dspy.InputField(
        desc="Párrafo completo que debe analizarse."
    )
    oraciones = dspy.InputField(
        desc="Oraciones numeradas del párrafo."
    )
    aspectos_oracion = dspy.InputField(
        desc="Aspectos que deben detectarse en cada oración."
    )
    aspectos_parrafo = dspy.InputField(
        desc = "Aspectos que deben detectarse en el párrafo completo."
    )

    resultado_json = dspy.OutputField(
        desc = """ 
        Devuelve exclusivamente un objeto JSON.
        
        El objeto JSON debe tener exactamente esta estructura: 
        {
        "oracion": [
        { 
            "oracion": 1,
            "aspectos": [
                {
                    "aspecto": "nombre_del_aspecto",
                    "se_detecta": true,
                }
            ]
            }
            ],
            "parrafo": [
                {
                "aspecto": "nombre_del_aspecto",
                "se_detecta": true,
                }
            ]
        }
        
        Debe aparecer exactamente un objeto por cada oración.
        Deben evaluarse todos los aspectos para cada oración.
        "negativas" se evalúa individualmente en cada oración.
        "uso_abundante_negativas" solo puede marcarse como true cuando al menos dos oraciones del párrafo hayan sido consideradas problemáticas por presentar una acumulación de elementos de modalidad negativa.
        Debe aparecer siempre la clave "parrafo", incluso cuando no se detecte ningún problema a nivel de párrafo.
        "se_detecta" debe ser siempre true o false.
         """
    )

evaluador_parrafo = dspy.Predict(EvaluarParrafo)

class EvaluarPalabras(dspy.Signature):
    parrafo = dspy.InputField(
        desc="Párrafo completo que debe analizarse."
    )

    palabras = dspy.InputField(
        desc="Lista de palabras del párrafo, con su número y posición."
    )

    aspectos_palabra = dspy.InputField(
        desc="Aspectos que deben evaluarse para cada palabra."
    )

    resultado_json = dspy.OutputField(
        desc="""
        JSON con formato:

        {
            "palabras": [
                {
                    "palabra": "OMS",
                    "indice": 4,
                    "aspectos": [
                        {
                            "aspecto": "sigla",
                            "se_detecta": true
                        }
                    ]
                }
            ]
        }

        Debe aparecer únicamente una entrada para las palabras que presenten
        al menos uno de los aspectos analizados.

        Para cada palabra detectada deben incluirse todos los aspectos que
        correspondan.

        "se_detecta" debe ser siempre true o false.

        La posición "indice" debe corresponder a la posición de la palabra
        dentro de la lista proporcionada.
        """
    )


evaluador_palabras = dspy.Predict(EvaluarPalabras)



#def evaluate_text(texto, fin, aspectos_seleccionados=None):
#    aspectos_dict = get_aspectos(fin)
#    if aspectos_seleccionados is None:
#        aspectos_seleccionados = list(aspectos_dict.keys())

#    aspectos = [
#        {
#            "nombre": nombre,
#            "descripcion": aspectos_dict[nombre]
#        }
#        for nombre in aspectos_seleccionados
#        if nombre in aspectos_dict
#    ]

#    resultado = evaluador(
#        texto=texto,
#        aspectos=aspectos
#    )
#    json_text = resultado.resultado_json.strip()

#    if "```json" in json_text:
#        json_text = json_text.split("```json", 1)[1].split("```", 1)[0].strip()
#    elif "```" in json_text:
#        json_text = json_text.replace("```", "").strip()

#    datos = json.loads(repair_json(json_text))
#    if isinstance(datos, dict):

#        datos_normalizados = []

#        for nombre, valor in datos.items():

            # Convertir "True"/"False" en booleanos
#            if isinstance(valor, str):
#                se_detecta = valor.strip().lower() == "true"
#            else:
#                se_detecta = bool(valor)

#            datos_normalizados.append({
#                "aspecto": nombre,
#                "se_detecta": se_detecta,
#                "razonamiento": ""
#            })

#        datos = datos_normalizados

#    return datos

def separar_oraciones(texto):
    """
        Separa el texto en oraciones conservando el índice de inicio de cada una dentro del texto original.

        Devuelve:
        [
        { "oracion": "...",
         "inicio": 0 }, ...
         ]
         """

    oraciones = []  # Busca final de oración seguido de espacio o final de texto.
    patron = re.compile(
        r'[^.!?\n]+[.!?]+|[^\n]+(?=\n|$)',
        re.DOTALL
    )
    for match in patron.finditer(texto):
        oracion = match.group().strip()
        if not oracion:
            continue
            # Como strip() puede eliminar espacios iniciales, buscamos la posición real de la oración dentro del match.
        inicio = match.start() + len(match.group()) - len(match.group().lstrip())
        oraciones.append({
            "oracion": oracion,
            "inicio": inicio
        })
    return oraciones

def ev_sentences(texto, aspectos_seleccionados=None, aspectos_parrafo_seleccionados=None):
    oraciones = separar_oraciones(texto)
    aspectos_oracion_dict = get_aspectos_oracion()
    aspectos_parrafo_dict = get_aspectos_parrafo()

    if aspectos_seleccionados is None:
        aspectos_seleccionados = aspectos_oracion_dict.keys()
    if aspectos_parrafo_seleccionados is None:
        aspectos_parrafo_seleccionados = aspectos_parrafo_dict.keys()

    aspectos_oracion = [
        {
            "nombre": nombre,
            "descripcion": aspectos_oracion_dict[nombre]
        }
        for nombre in aspectos_seleccionados
        if nombre in aspectos_oracion_dict
    ]
    aspectos_parrafo = [
        {
            "nombre": nombre,
            "descripcion": aspectos_parrafo_dict[nombre]
        }
        for nombre in aspectos_parrafo_seleccionados
        if nombre in aspectos_parrafo_dict
    ]

    oraciones_info = [
        {
            "numero": i+1,
            "oracion": item["oracion"],
        }
        for i, item in enumerate(oraciones)
    ]

    if not oraciones:
        return {
            "oracion": [],
            "parrafo": []
        }

    resultado = evaluador_parrafo(
        parrafo = texto,
        oraciones = oraciones_info,
        aspectos_oracion = aspectos_oracion,
        aspectos_parrafo = aspectos_parrafo
    )

    json_text = resultado.resultado_json.strip()

    if "```json" in json_text:
        json_text = (
            json_text
            .split("```json", 1)[1]
            .split("```", 1)[0]
            .strip()
        )
    elif "```" in json_text:
        json_text = json_text.split("```", "").strip()

    datos = json.loads(repair_json(json_text))

    if not isinstance(datos, dict):
        return {
            "oracion": [],
            "parrafo": []
        }

    resultados_oraciones = datos.get("oracion", [])
    resultados_parrafo = datos.get("parrafo", [])

    oraciones_detectadas = {
        "oracion": [],
        "parrafo": []
    }

    for resultado_oracion in resultados_oraciones:

        if not isinstance(resultado_oracion, dict):
            continue

        numero = resultado_oracion.get("oracion")

        # Comprobar que el número es válido
        if not isinstance(numero, int):
            continue

        if numero<1 or numero > len(oraciones):
            continue

        item = oraciones[numero-1]

        aspectos = resultado_oracion.get("aspectos", [])

        if not isinstance(aspectos, list):
            print("ERROR: 'aspectos' no es una lista")
            continue

        for aspecto in aspectos:

            if not isinstance(aspecto, dict):
                print("ERROR: el aspecto no es un diccionario")
                continue

            if aspecto.get("se_detecta", False):
                oraciones_detectadas["oracion"].append({
                    "inicio": item["inicio"],
                    "oracion": item["oracion"],
                    "aspecto": aspecto.get("aspecto", ""),
                    "razonamiento": aspecto.get("razonamiento", "")
                })

    for aspecto in resultados_parrafo:
        if not isinstance(aspecto, dict):
            continue

        if aspecto.get("se_detecta", False):
            oraciones_detectadas["parrafo"].append({
                "aspecto": aspecto.get("aspecto", ""),
                "razonamiento": aspecto.get("razonamiento", "")
            })

    return oraciones_detectadas

def separar_palabras(texto):
    """
    Separa el texto en palabras conservando la posición
    de cada palabra dentro del texto original.
    """

    palabras = []

    patron = re.compile(r'\b\w+\b', re.UNICODE)

    for i, match in enumerate(patron.finditer(texto), start=1):
        palabras.append({
            "indice": i,
            "palabra": match.group(),
            "inicio": match.start(),
            "fin": match.end()
        })

    return palabras

def ev_words(texto, aspectos_seleccionados=None):

    palabras = separar_palabras(texto)
    oraciones = separar_oraciones(texto)

    aspectos_dict = get_aspectos_palabra()

    if aspectos_seleccionados is None:
        aspectos_seleccionados = aspectos_dict.keys()

    aspectos_palabra = [
        {
            "nombre": nombre,
            "descripcion": aspectos_dict[nombre]
        }
        for nombre in aspectos_seleccionados
    ]

    palabras_info = [
        {
            "indice": palabra["indice"],
            "palabra": palabra["palabra"]
        }
        for palabra in palabras
    ]

    resultado = evaluador_palabras(
        parrafo=texto,
        palabras=palabras_info,
        aspectos_palabra=aspectos_palabra
    )

    if "```json" in resultado.resultado_json:
        json_text = (
            resultado.resultado_json
            .split("```json", 1)[1]
            .split("```", 1)[0]
        )
    else:
        json_text = resultado.resultado_json

    datos = json.loads(repair_json(json_text))

    if isinstance(datos, list):
        resultados_palabras = datos
    elif isinstance(datos, dict):
        resultados_palabras = datos.get("palabras", [])
    else:
        resultados_palabras = []

    palabras_detectadas = []

    for resultado_palabra in resultados_palabras:

        if not isinstance(resultado_palabra, dict):
            continue

        indice = resultado_palabra.get("indice")

        if not isinstance(indice, int):
            continue

        if indice < 1 or indice > len(palabras):
            continue

        palabra = palabras[indice - 1]

        oracion = ""
        inicio_oracion = None

        for item in oraciones:
            inicio_item = item["inicio"]
            fin_oracion = inicio_item + len(item["oracion"])

            if inicio_item <= palabra["inicio"] <= fin_oracion:
                oracion = item["oracion"]
                inicio_oracion = inicio_item
                break

        for aspecto in resultado_palabra.get("aspectos", []):

            if not isinstance(aspecto, dict):
                continue

            if aspecto.get("se_detecta", False):
                palabras_detectadas.append({
                    "palabra": palabra["palabra"],
                    "inicio": palabra["inicio"],
                    "fin": palabra["fin"],
                    "aspecto": aspecto.get("aspecto", ""),
                    "razonamiento": aspecto.get("razonamiento", ""),
                    "oracion": oracion,
                    "inicioFrase": inicio_oracion
                })

    return palabras_detectadas


class GenerarTablaHTML(dspy.Signature):
    """
    Genera una tabla HTML únicamente si el texto contiene datos
    estructurados suficientes para representarlos en forma tabular.
    """

    texto = dspy.InputField(
        desc="Texto del que se desea extraer una tabla."
    )

    es_posible = dspy.OutputField(
        desc="""
        Responde únicamente True o False.
        True si el texto contiene suficiente información estructurada
        para construir una tabla.
        False en caso contrario.
        """
    )

    caption = dspy.OutputField(
        desc = """
        Si es_posible=True, genera un título breve y descriptivo para la tabla,
        que permita entender qué información muestra.
        No incluyas la plabra "Tabla", números, HTML ni comillas.
        Devuelve únicamente el texto del título.
        
        Si es_poisble=False, devuelve una cadena vacía.
        """
    )

    tabla_html = dspy.OutputField(
        desc="""
        Si es_posible=True, devuelve únicamente el código HTML de una tabla
        válida utilizando las etiquetas:
        <table>, <thead>, <tbody>, <tr>, <th>, <td>.

        No icnluyas la etiqueta <caption>.
        No incluyas markdown, ni ```html.

        Si es_posible=False, devuelve una cadena vacía.
        """
    )

    razon = dspy.OutputField(
        desc="""
        Explica brevemente por qué sí o por qué no ha sido posible
        generar la tabla.
        """
    )


generador_tabla = dspy.Predict(GenerarTablaHTML)


def generar_tabla_html(texto):
    resultado = generador_tabla(texto=texto)

    posible = str(resultado.es_posible).strip().lower() == "true"

    html = resultado.tabla_html.strip()
    caption = resultado.caption.strip()

    # Eliminar posibles bloques markdown
    if html.startswith("```"):
        html = html.replace("```html", "").replace("```", "").strip()

    if posible:
        html = html.replace(
            "<table>",
            f"<table>\n<caption>{caption}</caption>", 1
        )
        return {
            "success": True,
            "html": html,
            "caption": caption,
            "message": "Tabla generada correctamente."
        }

    return {
        "success": False,
        "html": None,
        "caption": None,
        "message": "No es posible generar una tabla HTML con la información disponible.",
        "reason": resultado.razon
    }