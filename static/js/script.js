function mudarCor(cor) {
  const bloco = document.getElementById("bloco-texto");
  if (bloco) {
    bloco.querySelectorAll("*").forEach(el => el.style.color = cor);
  }
}

function mudarTamanho(tamanho) {
  const bloco = document.getElementById("bloco-texto");
  if (bloco) {
    bloco.querySelectorAll("*").forEach(el => el.style.fontSize = tamanho);
  }
}
