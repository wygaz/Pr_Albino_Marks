document.addEventListener('DOMContentLoaded', function () {
    const campo = document.querySelector('textarea[name="conteudo_html"]');
    if (campo) {
        campo.readOnly = true;
        const botao = document.createElement('button');
        botao.textContent = 'Habilitar edição manual';
        botao.type = 'button';
        botao.style.marginBottom = '10px';
        botao.onclick = function () {
            campo.readOnly = false;
            campo.style.border = '2px solid #cc0000';
            botao.disabled = true;
            botao.textContent = 'Edição habilitada';
        };
        campo.parentNode.insertBefore(botao, campo);
    }
});
