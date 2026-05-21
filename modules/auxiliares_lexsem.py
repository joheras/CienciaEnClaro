import csv

import pandas as pd
import re


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

def listBaul():
    """
    Devuelve la listsa de las palabras en el excel "Palabras baúl CienciaEnClaro.xlsx"
    """
    df = pd.read_excel("static/Palabras baúl CienciaEnClaro.xlsx")
    lista_baul = (
        df["Item"].dropna().astype(str).str.strip().str.lower().tolist()
    )
    return lista_baul

# Para las palabras baúl
def tiene_complemento(texto, end_index):
    ventana = texto[end_index:end_index + 60].lower()

    patrones = [
        r"\bde\b",
        r"\bdel\b",
        r"\bcon\b",
        r"\bpara\b",
        r"\bque\b",
        r"\bcomo\b",
        r"\bmediante\b",
        r"\bentre\b"
    ]

    return any(re.search(p, ventana) for p in patrones)
def tokenizar(texto):
    return [(m.group(), m.start(), m.end())
            for m in re.finditer(r"\b[\wáéíóúñüÁÉÍÓÚÑÜ]+\b", texto)]