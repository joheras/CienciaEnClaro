from ollama import chat
from ollama import ChatResponse

def obtenerSugerencia(comment):
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
        model = "mistral",
        messages = [
            {
                "role": "user",
                "content": instruccion
            }
        ]
    )
    sugerencia = response.message.content.strip()
    return sugerencia

