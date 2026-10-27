(function () {
  function atualizarPeriodo() {
    var eletiva = document.getElementById("eletiva");
    var periodo = document.getElementById("periodo");
    var ajuda = document.getElementById("periodo-ajuda");
    if (!eletiva || !periodo) return;
    var obrigatorio = eletiva.value === "0";
    periodo.required = obrigatorio;
    if (ajuda) ajuda.textContent = obrigatorio
      ? "Obrigatório para disciplinas não eletivas."
      : "Opcional para disciplinas eletivas.";
  }
  document.addEventListener("DOMContentLoaded", function () {
    var eletiva = document.getElementById("eletiva");
    if (eletiva) eletiva.addEventListener("change", atualizarPeriodo);
    atualizarPeriodo();
  });
}());
