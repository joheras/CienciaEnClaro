import textstat

def fernandez_huerta(texto):
    """Dado un texto, devuelve el índice de Fernández-Huerta"""
    return textstat.fernandez_huerta(texto)

#Pongo en una lista las palabras comunes:
# Lista de palabras comunes sacadas de: https://github.com/mazyvan/most-common-spanish-words/
archivos = ["most-common-spanish-words.txt", "most-common-spanish-words-v2.txt", "most-common-spanish-words-v3.txt",
                "most-common-spanish-words-v4.txt", "most-common-spanish-words-v5.txt"]
def palabras_comunes():
    contenido = set()
    todas = set()
    for archivo in archivos:
        with open("mazyvan/"+archivo, "r", encoding="utf-8") as f:
            contenido.update(f.read().splitlines())
            for cont in contenido:
                todas.update(cont.split('|'))
    for t in todas:
        t.split('|')
    return set(todas)