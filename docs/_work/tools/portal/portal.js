(function () {
  "use strict";
  var boot = JSON.parse(document.getElementById("ui-boot").textContent);
  var order = boot.order, meta = boot.meta;
  var docEl = document.getElementById("ui-doc");
  var tocEl = document.getElementById("ui-toc");
  var pagerEl = document.getElementById("ui-pager");
  var side = document.getElementById("ui-side");
  var menu = document.getElementById("ui-menu");
  var results = document.getElementById("ui-results");
  var input = document.getElementById("ui-q");
  var current = null;

  function parseHash() {
    var raw = "";
    try { raw = decodeURIComponent((location.hash || "").slice(1)); } catch (e) { raw = ""; }
    var i = raw.indexOf("~");
    var id = i < 0 ? raw : raw.slice(0, i);
    var anchor = i < 0 ? "" : raw.slice(i + 1);
    if (!meta[id]) { id = "hub"; anchor = ""; }
    return { id: id, anchor: anchor };
  }

  function find(anchor) {
    if (!anchor) return null;
    var all = docEl.querySelectorAll("[id]");
    for (var i = 0; i < all.length; i++) { if (all[i].id === anchor) return all[i]; }
    return null;
  }

  function show(id, anchor) {
    var t = document.getElementById("t-" + id);
    if (!t) return;
    if (current !== id) {
      docEl.replaceChildren(t.content.cloneNode(true));
      current = id;
      buildToc();
      buildPager(id);
      markNav(id);
      window.scrollTo(0, 0);
    }
    closeResults();
    closeNav();
    var el = find(anchor);
    if (el) { el.scrollIntoView(); }
  }

  function go(id, anchor) {
    var h = "#" + id + (anchor ? "~" + anchor : "");
    try {
      if (location.hash !== h) { history.pushState(null, "", h); }
    } catch (e) {
      try { location.hash = h; } catch (e2) { /* the page still shows the document */ }
    }
    show(id, anchor);
  }

  function markNav(id) {
    var links = side.querySelectorAll("a[data-doc]");
    for (var i = 0; i < links.length; i++) {
      if (links[i].getAttribute("data-doc") === id) {
        links[i].setAttribute("aria-current", "page");
        if (links[i].scrollIntoView) { links[i].scrollIntoView({ block: "nearest" }); }
      } else {
        links[i].removeAttribute("aria-current");
      }
    }
  }

  function buildToc() {
    var hs = docEl.querySelectorAll("h2, h3");
    tocEl.textContent = "";
    if (hs.length < 3) return;
    var h = document.createElement("h2");
    h.textContent = "On this page";
    var ul = document.createElement("ul");
    for (var i = 0; i < hs.length; i++) {
      var el = hs[i];
      var li = document.createElement("li");
      li.className = el.tagName === "H3" ? "l3" : "l2";
      var a = document.createElement("a");
      a.href = "#" + current + "~" + el.id;
      a.setAttribute("data-doc", current);
      a.setAttribute("data-anchor", el.id);
      a.textContent = el.textContent.replace(/#$/, "").trim();
      li.appendChild(a);
      ul.appendChild(li);
    }
    tocEl.appendChild(h);
    tocEl.appendChild(ul);
  }

  function pagerLink(id, cls, label) {
    var a = document.createElement("a");
    a.href = "#" + id;
    a.className = cls;
    a.setAttribute("data-doc", id);
    var s = document.createElement("small");
    s.textContent = label;
    var b = document.createElement("span");
    b.textContent = meta[id].label;
    a.appendChild(s);
    a.appendChild(b);
    return a;
  }

  function buildPager(id) {
    pagerEl.textContent = "";
    var i = order.indexOf(id);
    if (i > 0) pagerEl.appendChild(pagerLink(order[i - 1], "prev", "Previous"));
    if (i < order.length - 1) pagerEl.appendChild(pagerLink(order[i + 1], "next", "Next"));
  }

  /* ---- search over the text of every document */
  var index = null;
  function buildIndex() {
    index = [];
    order.forEach(function (id) {
      var t = document.getElementById("t-" + id);
      if (!t) return;
      var heading = meta[id].label, anchor = "";
      var els = t.content.querySelectorAll("h1,h2,h3,h4,p,li,td,th");
      for (var i = 0; i < els.length; i++) {
        var el = els[i];
        var txt = el.textContent.replace(/\s+/g, " ").replace(/#$/, "").trim();
        if (el.tagName.charAt(0) === "H") {
          heading = txt; anchor = el.id || "";
          index.push({ id: id, anchor: anchor, heading: heading, text: txt, head: true });
        } else if (txt.length > 2) {
          index.push({ id: id, anchor: anchor, heading: heading, text: txt, head: false });
        }
      }
    });
  }

  function snippet(text, word) {
    var i = text.toLowerCase().indexOf(word);
    var start = Math.max(0, i - 50);
    var end = Math.min(text.length, i + word.length + 90);
    var span = document.createElement("span");
    span.className = "r-snip";
    if (start > 0) span.appendChild(document.createTextNode("…"));
    span.appendChild(document.createTextNode(text.slice(start, i)));
    var m = document.createElement("mark");
    m.textContent = text.slice(i, i + word.length);
    span.appendChild(m);
    span.appendChild(document.createTextNode(text.slice(i + word.length, end)));
    if (end < text.length) span.appendChild(document.createTextNode("…"));
    return span;
  }

  function search(q) {
    var words = q.toLowerCase().split(/\s+/).filter(function (w) { return w.length > 0; });
    results.textContent = "";
    if (q.trim().length < 2 || words.length === 0) { results.hidden = true; return; }
    if (!index) buildIndex();
    var hits = index.filter(function (e) {
      var low = e.text.toLowerCase();
      return words.every(function (w) { return low.indexOf(w) >= 0; });
    });
    hits.sort(function (a, b) { return (b.head ? 1 : 0) - (a.head ? 1 : 0); });
    var seen = {}, shown = [];
    for (var i = 0; i < hits.length && shown.length < 40; i++) {
      var key = hits[i].id + "~" + hits[i].anchor + "~" + (hits[i].head ? "h" : hits[i].text.slice(0, 40));
      if (seen[key]) continue;
      seen[key] = 1;
      shown.push(hits[i]);
    }
    results.hidden = false;
    if (shown.length === 0) {
      var none = document.createElement("p");
      none.className = "r-none";
      none.textContent = "Nothing found for “" + q.trim() + "”.";
      results.appendChild(none);
      return;
    }
    var ul = document.createElement("ul");
    shown.forEach(function (e) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = "#" + e.id + (e.anchor ? "~" + e.anchor : "");
      a.setAttribute("data-doc", e.id);
      if (e.anchor) a.setAttribute("data-anchor", e.anchor);
      var d = document.createElement("span");
      d.className = "r-doc";
      d.textContent = meta[e.id].section + " › " + meta[e.id].label;
      var h = document.createElement("span");
      h.className = "r-head";
      h.textContent = e.heading;
      a.appendChild(d);
      a.appendChild(h);
      if (!e.head) a.appendChild(snippet(e.text, words[0]));
      li.appendChild(a);
      ul.appendChild(li);
    });
    results.appendChild(ul);
  }

  function closeResults() { results.hidden = true; results.textContent = ""; }
  function closeNav() { document.body.classList.remove("nav-open"); menu.setAttribute("aria-expanded", "false"); }

  var timer = null;
  input.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(function () { search(input.value); }, 120);
  });
  input.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { input.value = ""; closeResults(); }
  });
  document.addEventListener("keydown", function (e) {
    var tag = (document.activeElement && document.activeElement.tagName) || "";
    if (e.key === "/" && tag !== "INPUT" && tag !== "TEXTAREA") { e.preventDefault(); input.focus(); }
  });

  menu.addEventListener("click", function () {
    var open = document.body.classList.toggle("nav-open");
    menu.setAttribute("aria-expanded", open ? "true" : "false");
  });

  /* ---- clicks: document links, the skip link, diagram buttons */
  document.addEventListener("click", function (e) {
    var t = e.target;
    if (!(t instanceof Element)) return;
    var btn = t.closest(".dfit, .dfull");
    if (btn) {
      var fig = btn.closest(".diagram");
      var wantFit = btn.classList.contains("dfit");
      var on = btn.getAttribute("aria-pressed") !== "true";
      fig.classList.remove("fit", "full");
      fig.querySelectorAll(".dfit, .dfull").forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
      if (on) { fig.classList.add(wantFit ? "fit" : "full"); btn.setAttribute("aria-pressed", "true"); }
      return;
    }
    var a = t.closest("a");
    if (!a) return;
    if (a.classList.contains("skip")) { e.preventDefault(); docEl.focus(); return; }
    var id = a.getAttribute("data-doc");
    if (id && meta[id] && !e.metaKey && !e.ctrlKey && !e.shiftKey && e.button === 0) {
      e.preventDefault();
      go(id, a.getAttribute("data-anchor") || "");
    }
  });

  function onRoute() { var p = parseHash(); show(p.id, p.anchor); }
  window.addEventListener("hashchange", onRoute);
  window.addEventListener("popstate", onRoute);
  onRoute();
})();
