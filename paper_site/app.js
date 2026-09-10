/* minimal progressive enhancement: TOC active-section highlight + smooth top link */
(function () {
  "use strict";
  var toc = document.querySelector(".toc-inner");
  if (toc) {
    var links = Array.prototype.slice.call(toc.querySelectorAll("a"));
    var targets = links
      .map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); })
      .filter(Boolean);
    if ("IntersectionObserver" in window && targets.length) {
      var seen = new Set();
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) seen.add(e.target.id); else seen.delete(e.target.id);
        });
        var current = targets.filter(function (t) { return seen.has(t.id); })[0];
        links.forEach(function (a) {
          a.classList.toggle("active", current && a.getAttribute("href") === "#" + current.id);
        });
      }, { rootMargin: "-10% 0px -70% 0px" });
      targets.forEach(function (t) { io.observe(t); });
    }
  }
})();
