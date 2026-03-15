/**
 * Gallery — Urban Wildlife India
 * Category filters and mobile nav toggle.
 * PhotoSwipe is initialised inline on single photo pages only.
 */

/* ── Category Filters ── */
function initFilters() {
  const buttons = document.querySelectorAll(".filter-btn");
  const items   = document.querySelectorAll(".gallery-item");

  if (!buttons.length || !items.length) return;

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      const filter = btn.dataset.filter;

      items.forEach((item) => {
        // data-categories holds a space-separated list of all category slugs
        const cats = (item.dataset.categories || item.dataset.category || "").split(" ");
        const matches = filter === "all" || cats.includes(filter);
        item.classList.toggle("hidden", !matches);
      });
    });
  });
}

/* ── Mobile Nav Toggle ── */
function initNav() {
  const toggle = document.querySelector(".nav-toggle");
  const links  = document.querySelector(".nav-links");
  if (!toggle || !links) return;

  toggle.addEventListener("click", () => {
    const open = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initFilters();
  initNav();
});
