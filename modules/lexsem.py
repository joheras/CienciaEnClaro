from modules.auxiliares_lexsem import *

def extranjerismos(palabra):
    """
    Dada una palabra, devuelve True si se considera extranjerismo y False si no.
    Se consideran extranjerismos aquellas palabras que devuelve la función "listExtranjerismos()"
    """
    lista = listExtranjerismos()
    if palabra in lista:
        return True
    else:
        return False