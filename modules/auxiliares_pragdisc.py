import textstat

conectores_cronologicos = ["en primer lugar", "en segundo", "en tercero", "ante todo", "fundamentalmente",
                           "después", "por fin", "para empezar", "finalmente", "por último", "sobre todo"]
conectores_agrupadores = ["de modo accesorio", "sobre todo", "de todos modos", "de cualquier forma", "de cualquier manera",
                          "cabe destacar", "de modo idéntico", "al mismo tiempo", "así mismo", "se puede señalar", "inclusive", "además",
                          "de la misma forma"]
conectores_opositores = ["no obstante", "por otra parte", "como contrapartida", "sin embargo", "a pesar de", "a diferencia de",
                         "por un lado", "y por el otro", "en otro orden de ideas", "al otro extremo", "ahora bien",
                         "por el contrario", "mientras que", "antagónicamente", "en contraposición a", "al revés que"]
conectores_ejemplificantes = ["por ejemplo", "tal es el caso", "así como", "tal como", "si usamos una imagen", "si apelamos a un símil",
                              "similarmente", "identificante"]
conectores_parafraseadores = ["es decir", "al principio", "en otras palabras", "de todos modos", "de hecho", "en un inicio", "esto es",
                              "en todo caso", "lo que es lo mismo", "de cualquier manera", "de cualquier modo", "de cualquier forma"]
conectores_resultado = ["como consecuencia", "por lo consiguiente", "por lo mismo", "por esta razón", "por ello", "en consecuencia",
                        "por ende", "por tal motivo", "en concordancia", "como resultado", "por lo cual"]
conectores_comparacion = ["de modo similar", "de igual forma", "de igual manera", "de igual modo", "de igual situación"]
conectores_conclusion = ["en definitiva", "resumiendo", "resumiendo lo planteado", "para terminar", "concretizando", "en definitiva",
                         "en resumen", "englobando", "en conclusión", "por úlitmo", "en síntesis", "finalizando", "en todo caso"]
conect = set(conectores_cronologicos + conectores_agrupadores + conectores_opositores + conectores_ejemplificantes + conectores_parafraseadores + conectores_resultado
+conectores_comparacion + conectores_conclusion)



def numero_conectores(texto):
    """Dado un párrafo devuelve el cociente de dividir el número de oraciones menos 1 entre 2."""
    numFrases = textstat.sentence_count(texto)
    numero = (numFrases-1) // 2
    return int(numero)



def aux_conectores(texto):
    necesita = numero_conectores(texto)
    tiene = 0
    conectores = {}
    texto_min = texto.lower()
    for conector in conect:
        conector_min = conector.lower()
        pos = texto_min.find(conector_min)
        while pos!=-1:
            fin = pos + len(conector_min)

            antes_ok = (
                pos == 0 or not texto[pos-1].isalnum()
            )
            despues_ok = (
                fin == len(texto) or not texto[fin].isalnum()
            )

            if antes_ok and despues_ok:
                tiene = tiene + 1
                conectores[conector_min] = conectores.get(conector_min, 0) + 1

                despues = texto[fin:]
                if not despues.startswith(","):
                    return tiene<necesita, conectores, False, pos, conector_min
                if pos==0:
                    pass
                elif texto_min[:pos].endswith(". "):
                    pass
                elif texto_min[:pos].endswith(", "):
                    pass
                elif texto_min[:pos].endswith("; "):
                    pass
                else:
                    return tiene<necesita, conectores, False, pos, conector_min
            pos = texto_min.find(conector_min, pos+1)
    return tiene<necesita, conectores, True, None, None


