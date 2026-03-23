# pip install spacy==3.7.5
#python -m spacy download es_core_news_sm
import nltk
import spacy
import re

nlp = spacy.load("es_core_news_sm")


def longitud_parrafo(texto):
    """ Dado un párrafo devuelve el número de frases que tiene """
    if len(texto) == 0:
        return 0
    else:
        # Si el párrafo no está vacío lo partimos en frases
        frases = nltk.sent_tokenize(texto)
        return len(frases) # Devolvemos el número de frases que tiene

def longitud_frase(texto):
    "Dada una oración devuelve el número de palabras que tiene"
    palabras = [w for w in nltk.word_tokenize(texto, language="spanish") if w.isalpha()]
    return len(palabras)

def orden_sintactico(texto):
    "Dada una oración devuelve TRUE si sigue la estructura sujeto-vebo-complementos y FALSE en caso contrario"
    doc = nlp(texto)
    sujeto = [t for t in doc if t.dep_ in ("nsubj", "nsubj_pass")]
    verbo = [t for t in doc if t.dep_ == "ROOT" and t.pos_=="VERB"]
    objeto = [t for t in doc if t.dep_ in ("obj", "iobj")]

    if sujeto and verbo and objeto:
        if not(sujeto[0].i < verbo[0].i < objeto[0].i):
            return False
    return True


# La siguiente función nos dice si una oración es válida o no.
def oracion_valida(texto):
    """
    Comprueba si un texto puede considerarse una oración válida.
    Analiza la oración y verifica que exista un nodo raíz
    y al menos un elemento sintáctico que indique estructura predicativa.
    """
    doc = nlp(texto)
    if not list(doc.sents):
        return False

    sent = list(doc.sents)[0]
    root = next((t for t in sent if t.dep_ == "ROOT"), None)

    if root is None:
        return False

    # Debe haber estructura predicativa
    tiene_predicacion = any(
        t.dep_ in (
            "nsubj", "nsubj:pass",
            "obj", "obl", "xcomp",
            "ccomp", "advmod"
        )
        for t in sent
    )
    return tiene_predicacion

def coordinada(texto):
    """Dada una oración, devuelve TRUE si es una oración coordinada, y FALSE en caso contrario.
    Además, devuelve la frase partida en los trozos correspondientes para que sea simple.
    """
    posiblesCortes = []
    cortes = []
    resultado = ''
    booleanos = [] # Cuando valga False es porque esa frase no está completa

    doc = nlp(texto)
    for token in doc:
        if token.dep_ == "cc":
            if str(doc[token.i])!='o':
                posiblesCortes.append(token.i)
    if posiblesCortes == []:
        return False, texto
    else:
        final = posiblesCortes[-1]
        for i in range(len(posiblesCortes)):
            if (i==0 and posiblesCortes[i]!=final):
                cortes.append(doc[:posiblesCortes[i]])
            elif (i==0 and posiblesCortes[i]==final):
                cortes.append(doc[:posiblesCortes[i]])
                cortes.append(doc[posiblesCortes[i]+1:])
            elif posiblesCortes[i]==final:
                cortes.append(doc[posiblesCortes[i-1]+1:posiblesCortes[i]])
                cortes.append(doc[posiblesCortes[i]+1:])
            else:
                cortes.append(doc[posiblesCortes[i-1]+1:posiblesCortes[i]])

        # Comprobamos si cada trozo está completo o no y almacenamos la información en "booleanos"
        for trozo in cortes:
            booleanos.append(oracion_valida(str(trozo)))

        # Si algún trozo falla vamos a comprobar si se puede unir con el anterior o con el siguiente
        contador = 0 # Para recorrernos el vector booleanos
        ni = 0 # El contador de nuevos_cortes
        j = 0 # El contador de posiblesCortes
        i = 0
        nuevos_cortes = []
        while((False in booleanos) and (contador<len(booleanos) and j<len(posiblesCortes))): # Hay algún falso y todavía quedan cortes
            for x in range(len(booleanos)):
                if i!=x: # Si gusiona una frase con la siguiente, avanza en Cortes pero no en booleano, así que con este if lo hacemos avanzar uno para igualarlos.
                    continue
                # Si es True añade la información como estaba
                if booleanos[i]:
                    nuevos_cortes.append(cortes[i])
                    ni = len(nuevos_cortes)
                    contador = contador + 1
                    i = i+1
                else:
                    # Intenta fusionar con el anterior
                    if ni>0:
                        combinado = str(nuevos_cortes[ni-1]) + ' ' + str(doc[posiblesCortes[j]]) + ' ' + str(cortes[i])
                        # Si es frase
                        if oracion_valida(combinado):
                          nuevos_cortes[ni-1] = combinado
                          j = j+1
                          i = i+1
                          continue
                    # Si no es frase intenta fusionar con el siguiente
                    if (i<len(cortes)-1 and j<len(posiblesCortes)):
                        combinado = str(cortes[i]) + ' ' + str(doc[posiblesCortes[j]]) + ' ' + str(cortes[i+1])
                        if oracion_valida(combinado):
                            nuevos_cortes.append(combinado)
                            ni = len(nuevos_cortes)
                            i = i+2
                            j = j+1
                            continue

            cortes = nuevos_cortes
            booleanos = []
            for trozo in cortes:
                booleanos.append(oracion_valida(str(trozo)))

        if not(False in booleanos):
            for c in cortes:
                if resultado == '':
                    resultado = str(c) + '.'
                else:
                    resultado = resultado + ' ' + str(c)[0].upper()+str(c)[1:] + '.'
            resultado = resultado.replace('..', '.').replace(',.', '.').replace('\n.', '\n').replace('\n\n', '\n').replace(';.', '.')

    return resultado!=texto, resultado

def yuxtapuesta(texto):
    """Dada una oración, devuelve TRUE si es una oración yuxtapuesta, y FALSE en caso contrario.
    Además, devuelve la frase partida en los trozos correspondientes para que sea simple.
    """
    doc = nlp(texto)
    posiblesCortes = []
    resultado = ''
    booleanos = []  # Cuando valga False es porque esa frase no estaba completa
    puntuaciones = []
    result = []

    posiblesCortes = re.split(r'[,:;]', texto)
    posiblesCortes = [parte.strip() for parte in posiblesCortes]

    if posiblesCortes == []:
        return False, texto
    else:
        # Comprobamos si cada trozo está completo o no y almacenamos la información en booleanos
        for trozo in posiblesCortes:
            booleanos.append(oracion_valida(str(trozo)))

        for i in range(len(posiblesCortes) - 1):
            puntuaciones.append(texto.split(posiblesCortes[i])[1][0])

        # Si algún trozo falla vamos a comprobar si se puede unir con el anterio o el siguiente
        ni = 0  # El contador de nuevos_cortes
        j = 0  # el contador de posiblesCortes
        x = 0  # el contador de booleanos
        nuevos_cortes = []
        if not (False in booleanos):
            nuevos_cortes = posiblesCortes
        while ((False in booleanos) and (
                x < len(booleanos) and j < len(posiblesCortes))):  # Hay algún falso y todavía quedan cortes
            while x < len(booleanos):
                # Si es True añade la información como estaba
                if booleanos[x]:
                    nuevos_cortes.append(posiblesCortes[j])
                    ni = len(nuevos_cortes)
                    j = j + 1
                    x = x + 1
                else:
                    # Intenta fusionar con el anterior
                    if ni > 0:
                        combinado = str(nuevos_cortes[ni - 1]) + puntuaciones[j - 1] + ' ' + posiblesCortes[j]
                        # Si es frase
                        if oracion_valida(combinado):
                            nuevos_cortes[ni - 1] = combinado
                            j = j + 1
                            ni = len(nuevos_cortes)
                            x = x + 1
                            continue
                        # Si no es frase intenta fusionar con el siguiente
                    if (j < len(posiblesCortes) - 1):
                        combinado = posiblesCortes[j] + puntuaciones[j] + ' ' + posiblesCortes[j + 1]
                        if oracion_valida(combinado):
                            nuevos_cortes.append(combinado)
                            j = j + 2
                            ni = len(nuevos_cortes)
                            x = x + 2  # Porque hemos fusionado con el siguiente
                            continue

    cortes = nuevos_cortes
    booleanos = []
    for trozo in cortes:
        booleanos.append(oracion_valida(str(trozo)))

    if not (False in booleanos):
        for c in cortes:
            if resultado == '':
                resultado = str(c) + '.'
            else:
                resultado = resultado + ' ' + str(c)[0].upper() + str(c)[1:] + '.'
        resultado = resultado.replace('..', '.').replace(',.', '.').replace('?.', '?').replace(';.', '.')
    return resultado != texto, resultado

def concordancia(texto):
    """Dada una frase devuelve True si no tiene ningún fallo de concordancia, y False en caso contrario.
    Además, si está bien devuelve la oración original y si está mal devuelve una lista con los errores"""
    errores = []
    doc = nlp(texto)
    for token in doc:
        # Determinante y sustantivo
        if token.pos_=="DET":
            if token.head.pos_=="ADJ":
                head = "adjetivo"
            elif token.head.pos_=="NOUN":
                head = "sustantivo"
            elif token.head.pos_=="VERB":
                head = "verbo"
            elif token.head.pos_ == "PRON":
                head = "pronombre"
            else:
                head = str(token.head.pos_)
            if token.morph.get("Gender") and token.head.morph.get("Gender"):
                if token.morph.get("Gender") != token.head.morph.get("Gender"):
                    errores.append(f"Determinante ({token.text}) y {head} ({token.head.text}) no concordan en género")
            if token.morph.get("Number") and token.head.morph.get("Number"):
                if token.morph.get("Number") != token.head.morph.get("Number"):
                    errores.append(f"Determinante ({token.text}) y {head} ({token.head.text}) no concordan en número")

        #Adjetivo y sustantivo
        elif token.pos_ == "ADJ" and (token.dep_=="amod" or token.dep_=="flat" or token.dep_=="ROOT"):
            # Para evitar que, por problemas de spacy, detecte un sustantivo como nombre propio
            # Comprobar si se trata de nombre propio
            if token.head.pos_=="PROPN" and token.text.islower():
                errores.append(f"Posible error de concordancia con el {head} ({token.head.text})")

            if token.head.pos_=="ADJ":
                head = "adjetivo"
            elif token.head.pos_=="NOUN":
                head = "sustantivo"
            elif token.head.pos_=="VERB":
                head = "verbo"
            elif token.head.pos_ == "PRON":
                head = "pronombre"
            else:
                head = str(token.head.pos_)
            if token.morph.get("Gender") and token.head.morph.get("Gender"):
                if token.morph.get("Gender") != token.head.morph.get("Gender"):
                    errores.append(f"Adjetivo ({token.text}) y {head} ({token.head.text}) no concordan en género")
            if token.morph.get("Number") and token.head.morph.get("Number"):
                if token.morph.get("Number") != token.head.morph.get("Number"):
                    errores.append(f"Adjetivo ({token.text}) y {head} ({token.head.text}) no concordan en número")

        elif token.pos_ == "NOUN":
            if token.head.pos_=="ADJ":
                head = "adjetivo"
            elif token.head.pos_=="NOUN":
                head = "sustantivo"
            elif token.head.pos_=="VERB":
                head = "verbo"
            elif token.head.pos_ == "PRON":
                head = "pronombre"
            else:
                head = str(token.head.pos_)
            if token.morph.get("Gender") and token.head.morph.get("Gender"):
                if token.morph.get("Gender") != token.head.morph.get("Gender"):
                    errores.append(f"Sustantivo ({token.text}) y {head} ({token.head.text}) no concordan en género")
            if token.morph.get("Number") and token.head.morph.get("Number"):
                if token.morph.get("Number") != token.head.morph.get("Number"):
                    errores.append(f"Sustantivo ({token.text}) y {head} ({token.head.text}) no concordan en número")


        # Sujeto y verbo
        elif token.dep_ == "nsubj":
            if token.head.pos_=="ADJ":
                head = "adjetivo"
            elif token.head.pos_=="NOUN":
                head = "sustantivo"
            elif token.head.pos_=="VERB":
                head = "verbo"
            elif token.head.pos_ == "PRON":
                head = "pronombre"
            else:
                head = str(token.head.pos_)
            if token.morph.get("Person") and token.head.morph.get("Person"):
                if token.morph.get("Person") != token.head.morph.get("Person"):
                    errores.append(f"Sujeto ({token.text}) y {head} ({token.head.text}) no concordan en persona")
            if token.morph.get("Number") and token.head.morph.get("Number"):
                if token.morph.get("Number") != token.head.morph.get("Number"):
                    errores.append(f"Sujeto ({token.text}) y {head} ({token.head.text}) no concordan en número")

    if errores == []:
        return True, texto
    else:
        return False, errores

def pasiva_perifrastica(texto):
    """Dada una frase devuelve True si es una pasiva perifrastica y False en caso contrario.
    Una pasiva es perifrástrica si está compuesta por el verbo "ser" conjugado y un participio.
    Por ejemplo: La carta FUE ESCRITA por María."""
    doc = nlp(texto)
    for token in doc:
        if token.morph.get("VerbForm") == ["Part"]:
            # Ver si tiene como auxiliar "ser"
            for child in token.children:
                if child.lemma_ == "ser" and child.pos_=="AUX":
                    return True
    return False

def pasiva_refleja(texto):
    """Dada una frase devuelve True si es una pasiva refleja y False en caso contrario.
    Una psiva es refleja si está compuesta por "se" y un verbo transitivo.
    Por ejemplo: SE VENDIERON las entradas."""
    doc = nlp(texto)
    for token in doc:
        if token.dep_ == "expl:pass":
            # Se comprueba si hay sujeto paciente con el verbo
            return any(child.dep_ == "nsubj" for child in token.head.children)
    return False


def infinitivo(texto):
    """Dada una frase devuelve True si tiene algún verbo en infinitivo.
    En caso contrario devuelve False."""
    doc = nlp(texto)
    for token in doc:
        if token.pos_ == "VERB" and "Inf" in token.morph.get("VerbForm"):
            if token.head.pos_ not in ("VERB", "AUX"):
                return True
    return False

def gerundio(texto):
    """Dada una frase devuelve True si tiene algún verbo en gerundio.
    En caso contrario devuelve False."""
    doc = nlp(texto)
    for token in doc:
        if token.pos_ == "VERB" and "Ger" in token.morph.get("VerbForm"):
            # Miramos si tiene auxiliar
            tiene_aux = any(child.pos_ == "AUX" for child in token.children) or (token.head.pos_=="AUX")
            if not tiene_aux:
                return True
    return False

def participio(texto):
    """Dada una frase devuelve True si tiene algún verbo en participio.
    En caso contrario devuelve False."""
    doc = nlp(texto)
    for token in doc:
        if token.pos_ == "VERB" and "Part" in token.morph.get("VerbForm"):
            # Miramos si tiene auxiliar
            tiene_aux = any(Child.pos_=="AUX" for Child in token.children) or (token.head.pos_=="AUX")
            if not tiene_aux:
                return True
    return False

# def inciso(texto):


#def negaciones(texto):