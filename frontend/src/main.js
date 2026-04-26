import { respuestaIA } from './api/spelling';
import './styles/main.css';

const text = document.querySelector("#user-input"),
    buttonText = document.querySelector("#send-btn"),
    chat  = document.querySelector("#chat-messages"),
    bienvenida = document.querySelector("#welcome-screen"),
    chatDisplay = document.querySelector("#chat-display"),
    icono = document.querySelector(".editor__send-icon");

let esperandoRespuesta = false,
    cancelado = false;

text.addEventListener("input", () => {
    if(text.value.trim().length > 0) {
        buttonText.disabled = false;
    } else {
        buttonText.disabled = true;
    }
    text.style.height = "auto";
    text.style.height = text.scrollHeight + "px";
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
        if(tecla.shiftKey) {}
        else {
            tecla.preventDefault();
            buttonText.click();
        }
    }
} );

