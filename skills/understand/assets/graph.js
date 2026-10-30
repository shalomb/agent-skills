/* Graph view: Cytoscape on the elements in #graph-data. Filter and search; click opens the source view. */
(function () {
  var canvas = document.getElementById("graph-canvas");
  var elements = JSON.parse(document.getElementById("graph-data").textContent);
  var css = getComputedStyle(document.documentElement);
  function token(name) { return css.getPropertyValue(name).trim() || "#888"; }
  var cy = cytoscape({
    container: canvas,
    elements: elements,
    layout: { name: "cose", animate: false },
    style: [
      { selector: "node", style: {
        "label": "data(label)", "font-size": 11, "background-color": token("--md-sys-color-primary"),
        "color": token("--md-sys-color-on-surface"), "text-valign": "bottom", "text-margin-y": 4 } },
      { selector: "edge", style: {
        "width": 1.5, "line-color": token("--md-sys-color-outline"), "curve-style": "bezier",
        "target-arrow-shape": "triangle", "target-arrow-color": token("--md-sys-color-outline") } },
      { selector: ".dim", style: { "opacity": 0.15 } }
    ]
  });
  canvas.setAttribute("data-graph-nodes", String(cy.nodes().length));
  canvas.setAttribute("data-graph-edges", String(cy.edges().length));

  cy.on("tap", "node", function (event) {
    var href = event.target.data("href");
    if (href) { window.location.href = href; }
  });

  var search = document.getElementById("graph-search");
  var kind = document.getElementById("graph-kind");
  function applyFilter() {
    var needle = (search.value || "").toLowerCase();
    var wanted = kind.value;
    cy.nodes().forEach(function (node) {
      var text = (node.data("label") + " " + node.id()).toLowerCase();
      var show = (!needle || text.indexOf(needle) >= 0) && (!wanted || node.data("kind") === wanted);
      node.toggleClass("dim", !show);
      var item = document.getElementById(node.id());
      if (item) { item.hidden = !show; }
    });
  }
  search.addEventListener("input", applyFilter);
  kind.addEventListener("change", applyFilter);
})();
