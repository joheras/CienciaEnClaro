from modules.auxiliares_morfosintaxis import *

# Los párrafos deben tener entre 2 y 5 oraciones
def parrafo_largo(texto):
    """Dado un párrafo (texto), devuelve un booleano y un entero.
    El booleano será True si el párrafo es demasiado largo (es decir, si tiene más de 5 oraciones).
    El booleano será False si el párrafo no es demasiado largo (menos de 5 oraciones).
    El entero que devuelve es el número de frases que tiene el párrafo.
     """
    long = longitud_parrafo(texto)
    return long>5, long
def parrafo_corto(texto):
    """Dado un párrafo (texto), devuelve un booleano y un entero.
    El booleano será True si el párrafo es demasiado corto (es decir, si tiene menos de 2 oraciones).
    El booleano será False si el párrafo no es demasiado corto (más de 2 oraciones).
    El entero que devuelve es el número de frases que tiene el párrafo.
     """
    long = longitud_parrafo(texto)
    return long<2, long

# Las oraciones deben tener como máximo 20 palabras
def oracion_larga(texto):
    """Dada una oración (texto), devuelve un booleano y un entero.
    El booleano será True si la oración es demasiado larga (es decir, si tiene más de 20 palabras).
    El booleano será False si la oración es demasiado corta (menos de 20 palabras).
    El entero que devuelve es el número de palabras que tiene la oración."""
    long = longitud_frase(texto)
    return long>20, long

# Las oraciones deben seguir el orden sujeto-verbo-complementos
def orden_incorrecto(texto):
    """Dada una oración (texto), devuelve un booleano.
    El booleano será True si la orden no sigue el orden correcto (es decir, si no sigue el orden sujeto-verbo-complementos)
    El booleano será False si la orden sigue el orden correcto.
    """
    return not(orden_sintactico(texto))

# Se debe evitar el uso de oraciones coordinadas
def oracion_coordinada(texto):
    """ Dada una oración (texto), devuelve un booleano y un string.
    El booleano será True si la oración es coordinada. En ese caso, el string será la oración dividida para evitar la coordinación.
    El booleano será False si la oración no es coordinada. En este caso, el string será la oración original.
    """
    return coordinada(texto)

# Se debe evitar el uso de oraciones yuxtapuestas
def oracion_yuxtapuesta(texto):
    """ Dada una oración (texto), devuelve un booleano y un string.
    El booleano será True si la oración es yuxtapuesta. En ese caso, el string será la oración dividida para evitar la yuxtaposición.
    El booleano será False si la oración no es yuxtapuesta. En este caso, el string será la oración original.
    """
    return yuxtapuesta(texto)

# Debe haber concordancia de persona, tiempo, género y número entre los elementos del texto
def error_concordancia(texto):
    """Dada una oración, devuelve un booleano y una lista.
    El booleano será True si la oración tiene algún error de concordancia.
    El booleano será False si la oración no tiene ningún error.
    Además, en caso de que haya algún error devolverá una lista con dichos errores. Y si no hay ninguno devolverá una lista vacía."""
    booleano, errores = concordancia(texto)
    if booleano:
        return False, []
    else:
        return True, errores

# La mayor parte de las oraciones deben enunciarse en voz activa
def voz_pasiva(texto):
    """Dada una oración, devuelve True si está enunciada en voz pasiva y False en caso contrario"""
    if pasiva_refleja(texto):
        return True
    if pasiva_perifrastica(texto):
        return True
    return False

# Promover el uso de verbos conjugados (mirar el uso abusivo de inifinitvos, gerundios y participios)
def verbos_no_conjugados(texto):
    """Dada una oración, devuelve True si encuentra algún verbo en infinitivo, gerundio o participio.
    Devuelve False en caso contrario."""
    if infinitivo(texto):
        return True
    elif gerundio(texto):
        return True
    elif participio(texto):
        return True
    return False

#def tiene_inciso(texto):

#def negaciones_dobles(texto):