import { respuestaIA } from '../api/spelling.js';
import { buildCambiosHTML, buildAlternativaHTML, attachCambiosToggles, attachAmbigHandlers } from './corrections.js';
import { getUsuarioActual } from './auth.js';
import { resetTextarea, getErroresActuales } from './editor.js';
import { guardarChat } from './history.js';

const text        = document.querySelector("#user-input");
const buttonText  = document.querySelector("#send-btn");
const chat        = document.querySelector("#chat-messages");
const bienvenida  = document.querySelector("#welcome-screen");
const chatDisplay = document.querySelector("#chat-display");
const icono       = document.querySelector(".editor__send-icon");

let esperandoRespuesta = false;
let abortController    = null;

buttonText.addEventListener("click", async () => {
    if (esperandoRespuesta) {
        if (abortController) abortController.abort();
        esperandoRespuesta = false;
        icono.src = "/src/assets/enviar.png";
        buttonText.disabled = true;
        text.disabled = false;
        return;
    }

    esperandoRespuesta = true;

    chat.querySelectorAll('.ambig-block:not(.ambig-block--locked)').forEach(b => {
        b.classList.add('ambig-block--locked');
    });

    const erroresParaMensaje = [...getErroresActuales()];

    let texto = text.value.replace(/^\n+|\n+$/g, '').trim();
    texto = texto.replace(/\n{3,}/g, '\n\n');
    const mensaje = document.createElement("div");
    mensaje.className = "message message--user";
    mensaje.innerHTML = `<p class="message__bubble">${texto.replace(/\n/g, '<br>')}</p>`;

    if (erroresParaMensaje.length > 0) {
        const sorted = [...erroresParaMensaje].sort((a, b) => b.offset - a.offset);
        let resaltado = texto;
        sorted.forEach(err => {
            const antes   = resaltado.slice(0, err.offset);
            const palabra = resaltado.slice(err.offset, err.offset + err.error_length);
            const despues = resaltado.slice(err.offset + err.error_length);
            resaltado = `${antes}<span class="error-highlight">${palabra}</span>${despues}`;
        });
        mensaje.querySelector('.message__bubble').innerHTML = resaltado.replace(/\n/g, '<br>');
    }

    chat.appendChild(mensaje);
    bienvenida.style.display = "none";
    resetTextarea();

    const typing = document.createElement("div");
    typing.className = "message__typing";
    typing.innerHTML = '<span class="message__typing-dot"></span>'.repeat(3);
    chat.appendChild(typing);
    text.disabled = true;
    chatDisplay.scrollTo({ top: chatDisplay.scrollHeight, behavior: 'smooth' });

    icono.src = "/src/assets/cancelar.png";
    buttonText.disabled = false;

    abortController = new AbortController();
    let datos;
    try {
        datos = await respuestaIA(texto, abortController.signal);
    } catch (e) {
        if (e.name === 'AbortError') {
            typing.remove();
            return;
        }
        throw e;
    }

    if (!datos) return;

    // Rehighlight del mensaje del usuario con los cambios precisos de la IA
    if (datos.cambios && datos.cambios.length > 0) {
        const erroresSet = new Set(
            datos.cambios
                .filter(c => c.original && c.original.trim())
                .map(c => c.original.toLowerCase())
        );

        const tokens    = texto.split(/(\s+)/);
        const resultado = tokens.map(token => {
            if (/^\s+$/.test(token)) return token.replace(/\n/g, '<br>');
            const limpio = token.replace(/[.,;:!?¡¿"'()]/g, '').toLowerCase();
            if (erroresSet.has(limpio) || erroresSet.has(token.toLowerCase())) {
                return `<span class="error-highlight">${token}</span>`;
            }
            return token;
        });

        mensaje.querySelector('.message__bubble').innerHTML = resultado.join('');
    }

    const textoCorregido = datos.texto_corregido.replace(/\n{3,}/g, '\n\n');
    let html = `<p class="message__bubble">${textoCorregido.replace(/\n/g, '<br>')}</p>`;

    if (datos.score) {
        const colorOrto = datos.score.ortografia.porcentaje >= 75 ? '#4caf50' : datos.score.ortografia.porcentaje >= 50 ? '#ff9800' : '#f44336';
        const colorGram = datos.score.gramatica.porcentaje >= 75 ? '#4caf50' : datos.score.gramatica.porcentaje >= 50 ? '#ff9800' : '#f44336';
        html += `<div class="message__score">
            <span style="color:${colorOrto}">🔤 Ortografía: ${datos.score.ortografia.porcentaje}% — ${datos.score.ortografia.nivel}</span>
            <span style="color:${colorGram}">📝 Gramática: ${datos.score.gramatica.porcentaje}% — ${datos.score.gramatica.nivel}</span>
        </div>`;
    }

    if (datos.cambios && datos.cambios.length > 0) {
        html += buildCambiosHTML(datos.cambios);
    }

    if (datos.alternativa && datos.alternativa.tiene_ambiguedad) {
        html += buildAlternativaHTML(datos.alternativa);
    }

    typing.className = "message message--ai";
    typing.innerHTML = html;
    attachCambiosToggles(typing);
    if (datos.alternativa && datos.alternativa.tiene_ambiguedad) {
        attachAmbigHandlers(typing, texto, datos.alternativa);
    }
    chatDisplay.scrollTo({ top: chatDisplay.scrollHeight, behavior: 'smooth' });
    text.disabled = false;
    esperandoRespuesta = false;
    buttonText.disabled = true;
    icono.src = "/src/assets/enviar.png";

    if (getUsuarioActual()) {
        await guardarChat(
            mensaje.querySelector('.message__bubble').innerHTML,
            html
        );
    }
});
