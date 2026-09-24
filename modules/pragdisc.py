from modules.auxiliares_pragdisc import *
import nltk

def falta_conectores(texto):
    frases = nltk.sent_tokenize(texto, language="spanish")

    necesita = numero_conectores(frases)
    tiene, _ = contar_conectores(texto)

    return tiene < necesita

def conectores_repe(texto):
    _, conectores = contar_conectores(texto)

    return any(cantidad > 1 for cantidad in conectores.values())

def conectores_punt(texto):
    texto_min = texto.lower()

    conectores_dos_puntos = ["por ejemplo"]

    conectores_con_complemento = {
        "mientras que",
        "a pesar de",
        "a diferencia de",
        "en contraposición a",
        "al revés que"
    }

    for conector in conect:
        conector_min = conector.lower()
        pos = texto_min.find(conector_min)

        while pos != -1:
            fin = pos + len(conector_min)

            antes_ok = (
                pos == 0 or not texto[pos - 1].isalnum()
            )

            despues_ok = (
                fin == len(texto) or not texto[fin].isalnum()
            )

            if antes_ok and despues_ok:

                inicio_oracion = (
                        pos ==0
                        or texto_min[:pos].endswith(". ")
                        or texto_min[:pos].endswith("; ")
                        or texto_min[:pos].endswith("(")
                )

                if inicio_oracion:

                    if texto[fin:].startswith(", "):
                        pass
                    elif (conector_min in conectores_dos_puntos and texto[fin:].startswith(":")):
                        pass
                    elif conector_min in conectores_con_complemento:
                        siguiente_coma = texto.find(",", fin)
                        if siguiente_coma == -1:
                            return True, pos, conector_min
                    else:
                        return True, pos, conector_min

                elif texto_min[:pos].endswith(", "):

                    if texto[fin:].startswith(","):
                        pass
                    elif (conector_min in conectores_dos_puntos and texto[fin:].startswith(":")):
                        pass
                    elif conector_min in conectores_con_complemento:
                        siguiente_coma = texto.find(",", fin)

                        if siguiente_coma == -1:
                            return True, pos, conector_min

                    else:
                        return True, pos, conector_min

                else:
                    if not texto[fin:].startswith(", "):
                        return True, pos, conector_min

            pos = texto_min.find(conector_min, pos + 1)

    return False