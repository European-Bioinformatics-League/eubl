(function () {
  const opening = new Date("2026-10-23T21:00:00+01:00");
  const closing = new Date("2026-10-24T09:00:00+01:00");

  const link = document.getElementById("test-link");
  const status = document.getElementById("test-status");

  if (!link || !status) return;

  function updateButton() {
    const now = new Date();

    if (now < opening) {
      status.textContent = "Registration NOT YET OPEN";
      link.removeAttribute("href");
      link.style.background = "#777";
      link.style.pointerEvents = "none";
      link.setAttribute("aria-disabled", "true");

    } else if (now < closing) {
      status.textContent = "Registration OPEN";
      link.href = "https://eubl.org/";
      link.style.background = "#16803c";
      link.style.pointerEvents = "auto";
      link.removeAttribute("aria-disabled");

    } else {
      status.textContent = "Registration CLOSED";
      link.removeAttribute("href");
      link.style.background = "#777";
      link.style.pointerEvents = "none";
      link.setAttribute("aria-disabled", "true");
    }
  }

  updateButton();
  setInterval(updateButton, 1000);
  document.addEventListener("visibilitychange", updateButton);
})();
