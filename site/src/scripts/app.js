/* adhd-md 官网。无依赖，够用就好。 */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ── 维度条：每维两根，前 = 灰，后 = 红 ───────────── */
  var dims = [].slice.call(document.querySelectorAll(".dim"));

  function paintDims() {
    dims.forEach(function (d, i) {
      var before = Number(d.dataset.before);
      var after = Number(d.dataset.after);
      var barB = d.querySelector(".b-before b");
      var barA = d.querySelector(".b-after b");
      var num = d.querySelector("em");
      // 错开一点，七根条同时动会糊成一块
      setTimeout(function () {
        barB.style.width = before + "%";
        barA.style.width = after + "%";
        num.textContent = before === after ? String(after) : before + " → " + after;
      }, reduced ? 0 : i * 45);
    });
  }

  // 直接画，不等滚动。等滚动才画的话，打印、全页截图、
  // 以及 IntersectionObserver 不可用的环境里条永远是空的。
  paintDims();

  /* ── 复制按钮 ───────────────────────────── */
  document.querySelectorAll(".copy").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var src = document.querySelector(btn.dataset.copy);
      if (!src) return;
      var text = src.textContent;
      var done = function () {
        var old = btn.textContent;
        btn.textContent = "已复制";
        btn.classList.add("done");
        setTimeout(function () {
          btn.textContent = old;
          btn.classList.remove("done");
        }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, fallback);
      } else {
        fallback();
      }
      function fallback() {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.style.cssText = "position:fixed;opacity:0";
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); done(); } catch (e) { /* 复制不了就算了 */ }
        document.body.removeChild(ta);
      }
    });
  });
})();
