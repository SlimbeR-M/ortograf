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
    chatDisplay.scrollTo({ top: chatDisplay.scrollHeight, behavior: 'smooth' });
});

text.addEventListener("keydown", (tecla) => {
    if(tecla.key === "Enter") {
        if(tecla.shiftKey) {
            /* Hace un salto xd */
        }
        else {
            tecla.preventDefault();
            buttonText.click();
        }
    }
} );