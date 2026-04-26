
/**
 * @param {string} texto - Texto ingresado por el usuario
 * @returns {Promise<string>} - Corrección de texto
 */
export const respuestaIA = async (texto) => {
    const respuesta = await fetch("http://localhost:8000/corregir", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({texto: texto})
    });

    const datos = await respuesta.json();

    return datos.texto_corregido;

}