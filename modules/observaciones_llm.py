#!/usr/bin/env python
# coding: utf-8

# In[1]:

import json
import dspy
from pydantic import BaseModel
import dspy

lm = dspy.LM('ollama_chat/gemma4:12b', api_base='http://ollama:11434',think=False)
dspy.configure(lm=lm)


ASPECTOS = {
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
    Existe una posible digresión cuando el texto incorpora información, comentarios o desarrollos que se alejan del tema principal sin contribuir de forma clara a su explicación o desarrollo. Se manifiesta mediante la introducción de ideas secundarias, ejemplos o detalles que interrumpen el hilo argumental y desvían la atención del lector. Un texto presenta una digresión cuando una parte significativa de su contenido no guarda una relación directa con el propósito comunicativo o con el tema central tratado.
    """,
}

# aspectos_seleccionados = [
#     "coherencia_interna",
#     "progresion_tematica",
#     "claridad_ideas",
#     "coherencia_externa",
#     "posible_disgresion"
    
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

def evaluate_text(texto,aspectos_seleccionados=None):
    
    if aspectos_seleccionados is None:
        aspectos_seleccionados = ASPECTOS.keys()
        
    aspectos = [
    {
        "nombre": nombre,
        "descripcion": ASPECTOS[nombre]
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

    datos = json.loads(json_text)
    return datos
