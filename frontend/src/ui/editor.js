import { revisarTexto } from '../api/spelling.js';

const text      = document.querySelector("#user-input");
const buttonText = document.querySelector("#send-btn");
const highlight = document.querySelector("#editor-highlight");

let debounceTimer   = null;
let erroresActuales = [];

export function getErroresActuales() {
    return erroresActuales;
}

export function resetTextarea() {
    clearTimeout(debounceTimer);
    text.value = '';
    text.style.height = '40px';
    highlight.innerHTML = '';
    highlight.style.height = '40px';
    buttonText.disabled = true;
    erroresActuales = [];
}

function mostrarErrores(texto, errores) {
    erroresActuales = errores || [];
    let textoAProcesar = texto.endsWith('\n') ? texto + ' ' : texto;
    if (!errores || errores.length === 0) {
        highlight.textContent = textoAProcesar;
        return;
    }

    errores.sort((a, b) => b.offset - a.offset);

    let resultado = textoAProcesar;
    errores.forEach(error => {
        const inicio   = error.offset;
        const final    = inicio + error.error_length;
        const palabra  = resultado.slice(inicio, final);
        const antes    = resultado.slice(0, inicio);
        const despues  = resultado.slice(final);
        const sugerencia = error.replacements.length > 0 ? error.replacements[0] : 'Sin sugerencias';
        resultado = `${antes}<span class="error" data-sugerencia="${sugerencia}">${palabra}</span>${despues}`;
    });

    highlight.innerHTML = resultado;
}

text.addEventListener("input", () => {
    if (text.value.trim().length > 0) {
        buttonText.disabled = false;
    } else {
        buttonText.disabled = true;
        erroresActuales = [];
    }
    text.style.height = "40px";
    const nuevoAlto = text.value === '' ? "40px" : text.scrollHeight + "px";
    text.style.height = nuevoAlto;
    highlight.style.height = nuevoAlto;
    highlight.scrollTop = text.scrollTop;

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
        const errores = await revisarTexto(text.value);
        mostrarErrores(text.value, errores);
        highlight.scrollTop = text.scrollTop;
    }, 400);
});

text.addEventListener("scroll", () => {
    highlight.scrollTop = text.scrollTop;
});

text.addEventListener("keydown", tecla => {
    if (tecla.key === "Enter") {
        if (tecla.shiftKey) {
            highlight.scrollTop = text.scrollTop;
        } else {
            tecla.preventDefault();
            buttonText.click();
        }
    }
});

highlight.addEventListener("click", () => {
    text.focus();
});

// Tooltip de sugerencias sobre el textarea
const tooltip = document.createElement('div');
tooltip.className = 'tooltip-sugerencia';
document.body.appendChild(tooltip);

text.addEventListener('mousemove', e => {
    if (erroresActuales.length === 0) {
        tooltip.style.opacity = '0';
        return;
    }

    const rect = text.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top + text.scrollTop;

    const style      = window.getComputedStyle(text);
    const lineHeight = parseFloat(style.lineHeight);
    const paddingTop = parseFloat(style.paddingTop);
    const paddingLeft = parseFloat(style.paddingLeft);

    const lineIndex = Math.floor((y - paddingTop) / lineHeight);
    const lines     = text.value.split('\n');

    let charIndex = 0;
    for (let i = 0; i < lineIndex && i < lines.length; i++) {
        charIndex += lines[i].length + 1;
    }

    if (lineIndex < lines.length) {
        const canvas = document.createElement('canvas');
        const ctx    = canvas.getContext('2d');
        ctx.font     = `${style.fontSize} ${style.fontFamily}`;
        const lineText = lines[lineIndex] || '';
        let col = 0;
        for (let i = 0; i <= lineText.length; i++) {
            if (ctx.measureText(lineText.slice(0, i)).width >= x - paddingLeft) break;
            col = i;
        }
        charIndex += col;
    }

    const error = erroresActuales.find(err =>
        charIndex >= err.offset && charIndex < err.offset + err.error_length
    );

    if (error && error.replacements.length > 0) {
        tooltip.textContent = `Sugerencias: ${error.replacements.slice(0, 5).join(', ')}`;
        tooltip.style.left  = e.clientX + 10 + 'px';
        tooltip.style.top   = e.clientY + 15 + 'px';
        tooltip.style.opacity = '1';
    } else {
        tooltip.style.opacity = '0';
    }
});

text.addEventListener('mouseleave', () => {
    tooltip.style.opacity = '0';
});
