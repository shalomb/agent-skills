/* Graph view: Cytoscape on the elements in #graph-data. Filter, search, and inspector card. */
(function () {
  var canvas = document.getElementById("graph-canvas");
  var inspector = document.getElementById("graph-inspector");
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
      { selector: "node.selected", style: {
        "border-width": 3, "border-color": token("--md-sys-color-tertiary"), "border-opacity": 0.95 } },
      { selector: "edge", style: {
        "width": 1.5, "line-color": token("--md-sys-color-outline"), "curve-style": "bezier",
        "target-arrow-shape": "triangle", "target-arrow-color": token("--md-sys-color-outline") } },
      { selector: ".dim", style: { "opacity": 0.15 } }
    ]
  });
  canvas.setAttribute("data-graph-nodes", String(cy.nodes().length));
  canvas.setAttribute("data-graph-edges", String(cy.edges().length));

  var activeNode = null;

  function clearElement(el) {
    while (el.firstChild) {
      el.removeChild(el.firstChild);
    }
  }

  function showInspector(node) {
    if (!inspector) return;
    if (activeNode) {
      activeNode.removeClass("selected");
    }
    activeNode = node;
    node.addClass("selected");

    var data = node.data();
    var label = data.label || node.id();
    var kind = data.kind || "file";
    var isHub = Boolean(data.hub);
    var summary = data.summary || "";
    var href = data.href || "";
    var remoteHref = data.remote_href || "";
    var remoteLabel = data.remote_label || "View on GitHub ↗";

    clearElement(inspector);

    // Header
    var header = document.createElement("div");
    header.className = "inspector-header";

    var titleWrap = document.createElement("div");
    titleWrap.className = "inspector-title-wrap";

    var titleEl = document.createElement("h4");
    titleEl.className = "inspector-title";
    titleEl.textContent = label;
    titleWrap.appendChild(titleEl);

    var badgesWrap = document.createElement("div");
    badgesWrap.className = "inspector-badges";

    var kindBadge = document.createElement("span");
    kindBadge.className = "inspector-badge kind";
    kindBadge.textContent = kind;
    badgesWrap.appendChild(kindBadge);

    if (isHub) {
      var hubBadge = document.createElement("span");
      hubBadge.className = "inspector-badge hub";
      hubBadge.textContent = "HUB";
      badgesWrap.appendChild(hubBadge);
    }
    titleWrap.appendChild(badgesWrap);
    header.appendChild(titleWrap);

    var closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "inspector-close";
    closeBtn.setAttribute("aria-label", "Close inspector");
    closeBtn.textContent = "×";
    closeBtn.addEventListener("click", hideInspector);
    header.appendChild(closeBtn);

    inspector.appendChild(header);

    // Summary
    var summaryEl = document.createElement("p");
    if (summary) {
      summaryEl.className = "inspector-summary";
      summaryEl.textContent = summary;
    } else {
      summaryEl.className = "inspector-summary empty";
      summaryEl.textContent = "No summary available";
    }
    inspector.appendChild(summaryEl);

    // Actions
    var actionsEl = document.createElement("div");
    actionsEl.className = "inspector-actions";

    if (href) {
      var primaryBtn = document.createElement("a");
      primaryBtn.href = href;
      primaryBtn.className = "inspector-btn primary";
      primaryBtn.textContent = "Open Source View";
      actionsEl.appendChild(primaryBtn);
    }

    if (remoteHref) {
      var secondaryBtn = document.createElement("a");
      secondaryBtn.href = remoteHref;
      secondaryBtn.target = "_blank";
      secondaryBtn.rel = "noopener noreferrer";
      secondaryBtn.className = "inspector-btn secondary";
      secondaryBtn.textContent = remoteLabel;
      actionsEl.appendChild(secondaryBtn);
    }

    inspector.appendChild(actionsEl);
    inspector.hidden = false;
  }

  function hideInspector() {
    if (activeNode) {
      activeNode.removeClass("selected");
      activeNode = null;
    }
    if (inspector) {
      inspector.hidden = true;
      clearElement(inspector);
    }
  }

  cy.on("tap", "node", function (event) {
    showInspector(event.target);
  });

  cy.on("dbltap", "node", function (event) {
    var href = event.target.data("href");
    if (href) {
      window.location.href = href;
    }
  });

  cy.on("tap", function (event) {
    if (event.target === cy) {
      hideInspector();
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      hideInspector();
    }
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
