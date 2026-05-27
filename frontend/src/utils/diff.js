export function diffPalabras(original, corregido) {
    const limpiar = w => w
        .replace(/[.,;:!?¡¿"'()«»…\-]+$/g, '')
        .replace(/^[.,;:!?¡¿"'()«»…\-]+/g, '')
        .toLowerCase();

    const normalizar = s => s.toLowerCase()
        .replace(/á/g,'a').replace(/é/g,'e').replace(/í/g,'i')
        .replace(/ó/g,'o').replace(/ú/g,'u').replace(/ü/g,'u').replace(/ñ/g,'n');

    const razon = (orig, corr) => {
        const oL = limpiar(orig), cL = limpiar(corr);
        const oN = normalizar(oL), cN = normalizar(cL);
        if (oL === cL && orig !== corr) return `Mayúscula corregida: '${orig}' → '${corr}'`;
        if (oN === cN && oL !== cL)    return `Tilde corregida: '${orig}' → '${corr}'`;
        if (oN === cN && orig !== corr) return `Tilde y mayúscula corregidas: '${orig}' → '${corr}'`;
        return `Ortografía corregida: '${orig}' → '${corr}'`;
    };

    const origWords = original.split(/\s+/).filter(Boolean);
    const corrWords = corregido.split(/\s+/).filter(Boolean);
    const m = origWords.length, n = corrWords.length;

    const dp = Array.from({length: m + 1}, () => new Array(n + 1).fill(0));
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            dp[i][j] = limpiar(origWords[i-1]) === limpiar(corrWords[j-1])
                ? dp[i-1][j-1] + 1
                : Math.max(dp[i-1][j], dp[i][j-1]);
        }
    }

    const ops = [];
    let i = m, j = n;
    while (i > 0 || j > 0) {
        if (i > 0 && j > 0 && limpiar(origWords[i-1]) === limpiar(corrWords[j-1])) {
            i--; j--;
        } else if (j > 0 && (i === 0 || dp[i][j-1] >= dp[i-1][j])) {
            ops.unshift({ type: 'ins', word: corrWords[j-1] });
            j--;
        } else {
            ops.unshift({ type: 'del', word: origWords[i-1] });
            i--;
        }
    }

    const cambios = [];
    let k = 0;
    while (k < ops.length) {
        if (ops[k].type === 'del' && k + 1 < ops.length && ops[k+1].type === 'ins') {
            const o = ops[k].word, c = ops[k+1].word;
            if (limpiar(o) === limpiar(c)) { k += 2; continue; }
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
