import { respuestaIA, revisarTexto } from './api/spelling';
import './styles/main.css';

const text = document.querySelector("#user-input"),
    buttonText = document.querySelector("#send-btn"),
    chat  = document.querySelector("#chat-messages"),
    bienvenida = document.querySelector("#welcome-screen"),
    chatDisplay = document.querySelector("#chat-display"),
    icono = document.querySelector(".editor__send-icon"),
    highlight = document.querySelector("#editor-highlight");

let esperandoRespuesta = false,
    cancelado = false,
    debounceTimer = null,
    erroresActuales = [];

text.addEventListener("input", () => {
    if(text.value.trim().length > 0) {
        buttonText.disabled = false;
    } else {
        buttonText.disabled = true;
    }
    text.style.height = "auto";
    const nuevoAlto = text.scrollHeight + "px";
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

buttonText.addEventListener("click", async() => {
    if(esperandoRespuesta) {
        cancelado = true;
        esperandoRespuesta = false;
        icono.src = "/src/assets/enviar.png";
        buttonText.disabled = true;
        text.disabled = false;
        return;
    }

    cancelado = false;
    esperandoRespuesta = true;

    // Mensaje del usuario
    let texto = text.value;
    const mensaje = document.createElement("div");
    mensaje.className = "message message--user";
    mensaje.innerHTML = `<p class = "message__bubble">${texto}</p>`;
    chat.appendChild(mensaje);

    //Limpiar y desabilitar
    bienvenida.style.display = "none";
    text.value = '';
    text.style.height = "auto";
    highlight.innerHTML = '';          
    highlight.style.height = "auto"; 
    erroresActuales = []; 

    //indicador de pensamiento
    const typing= document.createElement("div");
    typing.className = "message__typing";
    typing.innerHTML = '<span class="message__typing-dot"></span>'.repeat(3);
    chat.appendChild(typing);
    text.disabled = true;
    chatDisplay.scrollTo({ top: chatDisplay.scrollHeight, behavior: 'smooth' });

    icono.src = "/src/assets/cancelar.png";
    buttonText.disabled = false;
    const datos = await respuestaIA(texto)
    if(cancelado) {
        typing.remove();
        esperandoRespuesta = false;
        text.disabled = false;
        return;
    }

    // Construir HTML de la respuesta
    let html = `<p class="message__bubble">${datos.texto_corregido.replace(/\n/g, '<br>')}</p>`

    // Score del usuario
    if (datos.score) {
        const color = datos.score.porcentaje >= 75 ? '#4caf50' : datos.score.porcentaje >= 50 ? '#ff9800' : '#f44336'
        html += `<div class="message__score" style="color:${color}">
            <span>✏️ Escritura: ${datos.score.porcentaje}% — ${datos.score.nivel}</span>
        </div>`
    }

    // Cambios realizados
    if (datos.cambios && datos.cambios.length > 0) {
        html += `<div class="message__cambios">`
        datos.cambios.forEach(c => {
            if (c.tipo === 'reemplazo') {
                html += `<span class="cambio-tag">📝 ${c.razon}</span>`
            }
        })
        html += `</div>`
    }

    //mostrar respuesta
    typing.className = "message message--ai";
    typing.innerHTML = html;
    chatDisplay.scrollTo({ top: chatDisplay.scrollHeight, behavior: 'smooth' });
    text.disabled = false;
    esperandoRespuesta = false;
    buttonText.disabled = true;
    icono.src = "/src/assets/enviar.png";


});

text.addEventListener("keydown", (tecla) => {
    if(tecla.key === "Enter") {
        if(tecla.shiftKey) { highlight.scrollTop = text.scrollTop;}
        else {
            tecla.preventDefault();
            buttonText.click();
        }
    }
} );

const mostrarErrores = (texto, errores) => {
    erroresActuales = errores || [];
    let textoAProcesar = texto.endsWith('\n') ? texto + ' ' : texto;
    if(!errores || errores.length === 0) {
        highlight.textContent = textoAProcesar;
        return;
    }

    errores.sort((a,b) => b.offset - a.offset);

    let resultado = textoAProcesar;

    errores.forEach((error) => {
        let inicio = error.offset,
            final = inicio + error.error_length,
            palabra = resultado.slice(inicio, final),
            antes = resultado.slice(0, inicio),
            despues = resultado.slice(final);
        
        const sugerencia = error.replacements.length > 0 ? error.replacements[0] : 'Sin sugerencias';
        resultado = `${antes}<span class="error" data-sugerencia="${sugerencia}">${palabra}</span>${despues}`
    } )

    highlight.innerHTML = resultado;

}

highlight.addEventListener("click", () => {
    text.focus(); 
});



const tooltip = document.createElement('div');
tooltip.className = 'tooltip-sugerencia';
document.body.appendChild(tooltip);

text.addEventListener('mousemove', (e) => {
    if(erroresActuales.length === 0) {
        tooltip.style.opacity = '0';
        return;
    }

    const rect = text.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top + text.scrollTop;
    
    const style = window.getComputedStyle(text);
    const lineHeight = parseFloat(style.lineHeight);
    const paddingTop = parseFloat(style.paddingTop);
    const paddingLeft = parseFloat(style.paddingLeft);
    
    const lineIndex = Math.floor((y - paddingTop) / lineHeight);
    const lines = text.value.split('\n');
    
    let charIndex = 0;
    for(let i = 0; i < lineIndex && i < lines.length; i++) {
        charIndex += lines[i].length + 1;
    }
    
    if(lineIndex < lines.length) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.font = `${style.fontSize} ${style.fontFamily}`;
        const lineText = lines[lineIndex] || '';
        let col = 0;
        for(let i = 0; i <= lineText.length; i++) {
            if(ctx.measureText(lineText.slice(0, i)).width >= x - paddingLeft) break;
            col = i;
        }
        charIndex += col;
    }
    
    const error = erroresActuales.find(err =>
        charIndex >= err.offset && charIndex < err.offset + err.error_length
    );
    
    if(error && error.replacements.length > 0) {
        tooltip.textContent = `Sugerencias: ${error.replacements.slice(0, 5).join(', ')}`;
        tooltip.style.left = e.clientX + 10 + 'px';
        tooltip.style.top = e.clientY + 15 + 'px';
        tooltip.style.opacity = '1';
    } else {
        tooltip.style.opacity = '0';
    }
});

text.addEventListener('mouseleave', () => {
    tooltip.style.opacity = '0';
});