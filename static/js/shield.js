/**
 * Image Shielding — Urban Wildlife India
 *
 * Layers:
 *  1. Block context menu on all gallery surfaces (background-image divs, stage, shields).
 *  2. Block keyboard shortcuts: Ctrl/Cmd+S, U, F12, DevTools combos.
 *  3. Block drag on any <img> element (PhotoSwipe internal ones, etc.).
 *  4. Prevent text/selection on gallery surfaces.
 *
 * NOTE: CSS background-image (used for all gallery tiles and the single photo stage)
 * already prevents the "Save Image As" browser menu item on the painted surface.
 * This script adds a second layer for completeness.
 */
(function () {
  "use strict";

  const GALLERY_SELECTORS = [
    "img",
    ".img-shield",
    ".img-bg",
    ".img-wrap",
    ".gallery-item",
    ".photo-stage",
    ".photo-full",
    ".footnav-thumb",
  ];

  function isGallerySurface(el) {
    return GALLERY_SELECTORS.some((sel) => el.closest(sel));
  }

  /* 1 ── Context menu */
  document.addEventListener("contextmenu", (e) => {
    if (isGallerySurface(e.target)) {
      e.preventDefault();
      return false;
    }
  });

  /* 2 ── Keyboard shortcuts */
  document.addEventListener("keydown", (e) => {
    const ctrl = e.ctrlKey || e.metaKey;

    if (e.key === "F12")                            { e.preventDefault(); return false; }
    if (ctrl && e.key.toLowerCase() === "s")        { e.preventDefault(); return false; }
    if (ctrl && e.key.toLowerCase() === "u")        { e.preventDefault(); return false; }
    if (ctrl && e.shiftKey && e.key === "I")        { e.preventDefault(); return false; }
    if (ctrl && e.shiftKey && e.key === "C")        { e.preventDefault(); return false; }
    if (ctrl && e.shiftKey && e.key === "J")        { e.preventDefault(); return false; }
  });

  /* 3 ── Drag prevention on any <img> (e.g. PhotoSwipe internal images) */
  document.addEventListener("dragstart", (e) => {
    if (e.target.tagName === "IMG") e.preventDefault();
  });

  /* 4 ── Selection prevention on gallery surfaces */
  document.addEventListener("selectstart", (e) => {
    if (isGallerySurface(e.target)) e.preventDefault();
  });
})();
