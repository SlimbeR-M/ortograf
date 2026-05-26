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
    abortController = null,
    erroresActuales = [];

text.addEventListener("input", () => {
    if(text.value.trim().length > 0) {
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

buttonText.addEventListener("click", async() => {
    if(esperandoRespuesta) {
        if(abortController) abortController.abort();
        esperandoRespuesta = false;
        icono.src = "/src/assets/enviar.png";
        buttonText.disabled = true;
        text.disabled = false;
        return;
    }

    esperandoRespuesta = true;

    // Bloquear bloques de ambigüedad del turno anterior
    chat.querySelectorAll('.ambig-block:not(.ambig-block--locked)').forEach(b => {
        b.classList.add('ambig-block--locked');
    });

    // Capturar errores antes de limpiar (Bug 2 & 4)
    const erroresParaMensaje = [...erroresActuales];

    // Mensaje del usuario
    let texto = text.value.replace(/^\n+|\n+$/g, '').trim();
    texto = texto.replace(/\n{3,}/g, '\n\n');
    const mensaje = document.createElement("div");
    mensaje.className = "message message--user";
    mensaje.innerHTML = `<p class="message__bubble">${texto.replace(/\n/g, '<br>')}</p>`;

    // Aplicar highlight de errores inmediatamente, sin esperar la IA (Bug 2)
    if (erroresParaMensaje.length > 0) {
        const sorted = [...erroresParaMensaje].sort((a, b) => b.offset - a.offset);
        let resaltado = texto;
        sorted.forEach(err => {
            const antes = resaltado.slice(0, err.offset);
            const palabra = resaltado.slice(err.offset, err.offset + err.error_length);
            const despues = resaltado.slice(err.offset + err.error_length);
            resaltado = `${antes}<span class="error-highlight">${palabra}</span>${despues}`;
        });
        mensaje.querySelector('.message__bubble').innerHTML = resaltado.replace(/\n/g, '<br>');
    }

    chat.appendChild(mensaje);

    bienvenida.style.display = "none";
    resetTextarea();

    //indicador de pensamiento
    const typing= document.createElement("div");
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
    } catch(e) {
        if(e.name === 'AbortError') {
            typing.remove();
            return;
        }
        throw e;
    }

    if(!datos) return;

    // Re-aplicar highlight más preciso usando datos.cambios de la IA
    if (datos.cambios && datos.cambios.length > 0) {
        const erroresSet = new Set(
            datos.cambios
                .filter(c => c.original && c.original.trim())
                .map(c => c.original.toLowerCase())
        )

        // Dividir en tokens preservando espacios y saltos
        const tokens = texto.split(/(\s+)/)
        const resultado = tokens.map(token => {
            // Si es espacio o salto, convertir \n a <br> y devolver
            if (/^\s+$/.test(token)) {
                return token.replace(/\n/g, '<br>')
            }
            // Limpiar puntuación para comparar
            const limpio = token.replace(/[.,;:!?¡¿"'()]/g, '').toLowerCase()
            if (erroresSet.has(limpio) || erroresSet.has(token.toLowerCase())) {
                return `<span class="error-highlight">${token}</span>`
            }
            return token
        })

        mensaje.querySelector('.message__bubble').innerHTML = resultado.join('')
    }

    // Construir HTML de la respuesta
    const textoCorregido = datos.texto_corregido.replace(/\n{3,}/g, '\n\n');
    let html = `<p class="message__bubble">${textoCorregido.replace(/\n/g, '<br>')}</p>`

    // Score del usuario
    if (datos.score) {
        const colorOrto = datos.score.ortografia.porcentaje >= 75 ? '#4caf50' : datos.score.ortografia.porcentaje >= 50 ? '#ff9800' : '#f44336'
        const colorGram = datos.score.gramatica.porcentaje >= 75 ? '#4caf50' : datos.score.gramatica.porcentaje >= 50 ? '#ff9800' : '#f44336'
        html += `<div class="message__score">
            <span style="color:${colorOrto}">🔤 Ortografía: ${datos.score.ortografia.porcentaje}% — ${datos.score.ortografia.nivel}</span>
            <span style="color:${colorGram}">📝 Gramática: ${datos.score.gramatica.porcentaje}% — ${datos.score.gramatica.nivel}</span>
        </div>`
    }

    // Cambios realizados
    if (datos.cambios && datos.cambios.length > 0) {
        html += buildCambiosHTML(datos.cambios);
    }

    // Alternativa por ambigüedad
    if (datos.alternativa && datos.alternativa.tiene_ambiguedad) {
        html += buildAlternativaHTML(datos.alternativa);
    }

    //mostrar respuesta
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

function resetTextarea() {
    clearTimeout(debounceTimer);
    text.value = '';
    text.style.height = '40px';
    highlight.innerHTML = '';
    highlight.style.height = '40px';
    buttonText.disabled = true;
    erroresActuales = [];
}

function diffPalabras(original, corregido) {
    const normalizar = s => s.toLowerCase()
        .replace(/á/g,'a').replace(/é/g,'e').replace(/í/g,'i')
        .replace(/ó/g,'o').replace(/ú/g,'u').replace(/ü/g,'u').replace(/ñ/g,'n');

    const razon = (orig, corr) => {
        const oL = orig.toLowerCase(), cL = corr.toLowerCase();
        const oN = normalizar(orig), cN = normalizar(corr);
        if (oL === cL && orig !== corr) return `Mayúscula corregida: '${orig}' → '${corr}'`;
        if (oN === cN && oL !== cL)    return `Tilde corregida: '${orig}' → '${corr}'`;
        if (oN === cN && orig !== corr) return `Tilde y mayúscula corregidas: '${orig}' → '${corr}'`;
        return `Ortografía corregida: '${orig}' → '${corr}'`;
    };

    const origWords = original.split(/\s+/).filter(Boolean);
    const corrWords = corregido.split(/\s+/).filter(Boolean);
    const m = origWords.length, n = corrWords.length;

    // LCS DP table
    const dp = Array.from({length: m + 1}, () => new Array(n + 1).fill(0));
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            dp[i][j] = origWords[i-1] === corrWords[j-1]
                ? dp[i-1][j-1] + 1
                : Math.max(dp[i-1][j], dp[i][j-1]);
        }
    }

    // Backtrack collecting individual del/ins ops
    const ops = [];
    let i = m, j = n;
    while (i > 0 || j > 0) {
        if (i > 0 && j > 0 && origWords[i-1] === corrWords[j-1]) {
            i--; j--;
        } else if (j > 0 && (i === 0 || dp[i][j-1] >= dp[i-1][j])) {
            ops.unshift({ type: 'ins', word: corrWords[j-1] });
            j--;
        } else {
            ops.unshift({ type: 'del', word: origWords[i-1] });
            i--;
        }
    }

    // Pair adjacent del+ins as individual word replacements
    const cambios = [];
    let k = 0;
    while (k < ops.length) {
        if (ops[k].type === 'del' && k + 1 < ops.length && ops[k+1].type === 'ins') {
            const o = ops[k].word, c = ops[k+1].word;
            cambios.push({ tipo: 'reemplazo', original: o, corregido: c, razon: razon(o, c) });
            k += 2;
        } else if (ops[k].type === 'del') {
            cambios.push({ tipo: 'reemplazo', original: ops[k].word, corregido: '', razon: `Ortografía corregida: '${ops[k].word}' → ''` });
            k++;
        } else {
            cambios.push({ tipo: 'reemplazo', original: '', corregido: ops[k].word, razon: `Ortografía corregida: '' → '${ops[k].word}'` });
            k++;
        }
    }
    return cambios;
}

function buildCambiosHTML(cambios) {
    const reemplazos = cambios.filter(c => c.original && c.original.trim());
    if (reemplazos.length === 0) return '';

    const cats = [
        { emoji: '🔤', label: 'Tildes y acentos',   test: r => /[Tt]ilde/.test(r),             items: [] },
        { emoji: '📍', label: 'Mayúsculas',          test: r => /[Mm]ayúscula/.test(r),         items: [] },
        { emoji: '✏️', label: 'Puntuación',          test: r => /[Pp]untuación/.test(r),        items: [] },
        { emoji: '🔁', label: 'Semántica/gramática', test: r => /semántica|gramatical/.test(r), items: [] },
        { emoji: '➡️', label: 'Ortografía',          test: null,                                items: [] },
    ];

    reemplazos.forEach(c => {
        const r = c.razon || '';
        (cats.find(cat => cat.test && cat.test(r)) || cats[cats.length - 1]).items.push(c);
    });

    let catsHTML = '';
    cats.forEach(cat => {
        if (cat.items.length === 0) return;
        const items = cat.items.map(c =>
            `<li class="cambios-cat__item"><span class="cambios-original">${c.original}</span><span class="cambios-arrow"> → </span><span class="cambios-corregido">${c.corregido}</span></li>`
        ).join('');
        catsHTML += `<div class="cambios-cat cambios-section">
            <button class="cambios-cat__header cambios-toggle" type="button"><span class="cambios-chevron">▶</span>${cat.emoji} ${cat.label} (${cat.items.length})</button>
            <div class="cambios-section__body"><div class="cambios-section__inner"><ul class="cambios-cat__list">${items}</ul></div></div>
        </div>`;
    });

    return `<div class="cambios-resumen cambios-section">
        <button class="cambios-resumen__header cambios-toggle" type="button"><span class="cambios-chevron">▶</span>📋 Ver correcciones (${reemplazos.length})</button>
        <div class="cambios-section__body"><div class="cambios-section__inner">${catsHTML}</div></div>
    </div>`;
}

function buildAlternativaHTML(alt) {
    const a = alt.opcion_a, b = alt.opcion_b;
    return `<div class="ambig-block cambios-section">
        <button class="ambig-header cambios-toggle" type="button"><span class="cambios-chevron">▶</span>🔀 ¿Tu intención era otra?</button>
        <div class="cambios-section__body"><div class="cambios-section__inner">
            <div class="ambig-cards">
                <div class="ambig-card ambig-card--a">
                    <span class="ambig-card__label">${a.etiqueta}</span>
                    <p class="ambig-card__text">${a.texto.replace(/\n/g, '<br>')}</p>
                    <span class="ambig-card__desc">${a.descripcion}</span>
                </div>
                <div class="ambig-card ambig-card--b">
                    <span class="ambig-card__label">${b.etiqueta}</span>
                    <p class="ambig-card__text">${b.texto.replace(/\n/g, '<br>')}</p>
                    <span class="ambig-card__desc">${b.descripcion}</span>
                </div>
            </div>
        </div></div>
    </div>`;
}

function attachAmbigHandlers(messageDiv, textoOriginal, alternativa) {
    const block = messageDiv.querySelector('.ambig-block');
    if (!block) return;

    const cards = block.querySelectorAll('.ambig-card');
    if (cards.length < 2) return;

    const bubble = messageDiv.querySelector('.message__bubble');
    const opciones = [alternativa.opcion_a, alternativa.opcion_b];

    cards.forEach((card, idx) => {
        card.addEventListener('click', () => {
            if (block.classList.contains('ambig-block--locked')) return;

            const opcion = opciones[idx];

            // Actualizar burbuja con el texto de la opción elegida
            const textoNuevo = opcion.texto.replace(/\n{3,}/g, '\n\n');
            bubble.innerHTML = textoNuevo.replace(/\n/g, '<br>');

            // Recalcular correcciones entre texto original del usuario y la opción
            const nuevosCambios = diffPalabras(textoOriginal, opcion.texto);
            const resumen = messageDiv.querySelector('.cambios-resumen');
            if (resumen) {
                const nuevoHTML = buildCambiosHTML(nuevosCambios);
                if (nuevoHTML) {
                    const temp = document.createElement('div');
                    temp.innerHTML = nuevoHTML;
                    resumen.replaceWith(temp.firstElementChild);
                    const nuevoEl = messageDiv.querySelector('.cambios-resumen');
                    if (nuevoEl) attachCambiosToggles(nuevoEl);
                } else {
                    resumen.remove();
                }
            }

            // Marcar visualmente la opción elegida
            cards.forEach((c, i) => {
                c.classList.toggle('ambig-card--selected', i === idx);
                c.classList.toggle('ambig-card--inactive', i !== idx);
            });

            // Actualizar score de ortografía según los cambios de la opción elegida
            const scoreEl = messageDiv.querySelector('.message__score');
            if (scoreEl) {
                const errores = nuevosCambios.length;
                const palabras = Math.max(1, textoOriginal.split(/\s+/).filter(Boolean).length);
                const pct = Math.max(0, Math.round(100 - (errores / palabras * 20)));
                const color = pct >= 75 ? '#4caf50' : pct >= 50 ? '#ff9800' : '#f44336';
                const nivel = pct >= 75 ? 'Excelente' : pct >= 50 ? 'Bueno' : 'Necesita mejora';
                const spanOrto = scoreEl.querySelector('span');
                if (spanOrto) {
                    spanOrto.style.color = color;
                    spanOrto.textContent = `🔤 Ortografía: ${pct}% — ${nivel}`;
                }
            }
        });
    });
}

function attachCambiosToggles(container) {
    container.querySelectorAll('.cambios-toggle').forEach(btn => {
        btn.addEventListener('click', e => {
            e.stopPropagation();
            btn.closest('.cambios-section').classList.toggle('cambios-section--open');
        });
    });
}

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
        profileBtn.classList.add('sidebar__profile-btn--avatar');
        profileBtn.classList.remove('sidebar__profile-btn--login');
    } else {
        profileInitial.textContent = "Iniciar sesión";
        profileBtn.classList.remove('sidebar__profile-btn--avatar');
        profileBtn.classList.add('sidebar__profile-btn--login');
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
}
actualizarBotonPerfil();


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

async function guardarChat(textoUsuarioHTML, htmlIA) {
    if (!usuarioActual) return;

    // Guardar solo el innerHTML de la burbuja, sin el wrapper
    mensajesActuales.push({ rol: "usuario", contenido: textoUsuarioHTML });
    mensajesActuales.push({ rol: "ia", contenido: htmlIA });

    // Título: texto plano sin etiquetas HTML
    const titulo = textoUsuarioHTML.replace(/<[^>]*>/g, '').slice(0, 40) || "Nuevo chat";

    if (chatActualId) {
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