/* Tela de salas: mostra o campo de motivo apenas quando a sala estiver
   marcada como "Indisponível".

   O envio continua sendo feito pelo POST do próprio formulário; o
   back-end decide como persistir status e motivo. Sem JavaScript, o
   campo permanece visível e habilitado, então a tela continua utilizável. */

document.querySelectorAll("[data-sala-status]").forEach(function (select) {
  var id = select.dataset.salaStatus;
  var motivo = document.querySelector('[data-sala-motivo="' + id + '"]');
  if (!motivo) return;

  function atualizar() {
    var indisponivel = select.value === "Indisponível";
    motivo.hidden = !indisponivel;
    motivo.disabled = !indisponivel;
  }

  select.addEventListener("change", atualizar);
  atualizar();
});
