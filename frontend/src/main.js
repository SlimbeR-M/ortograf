import './styles/main.css';
import './ui/editor.js';
import './ui/chat.js';
import { onLogin, onLogout, getUsuarioActual } from './ui/auth.js';
import { cargarHistorial, limpiarHistorial, nuevoChat } from './ui/history.js';

onLogin(async () => {
    await cargarHistorial();
});

onLogout(() => {
    limpiarHistorial();
    nuevoChat();
});

if (getUsuarioActual()) cargarHistorial();
