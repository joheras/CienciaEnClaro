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
let analyzedParagraphNumber = null;
let totalOracionesPorParrafo = {};
let conteoErroresPorTipoParrafo = {};
let porcentajesPorTipoParrafo = {};
let currentParagraphFilter = "all";
let activeCommentId = null;
let enableSentenceHighlight = true;
let lastAnalyzedParagraphs = {};
let modifiedParagraphs = new Map();
let analysisPerformed = false;
let textIntentions = ["enseñar-explicar"];
let insertingTable = false;
const AVAILABLE_INTENTIONS = [
    { value: "informar", label: "Informar" },
    { value: "persuadir", label: "Persuadir" },
    { value: "entretener", label: "Entretener/deleitar" },
    { value: "enseñar-explicar", label: "Enseñar/explicar" },
    { value: "describir", label: "Describir" },
    { value: "aclarar", label: "Aclarar" },
    { value: "fomentar-interes", label: "Fomentar el interés" },
    { value: "concienciar", label: "Concienciar" },
    { value: "aconsejar", label: "Aconsejar" }
];
let lastStructure = null;
let originalContent = "";
let selectedComment = null;

let spellCheckMatches = [];

let spellcheckTimeout = null;

function scheduleSpellcheck() {
    clearTimeout(spellcheckTimeout);

    spellcheckTimeout = setTimeout(() => {
        checkSpelling();
    }, 800);
}

const menu = document.getElementById("customContextMenu");
const generateOption = document.getElementById("generateSuggestionOption");
const BLOCK_SELECTOR = "p, li, h1, h2, h3, h4, h5, h6";
const TABLE_SELECTOR = ".generated-table";

function setOriginalContent() {
    originalContent = quill.getContents();
}
function hasUnsavedChanges() {
    if (quill.getText().trim().length === 0){
        return false;
    }
    return JSON.stringify(quill.getContents()) !== JSON.stringify(originalContent);
}

let lastWidth = window.innerWidth;

window.addEventListener("resize", () => {
    if (window.innerWidth !== lastWidth) {
        lastWidth = window.innerWidth;

        requestAnimationFrame(() => {
            updateParagraphNumbers();
        });
    }
});

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
let activeType = null;

const Size = Quill.import('attributors/style/size');

// Para el subrayado de las sugerencias
const Parchment = Quill.import('parchment');
const AppUnderline = new Parchment.Attributor.Class(
    'appUnderline',
    'app-underline',
    {
        scope: Parchment.Scope.INLINE
    }
);
Quill.register(AppUnderline, true);

const BlockEmbed = Quill.import('blots/block/embed');

class TableBlot extends BlockEmbed {
    static create(value) {
        const node = super.create();

        node.innerHTML = value;
        node.setAttribute("contenteditable", "true");

        return node;
    }

    static value(node) {
        return node.innerHTML;
    }
}

TableBlot.blotName = 'generatedTable';
TableBlot.tagName = 'div';
TableBlot.className = 'generated-table';

Quill.register(TableBlot);

document.addEventListener("keydown", function (event) {

    if (event.key !== "Backspace" && event.key !== "Delete") {
        return;
    }

    const selection = window.getSelection();

    if (!selection || selection.rangeCount === 0) {
        return;
    }

    const range = selection.getRangeAt(0);

    // Comprobar dónde está el cursor
    let node = range.commonAncestorContainer;

    if (node.nodeType === Node.TEXT_NODE) {
        node = node.parentElement;
    }

    const table = node.closest(".generated-table");

    // Si no estamos dentro de una tabla, dejamos que Quill gestione el evento
    if (!table) {
        return;
    }

    // Estamos dentro de una tabla:
    // impedir que Quill elimine el BlockEmbed
    event.preventDefault();
    event.stopImmediatePropagation();

    // Hacer que el navegador borre el contenido seleccionado
    document.execCommand(
        "delete",
        false,
        null
    );

}, true);

Size.whitelist = [
  '10px',
  '12px',
  '14px',
  '16px',
  '18px',
  '20px',
  '24px',
  '28px',
  '32px'
];

Quill.register(Size, true);
Quill.register('modules/imageResize', ImageResize.default);

quill = new Quill('#editor', {
    theme: 'snow',
    modules: {
        imageResize: {
            modules: ['Resize', 'DisplaySize']
        },
        toolbar: {
            container: "#toolbar",
            history: {
                delay: 1000,
                maxStack: 500,
                userOnly: true
            },
            handlers: {
                //addComment: addCom,
                //analyze: analyzeText,
                paragraph: addCommentParagraph,
                comment10: addCommentText,
                undo: function () {
                    this.quill.history.undo();
                },
                redo: function() {
                    this.quill.history.redo();
                }
            }
        }
    }
});

const picker = document.querySelector('.ql-size');
picker.value = '12px';
picker.dispatchEvent(new Event('change'));

const editor = document.querySelector('.ql-editor');
const numbers = document.getElementById('paragraphNumbers');

document.querySelector(".ql-size").value = "12px";

editor.addEventListener('scroll', () => {
  numbers.scrollTop = editor.scrollTop;
});

window.addEventListener('beforeunload', function(e){
    if (hasUnsavedChanges()){
        e.preventDefault();
        e.returnValue = ''
    }
});

//Al hacer click en una palabra resaltada se abre el popup de sugerencias
quill.root.addEventListener("contextmenu", handleContextMenu);

quill.root.addEventListener("scroll", () => {
    if (spellcheckMatches) {
        renderSpellcheck(spellcheckMatches);
    }
});

quill.root.addEventListener("input", function(event) {

    const table = event.target.closest(".generated-table");

    if (!table) {
        return;
    }

    // El usuario ha modificado el contenido de una tabla
    lastStructure = null;

    console.log("Tabla modificada: será necesario volver a analizar.");

});


const resizer = document.getElementById('panelResizer');
const container = document.querySelector('.container');

let resizing = false;
resizer.addEventListener('mousedown', () => {
  resizing = true;
  document.body.style.cursor = 'col-resize';
});

document.addEventListener('mousemove', (e) => {
  if (!resizing) return;

  const rect = container.getBoundingClientRect();

  // ancho del panel derecho
  let width = rect.right - e.clientX;

  // límites
  width = Math.max(250, Math.min(width, 700));

  container.style.setProperty('--left-panel-width', `${width}px`);
});

document.addEventListener('mouseup', () => {
  resizing = false;
  document.body.style.cursor = '';
});

document.getElementById("newDocumentBtn").addEventListener("click", () => {
    if (hasUnsavedChanges()) {

        if (!confirm("Se eliminará todo el contenido. ¿Deseas continuar?")) {
            return;
        }
    }
    analysisPerformed = false;

    resetEditor();
    setOriginalContent();
});

document.getElementById("toggleHighlight").addEventListener("change", (e) => {
    enableSentenceHighlight = e.target.checked;

    // Si lo desactiva, limpia los resaltados
    if(!enableSentenceHighlight) {
        clearHighlights();
    } else {
        if (activeType) {
            highlightByType(activeType);
        }
    }
})

function resetEditor() {
    // Vaciar el editor
    quill.setContents([]);

    clearSpellcheck();

    // Limpiar comentarios
    comments = [];

    lastAnalyzedParagraphs = {};
    modifiedParagraphs.clear();
    lastStructure = null;

    analysisPerformed = false;
    hasPendingChanges = false;
    hasFullAnalysis = false;
    hasParagraphAnalysis = false;
    analyzingParagraph = false;
    analyzedParagraphStart = null;
    analyzedParagraphNumber = null;

    activeCommentId = null;
    activeType = null;

    // Limpiar numeración de párrafos
    paragraphNumbers = [];

    // Actualizar la interfaz
    updateParagraphFilter();
    renderComments();
    updateParagraphNumbers();
    highlightParagraphFromFilter();

    // Restablecer otros estados si los tienes
    contenidoModificado = false;
}
//const editToggle = document.getElementById("editToggle");
//const editLabel = document.getElementById("editLabel");
//setEditMode(true);
//editToggle.addEventListener("change", () => {
//    setEditMode(editToggle.checked);
//})

// para que la aplicación empiece en el modo escribir
quill.enable(true);
//document.getElementById("filterContainer").style.display="none";
//document.getElementById("filterText").style.display="none";
document.getElementById("analysisContainer").style.display="none";
document.getElementById("analyzeBtn").style.display = "none";
//document.getElementById("paragraphBtn").style.display = "none";
//document.getElementById("addCommentFirst10Btn").style.display = "none";
document.getElementById("recalculateBtn").style.display = "none";
document.getElementById("generateSuggestionBtn").style.display="none";
document.querySelector(".highlight-switch-block").style.display = "none";
document.getElementById("filterParagraph").addEventListener("change", () => {
    clearHighlights();
    renderComments();
    highlightParagraphFromFilter();

    if (activeType) {
        highlightByType(activeType);
    }
    updateGenerateSuggestionButton();
})
document.getElementById("commentsList").style.display="none";

function detectAndFormatTitles() {
    const blocks = quill.root.querySelectorAll("p");

    blocks.forEach((block) => {
        const text = block.textContent.trim();

        if (!text) return;

        // No debe terminar en un signo de puntuación de cierre
        const terminaEnPuntuacion = /[.!?:;!?]$/.test(text);

        // Comprobar que el bloque está en negrita
        const contenido = block.querySelectorAll("*");

        let totalLength = text.length;
        let boldLength = 0;

        if (contenido.length === 0) {
            if (block.style.fontWeight === "bold") {
                boldLength = totalLength;
            }
        } else {
            contenido.forEach((elemento) => {
                if (elemento.textContent.trim()) {
                    const estilo = window.getComputedStyle(elemento);
                    if (
                        estilo.fontWeight === "bold" ||
                        parseInt(estilo.fontWeight) >= 700
                    ) {
                        boldLength += elemento.textContent.trim().length;
                    }
                }
            });
        }

        const estaEnNegrita = boldLength >= totalLength * 0.8;

        // Criterios para considerar que es un título
        if (
            !terminaEnPuntuacion &&
            estaEnNegrita
        ) {
            const index = quill.getIndex(Quill.find(block));

            quill.formatLine(index, 1, "header", 1);
        }
    });
}

document.getElementById("exampleTextBtn").addEventListener("click", async() => {
    try {
        resetEditor();
        setOriginalContent();
        const response = await fetch("/static/ejemplo.docx");
        if (!response.ok) throw new Error("No se pudo cargar el archivo");

        const arrayBuffer = await response.arrayBuffer();

        const result = await mammoth.convertToHtml({
            arrayBuffer: arrayBuffer
        });

        quill.setContents([]);
        quill.clipboard.dangerouslyPasteHTML(result.value);
        //const text = await response.text(); //Esto sirve si el texto que estoy cargando es un txt

        //quill.setText(text);

        setTimeout(() => {
            detectAndFormatTitles();
            quill.formatText(0, quill.getLength(), {color: "#000000"});
            updateParagraphNumbers();
            updateParagraphFilter();
            showIntentionalityModal();
            setOriginalContent();
        }, 0);

    } catch (error) {
        console.error(error);
        alert("Error cargando el texto de ejemplo");
    }
});

document.getElementById("intentionalityConfigBtn").addEventListener("click", () => {
        showIntentionalityModal();
    });

let editorWasEmpty = false;
quill.root.addEventListener("paste", () => {
    clearSpellcheck();
    editorWasEmpty = quill.getText().trim().length===0;
    setTimeout(() => {

        detectAndFormatTitles();

        const text = quill.getText().trim();

        if (editorWasEmpty && text.length > 0) {
            showIntentionalityModal();
        }

    }, 100);
});

document.getElementById("loadFileBtn").addEventListener("click", () => {
    clearSpellcheck();
    document.getElementById("fileInput").click();
});

document.getElementById("fileInput").addEventListener("change", async (e) => {
    clearSpellcheck();
    const file = e.target.files[0];
    if (!file) return;

    const name = file.name.toLowerCase();

    try {
        // 📄 TXT
        if (name.endsWith(".txt")) {
            const text = await file.text();
            quill.setText(text);
        }

        // 📄 DOCX
        else if (name.endsWith(".docx")) {
            const arrayBuffer = await file.arrayBuffer();

            const result = await mammoth.convertToHtml({ arrayBuffer });

            const html = result.value;

            quill.clipboard.dangerouslyPasteHTML(html);

            setTimeout(() => {
                detectAndFormatTitles();
            }, 0);

        }

        else {
            alert("Formato no soportado");
            return;
        }

        comments = [];
        hasPendingChanges = false;
        commentsLocked = false;
        updateParagraphNumbers();
        document.getElementById("filterParagraph").value = "all";
        updateParagraphFilter();
        const paragraphFilter = document.getElementById("filterParagraph");
        paragraphFilter.value = "all";
        paragraphFilter.dispatchEvent(new Event("change"));
        updateFilterOptions();
        renderComments();
        showIntentionalityModal();
        setOriginalContent();
    } catch(err) {
        console.error(err);
        alert("Error al cargar el archivo");
    }
});

document.getElementById("downloadBtn").addEventListener("click", async () => {
    clearHighlights();
    const html = quill.root.innerHTML;
    //const { Document, Packer, Paragraph, TextRun } = window.docx;
    const content = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
            body {
                font-family: Calibri, Arial, sans-serif;
                font-size: 12pt;
                line-height: 1.5;
            }
            </style>
        </head>
        <body>
            ${html}
        </body>
        </html>
    `;
    // Convertir a DOCX
    const converted = window.htmlDocx.asBlob(content);

    // Descargar
    saveAs(converted, "texto.docx");
/*
    const delta = quill.getContents();

    const doc = new Document({
        sections: [{
            children: delta.ops.map(op => {
                if (typeof op.insert !== "string") return null;

                return new Paragraph({
                    children: [
                        new TextRun({
                            text: op.insert,
                            bold: op.attributes?.bold || false,
                            italics: op.attributes?.italic || false,
                            underline: op.attributes?.underline || false,
                            strike: op.attributes?.strike || false,
                        })
                    ]
                });
            }).filter(Boolean)
        }]

    });
       const blob = await Packer.toBlob(doc);
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "texto.docx";
    a.click();

    URL.revokeObjectURL(url);
 */
});


document.getElementById("downloadPdfBtn").addEventListener("click", () => {
    clearHighlights();

    const editor = quill.root.cloneNode(true);
    editor.querySelectorAll("ol li").forEach(li => {
        li.style.display = "block";
        li.style.listStyle = "none";
    });
    editor.querySelectorAll("ol").forEach(ol => {

    const ul = document.createElement("ul");

    Array.from(ol.children).forEach((li, index) => {

        const newLi = li.cloneNode(true);

        // Eliminar el pseudoelemento de Quill
        newLi.removeAttribute("data-list");

        // Añadir el número como texto
        newLi.innerHTML = `<strong>${index + 1}.</strong> ${newLi.innerHTML}`;

        ul.appendChild(newLi);
    });

    ol.replaceWith(ul);
});
    const style = document.createElement("style");
    style.textContent = `
    .ql-editor ol > li::before,
    .ql-editor ul > li::before{
        content: none !important;
    }
    
    .ql-editor ol,
    .ql-editor ul{
        padding-left: 24px !important;
    }
    `;

    editor.prepend(style);


    editor.style.fontSize = "12pt";
    editor.style.fontFamily = "Arial";
    editor.style.padding = "0";
    editor.style.margin = "0";
    editor.style.paddingBottom = "20px";

    html2pdf()
        .set({
            margin: [40, 40, 60, 40],
            filename: "texto.pdf",
            image: { type: "jpeg", quality: 1 },
            html2canvas: {
                scale: 2,
                useCORS: true,
                letterRendering: true
            },
            jsPDF: {
                unit: "pt",
                format: "a4",
                orientation: "portrait"
            },
            pagebreak: {
                mode: ["css", "legacy", "avoid-all"]
            }
        })
        .from(editor)
        .save();
});


// Para que al hacer click en un párrafo se actualice el filtro automáticamente
document.querySelector(".ql-editor").addEventListener("click", (e) => {
    let p = e.target.closest(BLOCK_SELECTOR);

    if (!p) return;

    // Obtener índice del párrafo
    const paragraphs = quill.root.querySelectorAll(BLOCK_SELECTOR);
    let visibleIndex = 1;
    let targetIndex = null;

    paragraphs.forEach(paragraph => {
        const text = paragraph.textContent.replace(/\u200B/g, "").trim();
        if (text.length > 0) {
            if (paragraph === p) {
                targetIndex = visibleIndex;
            }
            visibleIndex++;
        }
    });
    if (targetIndex === null) return;

    const select = document.getElementById("filterParagraph");

    // Evitar asignar si ya está seleccionado
    if(select.value === String(targetIndex)) return;

    select.value = String(targetIndex);

    select.dispatchEvent(new Event("change"));
});

quill.on("selection-change", (range) => {
    if (!range) return;
    let index = range.index;
    const text = quill.getText();
    // Para que me marque bien si justo pongo el cursor después del punto final del párrafo
    if (text[index] === "\n" && index > 0) {
        index -= 1;
    }
    const paragraphNumber = getParagraphNumberFromIndex(index);
    if (!paragraphNumber) return;

    const select = document.getElementById("filterParagraph");

    if (select.value !== String(paragraphNumber)) {
        select.value = String(paragraphNumber);
        select.dispatchEvent(new Event("change"));
    }
})

quill.format("font", false);
quill.format("size", "12px");
quill.format("align", false); // izquierda

quill.on("selection-change", highlightActiveParagraph);

quill.root.querySelectorAll(BLOCK_SELECTOR).forEach(p =>
    p.classList.add("active-paragraph"));

quill.on("text-change", (delta, oldDelta, source) => {
    if (source!== "user") return;

    clearSpellcheck();

    if(insertingTable){
        return;
    }

    const textoActual = quill.getText().trim();

    scheduleSpellcheck();

    if (!textoActual){
        comments = [];
        lastAnalyzedParagraphs = {};
        modifiedParagraphs.clear();
        lastStructure = null;
        analysisPerformed = false;
        hasPendingChanges = false;

        updateParagraphNumbers();
        updateAnalyzeButton();
        renderComments();

        return;
    }

    const changed = getChangedParagraphs();

    const structureChanged =
        JSON.stringify(getDocumentStructureSignature()) !==
        JSON.stringify(lastStructure);

    if (!changed.length && !structureChanged) {
        // Solo se ha modificado algo que no afecta al análisis, como una tabla
        hasPendingChanges = false;
        updateAnalyzeButton();
        renderComments();
        return;
    }

    hasPendingChanges = true;
    lockComments();

    changed.forEach(par => {
        modifiedParagraphs.set(par.index, true);
    });
    updateParagraphNumbers();
    updateAnalyzeButton();
    renderComments();

});

//document.getElementById("addCommentBtn").onclick = addCom;
//document.getElementById("analyzeBtn").addEventListener("click", analyzeText);

//document.getElementById("paragraphBtn").onclick = () => {
 //   if (quill.isEnabled()){
//        return;
//    } else {
//        addCommentParagraph();
//    }
//}

async function reanalyzeModifiedParagraphs() {
    unlockComments();
    const structureChanged = JSON.stringify(getDocumentStructureSignature())!== JSON.stringify(lastStructure);

    const changed = getChangedParagraphs();
    if (!changed.length && !structureChanged){
        console.log("No hay cambios que recalcular");
        return;
    }
    const overlay = document.getElementById("analysisOverlay");
    overlay.style.display = "flex";

    const total = changed.length;
    let current = 0;
    resetProgress();
    updateProgress(current, total, "paragraph");

    comments = comments.filter(c => !c.global);

    const textoCompleto = quill.getText();

    const paragraphs = Array.from(quill.root.querySelectorAll(BLOCK_SELECTOR))
        .filter(x =>
        x.textContent.replace(/\u200B/g, "").trim().length > 0);

    for (const par of changed) {
        const p = paragraphs[par.index - 1];
        if (!p) continue;
        const start = quill.getIndex(Quill.find(p));

        const data = await analyzeSingleParagraph(par.text, start);
        comments = comments.filter(c => c.paragraph !== par.index);
        data.forEach(item => {
            comments.push(buildComment(item, par.text, par.index, start));
        });
        lastAnalyzedParagraphs[par.index] = {
            text: par.text,
            tag: p.tagName
        };
        modifiedParagraphs.delete(par.index);
        current++;
        if (current<changed.length){
            updateProgress(current, total, "paragraph");
        }
    }
/*
    const tables = Array.from(
    quill.root.querySelectorAll(".generated-table")
    );

    for (let tableIndex = 0; tableIndex < tables.length; tableIndex++) {

        const tableComments = await analyzeGeneratedTable(
            tables[tableIndex],
            tableIndex
        );

        comments.push(...tableComments);
    }

 */
    let globalComments = [];

    const globalResponse = await fetch("/analyse_document", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            texto: textoCompleto,
            intencionalidad: textIntentions
        })
    });
    const globalData = await globalResponse.json();


    updateProgress(total, total, "global");

    globalComments = (globalData.comentarios_globales || []).flatMap(c => c.global || [])
        .map(c=> ({
        ...c,
        global: true,
        paragraphStart: -1,
        index: -1,
        localIndex: -1,
        paragraph: -1
    }));

    comments.push(...globalComments);
    hasPendingChanges = modifiedParagraphs.size>0;
    if (hasPendingChanges && analysisPerformed) {
        lockComments();
    } else {
        unlockComments();
    }

    activeCommentId = null;
    activeType = null;
    analyzedParagraphStart = null;

    resetAnalysisFilters
    renderComments();
    updateParagraphFilter();
    updateParagraphNumbers();
    updateAnalyzeButton();
    overlay.style.display = "none";
    analysisPerformed = true;
    lastStructure = getDocumentStructureSignature();
}
document.getElementById("recalculateBtn").onclick = reanalyzeModifiedParagraphs;
/*
document.getElementById("addCommentFirst10Btn").onclick = () => {
    if (quill.isEnabled()){
        return;
    } else {
        addCommentText();
    }
};

 */

function getDocumentStructureSignature() {

    const elements = Array.from(
        quill.root.querySelectorAll(
            //`${BLOCK_SELECTOR}, .generated-table`
            BLOCK_SELECTOR
        )
    );

    return elements
        .filter(n =>
             n.textContent
                .replace(/\u200B/g, "")
                .trim()
        )
        .map(n => {
/*
            // Tabla generada
            if (n.classList.contains("generated-table")) {

                const table = n.querySelector("table");

                if (!table) {
                    return {
                        tag: "TABLE",
                        text: ""
                    };
                }

                const partes = [];

                // Caption
                const caption = table.querySelector("caption");

                if (caption) {
                    partes.push(
                        caption.textContent
                            .replace(/\u200B/g, "")
                            .trim()
                    );
                }

                // Filas
                table.querySelectorAll("tr").forEach(row => {

                    const celdas = Array.from(
                        row.querySelectorAll("th, td")
                    )
                    .map(cell =>
                        cell.textContent
                            .replace(/\u200B/g, "")
                            .trim()
                    )
                    .filter(Boolean);

                    if (celdas.length > 0) {
                        partes.push(celdas.join(" "));
                    }
                });

                return {
                    tag: "TABLE",
                    text: partes.join("\n")
                };
            }

 */

            // Párrafos, títulos, etc.
            return {
                tag: n.tagName,
                text: n.textContent
                    .replace(/\u200B/g, "")
                    .trim()
            };
        });
}

document.getElementById("filterType").addEventListener("change", () => {
    renderComments();
})

updateParagraphNumbers();
updateParagraphFilter();
updateFilterOptions();

//const writeBtn = document.getElementById("writeModeBtn");
const feedBackBtn = document.getElementById("feedbackModeBtn");
//const analysisBtn = document.getElementById("analysisModeBtn");
//writeBtn.onclick = () => setMode("write");
document.getElementById("feedbackModeBtn").addEventListener("click", async() => {
    if (hasPendingChanges && analysisPerformed) {
        await reanalyzeModifiedParagraphs();
    } else {
        await addCommentText();
    }
});
/*
analysisBtn.onclick = () => {
    setMode("analysis");
    //forceLockEditing();
    analyzeText();
}

 */

// Referencias a la sugerencia
const modal = document.getElementById("suggestionModal");
const generateBtn = document.getElementById("generateSuggestionBtn");
const closeModalBtn = document.getElementById("closeModalBtn");
const newSuggestionBtn = document.getElementById('newSuggestionBtn');
const useSuggestionBtn = document.getElementById('useSuggestionBtn');

const originalTextArea = document.getElementById('originalText');
const suggestedTextArea = document.getElementById('suggestedText');
const highlightSwitch = document.getElementById("toggleHighlight");

/*
De cuando lo hacíamos con el párrafo
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

 */
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
    const start = getUpdatedSentenceIndex(currentModalComment);
    const originalSentence = currentModalComment.oracion;
    const newSentence = currentModalComment.suggestion;

    const Delta = Quill.import("delta");
    quill.updateContents(
        new Delta()
            .retain(start)
            .delete(originalSentence.length)
            .insert(newSentence)
    );
    modifiedParagraphs.set(currentModalComment.paragraph, true);
    suggestionModal.style.display = "none";
    currentModalComment = null;
    updateParagraphNumbers();
    updateParagraphFilter();
    hasPendingChanges=true;
    updateAnalyzeButton();
    updateParagraphNumbers();
    lockComments();
    /*
    // Cuando era del párrafo completo
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

     */
});


function updateAnalyzeButton() {
    const btn = document.getElementById("feedbackModeBtn");

    if (analysisPerformed && hasPendingChanges) {
        btn.textContent = "Reanalizar";
        btn.classList.add("reanalyze-btn");
    } else {
        btn.textContent = "Analizar";
        btn.classList.remove("reanalyze-btn");
    }
}

function setMode(mode) {
    appMode = mode;

    //const isWrite = mode === "write";
    const isFeedback = mode === "feedback";
    const isAnalysis = mode === "analysis";

    //writeBtn.classList.toggle("active", isWrite);
    feedBackBtn.classList.toggle("active", isFeedback);
    //analysisBtn.classList.toggle("active", isAnalysis);

    /*if (isWrite) {
        editToggle.disabled = false;
        setEditMode(editToggle.checked);
    } else {
        editToggle.checked = false;
        editToggle.disabled = true;
        setEditMode(false);
    }

     */

    const showFilter = mode !== "analysis";

    document.getElementById("commentsList").style.display = isFeedback ? "block" : "none";
    document.getElementById("filterContainer").style.display = showFilter ? "block" : "none";
    document.getElementById("filterText").style.display = isFeedback ? "block" : "none";
    //document.getElementById("paragraphBtn").style.display = isFeedback ? "block" : "none";
    //document.getElementById("addCommentFirst10Btn").style.display = isFeedback ? "block" : "none";
    document.getElementById("analysisContainer").style.display = isAnalysis ? "block" : "none";
    document.getElementById("analyzeBtn").style.display = isAnalysis ? "block" : "none";
    document.getElementById("filterType").addEventListener("change", () => {
        updateParagraphFilterState();
    });
    document.querySelector(".highlight-switch-block").style.display = showFilter ? "inline-flex" : "none";

    //if (isFeedback && hasPendingChanges){
    //    document.getElementById("recalculateBtn").style.display="block";
    //} else {
    //    document.getElementById("recalculateBtn").style.display="none";
    //}
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
    const types = [...new Set(comments.map(c => c.type).filter(t=>t))]; // Tipos únicos

    const previousValue = select.value;

    select.innerHTML = "";

    const baseOptions = [
        {value: "todos", label: "Todos"},
        {value:"morfosintaxis", label:"Morfosintáctico"},
        {value: "léxico-semántico", label:"Léxico-semántico"},
        {value: "pragmático-discursivo", label:"Pragmático-discursivo"},
        {value: "legibility", label: "Accesibilidad"},
        {value: "estadistica", label:"Estadísticas"}
    ];

    baseOptions.forEach(opt => {
        const option = document.createElement("option");
        option.value = opt.value;
        option.textContent = opt.label;
        select.appendChild(option);
    });

    // Añadimos la opción "Todos"
    //const allOption = document.createElement("option");
    //allOption.value = "todos";
    //allOption.textContent ="Todos";
    //select.appendChild(allOption);

    // Añadir opciones únicas
    types.forEach(type => {

        // Evitar duplicados con los que he añadido al principio
        if(baseOptions.some(opt => opt.value === type)) return;

        const option = document.createElement("option");
        option.value = type;

        if (type == "index"){
            option.textContent = "Por índice";
        } else if (type == "paragraph"){
            option.textContent = "Por párrafo";
        } else {
            const cleanLabel = (type || "desconocido").replace(/-/g, " ");
            option.textContent = cleanLabel.charAt(0).toUpperCase() + cleanLabel.slice(1);
        }
        select.appendChild(option);
    });

    //Predeterminado: "Todos"
    if ([...select.options].some(opt => opt.value === previousValue)) {
        select.value = previousValue;
    } else {
        select.value = "todos";
    }
    updateParagraphFilterState();
}

function updateParagraphFilter() {
    const select = document.getElementById("filterParagraph");

    // Guardo el valor actual del filtro
    const previousValue = select.value;

    const paragraph = getVisibleParagraphs();

    select.innerHTML = "";

    // Opción texto completo
    const allOption = document.createElement("option");
    allOption.value = "all";
    allOption.textContent = "Todos";
    select.appendChild(allOption);

    // Párrafos
    let count = 1;

    paragraph.forEach(({node, text}, index) => {
        const cleanText = text.replace(/\u200B/g, "").trim();
        if (cleanText.length > 0) {
            const type = getNodeType(node);
            const option = document.createElement("option");
            option.value = count;
            option.textContent = `${count}º (${type})`;
            select.appendChild(option);
            count++;
        }
    });

    // Tablas
    const tables = Array.from(
        quill.root.querySelectorAll(".generated-table")
    );

    tables.forEach((table, tableIndex) => {
        const tableValue = -(tableIndex + 2); // la primera tabla empieza en -2

        const option = document.createElement("option");
        option.value = tableValue;
        option.textContent = `Tabla ${tableIndex + 1}`;

        select.appendChild(option);
    });

    // Si había un filtro previo, lo restauramos. Si no ponemos el texto completo
    if([...select.options].some(opt => String(opt.value) === String(previousValue))) {
        select.value = String(previousValue);
    } else {
        select.value = "all";
    }
    updateParagraphLabel();
}
function updateParagraphFilterState() {
    const filterType = document.getElementById("filterType");
    const filterParagraph = document.getElementById("filterParagraph");

    if (filterType.value === "legibility") {
        filterParagraph.value = "all";
        filterParagraph.disabled = true;

        filterParagraph.dispatchEvent(new Event("change"));
    } else {
        filterParagraph.disabled = false;
    }

    updateParagraphLabel();
}

function resetAnalysisFilters() {
    document.getElementById("filterParagraph").value = "all";
    document.getElementById("filterType").value = "Todos";

    updateParagraphFilter();
    updateFilterOptions();
    highlightParagraphFromFilter();
}

// Para saber el texto de qué tipo es
function getNodeType(node) {
    switch (node.tagName.toUpperCase()) {
        case "P":
            return "Párrafo";
        case "LI":
            return "Lista";
        case "H1":
        case "H2":
        case "H3":
        case "H4":
        case "H5":
        case "H6":
            return "Título";
        default:
            return "";
    }
}

function updateParagraphLabel() {
    const select = document.getElementById("filterParagraph");
    const label = document.getElementById("filterParagraphLabel");
    label.textContent = select.value === "all" ? "Párrafos" : "Párrafo";
}

const select = document.getElementById("filterParagraph");
const label = document.getElementById("filterParagraphLabel");

select.addEventListener("change", () => {
    updateParagraphLabel
});

function renderComments(){
    //if (appMode === "write") return;

    const filter = document.getElementById("filterType").value;
    const paragraphFilter = document.getElementById("filterParagraph").value;
    const panel = document.getElementById("commentsList");

    panel.innerHTML = "";

    const commentClasses = {
      "morfosintaxis": "comment-morfosintaxis",
      "léxico-semántico": "comment-lexico",
      "pragmático-discursivo": "comment-pragmatico",
      "accesibilidad": "comment-accesibilidad",
      "estadísticas": "comment-estadisticas"
    };

    // Para filtrar
    let filtered = comments.filter(c => c.text !== "¿Quieres una sugerencia?");
    filtered = filtered.filter(c=> {
        if (c.name!=="parrafoCorto"){
            return true;
        }
        const info = lastAnalyzedParagraphs[c.paragraph];
        if (!info) return true;
        return !/^H[1-6]$/.test(info.tag);
    });

    const existsType = filtered.some(c => c.name === activeType);
    if (!existsType){
        activeType = null;
        activeCommentId = null;
        clearHighlights();
    }

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
        filtered = filtered.filter( c=> c.type!=="estadistica" || c.global)
        // Si está seleccionado "Texto completo" quitar todos los resaltados
        highlightParagraphFromFilter(null);
    }

    if (filtered.length === 0) {
        if (analysisPerformed) {
            panel.style.display = "block";
            panel.innerHTML = `
            <div class="no-comments">
                No se han detectado comentarios.
            </div>
        `;
        } else {

        }
        panel.style.display = "block";
            panel.innerHTML = `
            <div class="no-comments">
                Analiza el documento para obtener comentarios.
            </div>
        `;
        return;
    } else {
        panel.style.display = "block";
    }

    const activeComment = comments.find(c => c.id === activeCommentId);


    // Para que salgan al principio los globales
    filtered.sort((a, b) => {
        const prioridad = c => {
            if (c.global && c.type === "estadistica") return 0;
            if (c.global) return 1;
            return 2;
        };
        return prioridad(a)-prioridad(b);
    });
    // Agrupar comentarios
    const grouped = filtered.reduce((acc, comment) => {

        const key = comment.type === "estadistica"
            ? comment.text
            : (comment.name || comment.text);
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

        if(commentClasses[first.type]) {
            div.classList.add(commentClasses[first.type]);
        }

        if (commentsLocked) {
            div.classList.add("comment-disabled");
        }

        // Cabecera (texto + etiqueta tipo)
        const title = document.createElement("div");
        title.className = "comment-title";
        div.style.cursor = "pointer";


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

        paragraphText = `Se han detectado `;
        const descriptionMap = {
            parrafoCorto: `los siguientes párrafos cortos. Cada párrafo debería tener mínimo dos oraciones.`,
            parrafoLargo: `los siguientes párrafos largos. Cada párrafo debería tener máximo cinco oraciones.`,
            oracionLarga: `las siguientes oraciones largas. Cada oración debería tener máximo 20 palabras.`,
            orden: `las siguientes oraciones que no siguen el orden sintáctico sujeto-verbo-complementos.`,
            coordinada: `las siguientes oraciones coordinadas.`,
            yuxtapuesta: `las siguientes oraciones yuxtapuestas.`,
            extranjerismo: " los siguientes extranjerismos."
        };
        desc.innerText = "Descripción: " + paragraphText + descriptionMap[first.name];

         */

        const descriptionMap = {
            parrafoCorto: `
                <span class="highlight">Parece que el párrafo contiene una única oración, considere construir un párrafo que incluya al menos dos oraciones relacionadas entre sí.</span><br><br>
                Los párrafos con una sola oración presentan información fragmentada y dificultan la construcción de relaciones entre las ideas.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>La temperatura media global ha aumentado durante las últimas décadas.</em><br><br>
        
                <u>Después:</u><br>
                <em>La temperatura media global ha aumentado durante las últimas décadas. Este incremento se relaciona principalmente con las emisiones de gases de efecto invernadero.</em>`,
            parrafoLargo: `
                <span class="highlight"> Parece que el párrafo es muy largo, considere dividir la información en varios párrafos más breves, procurando que cada párrafo desarrolle una única idea principal.</span><br><br>
                Los párrafos largos aumentan el esfuerzo de lectura, dificultan la localización de las ideas principales y favorecen la pérdida de información relevante.<br><br>`,
            oracionLarga: `
                <span class="highlight">Parece que la oración es muy larga, considere dividir la oración en varias oraciones más breves.</span><br><br>
                Las oraciones extensas (que superan las 25 palabras) incrementan la carga cognitiva y dificultan la identificación de las relaciones sintácticas.<br><br>
                Para saber la longitud de una oración pon el ratón sobre ella.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em> Los investigadores analizaron los datos obtenidos en diferentes estaciones meteorológicas distribuidas por diversas regiones durante varias décadas con el fin de identificar tendencias relacionadas con la temperatura y las precipitaciones.</em><br><br>
                <u>Después:</u><br>
                <em>Los investigadores analizaron datos de diversas estaciones meteorológicas. El estudio incluyó varias regiones y varias décadas. El objetivo fue identificar tendencias relacionadas con la temperatura y las precipitaciones.</em>`,
            inciso: `
            <span class="highlight">Parece que la oración contiene incisos o aclaraciones, considere eliminar los incisos innecesarios o convertirlos en oraciones independientes.</span><br><br>
                Los incisos o aclaraciones interrumpen la lectura y dificultan la identificación de la estructura principal de la oración.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em> El informe, <span class="highlight">elaborado por un grupo internacional de expertos</span>, algunos de ellos especializados en climatología marina, fue publicado recientemente.</em><br><br>
                <u>Después:</u><br>
                <em>Un grupo internacional de expertos elaboró el informe. Algunos especialistas trabajaban en climatología marina. El informe se publicó recientemente.</em>`,
            modificador:  `
            <span class="highlight">Parece que la oración contiene un uso de complementos entre sujeto y verbo, considere reorganizar la oración para situar el complemento (o modificador/adyacente) al final de la oración y evitar que aparezca entre sujeto y verbo.</span><br><br>
                La separación del sujeto y el verbo con modificadores, adyacentes o complementos dificulta la identificación de losnúcleos de la oración.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em> Los científicos, <span class="highlight">tras analizar miles de registros</span>, concluyeron que la temperatura había aumentado.</em><br><br>
                <u>Después:</u><br>
                <em>Los científicos concluyeron que la temperatura había aumentado tras analizar miles de registros.</em>`,

            orden: `
                <span class="highlight">Parece que la oración sigue un orden sintáctico poco natural en español, considere priorizar el orden sujeto + verbo + complementos.</span><br><br>
                Las oraciones que siguen el orden natural del español (sujeto+verbo+complementos) requieren un menor esfuerzo de interpretación.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em> Aumentó considerablemente la temperatura media global durante el último siglo.</em><br><br>
                <u>Después:</u><br>
                <em>La temperatura media global aumentó considerablemente durante el último siglo.</em>`,
            coordinada: `
                <span class="highlight">Parece que hay un exceso de coordinaciones en la oración, considere dividir la información en varias oraciones para evitar el exceso de coordinaciones.</span><br><br>
                Las oraciones que acumulan varios elementos unidos con conjunciones generan sensación de información poco jerarquizada y menos comprensible.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em> El estudio analizó temperaturas <span class="highlight">y</span> precipitaciones <span class="highlight">y</span> vientos <span class="highlight">y</span> humedad <span class="highlight">y</span> cobertura vegetal.</em><br><br>
                <u>Después:</u><br>
                <em>El estudio analizó las temperaturas y las precipitaciones. También examinó los vientos, la humedad y la cobertura vegetal.</em>`,
            yuxtapuesta: `
                <span class="highlight">Parece que hay un exceso de yuxtaposiciones en la oración, considere dividir la información en varias oraciones para evitar el exceso de yuxtaposiciones.</span><br><br>
                Las oraciones que acumulan varios elementos unidos con signos de puntuación (comas y/o puntos y coma) generan sensación de información poco jerarquizada y menos comprensible.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em> El estudio analizó temperaturas<span class="highlight">,</span> precipitaciones<span class="highlight">,</span> vientos<span class="highlight">,</span> humedad<span class="highlight">,</span> cobertura vegetal<span class="highlight">,</span> heladas<span class="highlight">,</span> granizo<span class="highlight">,</span> otros fenómenos adversos.</em><br><br>
                <u>Después:</u><br>
                <em>El estudio analizó las temperaturas y las precipitaciones. También examinó los vientos, la humedad y la cobertura vegetal. Por último, se centró en estudiar las heladas, el granizo, así como otros fenómenos adversos.</em>`,
            relativo: `
                <span class="highlight">Parece que la oración de relativo es compleja, considere simplificar la estructura de la oración o acercar el antecedente (o elemento al que se refiere el relativo) a la expresión de relativo.</span><br><br>
                Las oraciones con fórmulas de relativo encapsuladas una dentro de otra y/o alejadas de su antecedente o elemento al que se refiere se comprenden peor porque puede producirse una pérdida del referente.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em> Los modelos <span class="highlight">que</span> utilizan los investigadores <span class="highlight">que</span> trabajan en centros especializados permiten realizar proyecciones.</em><br><br>
                <u>Después:</u><br>
                <em>Los investigadores utilizan modelos especializados. Estos modelos permiten realizar proyecciones.</em>`,
            concordancia: `
                <span class="highlight">Parece que hay falta de concordancia en la oración, considere revisar la concordancia (en género, número, persona o tiempo verbal) de todos los elementos de la oración.</span><br><br>
                La concordancia en español afecta al género, número, persona o tiempo verbal. La falta de concordancia genera dudas sobre las relaciones gramaticales.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em> Los datos <span class="highlight">obtenida</span> muestran una tendencia.</em><br><br>
                <u>Después:</u><br>
                <em>Los datos obtenidos muestran una tendencia.</em>`,
            pasiva: `
                <span class="highlight">Parece que se ha usado la voz pasiva, considere transformar la oración a voz activa.</span><br><br>
                La voz pasiva suele resultar más compleja de interpretar que la voz activa.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em> Las mediciones <span class="highlight">fueron realizadas</span> por los investigadores.</em><br><br>
                <u>Después:</u><br>
                <em>Los investigadores realizaron las mediciones.</em>`,
            eliptico: `
                <span class="highlight">Parece que se han encadenado varias oraciones son sujeto explícito, considere explicitar el sujeto en alguna de las oraciones marcadas.</span><br><br>
                El encadenamiento de oraciones sin sujeto explícito en el mismo párrafo puede dificultar la identificación del sujeto que realiza la acción y genera ambigüedad entre los agentes implicados.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em> La degradación de los ecosistemas locales avanza a un ritmo alarmante debido a la acumulación de residuos plásticos. Requiere de acciones urgentes y políticas globales estrictas para mitigar los efectos del cambio climático en las próximas décadas. Se busca, por lo tanto, restaurar el equilibrio natural mediante la implementación masiva de energías renovables y la reforestación de áreas protegidas. Exige también una profunda concienciación ciudadana que transforme los hábitos de consumo diario en acciones verdaderamente sostenibles.</em><br><br>
                <u>Después:</u><br>
                <em><span class="highlight">La degradación de los ecosistemas locales</span> avanza a un ritmo alarmante debido a la acumulación de residuos plásticos. <span class="highlight">Esta crisis ambiental</span> requiere de acciones urgentes y políticas globales estrictas para mitigar los efectos del cambio climático en las próximas décadas. Se busca, por lo tanto, restaurar el equilibrio natural mediante la implementación masiva de energías renovables y la reforestación de áreas protegidas. <span class="highlight">La situación actual</span> exige también una profunda concienciación ciudadana que transforme los hábitos de consumo diario en acciones verdaderamente sostenibles. </em>`,
            nopersonal: `
                <span class="highlight">Parece que se han usado formas verbales no personales en la oración, considere priorizar los verbos conjugados en lugar de los infinitivos, gerundios o participios.</span><br><br>
                El uso de infinitivos, gerundios o participios al principio de la oración aumentan la complejidad del texto. Lo mismo ocurre cuando estas formas no van acompañadas de verbos en forma personal. <br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Para <span class="highlight">realizar</span> la evaluación y <span class="highlight">obtener</span> los resultados...</em><br><br>
                <u>Después:</u><br>
                <em>El equipo evaluó los datos y obtuvo los resultados.</em>`,
            gerundio: `
                <span class="highlight">Parece que se ha usado el gerundio de posterioridad, considere evitarlo, por ejemplo, dividiendo la información en dos oraciones.</span><br><br>
                El uso del gerundio para expresar una acción posterior a la principal no es normativo en español.<br><br>
                Más información: https://www.rae.es/libro-estilo-justicia/las-palabras-y-sus-grupos-problemas-y-actuaciones/gerundio/usos-incorrectos/gerundio-de-posterioridad <br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Se publicó el informe, <span class="highlight">generando</span> un intenso debate.</em><br><br>
                <u>Después:</u><br>
                <em>Se publicó el informe. Esta publicación generó un intenso debate.</em>`,
            conector: `
                <span class="highlight">Parece que hay una ausencia de conectores en el párrafo, considere introducir algún conector al inicio del párrafo o entre oraciones para conectar las ideas.</span><br><br>
                Los conectores o marcadores discursivos ayudan a dar cohesión al texto. <br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Las temperaturas aumentaron. Las precipitaciones disminuyeron.</em><br><br>
                <u>Después:</u><br>
                <em>Las temperaturas aumentaron y, <span class="highlight">además</span>, las precipitaciones disminuyeron.</em>`,
            conectorRepe: `
                <span class="highlight">Parece que hay una repetición de conectores, considere modificar alguno de los conectores repetidos.</span><br><br>
                La variación en el uso de los conectores o marcadores discursivos ayuda a mejorar el texto. Esta variación debe hacerse atendiendo la relación lógica entre las distintas partes de la oración o el párrafo. <br><br>
                <strong>Ejemplo</strong><br><br>
                Sustituir repeticiones de <em>además</em> por otros conectores o marcadores que también indiquen adición como: <em>asimismo</em>, <em>igualmente</em>, <em>por otra parte</em>, <em>además de ello</em>.`,
            conectoresPunt: `
                <span class="highlight">Parece que falta una coma (,) junto al conector, considere revisar la puntuación del conector o conectores resaltados en el texto.</span><br><br>
                Los conectores van acompañados de coma cuando aparecen en el inicio de la oración o entrecomillados si están en el interior de la oración.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Sin embargo los resultados fueron concluyentes.</em><br><br>
                <u>Después:</u><br>
                <em>Sin embargo<span class="highlight">,</span> los resultados fueron concluyentes.</em>`,
            secun: `
                <span class="highlight">Parece que la oración presenta información secundaria, considere revisar la información de la oración, eliminar aquella que resulte accesoria y mantener solamente la información principal de la idea que se quiere transmitir.</span><br><br>
                Los párrafos que presentan más de una idea, temas laterales poco justificados o gran número de detalles resultan menos comprensibles.<br><br>
                <strong>Ejemplo</strong><br><br>
                Eliminar anécdotas o datos históricos que no contribuyen a la explicación principal.`,
            destinatario: `
                <span class="highlight">Parece que la información proporcionada podría resultar compleja/abstracta para un receptor no experto. Considere adaptarla a un destinatario con estudios medios.</span><br><br>
                El nivel de profundidad científica en los textos divulgativos debe adecuarse a un lector sin conocimiento universitario. <br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Forzamiento radiactivo antropogénico.</em><br><br>
                <u>Después:</u><br>
                <em>Aumento del calor retenido por la atmósfera debido a actividades humanas.</em>`,
            finalidad: `
                <span class="highlight">Parece que podría haber falta de adecuación a la finalidad comunicativa de los textos divulgativos, considere ajustar el tono y la estructura del texto a los objetivos comunicativos prioritarios de la divulgación.</span><br><br>
                Cada finalidad comunicativa requiere un determinado uso de estrategias discursivas. Los textos divulgativos suelen tener finalidades comunicativas como:<br>
                - Informar<br>
                - Persuadir<br>
                - Entretener/deleitar<br>
                - Enseñar/explicar<br>
                - Describir<br>
                - Aclarar<br>
                - Fomentar el interés<br>
                - Concienciar<br>
                - Aconsejar<br><br>
                <strong>Ejemplo</strong><br><br>
                Un texto divulgativo debe priorizar la explicación antes que la discusión metodológica detallada.</em><br><br>
            `,
            coherenciaInt: `
                <span class="highlight">Parece que podría haber falta de coherencia interna en texto, considere revisarla evitando caer en reiteraciones, vacíos de información y contradicciones.</span><br><br>
                Los textos requieren una coherencia interna entre las ideas y una progresión temática. Para lograrlo, se debe evitar caer en contradicción, reiteraciones o saltos de información. <br><br>
                `,
            progresion: `
                <span class="highlight">Parece que falta progresión temática en el texto, considere revisar la relación lógica (cronológica, causal, sumativa, contrastiva…) entre las partes/párrafos.</span><br><br>
                La información debe seguir siempre una relación lógica (temporal, de causa-efecto, sumativa, contrastiva…) para que el mensaje se entienda mejor.<br><br>
                <strong>Ejemplo</strong><br><br>
                Definición → causas → consecuencias → soluciones.<br><br>
                `,
            claridad: `
                <span class="highlight">Parece que hay falta de conexión entre las ideas, considere revisar la conexión (temporal, causal, sumativa, contrastiva…) entre las ideas. El uso de conectores y marcadores discursivos puede contribuir a conseguirlo.</span><br><br>
                La información debe seguir siempre una relación lógica (temporal, de causa-efecto, sumativa, contrastiva…) para que el mensaje se entienda mejor. <br><br>
                <strong>Ejemplo</strong><br><br>
                <span class="highlight">Como consecuencia</span> de este aumento de temperatura, los glaciares pierden masa.<br><br>
                `,
            coherenciaExt: `
                <span class="highlight">Parece que podría haber falta de coherencia externa en el texto, considere revisarlo asegurándose de que cuenta con un párrafo introductorio, un desarrollo y un párrafo conclusivo.</span><br><br>
                Los textos divulgativos disponen de una estructura básica dividida en tres partes: introducción, desarrollo y conclusión. Este tipo de textos resultan más claros cuando dicha estructura es perceptible por el lector.<br><br>
                `,
            digresion: `
                <span class="highlight">Parece que el párrafo es complejo, considere revisar la complejidad de las oraciones del párrafo. Reduzca, por ejemplo, el uso acumulado de varios de estos elementos: subordinaciones, coordinaciones, incisos, nominalizaciones y cambios temáticos.</span><br><br>
                Los textos que presentan digresiones o se desvían del tema principal son más difíciles de entender.<br><br>
                <strong>Ejemplo</strong><br><br>
                Si el texto explica el cambio climático, evite incluir extensas descripciones sobre la historia de la navegación, salvo que tengan relación directa con el tema tratado.<br><br>
                `,
            parrafoComplejo: `
                <span class="highlight">Parece que la información proporcionada podría resultar compleja/abstracta para un receptor no experto. Considere adaptarla a un destinatario con estudios medios.</span><br><br>
                El párrafo resulta complejo cuando acumulan subordinaciones, coordinaciones, incisos, nominalizaciones y cambios temáticos. La concentración de varios de estos recursos en un solo párrafo incrementa significativamente el esfuerzo de lectura. <br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>El informe, elaborado por diferentes grupos de investigación y revisado posteriormente por especialistas internacionales, analiza múltiples aspectos, que resultan fundamentales, relacionados con la temperatura, la biodiversidad, los recursos hídricos y la economía.</em><br><br>
                <u>Después:</u><br>
                <em>El informe fue elaborado por diversos grupos de investigación. Posteriormente, especialistas internacionales revisaron el documento. El estudio analiza aspectos fundamentales como la temperatura, la biodiversidad, los recursos hídricos y la economía.</em>`,
            siglas: `
                <span class="highlight">Parece que se han usado siglas o abreviaturas, considere revisar la pertinencia de su uso. En caso de que sean necesarias, se podría pensar en desplegarlas cuando se usen por primera vez en el texto.</span><br><br>
                Los textos con siglas o abreviaturas son más difíciles de entender. Su comprensión mejora si las siglas y abreviaturas se despliegan en el primer uso.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>El análisis del IPCC evidencia alteraciones del sistema climático.</em><br><br>
                <u>Después:</u><br>
                <em>El <span class="highlight">informe del Grupo Intergubernamental de Expertos sobre el Cambio Climático</span> (IPCC) muestra alteraciones del sistema climático.</em>`,
            redundancias: `
                <span class="highlight">Parece que existen redundancias y/o formulaciones enfáticas en el texto, considere revisar este aspecto. Las construcciones absolutas y la adjetivación excesiva suelen contribuir a generar estas redundancias.</span><br><br>
                Los textos que incorporan expresiones innecesariamente largas o repetitivas se alargan y aumentan la carga de procesamiento de la información. En este sentido, se sugiere evitar expresiones redundantes, adjetivación excesiva y construcciones absolutas.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em><span class="highlight">Terminado el minucioso análisis del deshielo</span>, los investigadores descubrieron un abismo <span class="highlight">destructivo y catastrófico</span> en los glaciares. La masa de hielo se reduce <span class="highlight">notablemente</span> en un lapso de tiempo <span class="highlight">récord</span>, lo que provocará consecuencias futuras que alterarán <span class="highlight">absolutamente</span> todo el equilibrio ecológico global, haciendo que el colapso de los ecosistemas marinos sea <span class="highlight">totalmente</span> inevitable.</em><br><br>
                <u>Después:</u><br>
                <em>Los investigadores cuantificaron una pérdida severa en la masa de los glaciares tras analizar el deshielo. El hielo se reduce en un periodo récord, lo que generará efectos que alterarán el equilibrio ecológico global y comprometerán la estabilidad de los ecosistemas marinos.</em>`,
            faltaEnum: `
                <span class="highlight">Parece que se podría incluir una enumeración para disminuir la complejidad de la información, considere hacerlo.</span><br><br>
                Las listas o enumeraciones aligeran la carga de información en párrafos altamente informativos. Por eso, se suele recomendar que las secuencias complejas se transformen en enumeraciones.`,
            enum: `
                <span class="highlight">Parece que el texto de la enumeración no es uniforme, considere revisar el estilo de la enumeración del texto para asegurar su homogeneidad.</span><br><br>
                Los elementos de una lista o enumeración deben presentar estructuras gramaticales similares como, por ejemplo, empezar por un sustantivo, un artículo o un infinitivo. De ese modo, se consigue una lectura más rápida y sencilla.
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em><ul>
                <li>Reducir emisiones.</li>
                <li>La protección de bosques. </li>
                <li>Que se mejore la eficiencia energética. </li></ul>
                </em><br><br>
                <u>Después:</u><br>
                <em><ul>
                <li><span class="highlight">Reducir</span> emisiones.</li>
                <li><span class="highlight">Proteger</span> bosques.</li>
                <li><span class="highlight">Mejorar</span> la eficiencia energética.</li>
                </ul></em>`,
            enumIncos: `
                <span class="highlight">Parece que podría haber una inconsistencia en el sistema de listas y/o enumeraciones, considere revisar el formato de las enumeraciones del texto para asegurar su uniformidad.</span><br><br>
                Es recomendable que las listas o enumeraciones del texto mantengan siempre el mismo criterio y eviten utilizar números, letras o símbolos de forma arbitraria.<br><br>`,
            lexFrec: `
                <span class="highlight">Parece que se ha usado léxico poco frecuente, considere revisar el uso de palabras pocos frecuentes en español.</span><br><br>
                Los textos divulgativos requieren usar palabras frecuentes del español y ampliamente conocidas por los hispanohablantes para maximizar las posibilidades de que los lectores conozcan su significado. <br><br>
                Al hacer click con el botón derecho en alguna palabra remarcada dará la opción de generar una sugerencia.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Dilucidar.</em><br><br>
                <u>Después:</u><br>
                <em>Aclarar.</em>`,
            baul: `
                <span class="highlight">Parece que hay falta de precisión léxica, considere revisar el uso de palabras imprecisas (palabras baúl).</span><br><br>
                Es recomendable evitar el uso de palabras baúl o palabras imprecisas para evitar malentendidos. Estas palabras pueden sustituirse por términos más concretos y específicos.<br><br>
                Al hacer click con el botón derecho en alguna palabra remarcada dará la opción de generar una sugerencia.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Los sensores satelitales observaron varias cosas en el océano debido al cambio climático.</em><br><br>
                <u>Después:</u><br>
                <em>Los sensores satelitales observaron un aumento de 1,5ºC en la temperatura del océano debido al cambio climático.</em>`,
            rodeos: `
                <span class="highlight">Parece que hay rodeos expresivos o formulaciones innecesariamente largas en el texto, considere sustituir las expresiones complejas por verbos o construcciones más directas.</span><br><br>
                Las perífrasis y locuciones innecesarias alargan la oración sin aportar un significado adicional. Por ello, se recomienda sustituir las expresiones complejas por verbos directos.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Llevar a cabo una evaluación.</em><br><br>
                <u>Después:</u><br>
                <em>Evaluar.</em>`,
            extranjerismo: `
                <span class="highlight">Parece que se han utilizado extranjerismos, latinismos o arcaísmos, considere sustituirlos por equivalencias más actuales o ampliamente conocidas cuando sea posible.</span><br><br>
                Los extranjerismos, latinismos o arcaísmos resultan, con frecuencia, expresiones poco habituales en el español actual. Por ello, se recomienda que se sustituyan por equivalencias más actuales cuando sea posible.<br><br>
                Al hacer click con el botón derecho en alguna palabra remarcada dará la opción de generar una sugerencia.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Ad hoc.</em><br><br>
                <u>Después:</u><br>
                <em>Para este fin.</em>`,
            referente: `
                <span class="highlight">Parece que puede haberse producido una pérdida de referente en el texto, considere explicitar el referente o reformular las oraciones para evitar ambigüedades.</span><br><br>
                La pérdida del referente (objeto, persona o idea) en un texto puede generar falta de comprensión.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>El aumento de la temperatura global está acelerando el derretimiento de los glaciares árticos, que genera una alteración drástica en las corrientes marinas del Atlántico Norte, liberando además grandes cantidades de metano a la atmósfera. Su impacto en los ecosistemas locales y globales es impredecible, por lo que los científicos exigen frenarlo antes de que sea irreversible. </em><br><br>
                <u>Después:</u><br>
                <em>El <span class="highlight">aumento de la temperatura global</span> está acelerando el derretimiento de los glaciares árticos. Este <span class="highlight">deshielo</span> genera una alteración drástica en las corrientes marinas del Atlántico Norte y, al mismo tiempo, libera grandes cantidades de metano a la atmósfera. Las <span class="highlight">consecuencias</span> de dicha alteración marina en los ecosistemas locales y globales son impredecibles, por lo que los científicos exigen frenar el calentamiento global antes de que sea irreversible.</em>`,
            largas: `
                <span class="highlight">Parece que se han utilizado palabras largas o derivadas que pueden dificultar la lectura, considere sustituirlas por alternativas más breves y frecuentes.</span><br><br>
                Las palabras largas, provengan o no de otras palabras de las que derivan, resultan más difíciles de procesar. Por esa razón, se recomienda que se sustituyan por alternativas más breves.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Utilización.</em><br><br>
                <u>Después:</u><br>
                <em>Uso.</em>`,
            ambiguo: `
                <span class="highlight">Parece que alguna expresión admite varias interpretaciones, considere sustituirla o precisarla para evitar posibles ambigüedades.</span><br><br>
                Se deben evitar expresiones que admiten varias interpretaciones. Para ello, se puede recurrir a la sustitución de la palabra o a precisarla con un complemento.<br><br>
                Al hacer click con el botón derecho en alguna palabra remarcada dará la opción de generar una sugerencia.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Los expertos están preocupados por los últimos cambios en la corriente del hemisferio norte.</em><br><br>
                <u>Después:</u><br>
                <em>Los expertos están preocupados por los últimos cambios en la corriente <span class="highlight">marina</span> del hemisferio norte.</em>`,
            repeticion: `
                <span class="highlight">Parece que hay una repetición léxica cercana en el texto, considere sustituir alguna de las repeticiones mediante sinónimos, pronombres o reformulaciones.</span><br><br>
                Se debe evitar la repetición de palabras próximas entre sí. Para ello, se puede recurrir al uso de sinónimos, pronombres o reformulaciones.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Cambio climático... cambio climático... cambio climático...</em><br><br>
                <u>Después:</u><br>
                <em>Cambio climático... calentamiento global... alteración climática...</em>`,
            elemValor: `
                <span class="highlight">Parece que se han empleado elementos valorativos o subjetivos, considere priorizar formulaciones impersonales y basadas en la evidencia.</span><br><br>
                Los textos divulgativos escapan de la subjetividad y los elementos valorativos. En este sentido, se recomienda priorizar las formulaciones impersonales y basadas en la evidencia.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em><span class="highlight">Es evidente</span> que esta medida es excelente.</em><br><br>
                <u>Después:</u><br>
                <em>Diversos estudios indican resultados positivos asociados a esta medida.</em>`,
            tecnicismo: `
                <span class="highlight">Parece que se han utilizado tecnicismos que pueden dificultar la comprensión del texto, considere sustituir los innecesarios y explicar aquellos que resulten imprescindibles.</span><br><br>
                Los textos con numerosos términos especializados son más difíciles de entender. Su comprensión mejora si los tecnicismos innecesarios se sustituyen por palabras más generales y los términos necesarios se explican en el primer uso.<br><br>
                Al hacer click con el botón derecho en alguna palabra remarcada dará la opción de generar una sugerencia.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>La pérdida de la cubierta de hielo en el Océano Ártico genera un bucle de retroalimentación positiva que reduce drásticamente el <span class="highlight">albedo</span> de la región.</em><br><br>
                <u>Después:</u><br>
                <em>La pérdida de hielo en el Océano Ártico crea un efecto de bola de nieve que empeora la situación: reduce drásticamente la capacidad de la región para <span class="highlight">reflejar la luz del sol</span>.</em>`,
            negacion: `
                <span class="highlight">Parece que la oración acumula varias negaciones, considere reformularla en afirmativo siempre que sea posible.</span><br><br>
                La reiteración de negaciones en la oración incrementa la complejidad interpretativa. Por ello, se recomienda reformular la oración en afirmativo.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em><span class="highlight">No</span> es infrecuente que <span class="highlight">no</span> existan diferencias.</em><br><br>
                <u>Después:</u><br>
                <em>Es habitual que existan pocas diferencias.</em>`,
            negacionAbun: `
                <span class="highlight">Parece que existe un uso abundante de formulaciones negativas en el texto, considere expresar las ideas mediante formulaciones afirmativas cuando sea posible.</span><br><br>
                Las ideas se deben expresar con formulaciones afirmativas siempre que sea posible. La acumulación de oraciones negativas en el texto dificulta su comprensión.<br><br>`,
            sesgo: `
                <span class="highlight">Parece que podrían utilizarse expresiones más inclusivas, considere valorar el uso de términos colectivos, abstractos o epicenos cuando resulten adecuados.</span><br><br>
                Si bien la RAE considera el masculino el término inclusivo, aconseja el uso de expresiones más genéricas, como los sustantivos epicenos, siempre que sea posible. Se podría valorar, pues, el uso de términos colectivos, abstractos o epicenos cuando resulten adecuados.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Los <span class="highlight">investigadores</span> deben presentar sus resultados.</em><br><br>
                <u>Después:</u><br>
                <em>El <span class="highlight">personal investigador</span> debe presentar sus resultados.</em>`,
            apartados: `
                <span class="highlight">Parece que la información podría organizarse de forma más comprensible si se crean apartados, considere estructurar el contenido en apartados y subapartados.</span><br><br>
                La información se localiza mejor en los textos con apartados. Por esa razón, se recomienda organizar el contenido en apartados y subapartados.<br><br>`,
            principal: `
                <span class="highlight">Parece que la idea principal no aparece al comienzo del párrafo, considere situar la información más importante en una posición inicial.</span><br><br>
                La información más importante se debe situar al principio del párrafo.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Tras diversos análisis y revisiones, se concluyó que la temperatura había aumentado.</em><br><br>
                <u>Después:</u><br>
                <em><span class="highlight">La temperatura había aumentado.</span> Esta conclusión se obtuvo tras diversos análisis y revisiones.</em>`,
            titulo: `
                <span class="highlight">Parece que el título ofrece poca información sobre el contenido, considere utilizar un título más descriptivo y específico.</span><br><br>
                Los títulos deben anticipan adecuadamente el contenido para que el lector pueda prever qué información encontrará. Para ello, se recomienda utilizar títulos descriptivos y específicos.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Resultados.</em><br><br>
                <u>Después:</u><br>
                <em>Resultados sobre el aumento de temperatura global.</em>`,
            subtitulo: `
                <span class="highlight">Parece que faltan encabezados o subtítulos informativos, considere incorporar este tipo de elementos para facilitar la localización de la información.</span><br><br>
                La información se localiza mejor en los textos con encabezados. Por esa razón, se recomienda incluir este tipo de elementos. Este tipo de elementos se utilizan para introducir las ideas principales y/o favorecer que el lector las identifique.<br><br>
                <strong>Ejemplo</strong><br><br>
                <em>2.1. Causas del calentamiento global.</em><br>
                <em>2.2. Consecuencias sobre los ecosistemas.</em>`,
            recapitulacion: `
                <span class="highlight">Parece que no se incluyen recapitulaciones entre los distintos temas del texto, considere incorporar oraciones temáticas o recapitulativas antes de introducir nuevos contenidos.</span><br><br>
                Los textos divulgativos deben facilitar una exploración rápida del contenido. Para ello, se debe incluir una oración temática o recapitulativa antes de cambiar el tema para favorecer la asimilación de las ideas fundamentales ya expuestas. De ese modo, se consigue recuperar brevemente las ideas principales antes de avanzar.<br><br>
                <strong>Ejemplo</strong><br><br>
                <em>Una vez descritas las causas del fenómeno, analizaremos ahora sus principales consecuencias.</em>`,
            textoLargo: `
                <span class="highlight">Parece que el texto presenta una longitud elevada para el género divulgativo, considere reducir su extensión o distribuir mejor la información.</span><br><br>
                El texto supera la longitud habitual para el género de la difusión. Esta extensión suele situarse en las 1500 o 2000.<br><br>`,
            negrita: `
                <span class="highlight">Parece que la negrita se utiliza con una finalidad distinta de la habitual en divulgación, considere reservar su uso principalmente para títulos y encabezados.</span><br><br>
                Los textos divulgativos suelen utilizar la cursiva para resaltar las palabras. El uso de la negrita está reservado para los títulos.<br><br>`,
            cursiva: `
                <span class="highlight">Parece que la cursiva se emplea con una finalidad distinta de la recomendada, considere reservarla para extranjerismos, neologismos o resaltado puntual.</span><br><br>
                Se recomienda usar la cursiva únicamente para extranjerismos, neologismos o para resaltar palabras.<br><br>`,
            subrayado: `
                <span class="highlight">Parece que el subrayado se utiliza con una finalidad distinta de la habitual, considere reservarlo para los hipervínculos.</span><br><br>
                El uso del subrayado está reservado únicamente a los hipervínculos.<br><br>`,
            fernandezHuerta:first.description,
            szigrisztPazos: first.description,
            cultismo: `
                <span class="highlight">Parece que se han utilizado cultismos que pueden resultar poco accesibles para algunos lectores, considere sustituirlos por alternativas más frecuentes cuando existan.</span><br><br>
                Los cultismos pueden alejar al lector no especializado. Por ello, se recomienda no usar palabras de este tipo cuando existan alternativas más accesibles.<br><br>`,
            coloquialismo: `
                <span class="highlight">Parece que se han utilizado expresiones coloquiales, considere sustituirlas por formulaciones más adecuadas para un texto divulgativo.</span><br><br>
                Los textos divulgativos deben evitar expresiones excesivamente informales. Los coloquialismos pueden reducir la percepción de rigor y profesionalidad.<br><br>
                Al hacer click con el botón derecho en alguna palabra remarcada dará la opción de generar una sugerencia.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Las temperaturas <span class="highlight">se dispararon</span> una barbaridad.</em><br><br>
                <u>Después:</u><br>
                <em>Las temperaturas <span class="highlight">aumentaron</span> de forma muy significativa.</em>`,
            vulgarismo: `
                <span class="highlight">Parece que se han utilizado vulgarismos o giros inapropiados, considere sustituirlos por expresiones más adecuadas a los textos divulgativos.</span><br><br>
                Los textos divulgativos deben evitar expresiones vulgares o inapropiadas. Los vulgarismos pueden afectar a la credibilidad del documento y dificultar su difusión en contextos académicos o profesionales.<br><br>
                Más información: <a href="https://www.rae.es/libro-estilo-lengua-espa%C3%B1ola/palabras-del-diccionario-cuyo-uso-puede-no-ser-apropiado" target="_blank" rel="noopener noreferrer">https://www.rae.es/libro-estilo-lengua-espa%C3%B1ola/palabras-del-diccionario-cuyo-uso-puede-no-ser-apropiado</a>
                Al hacer click con el botón derecho en alguna palabra remarcada dará la opción de generar una sugerencia.<br><br>`,
            formato: `
                <span class="highlight">Parece que existen inconsistencias de formato en el documento, considere homogeneizar los criterios de formato y presentación.</span><br><br>
                Los textos divulgativos deben seguir criterios homogéneos de redacción y formato; y evitar la combinación de formatos.`,
            autor:`
                <span class="highlight">Parece que la referencia a un autor podría estar incompleta, considere añadir un hipervínculo u otra información que permita ampliar la referencia.</span><br><br>
                Las referencias a autores suelen ir acompañadas de un hipervínculo que permita al lector ampliar la información mencionada.`,
            ejemplo:`
                <span class="highlight">Parece que algunos conceptos abstractos carecen de ejemplos ilustrativos, considere incorporar ejemplos concretos que faciliten su comprensión.</span><br><br>
                Los conceptos abstractos se entienden mejor si van acompañados de ejemplos concretos. Dichos ejemplos facilitan la construcción de representaciones mentales y facilitan la comprensión de las ideas.`,
            metaforas:`
                <span class="highlight">Parece que se han empleado metáforas complejas, considere sustituirlas por explicaciones más directas o por metáforas más sencillas.</span><br><br>
                El texto recurre a metáforas difíciles de interpretar. No todos los lectores comparten los mismos referentes culturales por lo que se recomienda utilizar únicamente metáforas sencillas o explicaciones literales y directas.`,
            analogia: `
                <span class="highlight">Parece que algunos conceptos podrían explicarse mediante analogías cotidianas, considere incorporar comparaciones basadas en experiencias comunes.</span><br><br>
                Las analogías facilitan la comprensión de fenómenos difíciles de visualizar. Se recomienda, por tanto, utilizar comparaciones basadas en experiencias comunes.<br><br>
                <strong>Ejemplo</strong><br><br>
                <em>Los gases de efecto invernadero actúan de forma similar a una <span class="highlight">manta que retiene parte del calor</span> alrededor del planeta.</em>`,
            transicion: `
                <span class="highlight">Parece que faltan transiciones entre los distintos temas del texto, considere incorporar oraciones que faciliten el paso de un tema a otro.</span><br><br>
                Los textos divulgativos suelen introducir oraciones de transición entre secciones, apartados o cambios temáticos. Se recomienda incorporar este tipo de construcciones.<br><br>
                <strong>Ejemplo</strong><br><br>
                <em>Después de examinar los cambios observados, resulta necesario analizar sus posibles impactos futuros.</em>`,
            expresiones:`
                <span class="highlight">Parece que se han utilizado expresiones locales o regionales, considere sustituirlas por formulaciones de uso más general para facilitar la comprensión de un público más amplio.</span><br><br>
                Los textos dirigidos a un público amplio evitan las expresiones propias de una variedad geográfica concreta. Así se facilita la comprensión de los lectores de cualquier área geográfica. `,
            conoPrevio: `
                <span class="highlight">Parece que el texto presupone conocimientos previos especializados, considere introducir o explicar los conceptos necesarios para facilitar la comprensión.</span><br><br>
                Los textos dirigidos a un público amplio deben evitar da por supuesto el conocimiento de conceptos, teorías, instituciones o procesos especializados. Por esa razón, recomienda prescindir de expresiones que presupongan conocimientos compartidos e introduzca los conceptos necesarios para comprender el texto.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em><span class="highlight">Como todos sabemos</span>, el efecto invernadero es un fenómeno ampliamente conocido.</em><br><br>
                <u>Después:</u><br>
                <em>El efecto invernadero es un proceso natural mediante el cual determinados gases retienen parte del calor en la atmósfera terrestre.</em>`,
            contextualizacion: `
                <span class="highlight">Parece que falta contextualización de algunos autores, teorías, instituciones o documentos mencionados, considere incorporar una breve explicación cuando aparezcan por primera vez.</span><br><br>
                Los textos divulgativos deben ofrecer una breve contextualización cuando aparezca una referencia relevante a autores, teorías, instituciones o documentos por primera vez.<br><br>
                <strong>Ejemplo</strong><br><br>
                <u>Antes:</u><br>
                <em>Según <span class="highlight">Kuhn</span>, este fenómeno supone un cambio de paradigma.</em><br><br>
                <u>Después:</u><br>
                <em>Según <span class="highlight">Thomas Kuhn, filósofo e historiador de la ciencia conocido por sus estudios sobre los cambios científicos</span>, este fenómeno supone un cambio de paradigma.</em>`,

            estadística: first.description

        }
        const descriptionMapAntiguo = {
            parrafoCorto: "Los párrafos con una sola oración presentan información fragmentada y dificultan la construcción de relaciones entre las ideas.\nSe podría construir un párrafo que incluya al menos dos oraciones relacionadas entre sí.\n\nEjemplo\nAntes:\nLa temperatura media global ha aumentado durante las últimas décadas.\nDespués:\nLa temperatura media global ha aumentado durante las últimas décadas. Este incremento se relaciona principalmente con las emisiones de gases de efecto invernadero.",
            parrafoLargo: "Los párrafos largos aumentan el esfuerzo de lectura, dificultan la localización de las ideas principales y favorecen la pérdida de información relevante.\nSe podría dividir la información en varios párrafos más breves, procurando que cada párrafo desarrolle una única idea principal.",
            oracionLarga: "Las oraciones extensas (que superan las 25 palabras) incrementan la carga cognitiva y dificultan la identificación de las relaciones sintácticas.\nSe podría dividir la oración en varias oraciones más breves.\n\nEjemplo\nAntes:\nLos investigadores analizaron los datos obtenidos en diferentes estaciones meteorológicas distribuidas por diversas regiones durante varias décadas con el fin de identificar tendencias relacionadas con la temperatura y las precipitaciones.\nDespués:\nLos investigadores analizaron datos de diversas estaciones meteorológicas. El estudio incluyó varias regiones y varias décadas. El objetivo fue identificar tendencias relacionadas con la temperatura y las precipitaciones.",
            inciso: "Los incisos o alaraciones interrumpen la lectura y dificultan la identificación de la estructura principal de la oración.\nSería recomendable eliminar los incisos innecesarios o convertirlos en oraciones independientes.\n\nEjemplo\nAntes:\nEl informe, elaborado por un grupo internacional de expertos, algunos de ellos especializados en climatología marina, fue publicado recientemente.\nDespués:\nUn grupo internacional de expertos elaboró el informe. Algunos especialistas trabajaban en climatología marina. El informe se publicó recientemente.",
            orden: "Las oraciones que siguen el orden natural del español (sujeto+verbo+complementos) requieren un menor esfuerzo de interpretación.\nSe podría priorizar el orden sujeto+verbo+complementos en la oración.\n\nEjemplo\nAntes:\nAumentó considerablemente la temperatura media global durante el último siglo.\nDespués:\nLa temperatura media global aumentó consiblemente durante el último siglo.",
            coordinada: "Las oraciones que acumulan varios elementos unidos con conjunciones generan sensación de infomación poco jerarquizada y menos comprensible.\nSe podría dividir la información en varias oraciones.\n\nEjemplo\nAntes:\nEl estudio analizó temperaturas y precipitaciones y vientos y humedad y cobertura vegetal.\nDespués:\nEl estudio analizó las temperaturas y las precipitaciones. También examinó los vientos, la humedad y la cobertura vegetal.",
            yuxtapuesta: "Las oraciones que acumulan varios elementos unidos con signo de puntuación (comas y/o puntos y coma) generan sensación de información poro jerarquizada y menos comprensible.\nSe podría dividir la información en varias oraciones.\n\nEjemplo\nAntes:\nEl estudio analizó temperaturas, precipitaciones, vientos, humedad, cobertura vegetal, heladas, granizo, otros fenómenos adversos.\nDespués:\nEl estudio analizó las temperaturas y las precipitaciones. También examinó los vientos, la humedad y la cobertura vegetal. Por último, se centró en estudiar las heladas, el granizo, así como otros fenómenos adversos.",
            relativo: "Las oraciones con fórmulas de relativo alejadas de su antecedente o elemento al que se refiere se comprenden peor porque puede producirse una pérdida de referente.\nSe podría simplificar la estructura o acercar el antecedente a la expresión de relativo.\n\nEjemplo\nAntes:\nLos modelos que utilizan los investigadores que trabajan en centros especializados permiten realizar proyecciones.\nDespués\nLos investigadores utilizan modelos especializados. Estos modelos permiten realizar proyecciones.",
            concordancia: "La concordancia en español afecta al género, número, persona o tiempo verbal. La falta de concordancia genera dudas sobre las relaciones gramaticales.\nSería necesario revisar la concordancia de todos los elementos de la oración.\n\nEjemplo\nAntes:\nLos datos obtenida muestran una tendencia.\nDespués:\nLos datos obtenidos muestran una tendencia.",
            pasiva: "La voz pasiva suele resultar más compleja de interpretar que la voz activa.\nSe podría transformar la oración a voz activa cuando sea posible.\n\nEjemplo\nAntes:\nLas mediciones fueron realizadas por los investigadores.\nDespués:\nLos investigadores realizaron las mediciones.",
            eliptico: "El encadenamiento de oraciones sin sujeto explícito en el mismo párrafo puede dificultar la identificación del sujeto que realiza la acción y genera ambigüedad entre los agentes implicados.\nSe podría explicitar el sujeto en alguna de las oraciones.\n\nEjemplo\nAntes:\nSe analizaron los resultados.\nDespués:\nEl equipo investigador analizó los resultados.",
            nopersonal: "El uso de infinitivos, gerundios o participios al principio de la oración aumentan la complejidad del texto. Lo mismo ocurre cuando estas formas no van acompañadas de verbos en forma personal.\nSe podrían priorizar los verbos conjugados en la oración.\n\nEjemplo\nAntes:\nPara realizar la evaluación y obtener los resultados...\nDespués:\nEl equipo evaluó los datos y obtuvo los resultados.",
            gerundio: "El uso del gerundio para expresar una acción posterior a la principal no es normativo en español.\nPara evitar el gerundio de posterioridad, se podría dividir la información en dos oraciones.\nMás información: https://www.rae.es/libro-estilo-justicia/las-palabras-y-sus-grupos-problemas-y-actuaciones/gerundio/usos-incorrectos/gerundio-de-posterioridad\n\nEjemplo\nAntes:\nSe publicó el informe, generando un intenso debate.\nDespués:\nSe publicó el informe. Dicha publicación generó un intenso debate.",
            conector: "Los conectores o marcadores discursivos ayudan a dar cohesión al texto.\nSe podría introducir algún conector al inicio del párrafo o entre oraciones para conectar las ideas.\n\nEjemplo\nAntes:\nLas temperaturas aumentaron. Las precipitaciones disminuyeron.\nDespués:\nLas temperaturas aumentaron. Además, las precipitaciones disminuyeron.",
            conectorRepe: "La variación en el uso de los conectores ayuda a mejorar el texto. Dicha variación debe hacerse atendiendo la relación lógica entre las distintas partes de la oración o el párrafo.\n\nEjemplo\nSustituir repeticiones de 'además' por otros conectores que también indiquen adición como: asimismo, igualmente, por otra parte, además de ello.",
            conectoresPunt:"Los conectores van acompañados de coma cuando aparecen en el inicio de la oración o entrecomillados si están en el interior de la oración.\n\nEjemplo\nAntes:\nSin embargo los resultados fueron concluyentes.\nDespués:\nSin embargo, los resultados fueron concluyentes.",
            secun: "Los párrafos que presentan más de una idea, temas laterales poco justificados o gran número de detalles resultan menos comprensibles.\nEn estos casos, se recomienda que se mantenga únicamente la información necesaria.\n\nEjemplo\nEliminar anécdotas o datos históricos que no contribuyen a la explicación principal.",
            destinatario: "El nivel de profundidad científica en los textos divulgativos debe adecuarse a un lector sin conocimiento universitario.\n\nEjemplo\nAntes:\nForzamiento radiactivo antropogénico.\nDespués:\nAumento del calor retenido por la atmósfera debido a actividades humanas.",
            finalidad: first.description + "\nCada finalidad comunicativa requiere un determinado uso de estrategias discursivas. Los textos divulgativos suelen tener finalidades comunicativas como: informar, persuadir, entretener/deleitar, enseñar/explicar, describir, aclarar, fomentar el interés, concienciar o aconsejar.\nSe debería ajustar el tono y la estructura del texto a los objetivos comunicativos previstos.\n\nEjemplo\nUn texto divulgativo debe priorizar la explicación antes que la discusión metodológica detallada.",
            coherenciaInt: first.description + "\nLos textos requieren una coherencia interna entre las ideas y una prograsión temática. Para lograrlo, se debe evitar caer en contradicción, reiteraciones o saltos de información.",
            progresion: first.description + "\nLa información debe seguir siempre una relación lógica (temporal, de causa-efecto, sumativa, contrastiva...) para que el mensaje se entienda mejor.\n\nEjemplo\nDefinición -> causas -> consecuencias -> soluciones. ",
            claridad: first.description + "\nLa información debe seguir siempre una relación lógica (temporal, de causa-efecto, sumativa, contrastiva...) para que el mensaje se entienda mejor. Los conectores y marcadores discursivos ayudan a conseguirlo.\n\nEjemplo\nComo consecuencia de este aumento de temperatura, los glaciares pierden masa.",
            coherenciaExt: first.description + "\nLos textos divulgativos disponen de una estructura básica dividida en tres partes: introducción, desarrollo y conclusión. Este tipo de textos resultan más claros cucando dicha estructura es perceptible por el lector.",
            digresion: first.description + "\nLos textos que presentan digresiones o se desvían del tema principal son más difíciles de entender.\n\nEjemplo\nSi el texto explica el cambio climático, evite incluir extensas descripciones sobre la historia de la navegación, salvo que tengan relación directa con el tema tratado.",
            parrafoComplejo: "El párrafo resulta complejo cuando acumulan subordinaciones, coordinaciones, incisos y nominalizaciones. La concentración de varios de estos recursos en un solo párrafo incrementa significativamente el esfuerzo de lectura.\n\nEjemplo\nAntes:\nEl informe, elaborado por diferentes grupos de investigación y revisado posteriormente por especialistas internacionales, analiza múltiples aspectos, que resultan fundamentales, relacionados con la temperatura, la biodiversidad, los recursos hídricos y la economía.\nDespués:\nEl informe fue elaborado por diversos grupos de investigación. Posteriormente, especialistas internacionales revisaron el documento. El estudio analiza aspectos fundamentales como la temperatura, la biodiversidad, los recursos hídricos y la economía.",
            siglas:"",
            redundancias: "",
            faltaEnum: "",
            enum: "Los elementos de una lista o enumeración deben presentar estructuras gramaticales similares como, por ejemplo, empezar por un sustantivo, un artículo o un infinitivo. De ese modo, se consigue una lectura más rápida y sencilla.\n\nEjemplo\nAntes:\n- Reducir emisiones.\n- La protección de bosuqes.\n- Que se mejore la eficiencia energética.\nDespués:\n- Reducir emisiones.\n- Proteger bosques.\n- Mejorar la eficiencia energética.",
            enumIncos: "Es recomendable que las listas o enumeraciones del texto mantengas siempre el mismo criterio y eviten utilizar números, letras o símbolos de forma arbitraria.",
            lexFrec: "",
            baul: "Es recomendable evitar el uso de palabras baúl o palabras imprecisas para evitar malentendidos. Estas palabras pueden sustituirse por términos más concretos y específicos.\nSi clicas sobre una palabra marcada se generará una sugerencia.\n\nEjemplo\nAntes:\nSe observaron varias cosas en el oceáno debido al cambio climático.\nDespués:\nLos sensores datelitales observaron un aumento dde 1,5ºC en la temperatura del océano debido al cambio climático.",
            rodeos: "Las perífrasis y locuciones innecesarias alargan la oración sin aportar un significado adicional. Por ello, se recomienda sustituir las expresiones complejas por verbos directos.\n\nEjemplo\nAntes:\nLlevar a cabo una evaluación.\nDespués:\nEvaluar.",
            extranjerismo: "Los extranjerismos, latinismos o arcaísmos resultan, con frecuencia, expresiones poco habituales en el español actual. Por ello, se recomienda que se sustituyan por equivalencias más actuales cuando sea posible.\n\nEjemplo\nAntes:\nAd hoc.\nDespués:\nPara este fin.",
            largas: "Las palabras largas, provengan o no de otras palabras de las que derivan, resultan más difíciles de procesar. Por esa razón, se recomienda que se sustituyan por alternativas más breves.\n\nEjemplo\nAntes:\nUtilización.\nDespués:\nUso.",
            referente: "",
            ambiguo: "",
            repeticion: "",
            elemValor: "",
            tecnicismo: "Los textos con numerosos términos especializados son más difíciles de entender. Su comprensión mejora si los tecnicismos innecesarios se sustituyen por palabras más generales y los términos necesarios se explican en el primer uso.\nEjemplo\n\nAntes:\nLa pérdida de la cubierta de hielo en el Océano Ártico genera un bucle de retroalimentación positiva que reduce drásticamente el albedo de la región.\nDespués:\nLa pérdida de hielo en el Océano Ártico crea un efecto de bola de nieve que empeora la situación: reduce drásticamente la capacidad de la región para reflejar la luz del sol.",
            negacion: "La reiteración de negaciones en la oración incrementa la complejidad interpretativa. Por ello, se recomienda reformular la oración en afirmativo.\n\nEjemplo\nAntes:\nNo es infrecuente que no existan diferencias.\nDespués:\nEs habitual que existan pocas diferencias.",
            negacionAbun: "Las ideas se deben expresar con formulaciones afirmativas siempre que sea posible. La acumulación de oraciones negativas en el texto dificulta su compresión.",
            sesgo: "Si bien la RAE considera el masculino el término inclusivo, aconseja el uso de expresiones más genéricas, como los sustantivos epicenos, siempre que sea posible. Se podría valorar, pues, el uso de términos colectivos, abstractos o epicenos cuando resulten adecuados.\n\nEjemplo\nAntes:\nLos investigadores deben presentar sus resultados.\nDespués:\nEl personal investigador debe presentar sus resultados.",
            apartados: "",
            principal: "",
            titulo: "",
            subtitulo: "",
            recapitulacion: "",
            textoLargo: "El texto supera la longitud habitual para el género de la difusión. Esta extensión suele situarse en las 1500 o 2000.",
            negrita: "",
            cursiva: "",
            subrayado: "",
            fernandezHuerta:first.description,
            szigrisztPazos: first.description,
            cultismo: "",
            coloquialismo: "",
            vulgarismo: "",
            formato: "",
            autor: "",
            ejemplo: "",
            metaforas: "",
            analogias: "",
            transicion: "",
            expresiones: "",
            conoPrevio: "",
            contextualizacion: "",
            latinismo: "Los extranjerismos, latinismos o arcaísmos resultan, con frecuencia, expresiones poco habituales en el español actual. Por ello, se recomienda que se sustituyan por equivalencias más actuales cuando sea posible.\n\nEjemplo\nAntes:\nAd hoc.\nDespués:\nPara este fin.",
            estadística: first.description,

        }
        desc.innerHTML = descriptionMap[first.name] || first.text;
        //desc.innerText = descriptionMapAntiguo[first.name] || first.text;

        // Botón quitar sugerencia
        /*
        const btn = document.createElement("button");
        btn.innerText = "Ocultar comentario";
        btn.className = "comment-accept-btn";
        btn.style.display = "none";

         */
if (activeCommentId != null) {

    const existsInFiltered = filtered.some(c => c.id === activeCommentId);
    if (!existsInFiltered) {
        const activeComment = comments.find(c => c.id === activeCommentId);

        if (activeComment && activeComment.type === "estadistica" && !activeComment.global && paragraphFilter === "all") {
            const globalStats = filtered.find(c => c.type === "estadistica" && c.global);
            activeCommentId = globalStats ? globalStats.id : null;
        } else {
            activeCommentId = null;
        }
    }
}


        /*
        btn.onclick = () => {
            acceptSuggestion(first);
            renderComments(activeCommentId);
        };

         */
        let btn = null;

        div.onclick = (event) => {
            if(event.target.closest("a, button, input, select, textarea")) return;
              //Si está bloqueado no se puede clicar el comentario
              if (commentsLocked) return;

              if (activeCommentId === first.id) {
                  activeCommentId = null;
                  activeType = null;
                  clearHighlights();
                  renderComments();
                  return;
              }

              activeCommentId = first.id;
              activeType = first.name;
              clearHighlights();
              const isGlobalStatistics = first.global && first.type==="estadistica";
              if (enableSentenceHighlight && !isGlobalStatistics) {
                  highlightByType(first.name);
              }
              renderComments();
        };


        const groupHasActive = group.some(c => c.id === activeCommentId);

        const isActiveGroup = group[0].name === activeType;
        if (isActiveGroup){
            desc.style.display = "block";
        }
        //if (first.suggestion==="true" && isActiveGroup) {
            //btn = document.createElement("button");
            //btn.className = "generateSuggestionBtn";
            //btn.textContent = "Generar sugerencia";
            //btn.onclick = async () => {
            //    currentModalComment = first;
            //    originalTextArea.value = first.texto;
            //    suggestedTextArea.value = "";
            //    modal.style.display = "block";
            //    btn.disabled = true;
            //    btn.textContent = "Generando...";
            //    await generateSuggestion({first});

               // btn.disabled = false;
               // btn.textContent = "Regenerar sugerencia";

    //}
//}

        div.appendChild(title);
        div.appendChild(desc);
  //      if (btn!==null){
   //         div.appendChild(btn);
   //     }
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
  //if (appMode === "feedback") {
  //    document.getElementById("recalculateBtn").style.display = "block";
  //}
  renderComments();
}

function unlockComments() {
  commentsLocked = false;
  document.getElementById("recalculateBtn").style.display = "none";
}

// Añadir comentarios del texto completo
async function addCommentText() {
    //quill.removeFormat(0, quill.getLength());
    clearHighlights();
    modifiedParagraphs.clear();
    hasFullAnalysis = true;
    hasParagraphAnalysis = false;
/*
    if (appMode === "write") {
        alert("Cambia a modo Feedback para analizar el texto.");
        return;
    }


 */
    highlightParagraphs = false;
    unlockComments();
    analyzedParagraphStart = null;
    updateParagraphNumbers();
    updateParagraphFilter();

    const textoCompleto = quill.getText().trim();


    comments = [];

    let original;
    // Mostrar overlay de bloqueo
    const overlay = document.getElementById("analysisOverlay");
    overlay.style.display = "flex";

    const paragraphs = quill.root.querySelectorAll(BLOCK_SELECTOR);
    let visibleIndex = 1;

    const paragraphsArray = Array.from(paragraphs).filter(p =>
        p.textContent.replace(/\u200B/g, "").trim().length > 0);

    const total = paragraphsArray.length;
    let current = 0;
    updateProgress(current, total, "paragraph");

    lastAnalyzedParagraphs = {}

    for (let p of paragraphsArray) {
        const text = p.textContent.replace(/\u200B/g, "").trim();
        if (!text) continue;
        lastAnalyzedParagraphs[visibleIndex] = {text, tag: p.tagName};

        const oraciones = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
        totalOracionesPorParrafo[visibleIndex] = oraciones.length;

        const start = quill.getIndex(Quill.find(p));

        const data = await analyzeSingleParagraph(text, start);

        data.forEach(item => {
            comments.push(
                buildComment(item, text, visibleIndex, start)
            );

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
        current++;

        updateProgress(current, total, "paragraph");
        await new Promise(r => setTimeout(r, 0));
    }
/*
    const tables = Array.from(
        quill.root.querySelectorAll(".generated-table")
    );

    for (let tableIndex = 0; tableIndex < tables.length; tableIndex++) {

        const tableComments = await analyzeGeneratedTable(
            tables[tableIndex],
            tableIndex
        );

        comments.push(...tableComments);
    }

 */

    let globalComments = [];
    updateProgress(total, total, "global");
    const globalResponse = await fetch("/analyse_document", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            texto: textoCompleto,
            intencionalidad: textIntentions })
    });
    const globalData = await globalResponse.json();


    updateProgress(total+1, total, "global");

    globalComments = (globalData.comentarios_globales || []).flatMap(c => c.global || [])
        .map(c=> ({
            ...c,
            global: true,
            paragraphStart: -1,
            index: -1,
            localIndex: -1,
            paragraph: -1 }));

    comments.push(...globalComments);
    calcularPorcentajesPorParrafo();

    resetAnalysisFilters

    renderComments();

    hasPendingChanges = false;
    updateAnalyzeButton();

    updateGenerateSuggestionButton();
    // ocultar overlay
    overlay.style.display ="none";
    analysisPerformed=true;
    lastStructure = getDocumentStructureSignature();
}

// Añadir comentarios del párrafo seleccionado
async function addCommentParagraph() {
    //quill.removeFormat(0, quill.getLength());
    clearHighlights();
    modifiedParagraphs.clear();
    hasFullAnalysis = false;
    hasParagraphAnalysis = true;

    if (appMode === "write") {
        alert("Cambia a modo feedback para analizar el párrafo.");
        return;
    }
    quill.root.querySelectorAll(BLOCK_SELECTOR).forEach(p =>
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
    analyzedParagraphStart = start;
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
    const paragraphs = quill.root.querySelectorAll(BLOCK_SELECTOR);
    let currentParagraphNumber = null;
    let visibleIndex = 1;

    paragraphs.forEach((p) => {
        const pText = p.textContent.replace(/\u200B/g, "").trim();
        if (pText.length > 0){
            if (quill.getIndex(Quill.find(p)) === start) {
                currentParagraphNumber = visibleIndex;
                p.classList.add("active-paragraph");

                lastAnalyzedParagraphs[currentParagraphNumber] = {
                    text: paragraphText,
                    tag: p.tagName
                };

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
    const overlay = document.getElementById("analysisOverlay");
    overlay.style.display = "flex";

    let parrafo = paragraphText;
    comments = [];
    let data;
    try {
        const globalResponse = await fetch('/analyse_document', {
            method: "POST",
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                texto: textoCompleto,
                intencionalidad: textIntentions
            })
        });
        const globalData = await globalResponse.json();
        const response = await fetch("/analyse_paragraph", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({"parrafo": parrafo, "start": start, intencionalidad: textIntentions})
        });
        paragraphData = await response.json();
    } catch (err) {
        console.error("Error analizando el párrafo:", err);
        overlay.style.display = "none";
        return;
    }
    // Procesamos comentarios por chunks para no bloquear el hilo
    const CHUNK_SIZE = 5;
    const globalComments = (globalData.comentarios_globales || []).flatMap(c => c.global || [])
        .map(c=> ({
        ...c,
        global: true,
        paragraphStart: -1,
        index: -1,
        localIndex: -1,
        paragraph: -1
    }));
    const paragraphComments = Array.isArray(paragraphData)
        ? paragraphData
        : (paragraphData.comentarios || []);
    data = [...globalComments, ...paragraphComments];
    for (let i = 0; i< data.length; i+=CHUNK_SIZE) {
        const chunk = data.slice(i, i + CHUNK_SIZE);
        chunk.forEach(item => {
            if(item.global){
                comments.push(item)
            } else {
                comments.push(
                    buildComment(item, text, currentParagraphNumber, start)
                );
            }
        });
        // Dejamos que el navegador renderice
        await new Promise(r => setTimeout(r, 0));
    }

    resetAnalysisFilters
    updateFilterOptions();
    renderComments(activeCommentId);
    analyzingParagraph = false;
    hasPendingChanges = false;
    updateAnalyzeButton();

    updateGenerateSuggestionButton();
    // Ocultar overlay
    overlay.style.display = "none";
}

async function handleAnalyzeButton() {
    if (hasPendingChanges) {
        await reanalyzeModifiedParagraphs();
    } else {
        await addCommentText();
    }
}

function getParagraphNumberFromIndex(index) {
    const paragraphs = quill.root.querySelectorAll(BLOCK_SELECTOR);
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

function getVisibleParagraphs() {
    return Array.from(quill.root.querySelectorAll(BLOCK_SELECTOR))
        .map(p => ({
            node: p,
            text: p.textContent.replace(/\u200B/g, "").trim()
        }))
        .filter(p => p.text.length > 0);
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
    //forceLockEditing();
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

    //analysisContainer.innerHTML = "<strong>Análisis:</strong><br>" + description.replace(/\n/g, "<br>");
    analysisContainer.innerHTML = description.replace(/\n/g, "<br>");
}

const wrapper = document.querySelector(".editor-wrapper");

wrapper.addEventListener("scroll", () => {
    updateParagraphNumbers();
});

function updateParagraphNumbers() {
    const container = document.getElementById("paragraphNumbers");
    container.innerHTML = "";

    const wrapper = document.querySelector(".editor-wrapper");
    const editorRect = quill.root.getBoundingClientRect();

    const blocks = Array.from(
        quill.root.querySelectorAll(BLOCK_SELECTOR)
    ).filter(node => {
        return !node.closest(".generated-table")
    });
    let count = 1;

    blocks.forEach(node => {

        const text = (node.textContent || "").replace(/\u200B/g, "").trim();
        if (!text) {
            return
        }

        const row = document.createElement("div");
        row.style.position = "absolute";
        row.style.right = "6px";
        row.style.paddingRight = "6px";
        row.style.boxSizing = "border-box";

        const rect = node.getBoundingClientRect();

        row.style.top = (rect.top - editorRect.top + quill.root.scrollTop) + "px";

        // Si este párrafo es el analizado, le añadimos la clase
        let blot = Quill.find(node);
        if (blot) {
            const parStart = quill.getIndex(blot);
            if (blot) {
                const parStart = quill.getIndex(blot);

                if (
                    analyzedParagraphStart != null &&
                    analyzedParagraphStart === parStart
                ) {
                    row.classList.add("active-paragraph-number");
                }
            }
// El índice de modifiedParagraphs es el número visible
            row.textContent =
                count +
                (
                    analysisPerformed &&
                    modifiedParagraphs.has(count)
                        ? " *"
                        : ""
                );

            count++;

            container.appendChild(row);
        }
        ;

        const lastNode = blocks[blocks.length - 1];

        if (lastNode) {

            const rect = lastNode.getBoundingClientRect();

            const spacer = document.createElement("div");

            spacer.style.position = "absolute";
            spacer.style.top =
                quill.root.scrollHeight + "px";

            spacer.style.height = rect.height + "px";
            spacer.style.width = "100%";

            container.appendChild(spacer);
        }

        attachParagraphHover();
    });
}

// Para que la sugerencia me aparezca en el número del contador de párrafo
function attachParagraphHover() {
    const container = document.getElementById("paragraphNumbers");
    const paragraphs = quill.root.querySelectorAll(BLOCK_SELECTOR);

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


    let p = leaf.domNode;
    while (p && !p.matches(BLOCK_SELECTOR)) {
        p = p.parentElement;
    }
    if (!p) return;

    // Quitar clase a todos los párrafos
    quill.root.querySelectorAll(BLOCK_SELECTOR).forEach(p =>
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
    const paragraphs = quill.root.querySelectorAll(BLOCK_SELECTOR);
    const tables = quill.root.querySelectorAll(".generated-table");

    // Si todavía no se ha analizado, que todos los párrafos se muestren como activos
    if (!analysisPerformed) {
        paragraphs.forEach(p => p.classList.add("active-paragraph"));
        tables.forEach(table => table.classList.add("active-paragraph"));
        return;
    }

    // Quitar clase a todos
    paragraphs.forEach(p => p.classList.remove("active-paragraph"));
    tables.forEach(table => table.classList.remove("active-paragraph"));

    // Si es "Texto completo" activar todos
    if (paragraphFilter === "all") {
        paragraphs.forEach(p => p.classList.add("active-paragraph"));
        tables.forEach(table => table.classList.add("active-paragraph"));
        return;
    }

    const selectedValue = Number(paragraphFilter);

    if (selectedValue <= -2) {
        const tableIndex = -selectedValue - 2;
        const table = tables[tableIndex];
        if (table) {
            table.classList.add("active-paragraph");
        }
        return;
    }

    if(Number(paragraphFilter) === -1){
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
    const overlay = document.getElementById("suggestionOverlay");
    overlay.style.display = "flex";
    currentModalComment.suggestion = "";
    suggestedTextArea.innerHTML = "";
    try {
        // Generamos la sugerencia
        const response = await fetch("/generar_sugerencia", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                oracion: comment.oracion,
                palabra: comment.palabra,
                criterio: comment.name
            })
        });
        if (!response.ok){
            console.error(await response.text());
            return;
        }
        const data = await response.json();
        let sugerencia = data.sugerencia;
        currentModalComment.suggestion = sugerencia;
        // Limpieza
        sugerencia = sugerencia.trim().replace(/^"""/, "").replace(/"""$/, "").replace(/^```/, "").replace(/```$/, "").replace(/^\s+|\s+$/g, "").replace(/\n{2,}/g, "\n").replace(/^\n+|\n+$/g, "");

        const diff = diffWords(comment.oracion, sugerencia);
        originalTextArea.innerHTML = diff.original;
        suggestedTextArea.innerHTML = diff.suggested;
    } catch (err) {
        console.error("Error generando sugerencia:",err);
        suggestedTextArea.textContent = "error generando sugerencia";
    }
    overlay.style.display ="none";
}
/*
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

 */

// Para cerrar el popup de la sugerencia
function checkPopupClose(){
    if (!isHoveringNumber && !isHoveringPopup){
        hideSuggestionPopup();
        currentParagraphComment = null;

        document.querySelectorAll("#paragraphNumbers div")
            .forEach(div => div.classList.remove("active-paragraph-number-suggestion"))
    }
}

function acceptSuggestion(comment){
    if (!comment.suggestion) return;
    //Eliminar el comentario aceptado
    comments = comments.filter(c => c.id !== comment.id);

    // Bloqueamos el panel de comentarios y mostramos el botón "Recalcular"
    lockComments();

    // Hacer que el párrafo aceptado se vea negro
    const paragraphs = quill.root.querySelectorAll(BLOCK_SELECTOR);
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
    const paragraphs = quill.root.querySelectorAll(BLOCK_SELECTOR);
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
        body: JSON.stringify({ parrafo: paragraphText, start, intencionalidad: textIntentions })
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
function highlightError(index, length, type, suggestion = false, description, name, isActive) {

    const colors = {
        "morfosintaxis": "#F9E79F",
        "léxico-semántico": "#AED6F1",
        "pragmático-discursivo": "#A9DFBF",
        "accesibilidad": "#F5CBA7",
        "estadísticas": "#D7BDE2"
    };

    const color = colors[type] || "#fff3a0";

    quill.formatText(index, length, {
        background: color
    });

    if ((suggestion === true || suggestion === "true") && isActive) {
        quill.formatText(index, length, {
            appUnderline: true
        });
    }

    if (name==="oracionLarga") {
        const [leaf] = quill.getLeaf(index);
        if (leaf && leaf.parent && leaf.parent.domNode) {
            leaf.parent.domNode.title = description + " palabras.";
        }
    }
}
function clearHighlights() {
    quill.formatText(0, quill.getLength(), {
        background: false,
        appUnderline: false
    });
    //clearTableHighlights();
}
function highlightByType(type) {
    clearHighlights();
    if(!enableSentenceHighlight) return;

    const paragraphFilter = document.getElementById("filterParagraph").value;
    const selectedParagraph = paragraphFilter !== "all"
        ? Number(paragraphFilter)
        : null;

    comments.forEach(c => {
        if (c.name !== type) return;
        /*
        if (paragraphFilter!=="all") {
            const selectedParagraph = Number(paragraphFilter);
            if (c.paragraph!== selectedParagraph) return;

        }

         */
        if (selectedParagraph !== null && Number(c.paragraph) !== selectedParagraph){
            return;
        }

        if (c.global){
            return;
        }
        if (c.table) {
            highlightTableError(c);
            return;
        }
        if (c.paragraph === -1) return;

        const index = getUpdatedIndex(c);
        const isActive = c.name === activeType;

        highlightError(index, c.length, c.type, c.suggestion, c.description, c.name, isActive);

    })
}

function highlightTableError(comment) {
    const table = quill.root.querySelector(
        `.generated-table[data-table-index="${comment.tableIndex}"]`
    );

    if (!table)
    {
        console.log("No se encontró la tabla:", comment.tableIndex);
        return;
    }

    const cell = table.querySelector(
        `[data-table-cell-id="${comment.tableCellId}"]`
    );

    if (!cell)
    {
        console.log("No se encontró la celda:", comment.tableCellId);
        return;
    }

    const colors = {
        "morfosintaxis": "#F9E79F",
        "léxico-semántico": "#AED6F1",
        "pragmático-discursivo": "#A9DFBF",
        "accesibilidad": "#F5CBA7",
        "estadísticas": "#D7BDE2"
    };

    const color = colors[comment.type] || "#fff3a0";

    const text = cell.dataset.analysisText || "";

    const start = comment.localIndex;
    const end = start + comment.length;

    if (start < 0 || start >= text.length) {
        console.log("Posición inválida:", {
            text,
            start,
            end,
            comment
        });
        return;
    }

    const walker = document.createTreeWalker(
        cell,
        NodeFilter.SHOW_TEXT
    );

    let currentPosition = 0;
    let node;

    while (node = walker.nextNode()) {
        if (node.parentElement?.dataset.tableHighlight === "true") {
            currentPosition += node.textContent.length;
            continue;
        }

        const nodeStart = currentPosition;
        const nodeEnd = currentPosition + node.textContent.length;

        if (end > nodeStart && start < nodeEnd) {

            const localStart = Math.max(0, start - nodeStart);
            const localEnd = Math.min(
                node.textContent.length,
                end - nodeStart
            );

            if (localStart >= localEnd) {
                currentPosition = nodeEnd;
                continue;
            }

            const range = document.createRange();

            range.setStart(node, localStart);
            range.setEnd(node, localEnd);

            const span = document.createElement("span");
            span.style.backgroundColor = color;
            span.dataset.tableHighlight ="true";

            range.surroundContents(span);
        }

        currentPosition = nodeEnd;
    }
}

function findTextNodeAtOffset(container, offset) {

    const walker = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT
    );

    let currentOffset = 0;

    while (walker.nextNode()) {

        const node = walker.currentNode;
        const length = node.textContent.length;

        if (offset >= currentOffset &&
            offset <= currentOffset + length) {

            return node;
        }

        currentOffset += length;
    }

    return null;
}

/*
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
 */


// Párrafos que han cambiado
function getChangedParagraphs() {
    const paragraphs = quill.root.querySelectorAll(BLOCK_SELECTOR);
    let changes = [];
    let visibleIndex = 1;
    paragraphs.forEach(p => {
        const text = p.textContent.replace(/\u200B/g, "").trim();
        if (!text) return;
        const previous = lastAnalyzedParagraphs[visibleIndex];
        const current = {
            text,
            tag: p.tagName
        };

        if (!previous || previous.text !== current.text || previous.tag !== current.tag) {
            changes.push({index: visibleIndex, text: text, node: p});
        }
        visibleIndex++;
    });
    return changes;
}

function updateProgress(current, total, mode="paragraph") {
    const bar = document.getElementById("progressBar");
    const text = document.getElementById("progressText");
    const message = document.getElementById("loadingMessage");

    const totalSteps = total + 1;

    const percent = Math.round((current) / (totalSteps) * 100);

    if (mode === "paragraph"){
        const paragraphNumber = Math.min(current+1, total);
        message.textContent = `Analizando párrafo ${paragraphNumber} de ${total}...`;
    } else {
        message.textContent = "Analizando texto completo...";
    }

    bar.style.width = `${percent}%`;
    text.textContent = `${percent}%`; }

function resetProgress() {
    document.getElementById("progressBar").style.width = "0%";
    document.getElementById("progressText").textContent = "0%";
    document.getElementById("loadingMessage").textContent =
        "Analizando texto completo...";
}

function buildComment(item, paragraphText, paragraphIndex, paragraphstart){
    return {
        id: item.id,
        text: item.text,
        paragraphStart: paragraphstart,
        index: item.start,
        localIndex: item.start - paragraphstart,
        length: item.end - item.start,
        description: item.description,
        error: item.error,
        original: item.original,
        type: item.type,
        suggestion: item.suggestion,
        //mode: "paragraph",
        texto: paragraphText,
        paragraph: paragraphIndex,
        name: item.name,
        oracion: item.oracion,
        palabra: item.palabra,
        inicioFrase: item.inicioFrase
    };
}

function getUpdatedIndex(comment) {
    const paragraphs = quill.root.querySelectorAll(BLOCK_SELECTOR);

    let visibleIndex = 1;

    for (let p of paragraphs) {
        const text = p.textContent.replace(/\u200B/g, "").trim();
        if (!text) continue;

        if (visibleIndex === comment.paragraph) {
            const blot = Quill.find(p);
            const start = quill.getIndex(blot);

            // ✅ 1. Intento robusto por texto original
            if (comment.original) {
                const idx = text.indexOf(comment.original);
                if (idx !== -1) {
                    return start + idx;
                }
            }

            // ✅ 2. Fallback por posición relativa
            if (comment.localIndex != null) {
                return start + comment.localIndex;
            }
        }

        visibleIndex++;
    }

    return null;
}


function getUpdatedSentenceIndex(comment) {
    const paragraphs = quill.root.querySelectorAll(BLOCK_SELECTOR    );

    let visibleIndex = 1;

    for (const p of paragraphs) {
        const text = p.textContent.replace(/\u200B/g, "").trim();
        if (!text) continue;

        if (visibleIndex === comment.paragraph) {
            const blot = Quill.find(p);
            const paragraphStart = quill.getIndex(blot);

            return paragraphStart + (comment.inicioFrase - comment.paragraphStart);
        }

        visibleIndex++;
    }

    return null;
}
function showIntentionalityModal() {

    const modal = document.getElementById("intentionalityModal");
    const container = document.getElementById("intentionalityOptions");

    container.innerHTML = "";

    AVAILABLE_INTENTIONS.forEach(option => {

        const label = document.createElement("label");
        label.className = "intent-option";

        const checkbox = document.createElement("input");

        checkbox.type = "checkbox";
        checkbox.value = option.value;

        checkbox.checked = textIntentions.includes(option.value);

        label.appendChild(checkbox);
        label.append(" " + option.label);

        container.appendChild(label);
    });

    modal.style.display = "block";
}

function saveIntentionality() {

    const selected = [...document.querySelectorAll(
        "#intentionalityOptions input:checked"
    )].map(cb => cb.value);

    if (selected.length === 0) {
        alert("Debes seleccionar al menos una intención.");
        return;
    }

    textIntentions = selected;
    return selected;
}

document
    .getElementById("saveAndAnalyzeIntentionalityBtn")
    .addEventListener("click", async() => {
        const result = saveIntentionality();
        if (!result) return;
        closeIntentionalityModal();
        setMode("feedback");
        await addCommentText();
    });
document
    .getElementById("saveIntentionalityBtn")
    .addEventListener("click", async() => {
        const result = saveIntentionality();
        if (!result) return;
        closeIntentionalityModal();
        setMode("feedback");
    });

document.getElementById("cancelIntentionalityBtn").addEventListener("click", () => {
    closeIntentionalityModal();
});

function closeIntentionalityModal() {
    document.getElementById("intentionalityModal").style.display = "none";
}

/*
async function handleHighlightedWordClick(event) {
// Era de cuando se generaba la sugerencia al hacer click en una palabra
    if (activeType == null) {
        console.log("Sale: activeCommentId es null");
        return;
    }

    const selection = document.getSelection();
    if (!selection.rangeCount) {
        console.log("Sale: no hay selección");
        return;
    }

    const range = selection.getRangeAt(0);
    const blot = Quill.find(event.target, true);
    if (!blot) {
        console.log("Sale: blot es null", range.startContainer);
        return;
    }
    const index = quill.getIndex(blot) + range.startOffset;

    console.log("índice clic:", index);
    comments.forEach(c => {
    if (c.name !== activeType) return;

    const start = getUpdatedIndex(c);
    const end = start + c.length +1;



    console.log({
        palabra: c.palabra,
        start,
        end,
        index,
        dentro: index >= start && index <= end
    });
});
    const comment = comments.find( c => {
        if (c.name!==activeType) return false;
        if (c.suggestion!=="true") return false;
        const start = getUpdatedIndex(c);
        const end = start + c.length;
        return index >= start && index < end;
    }
    );
    if (!comment) return;

    currentModalComment = comment;
    originalText.innerHTML = highlightOriginalSentence(comment.oracion, comment.palabra);
    suggestedTextArea.value = "";

    modal.style.display = "block";
    const criterion = document.getElementById("suggestionCriterion");
    criterion.textContent = `(${comment.text})`;
    console.log(comment);
    await generateSuggestion(comment);
}

 */

async function handleContextMenu(event) {
    if (activeType == null) {
        console.log("Sale: activeCommentId es null");
        return;
    }

    const selection = document.getSelection();
    if (!selection.rangeCount) {
        console.log("Sale: no hay selección");
        return;
    }

    const range = selection.getRangeAt(0);
    const blot = Quill.find(event.target, true);
    if (!blot) {
        console.log("Sale: blot es null", range.startContainer);
        return;
    }
    const index = quill.getIndex(blot) + range.startOffset;

    const comment = comments.find( c => {
        if (c.name!==activeType) return false;
        if (c.suggestion!=="true") return false;
        const start = getUpdatedIndex(c);
        const end = start + c.length;
        return index >= start && index < end;
    }
    );
    if (!comment) return;


    // Criterios que permiten sugerencia
    const criteriosConSugerencia = [
        "baul",
        "lexFrec",
        "extranjerismo",
        "ambiguo",
        "tecnicismo",
        "coloquialismo",
        "vulgarismo",
        "largas"
    ];

    if (!criteriosConSugerencia.includes(comment.name)) {
        return;
    }

    event.preventDefault();

    selectedComment = comment;

    menu.style.left = event.pageX + "px";
    menu.style.top = event.pageY + "px";
    menu.style.display = "block";
}

generateOption.addEventListener("click", async () => {
    if (!selectedComment)
        return;

    currentModalComment = selectedComment;

    modal.style.display = "block";

    document.getElementById("suggestionCriterion").textContent =
        `(${selectedComment.text})`;

    menu.style.display = "none";

    suggestedTextArea.innerHTML = "";
    originalTextArea.textContent = selectedComment.oracion;

    await generateSuggestion(selectedComment);
});

document.addEventListener("click", () => {
    menu.style.display = "none";
})

// Para pintar las palabras cambiadas en las sugerencias
function escapeRegExp(text) {
    return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlightOriginalSentence(sentence, word) {
    return diffWords(original, suggested).original;
}
function highlightSuggestedSentence(original, suggested, oldWord) {
    return diffWords(original, suggested).suggested;
}

function diffWords(oldText, newText) {
    const oldWords = oldText.split(/\s+/);
    const newWords = newText.split(/\s+/);

    const m = oldWords.length;
    const n = newWords.length;

    const dp = Array.from({ length: m + 1 }, () =>
        Array(n + 1).fill(0)
    );

    for (let i = m - 1; i >= 0; i--) {
        for (let j = n - 1; j >= 0; j--) {
            if (oldWords[i] === newWords[j]) {
                dp[i][j] = dp[i + 1][j + 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1]);
            }
        }
    }

    const original = [];
    const suggested = [];

    let i = 0, j = 0;

    while (i < m && j < n) {

        if (oldWords[i] === newWords[j]) {
            original.push(oldWords[i]);
            suggested.push(newWords[j]);
            i++;
            j++;
        }
        else if (dp[i + 1][j] >= dp[i][j + 1]) {
            original.push(`<span class="original-word">${oldWords[i]}</span>`);
            i++;
        }
        else {
            suggested.push(`<span class="suggested-word">${newWords[j]}</span>`);
            j++;
        }
    }

    while (i < m) {
        original.push(`<span class="original-word">${oldWords[i]}</span>`);
        i++;
    }

    while (j < n) {
        suggested.push(`<span class="suggested-word">${newWords[j]}</span>`);
        j++;
    }

    return {
        original: original.join(" "),
        suggested: suggested.join(" ")
    };
}

// Para el botón que genera las tablas
async function generarTablaSeleccion() {

    const range = quill.getSelection();

    if (!range || range.length === 0) {
        alert("Selecciona el texto que quieres convertir en tabla.");
        return;
    }

    const textoSeleccionado = quill.getText(
        range.index,
        range.length
    ).trim();

    if (!textoSeleccionado) {
        alert("Selecciona un texto válido.");
        return;
    }


    const loadingOverlay = document.getElementById("tableLoadingOverlay");
    loadingOverlay.classList.add("active");

    try {

        const response = await fetch("/generar_tabla", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                texto: textoSeleccionado
            })
        });

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }

        const data = await response.json();


        if (data.success) {

            // Posición final de la selección
            const seleccionFin = range.index + range.length;

            // Obtener el último párrafo que forma parte de la selección
            const [ultimoParrafo] = quill.getLine(seleccionFin - 1);

            if (!ultimoParrafo) {
                return;
            }

            // Posición inicial del último párrafo
            const ultimoParrafoStart = quill.getIndex(ultimoParrafo);

            // Longitud del último párrafo
            const ultimoParrafoLength = ultimoParrafo.length();

            // Insertar justo al final del último párrafo,
            // antes del salto de línea de Quill
            const posicionTabla =
                ultimoParrafoStart + ultimoParrafoLength;

            insertingTable = true;

            // Insertar la tabla
            quill.insertEmbed(
                posicionTabla,
                'generatedTable',
                data.html,
                'user'
            );

            insertingTable = false;
            updateParagraphNumbers();

            //lastStructure = getDocumentAnalysisSignature();

            // Añadir salto de línea después de la tabla

            // Aquí decidiremos qué hacer con la tabla
        } else {
            alert(data.message);
            console.log("Razón:", data.reason);
        }

    } catch (error) {
        console.error("Error generando tabla:", error);
        alert("Ha ocurrido un error al generar la tabla.");
    } finally {
        loadingOverlay.classList.remove("active");
    }
}
document.getElementById("generateTableBtn")
    .addEventListener("click", generarTablaSeleccion);

function getTextoParaAnalisis() {
    const clone = quill.root.cloneNode(true);

    // Convertir cada tabla en su contenido textual
    clone.querySelectorAll(".generated-table").forEach(tableWrapper => {

        const table = tableWrapper.querySelector("table");

        if (!table) {
            tableWrapper.remove();
            return;
        }

        const partes = [];

        // Caption
        const caption = table.querySelector("caption");
        if (caption) {
            partes.push(caption.textContent.trim());
        }

        // Filas
        table.querySelectorAll("tr").forEach(row => {
            const celdas = Array.from(
                row.querySelectorAll("th, td")
            ).map(cell => cell.textContent.trim());

            if (celdas.length > 0) {
                partes.push(celdas.join(" "));
            }
        });

        // Sustituir el wrapper de la tabla por su texto
        const textoTabla = document.createTextNode(
            partes.join("\n")
        );

        tableWrapper.replaceWith(textoTabla);
    });

    return clone.textContent
        .replace(/\u200B/g, "")
        .trim();
}

function getDocumentAnalysisSignature() {
    return getTextoParaAnalisis();
}

function renderSpellcheck(matches) {
    const overlay = document.getElementById("spellcheckOverlay");

    if (!overlay) return;

    overlay.innerHTML = "";

    const editorRect = quill.root.getBoundingClientRect();
    const overlayRect = overlay.getBoundingClientRect();

    matches.forEach(match => {
        const bounds = quill.getBounds(
            match.offset,
            match.length
        );

        const error = document.createElement("div");

        error.classList.add(
            "spell-error",
            match.tipo === "ortografia"
                ? "spell-ortografia"
                : "spell-puntuacion"
        );

        // Convertimos las coordenadas de Quill
        // a coordenadas relativas al overlay
        error.style.left =
            `${editorRect.left - overlayRect.left + bounds.left}px`;

        error.style.top =
            `${editorRect.top - overlayRect.top + bounds.top + bounds.height - 3}px`;

        error.style.width =
            `${Math.max(bounds.width, 4)}px`;

        overlay.appendChild(error);
    });
}

function clearSpellcheck() {
    const overlay = document.getElementById("spellcheckOverlay");

    if (overlay) {
        overlay.innerHTML = "";
    }

    spellcheckMatches = [];
}

async function checkSpelling() {
    const texto = quill.getText();

    if (!texto.trim()) {
        clearSpellcheck();
        return;
    }

    try {
        const response = await fetch("/spellcheck", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                texto: texto
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error("Error /spellcheck:", {
                status: response.status,
                statusText: response.statusText,
                body: errorText
            });
            return;
        }

        const data = await response.json();

        spellcheckMatches = data.matches || [];
        renderSpellcheck(spellcheckMatches);

        renderSpellcheck(data.matches || []);

    } catch (error) {
        console.error("Error en el corrector:", error);
    }
}

/*

async function analyzeGeneratedTable(table, tableIndex) {

    table.dataset.tableIndex = tableIndex;

    // -2 = primera tabla, -3 = segunda, etc.
    const tableParagraph = -(tableIndex + 2);

    const cells = Array.from(
        table.querySelectorAll("th, td")
    );

    const tableComments = [];

    for (let cellIndex = 0; cellIndex < cells.length; cellIndex++) {

        const cell = cells[cellIndex];

        const text = cell.innerText
            .replace(/\u200B/g, "")
            .trim();

        if (!text) continue;

        const tableCellId =
            `table-${tableIndex}-cell-${cellIndex}`;

        cell.dataset.tableCellId = tableCellId;
        cell.dataset.analysisText = text;

        const data = await analyzeSingleParagraph(
            text,
            0
        );

        data.forEach(item => {

            const comment = buildComment(
                item,
                text,
                tableParagraph,  // -2, -3, -4...
                0
            );

            comment.table = true;
            comment.tableIndex = tableIndex;
            comment.cellIndex = cellIndex;
            comment.tableCellId = tableCellId;

            comment.localIndex = item.start;
            comment.length = item.end - item.start;

            tableComments.push(comment);
        });
    }

    return tableComments;
}

function clearTableHighlights() {

    const tables = quill.root.querySelectorAll(".generated-table");

    tables.forEach(table => {

        const spans = table.querySelectorAll(
            'span[data-table-highlight="true"]'
        );

        spans.forEach(span => {
            span.replaceWith(...span.childNodes);
        });
    });
}

 */