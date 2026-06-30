from modules.auxiliares_pragdisc import *


def falta_conectores(texto):
    return aux_conectores(texto)[0]

def conectores_repe(texto):
    repes = False
    conectores = aux_conectores(texto)[1]
    for cone in conectores.keys():
        if conectores[cone]>1:
            repes = True
    return repes

def conectores_punt(texto):
    result = aux_conectores(texto)
    return not(result[2]), result[3], result[4]