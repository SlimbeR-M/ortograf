import { diffPalabras } from '../utils/diff.js';

export function buildCambiosHTML(cambios) {
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

export function buildAlternativaHTML(alt) {
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

export function attachCambiosToggles(container) {
    container.querySelectorAll('.cambios-toggle').forEach(btn => {
        btn.addEventListener('click', e => {
            e.stopPropagation();
            btn.closest('.cambios-section').classList.toggle('cambios-section--open');
        });
    });
}

export function attachAmbigHandlers(messageDiv, textoOriginal, alternativa) {
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
            const textoNuevo = opcion.texto.replace(/\n{3,}/g, '\n\n');

            const textoActual = bubble.innerHTML.replace(/<br>/g, '\n').trimEnd();
            const puntuacionFinal = textoActual.match(/[.!?…]+$/)?.[0] ?? '';
            const textoConPunto = puntuacionFinal && !textoNuevo.trimEnd().match(/[.!?…]$/)
                ? textoNuevo.trimEnd() + puntuacionFinal
                : textoNuevo;

            bubble.innerHTML = textoConPunto.replace(/\n/g, '<br>');

            const nuevosCambios = diffPalabras(textoOriginal, opcion.texto);
            const nuevoHTML = buildCambiosHTML(nuevosCambios);
            const resumen = messageDiv.querySelector('.cambios-resumen');

            if (nuevoHTML) {
                const temp = document.createElement('div');
                temp.innerHTML = nuevoHTML;
                const nuevoEl = temp.firstElementChild;
                if (resumen) {
                    resumen.replaceWith(nuevoEl);
                } else {
                    block.insertAdjacentElement('beforebegin', nuevoEl);
                }
                attachCambiosToggles(nuevoEl);
            } else if (resumen) {
                resumen.remove();
            }

            cards.forEach((c, i) => {
                c.classList.toggle('ambig-card--selected', i === idx);
                c.classList.toggle('ambig-card--inactive', i !== idx);
            });

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
