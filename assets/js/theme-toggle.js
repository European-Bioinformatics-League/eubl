// Light/dark theme toggle in the header.
// The site follows the system setting by default. Clicking the button switches
// to the other theme and remembers the choice in localStorage ("theme"); if the
// choice matches the system setting, the override is dropped, so the site goes
// back to following the system.
(function () {
  var button = document.querySelector(".theme-toggle");
  if (!button) return;
  var root = document.documentElement;
  var system = window.matchMedia("(prefers-color-scheme: dark)");

  function systemTheme() { return system.matches ? "dark" : "light"; }
  function currentTheme() { return root.getAttribute("data-theme") || systemTheme(); }

  function update() {
    var current = currentTheme();
    var next = current === "dark" ? "light" : "dark";
    button.setAttribute("data-current", current);
    button.setAttribute("aria-label", "Switch to " + next + " theme");
    button.title = "Switch to " + next + " theme";
  }

  button.addEventListener("click", function () {
    var next = currentTheme() === "dark" ? "light" : "dark";
    try {
      if (next === systemTheme()) {
        root.removeAttribute("data-theme");
        localStorage.removeItem("theme");
      } else {
        root.setAttribute("data-theme", next);
        localStorage.setItem("theme", next);
      }
    } catch (e) {
      root.setAttribute("data-theme", next);
    }
    update();
  });
  if (system.addEventListener) system.addEventListener("change", update);

  button.hidden = false;
  update();
})();
