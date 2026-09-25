from openjev_decide import OpenJev
from modules.observaciones_llm import *
# code/openjev_decide.py
jev = OpenJev.from_pretrained("AlexWortega/openjev", subfolder="qwen3.5-4b-nli-v5", device="cuda")

texto1= """
Texto experimental sobre cambio climático y guía de observaciones
El cambio climático debe entenderse aquí como una alteración persistente de los patrones medios del sistema terrestre que afecta a la atmósfera, al océano, a la criosfera y a la biosfera, y que en 2026 se observa con claridad en indicadores como la concentración de dióxido de carbono, que los registros de NASA situaron en 431 ppm en abril de ese año, la temperatura media global, la extensión del hielo marino y la frecuencia de episodios extremos, aunque la interpretación de esos datos requiere series largas, contextos comparables y cautela metodológica, porque un valor aislado no explica por sí solo un proceso complejo y, sin embargo, a menudo se presenta como si cerrara el debate, algo que conviene evitar cuando se intenta comunicar ciencia a personas con distintas trayectorias lectoras. En ese marco, la literatura reciente del IPCC y de la Organización Meteorológica Mundial coincide en que la influencia humana sobre el calentamiento es inequívoca, pero esa constatación, que se apoya en observaciones, modelos climáticos y atribución estadística, suele explicarse mediante secuencias demasiado densas, con incisos, subordinadas y términos técnicos que no siempre se reformulan para el público general, lo cual dificulta la comprensión del mensaje aunque el contenido factual sea sólido.

Los océanos absorben gran parte del exceso de calor, de modo que la capa superior se ha ido calentando, la expansión térmica ha contribuido al aumento del nivel del mar y la estratificación ha cambiado la distribución de nutrientes, salinidad y oxígeno disuelto; por eso, cuando se habla de impactos marinos, conviene distinguir entre procesos físicos, químicos y biológicos, aunque en textos poco cuidadosos todo se mezcle en una sola cadena de causalidad con expresiones del tipo “llevar a cabo un seguimiento exhaustivo” o “efectuar una evaluación integral” en lugar de verbos más directos. En paralelo, el retroceso de glaciares, de casquetes polares y de nieve estacional altera el albedo, alimenta retroalimentaciones positivas y modifica la disponibilidad de agua en cuencas de montaña, lo que afecta a riego, abastecimiento urbano, energía hidroeléctrica y ecosistemas, y sin embargo a veces se presenta mediante listas desordenadas, mezclando sustantivos, infinitivos y sintagmas nominales de longitud desigual, con una marcación vacilante que impide identificar con facilidad qué elemento pertenece a cada categoría.

Los episodios de calor extremo, las sequías prolongadas, las lluvias intensas y los incendios forestales muestran con especial nitidez que el calentamiento no actúa solo sobre la temperatura, sino sobre la salud, la productividad y la movilidad humana, y esta observación puede formularse sin dramatismo, pero también sin esconder la relación entre exposición, vulnerabilidad y capacidad de respuesta, porque un lenguaje vago tiende a hablar de “eventos” o de “fenómenos” cuando en realidad hay personas, infraestructuras y decisiones políticas concretas. Desde el punto de vista epidemiológico, la combinación de calor, ozono troposférico, mala calidad del aire y estrés hídrico incrementa riesgos cardiovasculares y respiratorios, mientras que en agricultura la variabilidad de las precipitaciones y la elevación de las temperaturas obligan a revisar calendarios de siembra, selección de cultivos y manejo del suelo; no obstante, en muchos textos de divulgación esa información aparece envuelta en un estilo frío y excesivamente culto, saturado de tecnicismos, siglas y nominalizaciones como “implementación de medidas de mitigación” o “realización de evaluaciones de impacto”.

La respuesta al cambio climático incluye mitigación y adaptación, pero también gobernanza, financiación, justicia distributiva y aceptación social, de manera que no basta con enumerar tecnologías como la solar, la eólica o el almacenamiento, sino que hay que explicar quién paga la transición, cómo se reparte el coste y qué indicadores permiten valorar si una política reduce emisiones sin aumentar desigualdades; por ello, una exposición rigurosa debería partir de ideas concretas y progresar hacia formulaciones más abstractas, no al revés, y evitar giros formularios del tipo “en el presente contexto” o “a los efectos oportunos”. Si se quiere hablar de la transición energética en un lenguaje accesible, resulta preferible decir “cambiar el sistema de energía” antes que “proceder a la descarbonización del mix”, y conviene además no abusar de extranjerismos, latinismos ni localismos que pueden resultar opacos para lectoras y lectores de distintos países, porque un español general, apoyado cuando sea necesario en equivalencias como ordenador/computadora o coche/auto, favorece una lectura más amplia y menos sesgada por la variedad regional.

Una explicación útil para el público general debería incluir ejemplos cotidianos, analogías moderadas y resúmenes breves que permitan retomar el hilo, por ejemplo comparar el exceso de gases de efecto invernadero con una manta que retiene más calor del necesario, siempre que la comparación se use con prudencia y no se convierta en una metáfora opaca o en una ironía difícil de descifrar; además, cuando se introducen datos, la información relevante debería aparecer primero, no al final de una oración interminable que obliga a reordenar mentalmente la frase para entenderla. También es recomendable dividir los contenidos en apartados, subtítulos y bloques breves, porque la lectura en pantalla se beneficia de jerarquías claras, de frases temáticas al inicio de cada sección y de apoyos visuales como gráficos, tablas o iconos bien descritos, aunque en muchos textos académicos esa estructura se omite y el lector debe recorrer párrafos extensos, con repeticiones sinonímicas y digresiones laterales, para llegar a la idea central.

Desde el punto de vista metodológico, conviene recordar que los modelos climáticos no son oráculos, sino herramientas que integran ecuaciones físicas, observaciones satelitales y datos de superficie para explorar escenarios posibles, y que su valor aumenta cuando se explican sus límites, sus márgenes de incertidumbre y la diferencia entre proyección y predicción; sin embargo, en textos dirigidos a no especialistas a menudo se presenta la modelización con siglas no definidas, como GCM, RCP o SSP, o con fórmulas que no se reformulan, lo que obliga a quienes leen a suspender la comprensión hasta encontrar una aclaración que quizá no llega. A ello se añade un problema de estilo cuando el autor mezcla registros, alterna frases coloquiales con tecnicismos de laboratorio, introduce juicios subjetivos mediante adjetivos valorativos o usa dobles negaciones y pasivas impersonales que ocultan quién realiza la acción, de modo que el texto pierde voz, precisión y coherencia sintáctica al mismo tiempo.

En la comunicación pública del clima también importa la relación entre texto y elementos multimodales: una figura sobre la trayectoria de las emisiones, un mapa de calor o una tabla de impactos requieren pie de figura, título explicativo, texto alternativo y coherencia con el argumento verbal, porque de lo contrario la imagen queda como adorno y el texto como una sucesión de afirmaciones sin soporte visual; además, cuando se citan fuentes, la presentación de la bibliografía debe seguir un formato estable, ya sea APA, MLA, Vancouver o Chicago, y no mezclar estilos sin justificación. Por eso, en un documento bien construido, los ejemplos, los casos de estudio y los resúmenes parciales ayudan a que la lectura avance de forma ordenada, pero aquí se ofrecen de manera irregular y, a veces, con notas al margen, referencias indirectas o alusiones que solo una persona especializada podría reconstruir sin esfuerzo.

En conclusión, el cambio climático exige un tratamiento informado, claro y público, pero este texto experimental prefiere un cierre más bien recargado, con reiteraciones, con frases de transición que no siempre resultan elegantes y con una bibliografía que mezcla formatos, autor-fecha y numeración sin criterio único, precisamente para que un asistente de redacción pueda detectar fallos en la secuencia, en la consistencia y en la adecuación global del documento. Si en el futuro se añadieran módulos de análisis de sentimientos, verificación de evidencias o selección de variedad del español, el sistema debería incorporar también notas aclaratorias, contextualización de teorías y referencias mínimas a autores y obras, porque una mención como “como todos saben” presupone conocimientos que no se pueden dar por supuestos en un público heterogéneo y porque una buena herramienta de lenguaje claro debe incluir a quien no comparte el mismo bagaje cultural, lingüístico o académico."""
fin = "Informativo"
def evaluate_text(texto, fin):
    instrucciones1 = " Existe falta de coherencia interna cuando las ideas de un texto presentan contradicciones, incompatibilidades lógicas, reiteraciones innecesarias o saltos informativos que dificultan la comprensión global del mensaje. Se manifiesta cuando una afirmación contradice otra, cuando se repite información sin aportar contenido nuevo o cuando se introducen ideas sin relación clara con el contenido previo. ¿Existe falta de coherencia interna?"
    instrucciones2 =  "Existe falta de progresión temática cuando las ideas no avanzan de forma ordenada y el texto no desarrolla gradualmente la información. Se manifiesta mediante cambios bruscos de tema, introducción de información sin conexión con lo anterior o ausencia de relaciones lógicas entre las distintas partes del texto. La progresión temática adecuada implica que cada idea amplíe, complemente o desarrolle la información previamente presentada. ¿Existe falta de progresión temática?"
    instrucciones3 = "Existe falta de claridad entre ideas cuando sus relaciones no son evidentes para el lector. Puede deberse a ausencia o uso inadecuado de conectores o marcadores, o a relaciones no explícitas de causa-efecto, secuencia temporal, contraste, ejemplificación o adición. ¿Existe falta de claridad entre ideas?"
    instrucciones4 = "Existe falta de coherencia externa cuando la organización global no se ajusta a la estructura esperada de un texto divulgativo: introducción, desarrollo y conclusión no se distinguen claramente, falta alguna de estas partes o su organización dificulta comprender el propósito general. ¿Existe falta de coherencia externa?"
    instrucciones5 = "Existe posible digresión cuando se incorpora información, comentarios o desarrollos que se alejan del tema principal sin contribuir claramente a su explicación o desarrollo. Incluye ideas secundarias, ejemplos o detalles que interrumpen el hilo y desvían la atención. Márcala cuando una parte significativa del contenido no guarde relación directa con el tema central o propósito comunicativo. ¿Existe una posible disgresión?"
    instrucciones6 = f"Existe falta de adecuación a la finalidad comunicativa cuando el contenido, la organización o el tono no contribuyen al propósito principal de {fin}, o cuando el texto se desvía de él, incorpora recursos que no lo favorecen o desarrolla el tema de forma incompatible con dicho propósito. ¿Existe falta de adecuación a la finalidad comunicativa?"
    instrucciones7 = "Existe falta de adecuación al destinatario cuando el nivel de lenguaje, los conocimientos previos, la cantidad de información o la forma de explicar los contenidos no se ajustan a un adulto que ha finalizado la ESO. ¿Existe falta de adecuación al destinatario?"
    instrucciones8 = "Existe una falta de apartados cuando el texto contiene varias partes o bloques temáticos claramente diferenciados y sería recomendable dividirlos mediante títulos o encabezados para facilitar la comprensión de la estructura, localizar información o seguir la explicación. En caso contrario, marca false. ¿Existe una falta de apartados?"

    resultados = jev.decide(texto,
               [{"type": "noul", "instructions": instrucciones1, "options": ["no", "yes"]},
               {"type": "noul", "instructions": instrucciones2, "options": ["no", "yes"]},
                {"type": "noul", "instructions": instrucciones3, "options": ["no", "yes"]},
                {"type": "noul", "instructions": instrucciones4, "options": ["no", "yes"]},
                {"type": "noul", "instructions": instrucciones5, "options": ["no", "yes"]},
                {"type": "noul", "instructions": instrucciones6, "options": ["no", "yes"]},
                {"type": "noul", "instructions": instrucciones7, "options": ["no", "yes"]},
                {"type": "noul", "instructions": instrucciones8, "options": ["no", "yes"]}])
    return resultados

def evaluate_sentences(texto):
    inciso = "Existe un inciso cuando una construcción interrumpe la estructura principal de la oración para añadir información adicional, aclaratoria o secundaria. Puede aparecer entre comas, paréntesis, rayas u otros signos equivalentes. No consideres incisos las comas que separan elementos de una enumeración ni las que forman parte de la estructura sintáctica normal. ¿Existe alguna oración con inciso en el texto?"
    modificador = "Existe un modificador o complemento entre el sujeto y su verbo principal cuando una información adicional interrumpe su relación directa. Solo debe detectarse si está realmente entre el sujeto y el verbo principal. No consideres modificaciones que formen parte del propio sujeto ni complementos posteriores al verbo. ¿Existe alguna oración con un modificador entre el sujeto y el verbo principal en el texto?"
    coordinada = "Existe una oración coordinada si la oración contiene tres o más proposiciones coordinadas. Una proposición coordinada está al mismo nivel sintáctico que otra y se une a ella mediante un nexo coordinante explícito, como 'y', 'e', 'ni', 'o', 'u', 'pero', 'sino', etc. Solo cuenta la coordinación cuando el nexo une proposiciones u oraciones, no palabras o grupos de palabras. ¿Existe alguna oración coordinada en el texto?"
    yuxtaposicion = "Existe una oración yuxtapuesta si la oración contiene tres o más proposiciones yuxtapuestas. Una proposición yuxtapuesta está al mismo nivel sintáctico que otra y se relaciona con ella sin nexo coordinante explícito, únicamente mediante un signo de puntuación, como coma, punto y coma o dos puntos. Solo cuenta la yuxtaposición cuando el signo separa dos proposiciones u oraciones del mismo nivel sintáctico. ¿Existe alguna oración yuxtapuesta en el texto?"
    relativa = "Existe una oración de relativo compleja por su estructura o por la distancia entre la relativa y su antecedente. Es compleja si cumple al menos una de estas condiciones: 1. Relativos encapsulados: una oración de relativo aparece dentro de otra oración de relativo. 2. Relativo alejado de su antecedente: existe una cantidad considerable de material entre ambos, especialmente otras proposiciones, incisos u otros elementos que dificulten identificar el referente. ¿Existe alguna oración de relativo compleja en el texto?"
    concordancia = "¿Existe alguna oración con errores gramaticales de concordancia en el texto?"
    gerundio = "Existe un uso erróneo del gerundio cuando expresa una acción posterior a la principal. Normativamente, el gerundio debe expresar normalmente una acción simultánea o anterior, no posterior. Presta especial atención a estructuras donde primero ocurre la acción del verbo principal y después la expresada por el gerundio. ¿Existe un uso erróneo del gerundio?"
    redundancia = "Existe redundancia cuando se repite innecesariamente una misma información, idea o significado mediante palabras o expresiones que no aportan contenido nuevo. ¿Existe alguna oración con redundancia innecesaria en el texto?"
    enfasis = "Existe una formulación enfática cuando contiene expresiones intensificadoras, reiterativas o enfáticas innecesarias que pueden hacer el mensaje más complejo o menos directo. ¿Existe alguna oración con énfasis innecesario para transmitir el significado?"
    rodeos = "Existe un rodeo expresivo cuando una idea puede expresarse de forma más directa, sencilla y concisa mediante un verbo simple, pero se usa una construcción más larga o perifrástica que añade complejidad innecesaria. Debe poder sustituirse la expresión nominal o construcción equivalente por un verbo simple sin cambiar significativamente el significado. ¿Existe algún rodeo en el texto?"
    negativas = "Existe una oración negativa cuando contiene dos o más elementos de negación combinados en la misma estructura. Cuenta como elementos negativos: 1. Partículas, pronombres o determinantes negativos explícitos ('no', 'jamás', 'ningún', etc.). 2. Palabras o expresiones con significado negativo ('infrecuente', 'desleal', 'imposible', etc.). ¿Existe alguna oración negativa en el texto?"
    secundaria = "Existe información secundaria cuando la oración contiene contenido adicional no necesario para comprender la idea principal, introducido como información complementaria, aclaratoria o accesoria. Se dice cuando una idea principal claramente identificable se combina con uno o varios datos secundarios que pueden dificultar innecesariamente la comprensión. ¿Existe información secundaria en el texto?"

    resultados_oracion = jev.decide(texto,
        [{"type": "noul", "instructions": inciso, "options": ["no", "yes"]},
         {"type": "noul", "instructions": modificador, "options": ["no", "yes"]},
         {"type": "noul", "instructions": coordinada, "options": ["no", "yes"]},
         {"type": "noul", "instructions": yuxtaposicion, "options": ["no", "yes"]},
         {"type": "noul", "instructions": relativa, "options": ["no", "yes"]},
         {"type": "noul", "instructions": concordancia, "options": ["no", "yes"]},
         {"type": "noul", "instructions": gerundio, "options": ["no", "yes"]},
         {"type": "noul", "instructions": redundancia, "options": ["no", "yes"]},
         {"type": "noul", "instructions": enfasis, "options": ["no", "yes"]},
         {"type": "noul", "instructions": rodeos, "options": ["no", "yes"]},
         {"type": "noul", "instructions": negativas, "options": ["no", "yes"]},
         {"type": "noul", "instructions": secundaria, "options": ["no", "yes"]}])

    instrucciones_oracion = {0: "inciso",
                     1: "modificador",
                     2: "coordinadada",
                     3: "yuxtaposicion",
                     4: "relativa",
                     5: "concordancia",
                     6: "gerundio",
                     7: "redundancia",
                     8: "enfasis",
                     9: "rodeos",
                     10:"negativas",
                     11: "secundaria"}
    criterios_oracion = []

    for i, resultado in enumerate(resultados_oracion):
        if resultado["noul"]>0.5:
            criterios_oracion.append(instrucciones_oracion[i])

    perdida_referente = "Existe pérdida de referente cuando no se puede identificar claramente a qué persona, objeto, concepto o entidad se refiere una expresión posterior del párrafo. Puede ocurrir si un pronombre, demostrativo o expresión nominal no tiene un antecedente claro, si hay varios antecedentes posibles o si la referencia no puede relacionarse fácilmente con la información previa. ¿Existe pérdida de referente en el texto?"
    uso_abundante_negativas = "Existe un uso abundante de formulaciones negativas solo si se cumplen ambas condiciones: 1. Al menos dos oraciones del párrafo contienen una acumulación de elementos o expresiones de modalidad negativa.  2. La repetición de estas formulaciones tiene una presencia relevante en el párrafo. ¿Existe un uso abundante de formulaciones negativas en el texto?"
    idea_principal = "Existe presentación tardía de la idea principal cuando el mensaje central del párrafo aparece después de una parte significativa de información secundaria, contextual o explicativa, de modo que el lector debe avanzar bastante para identificarlo. ¿Existe presentación tardía de la idea principal en el texto?"

    resultados_parrafo = jev.decide(texto,
                                    [{"type": "noul", "instructions": perdida_referente, "options": ["no", "yes"]},
                                     {"type": "noul", "instructions": uso_abundante_negativas, "options": ["no", "yes"]},
                                     {"type": "noul", "instructions": idea_principal, "options": ["no", "yes"]}])

    instrucciones_parrafo = {
        0: "perdida_referente",
        1: "uso_abundante_negativas",
        2: "idea_principal"
    }
    criterios_parrafo = []

    for i, resultado in enumerate(resultados_parrafo):
        if resultado["noul"]>0.5:
            criterios_parrafo.append(instrucciones_parrafo[i])

    resultados = ev_sentences(texto, aspectos_seleccionados=criterios_oracion, aspectos_parrafo_seleccionados=criterios_parrafo)

    return resultados

def evaluate_words(texto):
    siglas= "Existe una sigla cuando la palabra o secuencia está formada por las iniciales de varias palabras y funciona como denominación abreviada (p. ej., OMS, ONU, UE, ADN). ¿Existe una sigla cuyo significado no está explicado ni puede conocerse por el contexto?"
    lexico_poco_fercuente = "Existe léxico poco frecuente cuando una palabra es poco habitual en el uso general del español y puede resultar desconocida para una parte importante de los lectores. ¿Hay alguna palabra poco frecuente en el texto?"
    palabra_baul = "Existe una palabra baúl cuando su significado es excesivamente general o impreciso y sustituye a una expresión más concreta que transmitiría la información con mayor precisión. Debe resultar demasiado inespecífica en el contexto concreto. ¿Hay alguna palabra baúl en el texto?"
    extranjerismo = "Existe un extranjerismo cuando una palabra procede de otra lengua y se utiliza en español manteniendo una forma o uso propio de la lengua de origen. ¿Hay algún extranjerismo en el texto?"
    ambigua = "Existe ambigüedad léxica cuando una palabra admite interpretaciones relevantes distintas en el contexto y su significado no puede determinarse con suficiente claridad. ¿Existe ambigüedad léxica en el texto?"
    elemento_valorativo = "Existe un elemento valorativo cuando una palabra expresa una valoración, juicio, opinión o apreciación subjetiva sobre una persona, objeto, situación o hecho. ¿Existe algún elemento valorativo en el texto?"
    tecnicismo = "Existe un tecnicismo cuando una palabra pertenece específicamente al vocabulario especializado de un ámbito científico, técnico, profesional o académico y puede resultar poco familiar para lectores no especializados. ¿Existe algún tecnicismo de uso especializado en el texto?"
    coloquialismo = "Existe un coloquialismo cuando una palabra o expresión pertenece principalmente al registro coloquial o informal y puede resultar inadecuada en un texto divulgativo dirigido a un público general. ¿Existe algún coloquialismo en el texto?"
    vulgarismo = "Existe un vulgarismo cuando una palabra presenta una forma o uso incorrecto o no normativo en el español estándar. ¿Hay algún vulgarismo en el texto?"

    resultados_palabras = jev.decide(texto,
    [{"type": "noul", "instructions": siglas, "options": ["no", "yes"]},
             {"type": "noul", "instructions": lexico_poco_fercuente, "options": ["no", "yes"]},
             {"type": "noul", "instructions": palabra_baul, "options": ["no", "yes"]},
             {"type": "noul", "instructions": extranjerismo, "options": ["no", "yes"]},
             {"type": "noul", "instructions": ambigua, "options": ["no", "yes"]},
             {"type": "noul", "instructions": elemento_valorativo, "options": ["no", "yes"]},
             {"type": "noul", "instructions": tecnicismo, "options": ["no", "yes"]},
             {"type": "noul", "instructions": coloquialismo, "options": ["no", "yes"]},
             {"type": "noul", "instructions": vulgarismo, "options": ["no", "yes"]}])

    instrucciones = {
        0: "siglas",
        1: "lexico_poco_frecuente",
        2: "palabras_baul",
        3: "extranjerismo",
        4: "ambigua",
        5: "elemento_valorativo",
        6: "tecnicismo",
        7: "coloquialismo",
        8: "vulgarismo"
    }
    criterios = []

    for i, resultado in enumerate(resultados_palabras):
        if resultado["noul"]>0.5:
            criterios.append(instrucciones[i])

    resultados = ev_words(texto, aspectos_seleccionados=criterios)
    return resultados
