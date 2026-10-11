/* Modo de edicao da grade horaria.
   O clique so monta o pedido: quem aprova ou recusa a alteracao e o servidor,
   na rota /editar/mover, comparando com as restricoes cadastradas. */

document.body.classList.add("editando");

var selecionada = null;

function toast(mensagem, tipo) {
  var caixa = document.getElementById("toasts");
  var el = document.createElement("div");
  el.className = "toast" + (tipo ? " " + tipo : "");
  el.textContent = mensagem;
  caixa.appendChild(el);
  setTimeout(function () { el.remove(); }, 4500);
}

document.querySelectorAll(".aula").forEach(function (el) {
  el.addEventListener("click", function () {
    document.querySelectorAll(".aula.selecionada")
      .forEach(function (e) { e.classList.remove("selecionada"); });
    el.classList.add("selecionada");
    selecionada = el.dataset.aula;
    toast("Aula selecionada. Escolha um horário vazio de destino.");
  });
});

document.querySelectorAll(".celula.livre").forEach(function (td) {
  td.addEventListener("click", function () {
    if (!selecionada) {
      toast("Selecione uma aula antes de escolher o destino.", "erro");
      return;
    }
    fetch("/editar/mover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        aula_id: parseInt(selecionada, 10),
        dia: td.dataset.dia,
        h: parseInt(td.dataset.h, 10)
      })
    })
      .then(function (r) { return r.json(); })
      .then(function (dados) {
        if (dados.ok) {
          toast(dados.mensagem);
          setTimeout(function () { window.location.reload(); }, 600);
        } else {
          toast(dados.mensagem, "erro");
        }
      })
      .catch(function () {
        toast("Não foi possível falar com o servidor.", "erro");
      });
  });
});
