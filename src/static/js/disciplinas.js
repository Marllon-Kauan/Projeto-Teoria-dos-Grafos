(function () {
  function ajustarOpcaoSemPeriodo(eletiva, periodo) {
    var opcao = periodo.querySelector('option[value=""]');
    if (eletiva.value === "1" && !opcao) {
      opcao = document.createElement("option");
      opcao.value = "";
      opcao.textContent = "Sem período específico";
      periodo.insertBefore(opcao, periodo.firstChild);
    } else if (eletiva.value !== "1" && opcao) {
      if (periodo.value === "") periodo.value = periodo.options[1] ? periodo.options[1].value : "";
      opcao.remove();
    }
  }

  function atualizarPeriodo() {
    var eletiva = document.getElementById("eletiva");
    var periodo = document.getElementById("periodo");
    var ajuda = document.getElementById("periodo-ajuda");
    if (!eletiva || !periodo) return;
    ajustarOpcaoSemPeriodo(eletiva, periodo);
    var obrigatorio = eletiva.value === "0";
    periodo.required = obrigatorio;
    if (ajuda) ajuda.textContent = obrigatorio
      ? "Obrigatório para disciplinas não eletivas."
      : "Opcional para disciplinas eletivas.";
  }
  document.addEventListener("DOMContentLoaded", function () {
    var eletiva = document.getElementById("eletiva");
    if (eletiva) eletiva.addEventListener("change", atualizarPeriodo);
    var formulario = document.querySelector("form[data-tem-turmas]");
    if (formulario) formulario.addEventListener("submit", function (evento) {
      var mudouRegra = document.getElementById("carga").value !== formulario.dataset.originalCarga ||
        document.getElementById("periodo").value !== formulario.dataset.originalPeriodo ||
        eletiva.value !== formulario.dataset.originalEletiva;
      var aviso = formulario.querySelector("p.ajuda");
      var nomesTurmas = aviso ? aviso.textContent.replace(/^As turmas com alocações que serão afetadas:\s*/, "").split(".")[0] : "afetadas";
      if (mudouRegra && formulario.dataset.temTurmas === "1" &&
          !window.confirm("As turmas " + nomesTurmas +
          " possuem alocações. As alocações serão removidas e será necessário gerar a grade novamente. Deseja continuar?")) {
        evento.preventDefault();
        return;
      }
      var confirmacao = document.getElementById("confirmar_alocacoes");
      if (confirmacao && mudouRegra && formulario.dataset.temTurmas === "1") confirmacao.value = "1";
    });
    atualizarPeriodo();
  });
}());
