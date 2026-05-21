from modules.auxiliares_lexsem import *

listaExtranjerismos = listExtranjerismos()
listaBaul = listBaul()

def extranjerismos(palabra):
    """
    Dada una palabra, devuelve True si se considera extranjerismo y False si no.
    Se consideran extranjerismos aquellas palabras que devuelve la función "listExtranjerismos()"
    """
    if palabra in listaExtranjerismos:
        return True
    else:
        return False

def detectar_palabras_baul(texto, pal):
    tokens = tokenizar(texto)
    if pal in listaBaul:
        match = re.search(rf"\b{re.escape(pal)}\b", texto, re.IGNORECASE)
        if match:
            start = match.start()
            end = match.end()
            # heurística: solo si NO está matizada
            if not tiene_complemento(texto, end):
                return True
    return False