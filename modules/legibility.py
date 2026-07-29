from modules.auxiliares_legibility import *
import textstat

# Para que un texto se considere legible dentro de la divulgación científica se considera
# que debe extraer una puntuación de entre 60 y 70 en el text de Fernández-Huerta
def indice_fernandezHuerta(texto):
    """Dado un texto, devuelve un real con el resultado del test y un string con la explicación a dicho número."""
    indice = round(fernandez_huerta(texto), 2)
    if indice<60 and indice!=0:
        resultado = '<span class="highlight">Parece que la legibilidad general del texto es mejorable, considere revisar los índices de legibilidad y simplificar la redacción cuando sea necesario.</span><br><br>Los textos dirigidos al público general deben cumplir unos índices de legibilidad. Un texto legible dentro de la divulgación científica debería extraer una puntuación de entre 60 y 70 (puntuación actual:  ' + str(indice) + ")"
    else:
        resultado = "El texto se considera legible dentro de la divulgación científica."
    return indice, resultado

def indice_szigriszt_pazos(texto):
    indice = round(szigriszt_pazos(texto), 2)
    if indice<50 and indice!=0:
        resultado = '<span class="highlight">Parece que la legibilidad general del texto es mejorable, considere revisar los índices de legibilidad y simplificar la redacción cuando sea necesario.</span><br><br>Los textos dirigidos al público general deben cumplir unos índices de legibilidad. Un texto legible dentro de la divulgación científica debería extraer una puntuación de entre 51 y 65 (puntuación actual: ' + str(indice) + ")"
    else:
        resultado = "El texto se considera legible dentro de la divulgación científica."
    return indice, resultado

def media_palabras_frases(texto):
    """Dado un texto devuelve la longitud media de sus frases"""
    numPal = textstat.lexicon_count(texto)
    numFrases = textstat.sentence_count(texto)
    return round(numPal/numFrases, 2)

def media_silabas_palabras(texto):
    """Dado un texto devuelve la media de las sílabas por palabra"""
    numPal = textstat.lexicon_count(texto)
    numSilabas = textstat.syllable_count(texto, lang="es")
    return round(numSilabas/numPal, 2)

#def palabra_compleja
