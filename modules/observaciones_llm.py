#!/usr/bin/env python
# coding: utf-8

# In[1]:

import json
from json_repair import repair_json
import dspy
from litellm.proxy.common_utils.callback_utils import initialize_callbacks_on_proxy
from pydantic import BaseModel
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
    Existe falta de coherencia interna cuando las ideas de un texto presentan contradicciones, incompatibilidades lógicas, reiteraciones innecesarias o saltos informativos que dificultan la comprensión global del mensaje. Se manifiesta cuando una afirmación contradice otra, cuando se repite información sin aportar contenido nuevo o cuando se introducen ideas sin relación clara con el contenido previo.
    """,

        "progresion_tematica": """
    Existe falta de progresión temática cuando las ideas no avanzan de forma ordenada y el texto no desarrolla gradualmente la información. Se manifiesta mediante cambios bruscos de tema, introducción de información sin conexión con lo anterior o ausencia de relaciones lógicas entre las distintas partes del texto. La progresión temática adecuada implica que cada idea amplíe, complemente o desarrolle la información previamente presentada.
    """,

        "claridad_ideas": """
    Existe falta de claridad entre ideas cuando las relaciones entre las distintas partes del texto no resultan evidentes para el lector. Se manifiesta por la ausencia o el uso inadecuado de conectores y marcadores discursivos, así como por la falta de relaciones explícitas de causa-efecto, secuencia temporal, contraste, ejemplificación o adición. Como consecuencia, el lector puede tener dificultades para comprender cómo se conectan las ideas entre sí.
    """,

        "coherencia_externa": """
    Existe falta de coherencia externa cuando la organización global del texto no se ajusta a la estructura esperada para un texto divulgativo. Se manifiesta cuando no se distinguen claramente la introducción, el desarrollo y la conclusión, cuando alguna de estas partes está ausente o cuando su organización dificulta la comprensión del propósito general del texto. Un texto presenta coherencia externa cuando su estructura global resulta clara, ordenada y fácilmente reconocible por el lector.
    """,

        "posible_disgresion": """
    Existe una posible digresión cuando el texto incorpora información, comentarios o desarrollos que se alejan del tema principal sin contribuir de forma clara a su explicación o desarrollo. Se manifiesta mediante la introducción de ideas secundarias, ejemplos o detalles que interrumpen el hilo argumental y desvían la atención del lector. Un texto presenta una digresión cuando una parte significativa de su contenido no guarda una relación directa con el propósito comunicativo o con el tema central tratado.
    """,

        "finalidad_comunicativa": """
    Existe una falta de adecuación a la finalidad comunicativa cuando el contenido, la organización o el tono del texto no contribuyen al propósito principal de {fin}. Se manifiesta cuando el texto se desvía de su objetivo comunicativo, incorpora información o recursos que no favorecen dicha finalidad o desarrolla el tema de una manera incompatible con el propósito previsto. 
    Un texto mantiene la finalidad comunicativa cuando todas sus partes contribuyen de forma coherente a {fin}.""",

        "destinatario": """
        Existe falta de adecuación al destinatario cuando el texto utiliza un nivel
    de lenguaje, unos conocimientos previos, una cantidad de información o una
    forma de explicar los contenidos que no se ajustan a un adulto que ha
    finalizado la educación secundaria obligatoria (ESO).
        """,
        "apartados": """
        Determina si sería recomendable organizar el texto en varios apartados
        diferenciados mediante títulos o encabezados.

        Debe marcarse como true cuando el texto completo contiene varias partes
        o bloques temáticos claramente diferenciados y la división mediante
        apartados ayudaría al lector a comprender mejor la estructura del
        contenido, localizar información o seguir la explicación.
        """
    }

def get_aspectos_parrafo():
    return {
        "perdida_referente": """
        Existe pérdida de referente cuando el lector no puede identificar
        con claridad a qué persona, objeto, concepto o entidad se refiere
        una expresión utilizada posteriormente en el párrafo.

        Puede producirse, por ejemplo, cuando se utiliza un pronombre,
        demostrativo, expresión nominal o referencia similar cuyo antecedente
        no está suficientemente claro, cuando existen varios posibles
        antecedentes y no se puede determinar cuál es el correcto, o cuando
        se introduce una referencia que el lector no puede relacionar
        fácilmente con la información presentada anteriormente.
        """,
        "uso_abundante_negativas": """
    Existe un uso abundante de formulaciones negativas cuando en un mismo
    párrafo dos o más oraciones presentan una acumulación de elementos o
    expresiones de modalidad negativa, de manera que la presencia reiterada
    de estas formulaciones puede dificultar la comprensión del texto.

    Para considerar que existe este aspecto, deben cumplirse ambas condiciones:
    - al menos dos oraciones del párrafo contienen una acumulación de
      elementos de modalidad negativa;
    - la repetición de estas formulaciones tiene una presencia relevante
      en el párrafo.

    No debe detectarse únicamente porque el párrafo contenga varias
    negaciones aisladas. Tampoco debe considerarse problemática la presencia
    normal de una negación en una oración.
    """,
        "idea_principal": """
        Existe una presentación tardía de la idea principal cuando la idea
        principal o el mensaje central del párrafo no aparece al principio,
        sino que se introduce después de información secundaria,
        contextual, explicativa o de otro tipo.

        Debe marcarse como true cuando el lector necesita leer una parte
        significativa del párrafo antes de identificar con claridad cuál es
        la idea principal que se quiere transmitir.

        Debe marcarse como false cuando la idea principal aparece al comienzo
        del párrafo y las oraciones posteriores la desarrollan, explican,
        justifican o amplían.
        """
    }

def get_aspectos_oracion():
    return {
        "inciso": """
            Existe un inciso cuando una construcción interrumpe la estructura principal
            de la oración para introducir información adicional, aclaratoria o secundaria.
            Puede aparecer entre comas, paréntesis, rayas u otros signos equivalentes.

            No deben considerarse incisos las comas que simplemente separan elementos
            de una enumeración ni las que forman parte de la estructura sintáctica normal
            de la oración.
            """,

        "modificador": """
            Existe un modificador o complemento entre el sujeto y el verbo cuando,
            una vez identificado el sujeto principal de la oración, aparece entre este
            y su verbo principal una información adicional que interrumpe la relación
            directa entre sujeto y verbo.
            
            Debe detectarse únicamente cuando el modificador o complemento se sitúa
        realmente entre el sujeto y su verbo principal. No deben considerarse
        modificaciones que formen parte del propio sujeto ni complementos que
        aparezcan después del verbo.
            
            """,
        "coordinada": """
        Detecta si la oración contiene tres o más proposiciones coordinadas.
        
        Una PROPOSICIÓN COORDINADA es una proposición u oración que está al mismo nivel sintáctico que otra proposición y que se une a ella mediante un
        NEXO COORDINANTE EXPLÍCITO.
        
        Los nexos coordinantes pueden ser, entre otros, "y", "e", "ni", "o", "u", "pero", "sino", etc.

        Solo debe considerarse coordinación cuando el nexo une proposiciones u oraciones, no cuando une palabras o grupos de palabras.
        
        """,
        "yuxtaposicion": """
        Detecta si la oración contiene tres o más proposiciones yuxtapuestas.
        
        Una PROPOSICIÓN YUXTAPUESTA es una proposición u oración que está al mismo nivel sintáctico que otra proposición y
        que se relaciona con ella sin un nexo coordinante explícito, utilizando únicamente un SIGNO DE PUNTUACIÓN.
        
        Los signos de puntuación pueden ser, entre otros, coma (","), punto y coma (";") y dos puntos (":").
        
        Solo debe considerarse yuxtaposición cuando el signo de puntuación separa dos proposiciones u oraciones del mismo nivel sintáctico

        """,
        "relativa": """
        Detecta si existe una ORACIÓN DE RELATIVO COMPLEJA debido a la
    estructura o a la distancia entre la oración de relativo y su
    antecedente.

    Una ORACIÓN DE RELATIVO es una oración subordinada que modifica o se
    refiere a un antecedente o elemento anterior. Se considera que una oración de relativo es COMPLEJA cuando presenta
    alguna de las siguientes características:

    1. RELATIVOS ENCAPSULADOS:
       Una oración de relativo aparece dentro de otra oración de relativo,
       de manera que una estructura relativa queda incluida dentro de otra.

    2. RELATIVO ALEJADO DE SU ANTECEDENTE:
       La oración de relativo está separada de su antecedente por una
       cantidad considerable de material lingüístico, especialmente cuando
       entre ambos aparecen otras proposiciones, incisos u otros elementos
       que pueden dificultar la identificación del referente.
        """,
        "concordancia": """
        Existe falta de concordancia cuando se produce un error gramatical de
    concordancia dentro de la oración.
    Debe detectarse únicamente cuando exista una discordancia gramatical
    real. No deben marcarse como errores las construcciones que sean
    gramaticalmente correctas aunque puedan resultar menos habituales o
    complejas.
        """,
        "gerundio": """
        Existe un uso erróneo del gerundio cuando el gerundio expresa una acción
        posterior a la acción principal de la oración. En español normativo, el
        gerundio debe expresar normalmente una acción simultánea o anterior a la
        acción principal, pero no una acción que ocurre posteriormente.
    
        Debe detectarse especialmente cuando una oración presenta una estructura
        en la que primero ocurre la acción expresada por el verbo principal y,
        posteriormente, ocurre la acción expresada por el gerundio.
        """,
        "redundancia": """
                Existe redundancia cuando la oración repite innecesariamente una misma
                información, idea o significado mediante palabras o expresiones que no
                aportan contenido nuevo. Debe detectarse únicamente cuando exista una repetición innecesaria de significado.
            """,

        "enfasis": """
                Existe una formulación enfática cuando la oración utiliza expresiones
                intensificadoras, reiterativas o enfáticas que no aportan información
                necesaria y que pueden hacer que el mensaje resulte más complejo o
                menos directo. Debe detectarse únicamente cuando el énfasis sea innecesario para transmitir el significado.
            """,
        "rodeos": """
        Existe un rodeo expresivo cuando una idea puede expresarse de forma
    más directa, sencilla y concisa mediante un verbo simple, pero se
    utiliza una construcción más larga o perifrástica que aporta una
    complejidad innecesaria.

    Debe detectarse cuando una expresión nominal o una construcción
    equivalente puede sustituirse por un verbo simple sin cambiar
    significativamente el significado.
        """,
        "negativas": """
    Detecta si la oración contiene dos o más elementos de negación que aparecen combinados dentro de la misma estructura oracional.
    Considera como elementos de modalidad negativa tanto:
        1. Partículas, pronombres o determinantes negativos explícitos (como "no", "jamás", "ningún", etc)
        2. Palabras o expresiones con significado negativo (como "infrecuente", "desleal", "imposible", etc)
    """,

        "info_secundaria": """
        Existe información secundaria en la oración cuando esta contiene una
        información adicional que no es necesaria para comprender la idea
        principal de la oración, pero que se introduce como contenido
        complementario, aclaratorio o accesorio.
    
        Debe detectarse cuando la oración combina una idea principal claramente
        identificable con uno o varios datos secundarios que pueden dificultar
        innecesariamente la comprensión del mensaje.
        """
    }

def get_aspectos_palabra():
    return {
        "sigla": """
        Existe una sigla cuando la palabra o secuencia analizada está formada
        por las letras iniciales de varias palabras y se utiliza como una
        denominación abreviada, por ejemplo, OMS, ONU, UE o ADN.

        Debe detectarse únicamente cuando se trate realmente de una sigla y cuando
        su significado no esté explicado o sea desconocido para el lector en el contexto del texto.
        Si una sigla aparece acompañada de su denominación completa o de
        una explicación que permita conocer su significado, no debe marcarse como sigla.
        
        No deben marcarse como siglas las palabras escritas completamente
        en mayúsculas que sean palabras comunes.
        """,

        "lexico_poco_frecuente": """
        Existe léxico poco frecuente cuando la palabra es poco habitual en
        el uso general del español y puede resultar desconocida para una
        parte importante de los lectores.

        Debe tenerse en cuenta la frecuencia de uso general de la palabra
        y no únicamente que sea una palabra larga, culta o especializada.
        No deben marcarse automáticamente los tecnicismos, ya que estos
        tienen una categoría específica.
        """,

        "palabra_baul": """
        Existe una palabra baúl cuando una palabra tiene un significado
        excesivamente general o impreciso y sustituye a una expresión más
        concreta que permitiría transmitir la información con mayor precisión.

        Deben detectarse palabras cuyo significado resulta demasiado
        inespecífico en el contexto concreto en el que aparecen.
        """,

        "extranjerismo": """
        Existe un extranjerismo cuando la palabra procede de otra lengua
        y se utiliza en español manteniendo una forma o uso propio de la
        lengua de origen.

        Debe detectarse únicamente cuando la palabra utilizada sea realmente
        un extranjerismo en el contexto analizado.
        """,

        "ambigua": """
        Existe ambigüedad léxica cuando la palabra puede interpretarse de
        distintas maneras relevantes en el contexto y su significado no
        puede determinarse con suficiente claridad.

        No debe marcarse una palabra simplemente porque tenga varios
        significados posibles en el diccionario. La ambigüedad debe afectar
        a la interpretación del texto concreto.
        """,

        "elemento_valorativo": """
        Existe un elemento valorativo cuando la palabra expresa una
        valoración, juicio, opinión o apreciación subjetiva sobre una
        persona, objeto, situación o hecho.
        """,

        "tecnicismo": """
        Existe un tecnicismo cuando la palabra pertenece de manera específica
        al vocabulario especializado de un ámbito científico, técnico,
        profesional o académico y puede resultar poco familiar para lectores
        no especializados.

        Debe detectarse únicamente cuando el uso de la palabra tenga un
        carácter especializado en el contexto analizado.
        """,

        "coloquialismo": """
        Existe un coloquialismo cuando la palabra o expresión pertenece
        principalmente al registro coloquial o informal de la lengua y puede
        resultar inadecuada en un texto divulgativo dirigido a un público
        general.

        No deben marcarse como coloquialismos las palabras de uso general
        simplemente porque puedan aparecer también en conversaciones
        informales.
        """,

        "vulgarismo": """
        Existe un vulgarismo cuando la palabra presenta una forma o un uso
        considerado incorrecto o no normativo en el español estándar.

        Debe detectarse únicamente cuando exista un uso lingüístico realmente
        no normativo. No deben marcarse como vulgarismos las variantes
        regionales o las formas coloquiales que sean correctas.
        """,
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
        desc="Lista de oraciones del párrafo, con su número y posición."
    )
    aspectos_oracion = dspy.InputField(
        desc="Lista de aspectos que deben evaluarse individualmente en cada oración."
    )
    aspectos_parrafo = dspy.InputField(
        desc = "Lista de aspectos que deben evaluarse teniendo en cuenta el párrafo completo y las relaciones entre sus oraciones."
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
        desc="Lista de aspectos que deben evaluarse para cada palabra."
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



def evaluate_text(texto, fin, aspectos_seleccionados=None):
    aspectos_dict = get_aspectos(fin)
    if aspectos_seleccionados is None:
        aspectos_seleccionados = aspectos_dict.keys()

    aspectos = [
        {
            "nombre": nombre,
            "descripcion": aspectos_dict[nombre]
        }
        for nombre in aspectos_seleccionados]

    resultado = evaluador(
        texto=texto,
        aspectos=aspectos
    )
    if "```json" in resultado.resultado_json:
        json_text = resultado.resultado_json.split("```json", 1)[1].split("```", 1)[0]
    else:
        json_text = resultado.resultado_json

    datos = json.loads(repair_json(json_text))
    if isinstance(datos, dict):

        datos_normalizados = []

        for nombre, valor in datos.items():

            # Convertir "True"/"False" en booleanos
            if isinstance(valor, str):
                valor_lower = valor.strip().lower()

                if valor_lower == "true":
                    se_detecta = True
                elif valor_lower == "false":
                    se_detecta = False
                else:
                    se_detecta = False
            else:
                se_detecta = bool(valor)

            datos_normalizados.append({
                "aspecto": nombre,
                "se_detecta": se_detecta,
                "razonamiento": ""
            })

        datos = datos_normalizados

    return datos

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

def evaluate_sentences(texto, aspectos_seleccionados=None, aspectos_parrafo_seleccionados=None):
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
    ]
    aspectos_parrafo = [
        {
            "nivel": "parrafo",
            "nombre": nombre,
            "descripcion": aspectos_parrafo_dict[nombre]
        }
        for nombre in aspectos_parrafo_seleccionados
    ]

    oraciones_info = [
        {
            "numero": i+1,
            "oracion": item["oracion"],
        }
        for i, item in enumerate(oraciones)
    ]

    resultado = evaluador_parrafo(
        parrafo = texto,
        oraciones = oraciones_info,
        aspectos_oracion = aspectos_oracion,
        aspectos_parrafo = aspectos_parrafo
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

    oraciones_detectadas = {
        "oracion": [],
        "parrafo": []
    }
    if isinstance(datos, list):
        resultados_oraciones = datos
        resultados_parrafo = []
    elif isinstance(datos, dict):
        resultados_oraciones = datos.get("oracion", [])
        resultados_parrafo = datos.get("parrafo", [])
    else:
        resultados_oraciones = []
        resultados_parrafo = []

    for resultado_oracion in resultados_oraciones:

        numero = resultado_oracion["oracion"]

        # Comprobar que el número es válido
        if not isinstance(numero, int):
            continue

        if numero<1 or numero > len(oraciones):
            continue

        item = oraciones[numero-1]

        aspectos_resultado = resultado_oracion.get("aspectos", [])

        if not isinstance(aspectos_resultado, list):
            print("ERROR: 'aspectos' no es una lista")
            continue

        for aspecto in aspectos_resultado:

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

def evaluate_words(texto, aspectos_seleccionados=None):

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