from ollama import chat
from ollama import ChatResponse
import json

def obtenerSugerenciaParrafo(comment):
    texto = comment.get("texto", "")
    instruccion = (f"""
    Reescribe en castellano el siguiente párrafo manteniendo toda la información. Cambia lo mínimo posible.
    REGLAS:
    - Frases de menos de 20 palabras.
    - Orden sujeto-verbo-complementos.
    - Evita la voz pasiva.
    - Evita incisos.
    - Usa verbos conjugados.
    - Evita varias negaciones en la misma frase.
    PÁRRAFO ORIGINAL:
    {texto}
    DEVUELVE SOLO EL NUEVO PÁRRAFO, SIN COMILLAS, SIN EXPLICACIONES, SIN SALTOS DE LÍNEA INICIALES NI FINALES.
    """)

    response: ChatResponse = chat(
        #model = "nichonauta/pepita-2-2b-it-v5",
        #model = "mistral",
        model = "gemma4:e4b",
        messages = [
            {
                "role": "user",
                "content": instruccion
            }
        ],
    think= False
    )
    sugerencia = response.message.content.strip()
    return sugerencia

def obtenerSugerencia(oracion, palabra, criterio):
    instrucciones_criterios = {
        "lexFrec": """
    Sustituye la palabra por otra más frecuente y habitual en español,
    manteniendo el mismo significado y adecuándola al contexto.
    """,

        "baul": """
    Sustituye la palabra por un término más específico y preciso,
    manteniendo el significado que tiene en el contexto.
    """,

        "extranjerismo": """
    Sustituye el extranjerismo por una palabra o expresión equivalente
    en español, siempre que exista una alternativa natural.
    """,

        "ambiguo": """
    Sustituye la palabra por una expresión que resulte más clara y
    elimine la posible ambigüedad en este contexto.
    """,

        "tecnicismo": """
    Sustituye la palabra por un término o expresión más comprensible
    para un lector general, manteniendo el significado.
    """,

        "coloquialismo": """
    Sustituye la palabra por una expresión neutra y adecuada para
    un texto dirigido a un público general.
    """,

        "vulgarismo": """
    Sustituye la palabra por su forma normativa o por una expresión
    correcta equivalente.
    """,

        "largas": """
    Sustituye la palabra por una alternativa más sencilla y habitual,
    preferiblemente más corta, siempre que mantenga el mismo significado
    en el contexto.
    """
    }
    instruccion_criterio = instrucciones_criterios.get(
        criterio,
        "Sustituye la palabra por una alternativa más clara y adecuada para un lector general."
    )

    instruccion = f"""
    Recibirás una oración y una palabra marcada como "{criterio}".

    Tu tarea consiste únicamente en sustituir esa palabra por una
    alternativa adecuada según el problema detectado.

    Problema detectado:
    {instruccion_criterio}

    Reglas:
    - No cambies ninguna otra palabra de la oración.
    - Mantén el significado original.
    - Mantén el mismo tiempo y modo verbal, si la palabra marcada es un verbo.
    - Conserva el mismo orden de la oración.
    - Mantén el género y el número cuando corresponda.
    - La alternativa debe ser natural en el contexto de la oración.
    - No añadas información nueva.
    - No elimines información relevante.
    - Si no existe una alternativa adecuada, responde exactamente "SIN_CAMBIOS".
    
    La palabra o expresión generada DEBE cumplir TODAS las siguientes
    condiciones:
    - Debe ser léxico frecuente y habitual en español.
    - No debe ser una palabra baúl o de significado excesivamente general.
    - No debe ser un extranjerismo.
    - No debe ser un tecnicismo.
    - No debe ser un cultismo.
    - No debe ser un coloquialismo.
    - No debe ser un vulgarismo.
    - No debe ser un localismo o regionalismo.
    - No debe tener más de 10 letras.
    - No debe tener más de 5 sílabas.

    Oración:
    {oracion}

    Palabra marcada:
    {palabra}

    Criterio:
    {criterio}

    Devuelve únicamente la oración completa con la palabra sustituida.
    No añadas explicaciones, comillas ni comentarios.
    """

    response: ChatResponse = chat(
        #model = "nichonauta/pepita-2-2b-it-v5",
        #model = "mistral",
        #model = "gemma4:e4b",
        model = "gemma4:12b",
        messages = [
            {
                "role": "user",
                "content": instruccion
            }
        ],
    think= False
    )
    sugerencia = response.message.content.strip()
    return sugerencia