(function () {
  "use strict";
  function init() {
    var root = document.querySelector(".seletor-disciplinas");
    if (!root) return;
    var search = root.querySelector(".busca-disciplinas");
    var items = Array.prototype.slice.call(root.querySelectorAll("[data-disciplina-item]"));
    var count = root.querySelector("[data-contador-disciplinas]");
    var empty = root.querySelector("[data-vazio-disciplinas]");
    function selectedCount() {
      count.textContent = root.querySelectorAll('input[name="disciplinas"]:checked').length;
    }
    function filter() {
      var query = search.value.trim().toLowerCase();
      var visible = 0;
      items.forEach(function (item) {
        var match = !query || item.dataset.busca.indexOf(query) !== -1;
        item.hidden = !match;
        if (match) visible += 1;
      });
      empty.hidden = visible !== 0;
      selectedCount();
    }
    root.addEventListener("change", selectedCount);
    search.addEventListener("input", filter);
    selectedCount();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
}());
