function mudarCor(cor) {
  const bloco = document.getElementById("bloco-texto");
  if (bloco) {
    bloco.style.color = cor;
  }
}

function mudarTamanho(tamanho) {
  const bloco = document.getElementById("bloco-texto");
  if (bloco) {
    bloco.style.fontSize = tamanho;
  }
}
