/* adhd-md 官网。无依赖，够用就好。 */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ── 维度条：每维两根，前 = 灰，后 = 蓝 ───────────── */
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

  /* ── 明暗切换 ─────────────────────────────
     三态：没点过 → 跟随系统；点过 → 锁定选择并记住。 */
  var themeBtn = document.getElementById("theme-toggle");

  function themeColor(dark) {
    document.querySelectorAll('meta[name="theme-color"]').forEach(function (meta) {
      meta.setAttribute("content", dark ? "#101720" : "#f7f9fc");
    });
  }

  function updateThemeButton() {
    var dark = document.documentElement.dataset.theme === "dark";
    if (themeBtn) {
      themeBtn.setAttribute("aria-label", dark
        ? themeBtn.dataset.ariaToLight
        : themeBtn.dataset.ariaToDark);
    }
    themeColor(dark);
  }

  if (themeBtn) {
    updateThemeButton();
    themeBtn.addEventListener("click", function () {
      var dark = document.documentElement.dataset.theme === "dark";
      document.documentElement.dataset.theme = dark ? "light" : "dark";
      try { localStorage.setItem("adhd-md-theme", dark ? "light" : "dark"); } catch (e) {}
      updateThemeButton();
    });
  }

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function (event) {
    var saved = null;
    try { saved = localStorage.getItem("adhd-md-theme"); } catch (e) {}
    if (!saved) {
      document.documentElement.dataset.theme = event.matches ? "dark" : "light";
      updateThemeButton();
    }
  });

  var menu = document.getElementById("mobile-menu");
  if (menu) {
    var summary = menu.querySelector("summary");
    menu.addEventListener("toggle", function () {
      summary.setAttribute("aria-label", menu.open ? summary.dataset.closeLabel : summary.dataset.openLabel);
    });
    menu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        menu.open = false;
        if (link.hash) {
          var target = document.getElementById(link.hash.slice(1));
          if (target) {
            target.setAttribute("tabindex", "-1");
            target.focus({ preventScroll: true });
          }
        }
      });
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && menu.open) { menu.open = false; summary.focus(); }
    });
  }

  /* ── 复制按钮 ───────────────────────────── */
  var copyStatus = document.getElementById("copy-status");
  var copySuccess = document.body.dataset.copySuccess || "Copied.";
  var copyFailure = document.body.dataset.copyFailure || "Copy failed. Select and copy the text manually.";

  var statusTimer;
  function announceCopy(message) {
    if (!copyStatus) return;
    clearTimeout(statusTimer);
    copyStatus.textContent = message;
    statusTimer = setTimeout(function () { copyStatus.textContent = ""; }, 5000);
  }

  document.querySelectorAll(".copy").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var src = document.querySelector(btn.dataset.copy);
      if (!src) return;
      var text = src.textContent;
      var done = function () {
        btn.classList.add("done");
        announceCopy(copySuccess);
        setTimeout(function () {
          btn.classList.remove("done");
        }, 1600);
      };
      var failed = function () {
        btn.classList.remove("done");
        announceCopy(copyFailure);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, fallback);
      } else {
        fallback();
      }
      function fallback() {
        var ta = null;
        try {
          ta = document.createElement("textarea");
          ta.value = text;
          ta.style.cssText = "position:fixed;opacity:0";
          document.body.appendChild(ta);
          ta.focus();
          ta.select();
          if (document.execCommand("copy")) done();
          else failed();
        } catch (e) {
          failed();
        } finally {
          if (ta && ta.parentNode) ta.parentNode.removeChild(ta);
          btn.focus({ preventScroll: true });
        }
      }
    });
  });
})();
