from openjev_decide import OpenJev
from modules.observaciones_llm import *
import gc
import torch
# code/openjev_decide.py


def evaluate_text(texto, fin):
    jev = OpenJev.from_pretrained("AlexWortega/openjev", subfolder="qwen3.5-4b-nli-v5", device="cuda")
    instrucciones1 = " Existe falta de coherencia interna cuando las ideas de un texto presentan contradicciones, incompatibilidades lógicas, reiteraciones innecesarias o saltos informativos que dificultan la comprensión global del mensaje. Se manifiesta cuando una afirmación contradice otra, cuando se repite información sin aportar contenido nuevo o cuando se introducen ideas sin relación clara con el contenido previo. ¿Existe falta de coherencia interna?"
    instrucciones2 =  "Existe falta de progresión temática cuando las ideas no avanzan de forma ordenada y el texto no desarrolla gradualmente la información. Se manifiesta mediante cambios bruscos de tema, introducción de información sin conexión con lo anterior o ausencia de relaciones lógicas entre las distintas partes del texto. La progresión temática adecuada implica que cada idea amplíe, complemente o desarrolle la información previamente presentada. ¿Existe falta de progresión temática?"
    instrucciones3 = "Existe falta de claridad entre ideas cuando sus relaciones no son evidentes para el lector. Puede deberse a ausencia o uso inadecuado de conectores o marcadores, o a relaciones no explícitas de causa-efecto, secuencia temporal, contraste, ejemplificación o adición. ¿Existe falta de claridad entre ideas?"
    instrucciones4 = "Existe falta de coherencia externa cuando la organización global no se ajusta a la estructura esperada de un texto divulgativo: introducción, desarrollo y conclusión no se distinguen claramente, falta alguna de estas partes o su organización dificulta comprender el propósito general. ¿Existe falta de coherencia externa?"
    instrucciones5 = "Existe posible digresión cuando se incorpora información, comentarios o desarrollos que se alejan del tema principal sin contribuir claramente a su explicación o desarrollo. Incluye ideas secundarias, ejemplos o detalles que interrumpen el hilo y desvían la atención. Márcala cuando una parte significativa del contenido no guarde relación directa con el tema central o propósito comunicativo. ¿Existe una posible disgresión?"
    instrucciones6 = f"Existe falta de adecuación a la finalidad comunicativa cuando el contenido, la organización o el tono no contribuyen al propósito principal de {fin}, o cuando el texto se desvía de él, incorpora recursos que no lo favorecen o desarrolla el tema de forma incompatible con dicho propósito. ¿Existe falta de adecuación a la finalidad comunicativa?"
    instrucciones7 = "Existe falta de adecuación al destinatario cuando el nivel de lenguaje, los conocimientos previos, la cantidad de información o la forma de explicar los contenidos no se ajustan a un adulto que ha finalizado la ESO. ¿Existe falta de adecuación al destinatario?"
    instrucciones8 = "Existe una falta de apartados cuando el texto contiene varias partes o bloques temáticos claramente diferenciados y sería recomendable dividirlos mediante títulos o encabezados para facilitar la comprensión de la estructura, localizar información o seguir la explicación. En caso contrario, marca false. ¿Existe una falta de apartados?"

    resultados = jev.decide(texto,
               [{"type": "noul", "instructions": instrucciones1, "options": ["no", "yes"]},
               {"type": "noul", "instructions": instrucciones2, "options": ["no", "yes"]},
                {"type": "noul", "instructions": instrucciones3, "options": ["no", "yes"]},
                {"type": "noul", "instructions": instrucciones4, "options": ["no", "yes"]},
                {"type": "noul", "instructions": instrucciones5, "options": ["no", "yes"]},
                {"type": "noul", "instructions": instrucciones6, "options": ["no", "yes"]},
                {"type": "noul", "instructions": instrucciones7, "options": ["no", "yes"]},
                {"type": "noul", "instructions": instrucciones8, "options": ["no", "yes"]}])
    del jev
    torch.cuda.empty_cache()
    gc.collect()
    return resultados

def evaluate_sentences(texto):
    jev = OpenJev.from_pretrained("AlexWortega/openjev", subfolder="qwen3.5-4b-nli-v5", device="cuda")
    aspectos_oracion = {
        "inciso": "Existe un inciso cuando una construcción interrumpe la estructura principal de la oración para añadir información adicional, aclaratoria o secundaria. Puede aparecer entre comas, paréntesis, rayas u otros signos equivalentes. No consideres incisos las comas que separan elementos de una enumeración ni las que forman parte de la estructura sintáctica normal. ¿Existe alguna oración con inciso en el texto?",
    "modificador": "Existe un modificador o complemento entre el sujeto y su verbo principal cuando una información adicional interrumpe su relación directa. Solo debe detectarse si está realmente entre el sujeto y el verbo principal. No consideres modificaciones que formen parte del propio sujeto ni complementos posteriores al verbo. ¿Existe alguna oración con un modificador entre el sujeto y el verbo principal en el texto?",
    "coordinada": "Existe una oración coordinada si la oración contiene tres o más proposiciones coordinadas. Una proposición coordinada está al mismo nivel sintáctico que otra y se une a ella mediante un nexo coordinante explícito, como 'y', 'e', 'ni', 'o', 'u', 'pero', 'sino', etc. Solo cuenta la coordinación cuando el nexo une proposiciones u oraciones, no palabras o grupos de palabras. ¿Existe alguna oración coordinada en el texto?",
    "yuxtaposicion": "Existe una oración yuxtapuesta si la oración contiene tres o más proposiciones yuxtapuestas. Una proposición yuxtapuesta está al mismo nivel sintáctico que otra y se relaciona con ella sin nexo coordinante explícito, únicamente mediante un signo de puntuación, como coma, punto y coma o dos puntos. Solo cuenta la yuxtaposición cuando el signo separa dos proposiciones u oraciones del mismo nivel sintáctico. ¿Existe alguna oración yuxtapuesta en el texto?",
    "relativa": "Existe una oración de relativo compleja por su estructura o por la distancia entre la relativa y su antecedente. Es compleja si cumple al menos una de estas condiciones: 1. Relativos encapsulados: una oración de relativo aparece dentro de otra oración de relativo. 2. Relativo alejado de su antecedente: existe una cantidad considerable de material entre ambos, especialmente otras proposiciones, incisos u otros elementos que dificulten identificar el referente. ¿Existe alguna oración de relativo compleja en el texto?",
    "concordancia": "¿Existe alguna oración con errores gramaticales de concordancia en el texto?",
    "gerundio": "Responde sí únicamente si la oración contiene un verbo en gerundio y ese gerundio expresa una acción posterior a la acción principal. Responde no en todos los demás casos. ¿Existe un uso erróneo del gerundio?",
    "redundancia": "Existe redundancia cuando se repite innecesariamente una misma información, idea o significado mediante palabras o expresiones que no aportan contenido nuevo. ¿Existe alguna oración con redundancia innecesaria en el texto?",
    "enfasis": "Existe una formulación enfática cuando contiene expresiones intensificadoras, reiterativas o enfáticas innecesarias que pueden hacer el mensaje más complejo o menos directo. ¿Existe alguna oración con énfasis innecesario para transmitir el significado?",
    "rodeos": "Existe un rodeo expresivo cuando una idea puede expresarse de forma más directa, sencilla y concisa mediante un verbo simple, pero se usa una construcción más larga o perifrástica que añade complejidad innecesaria. Debe poder sustituirse la expresión nominal o construcción equivalente por un verbo simple sin cambiar significativamente el significado. ¿Existe algún rodeo en el texto?",
    "negativas": "Existe una oración negativa cuando contiene dos o más elementos de negación combinados en la misma estructura. Cuenta como elementos negativos: 1. Partículas, pronombres o determinantes negativos explícitos ('no', 'jamás', 'ningún', etc.). 2. Palabras o expresiones con significado negativo ('infrecuente', 'desleal', 'imposible', etc.). ¿Existe alguna oración negativa en el texto?",
    "secundaria": "Existe información secundaria cuando la oración contiene contenido adicional no necesario para comprender la idea principal, introducido como información complementaria, aclaratoria o accesoria. Se dice cuando una idea principal claramente identificable se combina con uno o varios datos secundarios que pueden dificultar innecesariamente la comprensión. ¿Existe información secundaria en el texto?"
    }

    aspectos_parrafo = {
        "perdida_referente": "Existe pérdida de referente cuando no se puede identificar claramente a qué persona, objeto, concepto o entidad se refiere una expresión posterior del párrafo. Puede ocurrir si un pronombre, demostrativo o expresión nominal no tiene un antecedente claro, si hay varios antecedentes posibles o si la referencia no puede relacionarse fácilmente con la información previa. ¿Existe pérdida de referente en el texto?",
    "uso_abundante_negativas": "Existe un uso abundante de formulaciones negativas solo si se cumplen ambas condiciones: 1. Al menos dos oraciones del párrafo contienen una acumulación de elementos o expresiones de modalidad negativa.  2. La repetición de estas formulaciones tiene una presencia relevante en el párrafo. ¿Existe un uso abundante de formulaciones negativas en el texto?",
    "idea_principal": "Existe presentación tardía de la idea principal cuando el mensaje central del párrafo aparece después de una parte significativa de información secundaria, contextual o explicativa, de modo que el lector debe avanzar bastante para identificarlo. ¿Existe presentación tardía de la idea principal en el texto?"

    }

    oraciones = separar_oraciones(texto)

    if not oraciones:
        return {
            "oracion": [],
            "parrafo": []
        }

    resultados_oraciones = []

    instrucciones_oracion = [
            {
                "type": "noul",
                "instructions": descripcion,
                "options": ["no", "yes"]
            }
            for descripcion in aspectos_oracion.values()
         ]

    for item in oraciones:
        texto_oracion = item["oracion"]

        evaluaciones =  jev.decide(
            texto_oracion,
            instrucciones_oracion
        )

        for criterio, evaluacion in zip(aspectos_oracion.keys(), evaluaciones):
            if evaluacion["noul"]>0.5:
                resultados_oraciones.append({
                    "inicio": item["inicio"],
                    "oracion": texto_oracion,
                    "aspecto": criterio,
                    "razonamiento": ""
                })

    instrucciones_parrafo = [
        {
            "type": "noul",
            "instructions": descripcion,
            "options": ["no", "yes"]
        }
        for descripcion in aspectos_parrafo.values()
    ]

    evaluaciones_parrafo = jev.decide(
        texto,
        instrucciones_parrafo
    )

    resultados_parrafo = []

    for criterio, evaluacion in zip(aspectos_parrafo.keys(), evaluaciones_parrafo):
        if evaluacion["noul"]>0.5:
            resultados_parrafo.append({
                "aspecto": criterio,
                "razonamiento": ""
            })

    #instrucciones_oracion = {0: "inciso",
    #                 1: "modificador",
    #                 2: "coordinadada",
    #                 3: "yuxtaposicion",
    #                 4: "relativa",
    #                 5: "concordancia",
    #                 6: "gerundio",
    #                 7: "redundancia",
    #                 8: "enfasis",
    #                 9: "rodeos",
    #                 10:"negativas",
    #                 11: "secundaria"}

    #for i, resultado in enumerate(resultados_oracion):
    #    if resultado["noul"]>0.5:
    #        criterios_oracion.append(instrucciones_oracion[i])


    #resultados_parrafo = jev.decide(texto,
    #                                [{"type": "noul", "instructions": perdida_referente, "options": ["no", "yes"]},
    #                                 {"type": "noul", "instructions": uso_abundante_negativas, "options": ["no", "yes"]},
    #                                 {"type": "noul", "instructions": idea_principal, "options": ["no", "yes"]}])

    #instrucciones_parrafo = {
    #    0: "perdida_referente",
    #    1: "uso_abundante_negativas",
    #    2: "idea_principal"
    #}

    #for i, resultado in enumerate(resultados_parrafo):
    #    if resultado["noul"]>0.5:
    #        criterios_parrafo.append(instrucciones_parrafo[i])

    #resultados = ev_sentences(texto, aspectos_seleccionados=criterios_oracion, aspectos_parrafo_seleccionados=criterios_parrafo)

    del jev
    torch.cuda.empty_cache()
    gc.collect()

    return {"oracion": resultados_oraciones, "parrafo": resultados_parrafo}

def evaluate_words(texto):
    jev = OpenJev.from_pretrained("AlexWortega/openjev", subfolder="qwen3.5-4b-nli-v5", device="cuda")
    aspectos = {
        "siglas": "Busca en la oración cualquier sigla, como OMS, ONU, UE o DNI. Si aparece una sigla y su significado no está explicado en la oración responde verdadero. Si no aparece ninguna sigla o si la sigla aparece acompañada de su significado responde falso.",
        "lexico_poco_frecuente": "Existe léxico poco frecuente cuando una palabra es poco habitual en el uso general del español y puede resultar desconocida para una parte importante de los lectores. ¿Hay alguna palabra poco frecuente en el texto?",
        "palabra_baul": "Existe una palabra baúl cuando su significado es excesivamente general o impreciso y sustituye a una expresión más concreta que transmitiría la información con mayor precisión. Debe resultar demasiado inespecífica en el contexto concreto. ¿Hay alguna palabra baúl en el texto?",
        "extranjerismo": "Existe un extranjerismo cuando una palabra procede de otra lengua y se utiliza en español manteniendo una forma o uso propio de la lengua de origen. ¿Hay algún extranjerismo en el texto?",
        "ambigua": "Existe ambigüedad léxica cuando una palabra admite interpretaciones relevantes distintas en el contexto y su significado no puede determinarse con suficiente claridad. ¿Existe ambigüedad léxica en el texto?",
        "elemento_valorativo": "Existe un elemento valorativo cuando una palabra expresa una valoración, juicio, opinión o apreciación subjetiva sobre una persona, objeto, situación o hecho. ¿Existe algún elemento valorativo en el texto?",
        "tecnicismo": "Existe un tecnicismo cuando una palabra pertenece específicamente al vocabulario especializado de un ámbito científico, técnico, profesional o académico y puede resultar poco familiar para lectores no especializados. ¿Existe algún tecnicismo de uso especializado en el texto?",
        "coloquialismo": "Existe un coloquialismo cuando una palabra o expresión pertenece principalmente al registro coloquial o informal y puede resultar inadecuada en un texto divulgativo dirigido a un público general. ¿Existe algún coloquialismo en el texto?",
        "vulgarismo": "Existe un vulgarismo cuando una palabra presenta una forma o uso incorrecto o no normativo en el español estándar. ¿Hay algún vulgarismo en el texto?"
    }

    oraciones = separar_oraciones(texto)

    resultados = []

    for oracion in oraciones:
        texto_oracion = oracion["oracion"]
        inicio_oracion = oracion["inicio"]
        fin_oracion = inicio_oracion + len(texto_oracion)

        evaluaciones = jev.decide(texto_oracion,
            [
                {
                    "type": "noul",
                    "instructions": descripcion,
                    "options": ["no", "yes"]
                }
                for descripcion in aspectos.values()
                ]
            )
    for criterio, evaluacion in zip(aspectos.keys(), evaluaciones):
        if evaluacion["noul"]>0.5:
            resultados.append({
                "palabra": "",
                "inicio": inicio_oracion,
                "fin": fin_oracion,
                "aspecto": criterio,
                "oracion": texto_oracion,
                "inicioFrase": inicio_oracion
            })

    #instrucciones = {
    #    0: "sigla",
    #    1: "lexico_poco_frecuente",
    #    2: "palabra_baul",
    #    3: "extranjerismo",
    #    4: "ambigua",
    #    5: "elemento_valorativo",
    #    6: "tecnicismo",
    #    7: "coloquialismo",
    #    8: "vulgarismo"
    #}
    #criterios = []

    #for i, resultado in enumerate(resultados_palabras):
    #    if resultado["noul"]>0.5:
    #        criterios.append(instrucciones[i])

    #resultados = ev_words(texto, aspectos_seleccionados=criterios)
    del jev
    torch.cuda.empty_cache()
    gc.collect()

    return resultados
