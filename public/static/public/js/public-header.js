(() => {
  const header = document.getElementById("public-site-header");
  const langMenu = document.getElementById("lang-menu");

  if (header) {
    const setHeaderShadow = () => {
      header.classList.toggle("public-header-scrolled", window.scrollY > 8);
    };

    setHeaderShadow();
    window.addEventListener("scroll", setHeaderShadow, { passive: true });
  }

  if (langMenu) {
    document.addEventListener("click", (event) => {
      if (!langMenu.hasAttribute("open")) return;
      if (langMenu.contains(event.target)) return;
      langMenu.removeAttribute("open");
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        langMenu.removeAttribute("open");
      }
    });
  }
})();
