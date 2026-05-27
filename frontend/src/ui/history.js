import { attachCambiosToggles } from './corrections.js';
import { getToken, getUsuarioActual } from './auth.js';

const chatHistoryList = document.querySelector("#chat-history-list");
const newChatBtn      = document.querySelector("#new-chat-btn");
const chat            = document.querySelector("#chat-messages");
const chatDisplay     = document.querySelector("#chat-display");
const bienvenida      = document.querySelector("#welcome-screen");

let chatActualId      = null;
let mensajesActuales  = [];

export function nuevoChat() {
    chatActualId     = null;
    mensajesActuales = [];
    chat.innerHTML   = '';
    bienvenida.style.display = "";
}

export function limpiarHistorial() {
    chatHistoryList.innerHTML = '';
}

export async function cargarHistorial() {
    if (!getUsuarioActual()) {
        chatHistoryList.innerHTML = '';
        return;
    }

    try {
        const res   = await fetch("http://localhost:8000/chats/", {
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
        li.className  = "sidebar__history-item";
        li.dataset.id = c.id;
        li.innerHTML  = `
            <button class="sidebar__history-btn" type="button">
                <span class="sidebar__history-title">${c.titulo}</span>
            </button>
            <button class="sidebar__history-delete" data-id="${c.id}" type="button" aria-label="Eliminar chat">✕</button>
        `;
        li.querySelector(".sidebar__history-btn").addEventListener("click", () => cargarChat(c.id));
        li.querySelector(".sidebar__history-delete").addEventListener("click", e => {
            e.stopPropagation();
            eliminarChat(c.id);
        });
        chatHistoryList.appendChild(li);
    });
}

async function cargarChat(id) {
    try {
        const res  = await fetch(`http://localhost:8000/chats/${id}`, {
            headers: { "Authorization": `Bearer ${getToken()}` }
        });
        const data = await res.json();

        chatActualId     = id;
        mensajesActuales = data.mensajes;
        chat.innerHTML   = '';
        bienvenida.style.display = "none";

        data.mensajes.forEach(m => {
            const div = document.createElement("div");
            if (m.rol === "usuario") {
                div.className = "message message--user";
                div.innerHTML = `<p class="message__bubble">${m.contenido}</p>`;
            } else {
                div.className = "message message--ai";
                div.innerHTML = m.contenido;
                attachCambiosToggles(div);
                div.querySelectorAll('.ambig-block').forEach(b => b.classList.add('ambig-block--locked'));
            }
            chat.appendChild(div);
        });

        chatDisplay.scrollTo({ top: chatDisplay.scrollHeight, behavior: 'smooth' });
    } catch {
        console.error("Error cargando chat");
    }
}

export async function guardarChat(textoUsuarioHTML, htmlIA) {
    if (!getUsuarioActual()) return;

    mensajesActuales.push({ rol: "usuario", contenido: textoUsuarioHTML });
    mensajesActuales.push({ rol: "ia",      contenido: htmlIA });

    const titulo = textoUsuarioHTML.replace(/<[^>]*>/g, '').slice(0, 40) || "Nuevo chat";

    if (chatActualId) {
        await eliminarChat(chatActualId, false);
    }

    try {
        const res  = await fetch("http://localhost:8000/chats/", {
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

newChatBtn.addEventListener("click", nuevoChat);
