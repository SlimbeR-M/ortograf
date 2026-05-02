
/**
 * @param {string} texto - Texto ingresado por el usuario
 * @returns {Promise<string>} - Corrección de texto
 */
export const respuestaIA = async (texto) => {
    const respuesta = await fetch("http://localhost:8000/corregir", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto })
    });
    return await respuesta.json();
}

export const revisarTexto = async (texto) => {
    const respuesta = await fetch("http://localhost:8000/revisar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto })
    });
    const datos = await respuesta.json();
    return datos.errores;
}