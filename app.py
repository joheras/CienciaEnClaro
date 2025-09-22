import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

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

@app.post("/add_comment_first_line")
async def add_comment_first_line(request: Request):
    """
    Añade un comentario a la primera línea del texto y devuelve:
    - text: el texto original
    - comment_text: el comentario
    - comment_id: un identificador único
    """
    data = await request.json()
    text = data.get("text", "")

    textos = text.split("\n")

    pos = 0
    result = []


    for texto in textos:
        if len(texto.split(" "))>20:
            comment_id = str(uuid.uuid4())  # ID único
            start = pos
            end = pos+len(texto)
            result.append({"id": comment_id,"start": start,"end": end,"text": "Texto demasiado largo",
                           "description":"El texto es demasiado largo", "suggestion":"versión corta","type":"longitud"})
        if len(texto)==0:
            pos = pos + 2
        else:
            pos = pos + len(texto)

    return JSONResponse(
        content = result

    #     {
    #     "id": comment_id,
    #     "start": start,
    #     "end": end,
    #     "text": "comentario fastapi",
    #     "suggestion":"prueba"
    # }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
