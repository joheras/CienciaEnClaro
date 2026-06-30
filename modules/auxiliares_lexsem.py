import csv

import pandas as pd
import re
import spacy
import nltk
nltk.download("own-1.4")
nltk.download("wordnet")
from nltk.corpus import wordnet as wn
nlp = spacy.load("es_core_news_sm")
import textstat

latinismos = set(["ab initio", "ad hoc", "ad infinitum", "a posteriori", "a priori", "corpore insepulto", "cum laude", "de facto",  "de iure", "ex cathedra", "grosso modo", "honoris causa", "in articulo mortis",
              "in illo tempore", "in memoriam", "in pectore", "in situ", "ipso facto", "motu proprio", "nemine discrepante", "post mortem", "sine die", "sine qua non", "sub iudice",
                  "sui generis", "vade retro", "alter ego", "curriculum vitae", "delirium tremens", "horror vacui", "lapsus calami", "lapsus linguae", "modus operandi", "numerus clausus",
                  "peccata minuta", "rara avis", "vox populi", "animus", "spiritus", "triclinium", "trivium", "quadrivium"])

tecnicismos = set(["armónico fundamental", "audimetría", "audímetro", "audiofrecuencia", "audiograma", "audiometría", "audiómetro", "diacústica", "fon", "fonio", "fonometría", "fonómetro", "fonotecnia", "fonotécnico", "fonotécnica", "reverberación", "sonio", "sonómetro",
                   "aerocriptografía", "aerocriptográfico", "aerocriptográfica", "aerodino", "flap", "girómetro", "módulo", "radiofaro", "radionavegación", "riza", "tonel", "turborreactor",
                   "antropopiteco", "australopiteco", "covada", "cromañón", "cromañona", "endogamia", "ergología", "ergológico", "ergológica", "etnocéntrico", "etnocéntrica", "etnocentrismo", "exogamia", "exogámico", "exogámica", "exógamo", "exógama", "homínido", "homínida", "matrilineal", "monogenismo", "monogenista",
                   "neandertal", "nomadismo", "patrilineal", "pitecántropo", "poligenismo", "poligenista", "prehomínido", "prehomínida", "tipología",
                   "crisocola", "excavación", "exciso", "excisa", "incisa", "monoansado", "monoansada", "ortostato", "prótomo", "ritón", "tell", "vaciado", "vaciada",
                   "árula", "biansado", "biansada", "bifaz", "calamistro", "cálato", "cálceo", "calcídico", "canistro", "canope", "capistro", "ceriolario", "cerógrafo", "ceroma", "ciborio", "cimba", "cista", "compluvio", "crátera"
                   "ablación", "abortar", "abrasión", "absceso", "abstergente", "absterger", "abstersión", "abstersivo", "abstersiva", "acacia", "acantocitosis", "accesión", "acceso", "acidemia", "hialurónico", "acidosis", "aciduria", "acinesia", "aclaramiento",
                   ""])

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



SUFIJOS_NOMINALIZACION = (
    # Deverbales
    "ción", "sión", "miento", "aje", "ada", "ido",
    # Deadjetivales
    "dad", "tad", "ez", "eza", "ura", "encia", "ancia"
)
def nominalizada(palabra):
    doc = nlp(palabra)
    nominalizaciones = []

    for token in doc:
        if token.pos_ == "NOUN":
            palabra = token.text.lower()
            if palabra.endswith(SUFIJOS_NOMINALIZACION):
                nominalizaciones.append(token.text)

    return palabra in nominalizaciones

def largas(palabra):
    numSilabas = textstat.syllable_count(palabra, lang="es")
    if numSilabas>5:
        return True
    elif len(palabra)>10:
        return True
    else:
        return False

def latin(palabra):
    if palabra in latinismos:
        return True
    else:
        return False

def tecnico(palabra):
    if palabra in tecnicismos:
        return True
    else:
        return False