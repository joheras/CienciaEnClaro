let quill;
let comments = [];
let commentIdCounter = 1;
let commentsLocked = false;
let isHoveringNumber = false;
let isHoveringPopup = false;
let analyzedParagraphStart = null; //Nos permite saber a qué párrafo se le ha aplicado la función addCommentParagraph
let appMode = "write"; //Puede ser "write", "feedback" o "analysis"
let hasPendingChanges = false; // Para saber si ha cambiado el texto desde la última vez que se ha analizado
let hasFullAnalysis = false;
let hasParagraphAnalysis = false;
let anaylizedParagraphNumber = null;
let totalOracionesPorParrafo = {};
let conteoErroresPorTipoParrafo = {};
let porcentajesPorTipoParrafo = {};

// Meter al css
let popupDiv = document.createElement("div");
popupDiv.className = "paragraph-suggestion-popup";
popupDiv.style.position = "absolute";
popupDiv.style.background = "#fff8c4";
popupDiv.style.border = "1px solid #ccc";
popupDiv.style.padding = "6px 10px";
popupDiv.style.borderRadius = "4px";
popupDiv.style.boxShadow = "0 2px 5px rgba(0,0,0,0.2)";
popupDiv.style.zIndex = "1000";
popupDiv.style.display = "none"; // Oculto al inicio
document.body.appendChild(popupDiv);

let highlightParagraphs = false;
let currentParagraphComment = null;
let currentModalComment = null; // mantener el comentario para el popup de la sugerencia

quill = new Quill('#editor', {
    theme: 'snow',
    modules: {
        toolbar: {
            container: "#toolbar",
            handlers: {
                //addComment: addCom,
                analyze: analyzeText,
                paragraph: addCommentParagraph,
                comment10: addCommentText
            }
        }
    }
});

const editToggle = document.getElementById("editToggle");
const editLabel = document.getElementById("editLabel");
setEditMode(true);
editToggle.addEventListener("change", () => {
    setEditMode(editToggle.checked);
})

// para que la aplicación empiece en el modo escribir
quill.enable(true);
document.getElementById("filterContainer").style.display="none";
document.getElementById("filterText").style.display="none";
document.getElementById("analysisContainer").style.display="none";
document.getElementById("analyzeBtn").style.display = "none";
//document.getElementById("paragraphBtn").style.display = "none";
document.getElementById("addCommentFirst10Btn").style.display = "none";
document.getElementById("recalculateBtn").style.display = "none";
document.getElementById("generateSuggestionBtn").style.display="none";
document.getElementById("filterParagraph").addEventListener("change", () => {
    renderComments();
    highlightParagraphFromFilter();
    updateGenerateSuggestionButton();
})
document.getElementById("commentsList").style.display="none";

quill.on("selection-change", highlightActiveParagraph);

quill.root.querySelectorAll("p").forEach(p =>
    p.classList.add("active-paragraph"));

quill.on("text-change", (delta, oldDelta, source) => {
    updateParagraphNumbers();
    updateParagraphFilter();

    // Solo reaccionar si el cambio lo hizo el usuario
    if (source === "user") {
        hasPendingChanges = true;
        // Si hay un análisis activo o comentarios visibles
        if (!commentsLocked && comments.length > 0) {
            lockComments();
        }
    }
});

//document.getElementById("addCommentBtn").onclick = addCom;
document.getElementById("analyzeBtn").addEventListener("click", analyzeText);

//document.getElementById("paragraphBtn").onclick = () => {
 //   if (quill.isEnabled()){
//        return;
//    } else {
//        addCommentParagraph();
//    }
//}
document.getElementById("recalculateBtn").onclick = () => {
    unlockComments();
    addCommentParagraph();
};
document.getElementById("addCommentFirst10Btn").onclick = () => {
    if (quill.isEnabled()){
        return;
    } else {
        addCommentText();
    }
};

document.querySelector(".ql-editor").setAttribute("spellcheck", "true");
document.getElementById("filterType").addEventListener("change", () => {
    renderComments();
})

updateParagraphNumbers();
updateParagraphFilter();

//const writeBtn = document.getElementById("writeModeBtn");
const feedBackBtn = document.getElementById("feedbackModeBtn");
const analysisBtn = document.getElementById("analysisModeBtn");
//writeBtn.onclick = () => setMode("write");
feedBackBtn.onclick = () => {
    setMode("feedback");
    forceLockEditing();
    addCommentText();
}
analysisBtn.onclick = () => {
    setMode("analysis");
    forceLockEditing();
    analyzeText();
}

// Referencias a la sugerencia
const modal = document.getElementById("suggestionModal");
const generateBtn = document.getElementById("generateSuggestionBtn");
const closeModalBtn = document.getElementById("closeModalBtn");
const newSuggestionBtn = document.getElementById('newSuggestionBtn');
const useSuggestionBtn = document.getElementById('useSuggestionBtn');

const originalTextArea = document.getElementById('originalText');
const suggestedTextArea = document.getElementById('suggestedText');


generateBtn.addEventListener('click', async () => {
    const paragraphFilter = document.getElementById("filterParagraph").value;
    if (paragraphFilter === "all") return;
    const paragraphIndex = Number(paragraphFilter);
    const paragraphs = quill.root.querySelectorAll("p");
    let paragraphText = "";

    let visibleIndex = 1;
    paragraphs.forEach(p => {
        const text = p.textContent.replace(/\u200B/g, "").trim();
        if (text.length > 0) {
            if (visibleIndex === paragraphIndex) {
                paragraphText = text;
            }
            visibleIndex++;
        }
    });

    if (!paragraphText) return;

    const range = quill.getSelection();
    const paragraphData = getParagraphAtCursor();

    currentModalComment = {
        index: paragraphData.start,
        texto: paragraphData.paragraphText,
        suggestion: ""
    };

    originalTextArea.value = paragraphText;
    suggestedTextArea.value = "";

    modal.style.display="block";

    // Generamos sugerencia
    await generateSuggestion(currentModalComment);
})
// Cerar modal sin cambios
closeModalBtn.addEventListener('click', ()=>{
    modal.style.display="none";
    currentModalComment = null;
})
//Generar otra sugerencia
newSuggestionBtn.addEventListener('click', async()=>{
    if (!currentModalComment) return;
    await generateSuggestion(currentModalComment);
});
// Usar sugerencia
useSuggestionBtn.addEventListener('click', () => {
    if (!currentModalComment) return;
    const start = currentModalComment.index;
    const text = quill.getText();

    let end = text.indexOf("\n", start);
    if (end === -1) end = text.length;

    const length = end-start;

    // Borrar el párrafo
    quill.deleteText(start, length);

    // Insertar sugerencia
    let newText = suggestedTextArea.value;
    quill.insertText(start, newText);

    modal.style.display="none";
    currentModalComment = null;
    updateParagraphNumbers();
    updateParagraphFilter();
    hasPendingChanges = true;
    lockComments();
});

function setMode(mode) {
    appMode = mode;

    //const isWrite = mode === "write";
    const isFeedback = mode === "feedback";
    const isAnalysis = mode === "analysis";

    //writeBtn.classList.toggle("active", isWrite);
    feedBackBtn.classList.toggle("active", isFeedback);
    analysisBtn.classList.toggle("active", isAnalysis);

    /*if (isWrite) {
        editToggle.disabled = false;
        setEditMode(editToggle.checked);
    } else {
        editToggle.checked = false;
        editToggle.disabled = true;
        setEditMode(false);
    }

     */

    document.getElementById("commentsList").style.display = isFeedback ? "block" : "none";
    document.getElementById("filterContainer").style.display = isFeedback ? "block" : "none";
    document.getElementById("filterText").style.display = isFeedback ? "block" : "none";
    //document.getElementById("paragraphBtn").style.display = isFeedback ? "block" : "none";
    document.getElementById("addCommentFirst10Btn").style.display = isFeedback ? "block" : "none";
    document.getElementById("analysisContainer").style.display = isAnalysis ? "block" : "none";
    document.getElementById("analyzeBtn").style.display = isAnalysis ? "block" : "none";

    if (isFeedback && hasPendingChanges){
        document.getElementById("recalculateBtn").style.display="block";
    } else {
        document.getElementById("recalculateBtn").style.display="none";
    }
    updateGenerateSuggestionButton();
    if (mode!=="feedback") {
        document.getElementById("generateSuggestionBtn").style.display="none";
    }
}
/*
// Añadir comentario manual
function addCom(){
    const range = quill.getSelection();
    if (!range || range.length === 0){
        alert("Selecciona un texto para comentar.");
        return;
    }

    const userComment = prompt("Escribe tu comentario:");
    if (!userComment) return;

    const id = "comment-"+commentIdCounter++;

    quill.formatText(range.index, range.length, {background: "yellow"});

    comments.push({id, text: userComment, index: range.index, length: range.length, suggestion: "Texto sugerido", description: "prueba", type: "usuario"});
    updateFilterOptions();
    renderComments();
}
*/
function updateFilterOptions() {
    const select = document.getElementById("filterType");
    const types = [...new Set(comments.map(c => c.type))]; // Tipos únicos

    select.innerHTML = "";

    // Añadimos la opción "Todos"
    const allOption = document.createElement("option");
    allOption.value = "todos";
    allOption.textContent ="Todos";
    select.appendChild(allOption);

    // Añadir opciones únicas
    types.forEach(type => {
        const option = document.createElement("option");
        option.value = type;

        if (type == "index"){
            option.textContent = "Por índice";
        } else if (type == "paragraph"){
            option.textContent = "Por párrafo";
        } else {
            const cleanLabel = type.replace(/-/g, " ");
            option.textContent = cleanLabel.charAt(0).toUpperCase() + cleanLabel.slice(1);
        }
        select.appendChild(option);
    });

    //Predeterminado: "Todos"
    select.value = "todos";
}

function updateParagraphFilter() {
    const select = document.getElementById("filterParagraph");
    const paragraph = quill.root.querySelectorAll("p");

    select.innerHTML = "";

    // Opción texto completo
    const allOption = document.createElement("option");
    allOption.value = "all";
    allOption.textContent = "Texto completo";
    select.appendChild(allOption);

    let count = 1;

    paragraph.forEach(p => {
        const text = p.textContent.replace(/\u200B/g, "").trim();
        if (text.length > 0) {
            const option = document.createElement("option");
            option.value = count;
            option.textContent = "Párrafo " + count;
            select.appendChild(option);
            count++;
        }
    });
    select.value = "all";
}


function renderComments(openCommentId = null){
    if (appMode === "write") return;

    const filter = document.getElementById("filterType").value;
    const paragraphFilter = document.getElementById("filterParagraph").value;
    const panel = document.getElementById("commentsList");

    panel.innerHTML = "";

    // Para filtrar
    let filtered = comments.filter(c => c.text !== "¿Quieres una saugerencia?");
    // Filtro por tipo
    if (filter != "todos") {
        filtered = filtered.filter(c => c.type === filter);
    }
    // Filtro por párrafo
    if (paragraphFilter !== "all") {
        const paragraphNum = Number(paragraphFilter)
        filtered = filtered.filter(c => c.paragraph === paragraphNum);
        // Resaltar solo ese párrafo
        highlightParagraphFromFilter(paragraphNum);
    } else {
        // Si está seleccionado "Texto completo" quitar todos los resaltados
        highlightParagraphFromFilter(null);
    }

    if (filtered.length === 0) {
        panel.style.display="none";
        return;
    } else {
        panel.style.display = "block";
    }


    // Agrupar comentarios
    const grouped = filtered.reduce((acc, comment) => {
        const key = comment.name || comment.text;
        if (!acc[key]) {
            acc[key] = [];
        }
        acc[key].push(comment);
        return acc;
    }, {});

    const tiposOracion = ["oracionLarga", "orden", "coordinada", "yuxtapuesta"];
    const tiposParrafo = ["parrafoCorto", "parrafoLargo"]

    const totalParagraphs = getTotalParagraphs();

    // Renderizar comentarios
    Object.values(grouped).forEach(group  => {
        const first = group[0];  // Como todos los text deberían ser iguales, nos quedaremos con el del primero
        const tipo = first.name;

        const div = document.createElement("div");
        div.className = "comment-item";

        // Cabecera (texto + etiqueta tipo)
        const title = document.createElement("div");
        title.className = "comment-title";
        title.style.cursor = "pointer";

        const textSpan = document.createElement("span");

        // A nivel oración
        let porcentajeOracion = 0;
        if (conteoErroresPorTipoParrafo[tipo]) {
            let erroresTotales = 0;
            let oracionesTotales = 0;
            Object.entries(conteoErroresPorTipoParrafo[tipo]).forEach(([parrafo, errores]) => {
                const erroresSet = errores.size;
                erroresTotales += erroresSet;
                oracionesTotales += totalOracionesPorParrafo[parrafo] || 0;
            });
            if (oracionesTotales > 0) {
                porcentajeOracion = ((erroresTotales / oracionesTotales) * 100).toFixed(1);
            } else {
                porcentajeOracion = 0;
            }
        }
        // A nivel párrafo
        const affectedParagraphs = new Set(
            group.map(c => c.paragraph).filter(p => p != null)
        );

        const porcentajeParrafo = totalParagraphs > 0
            ? ((affectedParagraphs.size / totalParagraphs) * 100).toFixed(1)
            : 0;

        // Texto final
        let label = first.text;
        const paragraphFilter = document.getElementById("filterParagraph").value;

        //if (porcentajeOracion > 0) {
        //    label += `(${porcentajeOracion}%)`;
        //} else if (porcentajeParrafo > 0) {
        //    label += `(${porcentajeParrafo}%)`;
        //}

        textSpan.innerText = label;
        title.appendChild(textSpan);

        // Descripción
        const desc = document.createElement("div");
        desc.className = "comment-desc";
        desc.style.display = "none";

        /*

        // Obtener párrafos únicos directamente
        const sourceComments = paragraphFilter !== "all"
        ? group.filter(c => c.paragraph === Number(paragraphFilter))
            : group;

        const paragraphsNumbers = [...new Set(
            sourceComments.map(c => c.paragraph).filter(n => n!=null)
        )].sort((a, b) => a-b);
        // Construir texto
        let paragraphText = "";
        if (paragraphsNumbers.length === 1) {
            paragraphText = `el párrafo ${paragraphsNumbers[0]} contiene`;
        } else if (paragraphsNumbers.length > 1) {
            const last = paragraphsNumbers.pop();
            paragraphText = `Los párrafos ${paragraphsNumbers.join(", ")} y ${last} contienen`;
        }
        // Descripciones
        const descriptionMap = {
            parrafoCorto: `${paragraphText} pocas oraciones. Cada párrafo debería tener mínimo dos oraciones.`,
            parrafoLargo: `${paragraphText} demasiadas oraciones. Cada párrafo debería tener máximo cinco oraciones.`,
            oracionLarga: `${paragraphText} oraciones demasiado largas. Cada oración debería tener máximo 20 palabras.`,
            orden: `${paragraphText} oraciones que no siguen el orden sintáctico sujeto-verbo-complementos.`,
            coordinada: `${paragraphText} oraciones coordinadas.`,
            yuxtapuesta: `${paragraphText} oraciones yuxtapuestas.`
        };
        let extraDetalle = "";
        //if (tiposOracion.includes(tipo)) {
        //    const detalle = construirTextoPorParrafo(tipo, paragraphFilter);
        //    if (detalle) {
        //        extraDetalle = " Además, " + detalle + ".";
        //    }
        //}
        desc.innerText = "Descripción: " + (descriptionMap[first.name] || first.description || "Sin descripción disponible") + extraDetalle;

         */
        paragraphText = `Se han detectado `;
        const descriptionMap = {
            parrafoCorto: `los siguientes párrafos cortos. Cada párrafo debería tener mínimo dos oraciones.`,
            parrafoLargo: `los siguientes párrafos largos. Cada párrafo debería tener máximo cinco oraciones.`,
            oracionLarga: `las siguientes oraciones largas. Cada oración debería tener máximo 20 palabras.`,
            orden: `las siguientes oraciones que no siguen el orden sintáctico sujeto-verbo-complementos.`,
            coordinada: `las siguientes oraciones coordinadas.`,
            yuxtapuesta: `las siguientes oraciones yuxtapuestas.`
        };
        desc.innerText = "Descripción: " + paragraphText + descriptionMap[first.name];

        // Botón quitar sugerencia
        const btn = document.createElement("button");
        btn.innerText = "Ocultar comentario";
        btn.className = "comment-accept-btn";
        btn.style.display = "none";

        btn.onclick = () => {
            acceptSuggestion(first);
            renderComments();
        };
        title.onclick = () => {
              //Si está bloqueado no se puede clicar el comentario
              if (commentsLocked) return;

              //const start = group[0].index;
              //const end = group[group.length - 1].index + group[group.length -1].length;
              // quill.setSelection(start, end-start); // Seleccionaba el texto marcado, lo comento porque no quiero que se marque

              // Resaltar las oraciones de ese comentario
              highlightByType(first.name);

              // Cerrar todo
              document.querySelectorAll("#commentsList .comment-desc")
                  .forEach(d => d.style.display = "none");
              document.querySelectorAll("#commentsList .comment-sugg")
                  .forEach(s => s.style.display = "none");
              document.querySelectorAll("#commentsList .comment-accept-btn")
                  .forEach(b => b.style.display = "none");
              document.querySelectorAll("#commentsList .comment-sugges-btn")
                  .forEach(b => b.style.display = "none");
              document.querySelectorAll("#commentsList .comment-accept-btn")
                  .forEach(b => b.style.display = "none");
              document.querySelectorAll("#commentsList .comment-nusug-btn")
                  .forEach(b => b.style.display = "none");

              // Abrir este
              desc.style.display = "block";
              if (first.suggestion && first.suggestion.trim() !== "") {
                  btn.style.display = "inline-block";
              }
        };

        if (openCommentId && first.id === openCommentId) {
            desc.style.display = "block";
            btn.style.display = "inline-block";
        }

        div.appendChild(title);
        div.appendChild(desc);
        div.appendChild(btn);
        panel.appendChild(div);
    });
    document.getElementById("filterType");
}

// Esta función la hago para el contenido de los comentarios separados por párrafos
function construirTextoPorParrafo(tipo, paragraphFilter) {
    if (!conteoErroresPorTipoParrafo[tipo]) return "";
    const partes = [];
    Object.entries(conteoErroresPorTipoParrafo[tipo]).forEach(([parrafo, errores]) => {
        if (paragraphFilter !== "all" && Number(parrafo) !== Number(paragraphFilter)) {
            return;
        }
        const total = totalOracionesPorParrafo[parrafo] || 0;
        if (total > 0) {
            const erroresCount = errores.size || 0;
            const porcentaje = ((erroresCount/total) * 100).toFixed(1);
            partes.push(`El párrafo ${parrafo} tiene un ${porcentaje}%`);
        } else {
            const porcentaje = 0;
        }
    });
    if (partes.length === 0) return "";
    if (partes.length===1) {
        return partes[0];
    }
    const last = partes.pop();
    return partes.join(", ") + " y " + last;
}
function lockComments() {
  commentsLocked = true;
  if (appMode === "feedback") {
      document.getElementById("recalculateBtn").style.display = "block";
  }
  renderComments();
}

function unlockComments() {
  commentsLocked = false;
  document.getElementById("recalculateBtn").style.display = "none";
}

// Añadir comentarios del texto completo
async function addCommentText() {
    quill.removeFormat(0, quill.getLength());
    hasFullAnalysis = true;
    hasParagraphAnalysis = false;
    if (appMode === "write") {
        alert("Cambia a modo Feedback para analizar el texto.");
        return;
    }
    highlightParagraphs = false;

    unlockComments();
    analyzedParagraphStart = null;
    updateParagraphNumbers();
    updateParagraphFilter();

    comments = [];
    let id;
    let text1;
    let start;
    let length;
    let description;
    let suggestion;
    let error;
    let original;
    let type;
    let name;
    let texto;
    let paragraph;

    // Mostrar overlay de bloqueo
    const overlay = document.getElementById("loadingOverlay");
    overlay.style.display = "flex";

    const paragraphs = quill.root.querySelectorAll("p");
    let visibleIndex = 1;

    for (let p of paragraphs) {
        const text = p.textContent.replace(/\u200B/g, "").trim();
        if (!text) continue;

        const oraciones = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
        totalOracionesPorParrafo[visibleIndex] = oraciones.length;

        const start = quill.getIndex(Quill.find(p));
        const data = await analyzeSingleParagraph(text, start);
        data.forEach(item => {
            comments.push({id: item.id,
            text: item.text,
            index: item.start,
            length: item.end - item.start,
            description: item.description,
            error: item.error,
            original: item.original,
            type: item.type,
            suggestion: item.suggestion,
                mode: "paragraph",
                texto: text,
                paragraph: visibleIndex,
            name: item.name
            });

            const paragraphText = text;
            const localIndex = item.start - start;
            const sentenceId = getSentenceIndexInParagraph(paragraphText, localIndex);

            if (!conteoErroresPorTipoParrafo[item.name]) {
                conteoErroresPorTipoParrafo[item.name] = {};
            }
            if (!conteoErroresPorTipoParrafo[item.name][visibleIndex]) {
                conteoErroresPorTipoParrafo[item.name][visibleIndex] = new Set();
            }
            conteoErroresPorTipoParrafo[item.name][visibleIndex].add(sentenceId);
        });
        visibleIndex++;
    }
    calcularPorcentajesPorParrafo();

    updateFilterOptions();
    renderComments();

    hasPendingChanges = false;

    updateGenerateSuggestionButton();
    // ocultar overlay
    overlay.style.display ="none";
}

// Añadir comentarios del párrafo seleccionado
async function addCommentParagraph() {
    quill.removeFormat(0, quill.getLength());
    hasFullAnalysis = false;
    hasParagraphAnalysis = true;

    if (appMode === "write") {
        alert("Cambia a modo feedback para analizar el párrafo.");
        return;
    }
    quill.root.querySelectorAll("p").forEach(p =>
        p.classList.remove("active-paragraph"));

    highlightParagraphs = true;
    unlockComments();
    analyzingParagraph = true;

    const text = getParagraphAtCursor();
    if (!text) {
        alert("Coloca el cursor dentro de un párrafo.");
        return;
    }

    const {paragraphText, start} = text;
    analyzingParagraphStart = start;
/*
    const range = quill.getSelection();
    const [leaf] = quill.getLeaf(range.index);
    let p = leaf.domNode;

    while (p && p.tagName !== "P") {
        p = p.parentElement;
    }
    if (!p) {
        alert("Coloca el cursor dentro de un párrafo.");
        return;
    }

    const blot = Quill.find(p);
    const paragraphStart = quill.getIndex(blot);
    analyzedParagraphStart = paragraphStart;
 */
    const paragraphs = quill.root.querySelectorAll("p");
    let currentParagraphNumber = null;
    let visibleIndex = 1;

    paragraphs.forEach((p) => {
        const pText = p.textContent.replace(/\u200B/g, "").trim();
        if (pText.length > 0){
            if (quill.getIndex(Quill.find(p)) === start) {
                currentParagraphNumber = visibleIndex;
                p.classList.add("active-paragraph");
            } else {
                p.classList.remove("active-paragraph");
            }
            visibleIndex++;
        } else {
            p.classList.remove("active-paragraph");
        }
    });

    analyzedParagraphNumber = currentParagraphNumber;


    updateParagraphNumbers();
    updateParagraphFilter();

    // Cambiar automáticamente el filtro de párrafo
    if (currentParagraphNumber!== null) {
        const filterSelect = document.getElementById("filterParagraph");
        filterSelect.value = currentParagraphNumber.toString();
        // Resaltar el párrafo según el filtro
        highlightParagraphFromFilter();
    }

    // Mostrar overlay de bloqueo
    const overlay = document.getElementById("loadingOverlay");
    overlay.style.display = "flex";

    let parrafo = text.paragraphText;
    comments = [];
    let data;
    try {
        const response = await fetch("/analyse_paragraph", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({"parrafo": parrafo, "start": start})
        });
        data = await response.json();
    } catch (err) {
        console.error("Error analizando el párrafo:", err);
        overlay.style.display = "none";
        return;
    }
    // Procesamos comentarios por chunks para no bloquear el hilo
    const CHUNK_SIZE = 5;
    data = Array.isArray(data) ? data : data.comentarios || [];
    for (let i = 0; i< data.length; i+=CHUNK_SIZE) {
        const chunk = data.slice(i, i + CHUNK_SIZE);
        chunk.forEach(item => {
            let commentObj = {
                id: item.id,
                text: item.text,
                index: item.start,
                length: item.end - item.start,
                description: item.description,
                error: item.error,
                original: item.original,
                type: item.type,
                suggestion: item.suggestion,
                mode: "paragraph",
                texto: item.parrafo,
                isParagraphSuggestion: false,
                paragraph: getParagraphNumberFromIndex(item.start)
            };
            comments.push(commentObj);
        });
        // Dejamos que el navegador renderice
        await new Promise(r => setTimeout(r, 0));
    }


    updateFilterOptions();
    renderComments();
    analyzingParagraph = false;
    hasPendingChanges = false;

    updateGenerateSuggestionButton();
    // Ocultar overlay
    overlay.style.display = "none";
}

function getParagraphNumberFromIndex(index) {
    const paragraphs = quill.root.querySelectorAll("p");
    let visibleIndex = 1;

    for (let i=0; i<paragraphs.length; i++) {
        const p = paragraphs[i];
        const text = p.textContent.replace(/\u200B/g, "").trim();

        if (text.length > 0) {
            const blot = Quill.find(p);
            const start = quill.getIndex(blot);
            const end = start + p.innerText.length;

            if (index >= start && index < end) {
                return visibleIndex;
            }
            visibleIndex++;
        }
    }
    return null;
}

// Me selecciona todo el párrafo donde está el cursor
function getParagraphAtCursor() {
    const text = quill.getText(); // Todo el texto
        const range = quill.getSelection();
        if (!range) return null;
        const cursorPos = range.index;

        //Buscar el inicio del párrafo (salto de línea anterior)
        let start = text.lastIndexOf("\n", cursorPos-1);
        if (start==-1){
            start = 0; // Si no hay salto de línea empezamos al inicio del texto
        } else {
            start = start +1; // Si hay salto de línea empezamos justo después de él
        }

        //Buscar el final del párrafo (salto de lína siguiente)
        let final = text.indexOf("\n", cursorPos);
        let end;
        if (final == -1){
            end = text.length; // Si no hay salto de lína acaba al final del texto
        } else {
            end = final
        }

        // Obtenemos el texto del párrafo
        const paragraphText = text.slice(start, end);

        return{
            paragraphText, start, end
        }
}

async function analyzeText() {
    forceLockEditing();
    if (appMode !== "analysis") return;
    const range = quill.getSelection();
    let text;
    let description;



    // Si hay texto seleccionado
    if (range && range.length > 0) {
        description = "Información sobre el texto seleccionado.";
        text = quill.getText(range.index, range.length).trim();
    } else {
        // Si no hay texto seleccionado
        description = "Información sobre el texto completo.";
        text = quill.getText().trim();
    }
/*
    // Mostrar resultado en el popup
    const popup = document.getElementById("analysisPopup");
    const closeBtn = document.getElementById("closePopupBtn");
    const textElem = document.getElementById("analysisText");
*/
    const analysisContainer = document.getElementById("analysisContainer");

    const info = await fetch("/resumen", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text})
    });
    const datos = await info.json();

    description = description + '\n\n' + datos;
   /* textElem.innerText = description;
    popup.style.display = "flex";
    popup.setAttribute('aria-hidden', 'false');
    // Cerrar popup al hacer click en el botón
    closeBtn.addEventListener('click', () => {
        popup.style.display = "none";
        popup.setAttribute('aria-hidden', 'true');
    });

    // También cerrar si se hace click fuera del cuadro
    popup.onclick = (e) => {
        if (e.target === popup) {
            popup.style.display = "none";
            popup.setAttribute('aria-hidden', 'true');
        }
    };
*/

    analysisContainer.innerHTML = "<strong>Análisis:</strong><br>" + description.replace(/\n/g, "<br>");
}

function updateParagraphNumbers() {
    const container = document.getElementById("paragraphNumbers");
    container.innerHTML = "";
    const paragraphs = quill.root.querySelectorAll("p");
    let count = 1;

    paragraphs.forEach(p => {
        const text = p.textContent.replace(/\u200B/g, "").trim();
        const row = document.createElement("div");
        row.style.height = p.offsetHeight + "px";
        row.style.display = "flex";
        row.style.alignItems = "flex-start";
        row.style.justifyContent = "flex-end";
        row.style.paddingRight = "6px";
        row.style.boxSizing = "border-box";

        if (text) {
            row.textContent = count++;

            // Si este párrafo es el analizado, le añadimos la clase
            const blot = Quill.find(p);
            const parStart = quill.getIndex(blot);
            if (analyzedParagraphStart!=null && analyzedParagraphStart === parStart){
                row.classList.add("active-paragraph-number");
            }
        } else {
                row.textContent = ""; // párrafo vacío -> hueco
            }
            container.appendChild(row);
    });
    container.scrollTop = quill.root.scrollTop;
    attachParagraphHover();
}

// Para que la sugerencia me aparezca en el número del contador de párrafo
function attachParagraphHover() {
    const container = document.getElementById("paragraphNumbers");
    const paragraphs = quill.root.querySelectorAll("p");

    paragraphs.forEach((p, idx) => {
        const numberDiv = container.children[idx];
        if (!numberDiv) return;

        numberDiv.addEventListener("mouseenter", async () => {
            isHoveringNumber = true;
            try {
                if (currentParagraphComment===p) return;
                currentParagraphComment = p;
                // Comprobamos si hay comentario con sugerencia en este párrafo
                const blot = Quill.find(p);
                const parStart = quill.getIndex(blot);
                const parEnd = parStart + p.innerText.length;

                const comment = comments.find(c =>
                    c.mode === "paragraph" &&
                    c.isParagraphSuggestion &&
                    c.index >= parStart &&
                    c.index < parEnd
                );

                //Limpiar clases de todos los números
                document.querySelectorAll("#paragraphNumbers div").forEach(div => {
                    div.classList.remove("active-paragraph-number-suggestion");
                });

                if (!comment) {
                hideSuggestionPopup();
                return;
                }

                // Marcar el número del párrafo con la sugerencia
                numberDiv.classList.add("active-paragraph-number-suggestion");

                if (!comment.suggestion || comment.suggestion === "Sugerencia generada automáticamente") {
                    await generateSuggestion(comment);
                }
                // Mostrar pop-up
                showSuggestionPopup(comment.suggestion, numberDiv, comment);
                } catch (err) {
                console.error("error al obtener la posición del párrafo: ", err);
            }
            });
        numberDiv.addEventListener("mouseleave", () => {
            isHoveringNumber = false;
            setTimeout(checkPopupClose, 50);
        });
    });
}

function showSuggestionPopup(text, targetDiv, comment){
    if (!popupDiv) return;

    popupDiv.addEventListener("mouseenter", () => {
        isHoveringPopup = true;
    });

    popupDiv.addEventListener("mouseleave", () => {
        isHoveringPopup = false;
        setTimeout(checkPopupClose, 50);
    });

    // Limpiar contenido anterior
    popupDiv.innerHTML = "";

    // Contenedor texto
    const textDiv = document.createElement("div");
    textDiv.style.marginBottom = "8px";
    textDiv.innerText = text;

    popupDiv.onmouseleave = (e) => {
        const toElement = e.relatedTarget;

        // Si volvemos al número no se cierra
        if (toElement && toElement.closest("#paragraphNumbers")) return;

        hideSuggestionPopup();
        currentParagraphComment = null;

        document.querySelectorAll("#paragraphNumbers div").forEach(div =>
        div.classList.remove("active-paragraph-number-suggestion"));
    }

    // Botón aplicar
    const applyBtn = document.createElement("button");
    applyBtn.innerText = "Aplicar sugerencia";
    applyBtn.style.padding = "4px 8px";
    applyBtn.style.cursor = "pointer";

    applyBtn.onclick = () =>{
        applyParagraphSuggestion(comment);
        hideSuggestionPopup();
    };

    popupDiv.appendChild(textDiv);
    popupDiv.appendChild(applyBtn);

    popupDiv.style.display = "block";

    const rect = targetDiv.getBoundingClientRect();
    const popupHeight = popupDiv.offsetHeight;
    const popupMargin = 8;
    const viewportHeight = window.innerHeight;

    let top = rect.bottom + popupMargin + window.scrollY;

    if (top + popupHeight > viewportHeight) {
        top = rect.top - popupHeight - popupMargin + window.scrollY;
        if (top < window.scrollY + 5) {
            top = window.scrollY + 5;
        }
    }
    let left = rect.right + 10 + window.scrollX;
    popupDiv.style.top = `${top}px`;
    popupDiv.style.left = `${left}px`;
}

function hideSuggestionPopup() {
    if (!popupDiv) return;
    popupDiv.style.display = "none";
}

function highlightActiveParagraph(){
    // Solo va a funcionar si tenemos activada la variable highlighParagraphs
    if (!highlightParagraphs) return;

    const range = quill.getSelection();
    if (!range) return;
    const index = range.index;

    let currentParagraphNumber = getParagraphNumberFromIndex(index);

    // Obtenemos el leaf en la posición del cursor
    const [leaf] = quill.getLeaf(index);
    if (!leaf) return;

    // Subimos hasta el párrafo <p> que lo contiene
    let p = leaf.domNode;
    while (p && p.tagName!=="P") {
        p = p.parentElement;
    }
    if (!p) return;

    // Quitar clase a todos los párrafos
    quill.root.querySelectorAll("p").forEach(p =>
    p.classList.remove("active-paragraph"));

    // Activamos este párrafo
    p.classList.add("active-paragraph");

    // Mostrar o no el botón "Recalcular"
    const recalcularBtn = document.getElementById("recalculateBtn");
    // Si el inicio del párrafo actual difiere del analizado, mostrar botón
    if (analyzedParagraphNumber !== null && currentParagraphNumber!== analyzedParagraphNumber && appMode === "feedback"){
        recalcularBtn.style.display = "block";
    } else {
        recalcularBtn.style.display = "none";
    }
}

function highlightParagraphFromFilter() {
    const paragraphFilter = document.getElementById("filterParagraph").value;
    const paragraphs = quill.root.querySelectorAll("p");

    // Quitar clase a todos
    paragraphs.forEach(p => p.classList.remove("active-paragraph"));

    // Si es "Texto completo" activar todos
    if (paragraphFilter === "all") {
        paragraphs.forEach(p => p.classList.add("active-paragraph"));
        return;
    }

    let visibleIndex = 1;
    let targetParagraph = null;
    paragraphs.forEach((p) => {
        const text = p.textContent.replace(/\u200B/g, "").trim();
        if (text.length > 0) {
            if (visibleIndex == paragraphFilter) {
                targetParagraph = p;
            }
            visibleIndex++;
        }
    });
    // Activar solo el seleccionado
    if (targetParagraph) {
        targetParagraph.classList.add("active-paragraph");
    }
}

async function generateSuggestion(comment){
    // Mostrar overlay de bloqueo
    const overlay = document.getElementById("loadingOverlay");
    overlay.style.display = "flex";
    try {
        // Generamos la sugerencia
        const response = await fetch("/generar_sugerencia", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({comment})
        });
        const data = await response.json();
        let sugerencia = data.sugerencia || "Sugerencia automática";

        // Limpieza
        sugerencia = sugerencia.trim().replace(/^"""/, "").replace(/"""$/, "").replace(/^```/, "").replace(/```$/, "").replace(/^\s+|\s+$/g, "").replace(/\n{2,}/g, "\n").replace(/^\n+|\n+$/g, "");
        suggestedTextArea.value = sugerencia;
    } catch (err) {
        console.error("Error generando sugerencia:",err);
        suggestedTextArea.value = "error generando sugerencia";
    }
    overlay.style.display ="none";
}

function applyParagraphSuggestion(comment){
    if (!comment || !comment.suggestion) return;

    // Obtener párrafo real en el editor
    const start = comment.index;
    const length = comment.texto.length;

    // Reemplazar texto completo del párrafo
    quill.deleteText(start, length);
    quill.insertText(start, comment.suggestion);

    // Eliminar el comentario asociado
    comments = comments.filter(c => c.id!== comment.id);

    // Cerrar popup
    hideSuggestionPopup();

    // Resetear estado para evitar que reaparezca
    currentParagraphComment = null;

    // Bloqueamos los comentarios y mostramos el botón "Recalcular"
    lockComments();

    // Limpiar estado visual
    analyzedParagraphStart = null;
    updateParagraphNumbers();
    updateParagraphFilter();
}

// Para cerrar el popup de la sugerencia
function checkPopupClose(){
    if (!isHoveringNumber && !isHoveringPopup){
        hideSuggestionPopup();
        currentParagraphComment = null;

        document.querySelectorAll("#paragraphNumbers div")
            .forEach(div => div.classList.remove("active-paragraph-numer-suggestion"))
    }
}

function acceptSuggestion(comment){
    if (!comment.suggestion) return;
    //Eliminar el comentario aceptado
    comments = comments.filter(c => c.id !== comment.id);

    // Bloqueamos el panel de comentarios y mostramos el botón "Recalcular"
    lockComments();

    // Hacer que el párrafo aceptado se vea negro
    const paragraphs = quill.root.querySelectorAll("p");
    paragraphs.forEach(p => {
        const blot = Quill.find(p);
        const parStart = quill.getIndex(blot);
        const parEnd = parStart + p.innerText.length;
        if (comment.index >= parStart && comment.index < parEnd) {
            p.classList.add("active-paragraph") // Negro
        }
    });

    // Refrescamos la lista de comentarios
    renderComments();
}

function updateGenerateSuggestionButton() {
    const btn = document.getElementById("generateSuggestionBtn");
    const paragraphFilter = document.getElementById("filterParagraph").value;

    const isFeedBack = appMode === "feedback";
    const isParagraphFiltered = paragraphFilter!=="all";

    const shouldShow = isFeedBack && (hasParagraphAnalysis || (hasFullAnalysis && isParagraphFiltered));
    btn.style.display = shouldShow ? "block" : "none";
}

function getTotalParagraphs() {
    const paragraphs = quill.root.querySelectorAll("p");
    let count = 0;

    paragraphs.forEach(p => {
        const text = p.textContent.replace(/\u200B/g, "").trim();
        if (text.length > 0) count++;
    });

    return count;
}

function getSentenceIdFromIndex(index) {
    const text = quill.getText();
    // Buscar inicio de oración
    let start = index;
    while (start > 0 && !/[.!?]/.test(text[start-1])) {
        start--;
    }
    // Buscar fin de oración
    let end = index;
    while(end < text.length && !/[.!?]/.test(text[end])) {
        end++;
    }

    // Incluir el punto final
    if(end < text.length) end++;
    // ID único de la oración
    return `${start} - ${end}`;
}

async function analyzeSingleParagraph(paragraphText, start) {
    const response = await fetch("/analyse_paragraph", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ parrafo: paragraphText, start })
    });

    const data = await response.json();

    if (Array.isArray(data)) return data;
    if (data.comentarios) return data.comentarios;
    console.error("Formato inesperado:", data);

    return [];
}

function calcularPorcentajesPorParrafo() {
    porcentajesPorTipoParrafo = {};

    Object.keys(conteoErroresPorTipoParrafo).forEach(tipo => {
        porcentajesPorTipoParrafo[tipo] = {};

        Object.entries(conteoErroresPorTipoParrafo[tipo]).forEach(([parrafo, errores]) => {
            const total = totalOracionesPorParrafo[parrafo] || 0;
            const erroresCount = errores.size || 0;

            let porcentaje = 0;
            if (total > 0) {
                porcentaje = ((erroresCount / total) * 100).toFixed(1);
            }

            porcentajesPorTipoParrafo[tipo][parrafo] = porcentaje;
        });
    });
}

function getSentenceIndexInParagraph(paragraphText, localIndex) {
    const sentences = paragraphText.split(/[.!?]+/).filter(s => s.trim().length > 0);

    let currentIndex = 0;

    for (let i = 0; i < sentences.length; i++) {
        const sentence = sentences[i];
        const start = paragraphText.indexOf(sentence, currentIndex);
        const end = start + sentence.length;

        if (localIndex >= start && localIndex <= end) {
            return i; // ← índice de la oración
        }

        currentIndex = end;
    }

    return null;
}

// Para marcar las oraciones
function highlightError(index, length, type) {
    let color = "#fff3a0";
    quill.formatText(index, length, {background: color});
}
function clearHighlights() {
    quill.removeFormat(0, quill.getLength());
}
function highlightByType(type) {
    clearHighlights();
    const paragraphFilter = document.getElementById("filterParagraph").value;
    comments.forEach(c => {
        if (c.name !== type) return;
        if (paragraphFilter!=="all") {
            const selectedParagraph = Number(paragraphFilter);
            if (c.paragraph!== selectedParagraph) return;

        }
    highlightError(c.index, c.length, c.name);
    })
}

// Función para el switch
function setEditMode(enabled) {
    quill.enable(enabled);

    editLabel.textContent = enabled ? "Editar" : "Bloqueado";
    document.getElementById("toolbar").style.opacity = enabled ? "1" : "0.5";
}
function forceLockEditing() {
    editToggle.checked = false;
    setEditMode(false);
}