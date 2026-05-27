const profileBtn    = document.querySelector("#profile-btn");
const profileInitial = document.querySelector("#profile-initial");
const authOverlay   = document.querySelector("#auth-overlay");
const authCloseBtn  = document.querySelector("#auth-close-btn");
const tabLogin      = document.querySelector("#tab-login");
const tabRegister   = document.querySelector("#tab-register");
const formLogin     = document.querySelector("#form-login");
const formRegister  = document.querySelector("#form-register");
const formForgot    = document.querySelector("#form-forgot");
const loginError    = document.querySelector("#login-error");
const registerError = document.querySelector("#register-error");
const forgotError   = document.querySelector("#forgot-error");

let usuarioActual  = null;
const loginCallbacks  = [];
const logoutCallbacks = [];

export function getUsuarioActual() {
    return usuarioActual;
}

export function getToken() {
    return localStorage.getItem("token");
}

export function onLogin(cb) {
    loginCallbacks.push(cb);
}

export function onLogout(cb) {
    logoutCallbacks.push(cb);
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

async function iniciarSesion(data) {
    usuarioActual = data.usuario;
    localStorage.setItem("token", data.token);
    localStorage.setItem("usuario", JSON.stringify(data.usuario));
    actualizarBotonPerfil();
    authOverlay.setAttribute("hidden", "");
    limpiarErrores();
    for (const cb of loginCallbacks) await cb(data);
}

function cerrarSesion() {
    usuarioActual = null;
    localStorage.removeItem("token");
    localStorage.removeItem("usuario");
    actualizarBotonPerfil();
    logoutCallbacks.forEach(cb => cb());
}

profileBtn.addEventListener("click", () => {
    if (usuarioActual) {
        cerrarSesion();
    } else {
        authOverlay.removeAttribute("hidden");
    }
});

authCloseBtn.addEventListener("click", () => {
    authOverlay.setAttribute("hidden", "");
    limpiarErrores();
});

authOverlay.addEventListener("click", e => {
    if (e.target === authOverlay) {
        authOverlay.setAttribute("hidden", "");
        limpiarErrores();
    }
});

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

document.querySelector("#login-submit").addEventListener("click", async () => {
    const email    = document.querySelector("#login-email").value.trim();
    const password = document.querySelector("#login-password").value;

    if (!email || !password) {
        mostrarError(loginError, "Completa todos los campos.");
        return;
    }

    try {
        const res  = await fetch("http://localhost:8000/auth/login", {
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

document.querySelector("#register-submit").addEventListener("click", async () => {
    const nombre   = document.querySelector("#register-name").value.trim();
    const email    = document.querySelector("#register-email").value.trim();
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
        const res  = await fetch("http://localhost:8000/auth/register", {
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
    const email     = document.querySelector("#forgot-email").value.trim();
    const password  = document.querySelector("#forgot-password").value;
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
        const res  = await fetch("http://localhost:8000/auth/reset-password", {
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

// Restaurar sesión guardada al cargar
const tokenGuardado   = localStorage.getItem("token");
const usuarioGuardado = localStorage.getItem("usuario");
if (tokenGuardado && usuarioGuardado) {
    usuarioActual = JSON.parse(usuarioGuardado);
}
actualizarBotonPerfil();
