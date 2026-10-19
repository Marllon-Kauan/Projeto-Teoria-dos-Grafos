/* Selecao rapida dos horarios bloqueados (RH07).
   Apenas marca/desmarca os checkboxes do formulario; o envio continua
   sendo feito pelo POST existente, com os campos "periodo" e "bloq". */

document.querySelectorAll("[data-bloq-acao]").forEach(function (botao) {
  botao.addEventListener("click", function () {
    var marcar = botao.dataset.bloqAcao === "marcar";
    document.querySelectorAll('input[name="bloq"]').forEach(function (caixa) {
      caixa.checked = marcar;
    });
  });
});

document.querySelectorAll("[data-bloq-dia]").forEach(function (botao) {
  botao.addEventListener("click", function () {
    var dia = botao.dataset.bloqDia;
    var marcar = botao.dataset.bloqModo === "marcar";
    document.querySelectorAll('input[name="bloq"]').forEach(function (caixa) {
      if (caixa.dataset.dia === dia) {
        caixa.checked = marcar;
      }
    });
  });
});
