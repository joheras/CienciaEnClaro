import pandas as pd

def listExtranjerismos():
    """
    Devuelve la lista de las palabras en el excel "Listado de extranjerismos crudos (CORPES XXI)"
    """

    # Leer el archivo Excel
    df = pd.read_excel("static/Listado de extranjerismos crudos (CORPES XXI).xlsx")

    # Combinar las columnas 'lema' y 'forma'
    palabras = pd.concat([df["Lema"], df["Forma"]])

    # Eliminar duplicados
    palabras_unicas = palabras.drop_duplicates()

    # Opcional: convertir a lista
    lista_palabras = palabras_unicas.tolist()

    return lista_palabras