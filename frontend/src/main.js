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
    mensaje.innerHTML = `<p class="message__bubble">${texto.replace(/\n/g, '<br>')}</p>`;
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

    //Mostrar error en burbuja de usuario
    if (datos.cambios && datos.cambios.length > 0) {
    let textoMarcado = texto.replace(/\n/g, '<br>')
    datos.cambios.forEach(c => {
        if (c.original && c.original.trim()) {
            textoMarcado = textoMarcado.replace(
                c.original,
                `<span class="error-highlight">${c.original}</span>`
            )
        }
    })
    mensaje.querySelector('.message__bubble').innerHTML = textoMarcado
}

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

    // Guardar en historial si hay sesión
    // Guardar en historial si hay sesión
    if (usuarioActual) {
        document.dispatchEvent(new CustomEvent("chatMensajeGuardado", {
            detail: { 
                usuario: mensaje.querySelector('.message__bubble').innerHTML,
                ia: html
            }
        }));
    }


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


// ─── AUTH MODAL ───────────────────────────────────────────────────────────────

const profileBtn = document.querySelector("#profile-btn");
const profileInitial = document.querySelector("#profile-initial");
const authOverlay = document.querySelector("#auth-overlay");
const authCloseBtn = document.querySelector("#auth-close-btn");
const tabLogin = document.querySelector("#tab-login");
const tabRegister = document.querySelector("#tab-register");
const formLogin = document.querySelector("#form-login");
const formRegister = document.querySelector("#form-register");
const formForgot = document.querySelector("#form-forgot");
const loginError = document.querySelector("#login-error");
const registerError = document.querySelector("#register-error");
const forgotError = document.querySelector("#forgot-error");

let usuarioActual = null;

// Abrir modal al hacer clic en el botón de perfil
profileBtn.addEventListener("click", () => {
    if (usuarioActual) {
        cerrarSesion();
    } else {
        authOverlay.removeAttribute("hidden");
    }
});

// Cerrar modal
authCloseBtn.addEventListener("click", () => {
    authOverlay.setAttribute("hidden", "");
    limpiarErrores();
});

authOverlay.addEventListener("click", (e) => {
    if (e.target === authOverlay) {
        authOverlay.setAttribute("hidden", "");
        limpiarErrores();
    }
});

// Tabs
tabLogin.addEventListener("click", () => {
    tabLogin.classList.add("auth-modal__tab--active");
    tabRegister.classList.remove("auth-modal__tab--active");
    formLogin.removeAttribute("hidden");
    formRegister.setAttribute("hidden", "");
    formForgot.setAttribute("hidden", "");
    limpiarErrores();
});

tabRegister.addEventListener("click", () => {
    tabRegister.classList.add("auth-modal__tab--active");
    tabLogin.classList.remove("auth-modal__tab--active");
    formRegister.removeAttribute("hidden");
    formLogin.setAttribute("hidden", "");
    formForgot.setAttribute("hidden", "");
    limpiarErrores();
});

// Login
document.querySelector("#login-submit").addEventListener("click", async () => {
    const email = document.querySelector("#login-email").value.trim();
    const password = document.querySelector("#login-password").value;

    if (!email || !password) {
        mostrarError(loginError, "Completa todos los campos.");
        return;
    }

    try {
        const res = await fetch("http://localhost:8000/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (!res.ok) {
            mostrarError(loginError, data.detail || "Credenciales incorrectas.");
            return;
        }

        iniciarSesion(data);
    } catch {
        mostrarError(loginError, "Error al conectar con el servidor.");
    }
});

// Registro
document.querySelector("#register-submit").addEventListener("click", async () => {
    const nombre = document.querySelector("#register-name").value.trim();
    const email = document.querySelector("#register-email").value.trim();
    const password = document.querySelector("#register-password").value;

    if (!nombre || !email || !password) {
        mostrarError(registerError, "Completa todos los campos.");
        return;
    }

    if (password.length < 6) {
        mostrarError(registerError, "La contraseña debe tener al menos 6 caracteres.");
        return;
    }

    try {
        const res = await fetch("http://localhost:8000/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nombre, email, password })
        });
        const data = await res.json();

        if (!res.ok) {
            mostrarError(registerError, data.detail || "Error al registrarse.");
            return;
        }

        iniciarSesion(data);
    } catch {
        mostrarError(registerError, "Error al conectar con el servidor.");
    }
});

// Recuperar contraseña
document.querySelector("#forgot-btn").addEventListener("click", () => {
    formLogin.setAttribute("hidden", "");
    formForgot.removeAttribute("hidden");
    limpiarErrores();
});

document.querySelector("#back-to-login").addEventListener("click", () => {
    formForgot.setAttribute("hidden", "");
    formLogin.removeAttribute("hidden");
    limpiarErrores();
});

document.querySelector("#forgot-submit").addEventListener("click", async () => {
    const email = document.querySelector("#forgot-email").value.trim();
    const password = document.querySelector("#forgot-password").value;
    const password2 = document.querySelector("#forgot-password2").value;

    if (!email || !password || !password2) {
        mostrarError(forgotError, "Completa todos los campos.");
        return;
    }

    if (password !== password2) {
        mostrarError(forgotError, "Las contraseñas no coinciden.");
        return;
    }

    if (password.length < 6) {
        mostrarError(forgotError, "La contraseña debe tener al menos 6 caracteres.");
        return;
    }

    try {
        const res = await fetch("http://localhost:8000/auth/reset-password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, nueva_password: password })
        });
        const data = await res.json();

        if (!res.ok) {
            mostrarError(forgotError, data.detail || "No se encontró esa cuenta.");
            return;
        }

        formForgot.setAttribute("hidden", "");
        formLogin.removeAttribute("hidden");
        mostrarError(loginError, "✅ Contraseña actualizada. Inicia sesión.");
        loginError.style.color = "var(--color-success)";
    } catch {
        mostrarError(forgotError, "Error al conectar con el servidor.");
    }
});

// ─── Funciones de sesión ─────────────────────────────────────────────────────

function iniciarSesion(data) {
    usuarioActual = data.usuario;
    localStorage.setItem("token", data.token);
    localStorage.setItem("usuario", JSON.stringify(data.usuario));
    actualizarBotonPerfil();
    authOverlay.setAttribute("hidden", "");
    limpiarErrores();
}

function cerrarSesion() {
    usuarioActual = null;
    localStorage.removeItem("token");
    localStorage.removeItem("usuario");
    actualizarBotonPerfil();
}

function actualizarBotonPerfil() {
    if (usuarioActual) {
        profileInitial.textContent = usuarioActual.nombre[0].toUpperCase();
        profileBtn.style.backgroundColor = "var(--color-accent)";
        profileBtn.style.color = "#fff";
    } else {
        profileInitial.textContent = "?";
        profileBtn.style.backgroundColor = "";
        profileBtn.style.color = "";
    }
}

function mostrarError(el, msg) {
    el.textContent = msg;
    el.removeAttribute("hidden");
}

function limpiarErrores() {
    [loginError, registerError, forgotError].forEach(el => {
        el.setAttribute("hidden", "");
        el.textContent = "";
        el.style.color = "";
    });
}

// Restaurar sesión al cargar
const tokenGuardado = localStorage.getItem("token");
const usuarioGuardado = localStorage.getItem("usuario");
if (tokenGuardado && usuarioGuardado) {
    usuarioActual = JSON.parse(usuarioGuardado);
    actualizarBotonPerfil();
}


// ─── HISTORIAL DE CHATS ───────────────────────────────────────────────────────

const chatHistoryList = document.querySelector("#chat-history-list");
const newChatBtn = document.querySelector("#new-chat-btn");

let chatActualId = null;
let mensajesActuales = []; // {rol, contenido}

function getToken() {
    return localStorage.getItem("token");
}

// Cargar historial del sidebar
async function cargarHistorial() {
    if (!usuarioActual) {
        chatHistoryList.innerHTML = '';
        return;
    }

    try {
        const res = await fetch("http://localhost:8000/chats/", {
            headers: { "Authorization": `Bearer ${getToken()}` }
        });
        const chats = await res.json();
        renderHistorial(chats);
    } catch {
        console.error("Error cargando historial");
    }
}

function renderHistorial(chats) {
    chatHistoryList.innerHTML = '';
    chats.forEach(c => {
        const li = document.createElement("li");
        li.className = "sidebar__history-item";
        li.dataset.id = c.id;
        li.innerHTML = `
            <button class="sidebar__history-btn" type="button">
                <span class="sidebar__history-title">${c.titulo}</span>
            </button>
            <button class="sidebar__history-delete" data-id="${c.id}" type="button" aria-label="Eliminar chat">✕</button>
        `;
        li.querySelector(".sidebar__history-btn").addEventListener("click", () => cargarChat(c.id));
        li.querySelector(".sidebar__history-delete").addEventListener("click", (e) => {
            e.stopPropagation();
            eliminarChat(c.id);
        });
        chatHistoryList.appendChild(li);
    });
}

// Cargar mensajes de un chat
async function cargarChat(id) {
    try {
        const res = await fetch(`http://localhost:8000/chats/${id}`, {
            headers: { "Authorization": `Bearer ${getToken()}` }
        });
        const data = await res.json();

        chatActualId = id;
        mensajesActuales = data.mensajes;

        chat.innerHTML = '';
        bienvenida.style.display = "none";

        data.mensajes.forEach(m => {
            const div = document.createElement("div");
            div.className = `message message--${m.rol === "usuario" ? "user" : "ai"}`;
            
            if (m.rol === "usuario") {
                div.innerHTML = `<p class="message__bubble">${m.contenido}</p>`;
            } else {
                // La IA guarda el HTML completo con score y cambios
                div.innerHTML = m.contenido;
            }
            
            chat.appendChild(div);
        });

        chatDisplay.scrollTo({ top: chatDisplay.scrollHeight, behavior: 'smooth' });
    } catch {
        console.error("Error cargando chat");
    }
}

// Guardar chat actual
async function guardarChat(textoUsuario, textoIA) {
    if (!usuarioActual) return;

    mensajesActuales.push({ rol: "usuario", contenido: textoUsuario });
    mensajesActuales.push({ rol: "ia", contenido: textoIA });

    const titulo = textoUsuario.replace(/<[^>]*>/g, '').slice(0, 40) || "Nuevo chat";

    if (chatActualId) {
        // Chat ya existe — actualizar (por ahora recrear)
        await eliminarChat(chatActualId, false);
    }

    try {
        const res = await fetch("http://localhost:8000/chats/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${getToken()}`
            },
            body: JSON.stringify({ titulo, mensajes: mensajesActuales })
        });
        const data = await res.json();
        chatActualId = data.id;
        await cargarHistorial();
    } catch {
        console.error("Error guardando chat");
    }
}

// Eliminar chat
async function eliminarChat(id, recargar = true) {
    try {
        await fetch(`http://localhost:8000/chats/${id}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${getToken()}` }
        });
        if (recargar) {
            if (chatActualId === id) nuevoChat();
            await cargarHistorial();
        }
    } catch {
        console.error("Error eliminando chat");
    }
}

// Nuevo chat
function nuevoChat() {
    chatActualId = null;
    mensajesActuales = [];
    chat.innerHTML = '';
    bienvenida.style.display = "";
}

newChatBtn.addEventListener("click", nuevoChat);

// Actualizar iniciarSesion y cerrarSesion para cargar historial
const _iniciarSesionOriginal = iniciarSesion;
iniciarSesion = async function(data) {
    _iniciarSesionOriginal(data);
    await cargarHistorial();
};

const _cerrarSesionOriginal = cerrarSesion;
cerrarSesion = function() {
    _cerrarSesionOriginal();
    chatHistoryList.innerHTML = '';
    nuevoChat();
};

// Guardar chat al recibir respuesta de la IA
// Esto se conecta al flujo existente — sobreescribimos el fin del click
const _buttonTextClick = buttonText.onclick;
document.addEventListener("chatMensajeGuardado", async (e) => {
    await guardarChat(e.detail.usuario, e.detail.ia);
});

// Cargar historial si ya hay sesión al iniciar
if (usuarioActual) cargarHistorial();