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
    debounceTimer = null;

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

    //indicador de pensamiento
    const typing= document.createElement("div");
    typing.className = "message__typing";
    typing.innerHTML = '<span class="message__typing-dot"></span>'.repeat(3);
    chat.appendChild(typing);
    text.disabled = true;
    chatDisplay.scrollTo({ top: chatDisplay.scrollHeight, behavior: 'smooth' });

    icono.src = "/src/assets/cancelar.png";
    buttonText.disabled = false;
    const respuesta = await respuestaIA(texto)
    if(cancelado) {
        typing.remove();
        esperandoRespuesta = false;
        text.disabled = false;
        return;
    }


    //mostrar respuesta
    typing.className = "message message--ai";
    typing.innerHTML = `<p class = "message__bubble">${respuesta}</p>`;
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
        
        resultado = `${antes}<span class="error">${palabra}</span>${despues}`
    } )

    highlight.innerHTML = resultado;

}