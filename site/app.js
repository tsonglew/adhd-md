/* adhd-md 官网。无依赖，够用就好。 */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ── 改前 / 改后对照 ───────────────────────────── */
  var STATE = {
    before: { score: 86.4, key: "before" },
    after:  { score: 100,  key: "after"  }
  };

  var tabs = [].slice.call(document.querySelectorAll(".tab"));
  var scoreEl = document.getElementById("score");
  var dims = [].slice.call(document.querySelectorAll(".dim"));
  var current = "before";

  function paintDims(which) {
    dims.forEach(function (d, i) {
      var v = Number(d.dataset[which]);
      var fill = d.querySelector("b");
      var num = d.querySelector("em");
      // 错开一点，六根条同时动会糊成一块
      setTimeout(function () {
        fill.style.width = v + "%";
        num.textContent = v;
      }, reduced ? 0 : i * 45);
    });
  }

  var raf = null;
  function countTo(target) {
    if (raf) cancelAnimationFrame(raf);
    var from = parseFloat(scoreEl.textContent) || 0;
    if (reduced) { scoreEl.textContent = target.toFixed(1); return; }
    var t0 = null, dur = 480;
    function step(ts) {
      if (t0 === null) t0 = ts;
      var p = Math.min(1, (ts - t0) / dur);
      var eased = 1 - Math.pow(1 - p, 3);
      scoreEl.textContent = (from + (target - from) * eased).toFixed(1);
      if (p < 1) raf = requestAnimationFrame(step);
    }
    raf = requestAnimationFrame(step);
  }

  function show(which) {
    if (which === current) return;
    current = which;
    tabs.forEach(function (t) {
      var on = t.id === "tab-" + which;
      t.classList.toggle("is-on", on);
      t.setAttribute("aria-selected", String(on));
      document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
    });
    countTo(STATE[which].score);
    paintDims(which);
  }

  tabs.forEach(function (t) {
    t.addEventListener("click", function () {
      show(t.id.replace("tab-", ""));
    });
    // 左右方向键切换，tablist 的标准交互
    t.addEventListener("keydown", function (e) {
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      e.preventDefault();
      var other = tabs[(tabs.indexOf(t) + 1) % tabs.length];
      other.focus();
      show(other.id.replace("tab-", ""));
    });
  });

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

  /* ── 维度条初始化 ─────────────────────────────
     直接画，不等滚动。等 IntersectionObserver 才画的话，
     打印、全页截图、以及 IO 不可用的环境里六根条永远是 0。 */
  paintDims(current);
})();
