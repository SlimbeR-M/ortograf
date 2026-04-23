import './styles/main.css';

const text = document.querySelector("#user-input"),
    buttonText = document.querySelector("#send-btn"),
    chat  = document.querySelector("#chat-messages"),
    bienvenida = document.querySelector("#welcome-screen"),
    chatDisplay = document.querySelector("#chat-display");

text.addEventListener("input", () => {
    if(text.value.trim().length > 0) {
        buttonText.disabled = false;
    } else {
        buttonText.disabled = true;
    }
});

buttonText.addEventListener("click", () => {
    let texto = text.value;
    const mensaje = document.createElement("div");
    mensaje.className = "message message--user";
    mensaje.innerHTML = `<p class = "message__bubble">${texto}</p>`;
    chat.appendChild(mensaje);
    bienvenida.style.display = "none";
    text.value = '';
    buttonText.disabled = true;
    respuestaIA();
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

const respuestaIA = ()=> {
    const mensajeIA= document.createElement("div");
    mensajeIA.className = "message__typing";
    mensajeIA.innerHTML = '<span class="message__typing-dot"></span>'.repeat(3);
    chat.appendChild(mensajeIA);
    text.disabled = true;
    chatDisplay.scrollTo({ top: chatDisplay.scrollHeight, behavior: 'smooth' });
    setTimeout(() => {
        mensajeIA.innerHTML = "";
        mensajeIA.className = "message message--ai";
        mensajeIA.innerHTML = '<p class = "message__bubble">Ta bien</p>';
        chatDisplay.scrollTo({ top: chatDisplay.scrollHeight, behavior: 'smooth' });
        text.disabled = false;
    }, 3000);
}