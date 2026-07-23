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
    instruccion = (f"""
    Recibirás una oración y una palabra marcada como {criterio}.

Tu tarea consiste únicamente en sustituir esa palabra por otra más específica.

Reglas:
- No cambies ninguna otra palabra.
- Mantén el mismo significado.
- Conserva el mismo tiempo verbal.
- Conserva el mismo orden de la oración.
- Si es necesario, adapta únicamente el género o el número del nuevo término.
- Si no existe una alternativa mejor, responde exactamente "SIN_CAMBIOS".

Oración:
{oracion}

Palabra:
{palabra}

Devuelve solo la oración modificando la palabra baúl por la alternativa.
    """)

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