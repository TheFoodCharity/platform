// Duration must match the @keyframes toast-dismiss animation in styles.css
const DISMISS_DELAY_MS = 3300;

function armToast(el) {
  if (el.dataset.toastArmed) return;
  el.dataset.toastArmed = "1";
  setTimeout(() => el.remove(), DISMISS_DELAY_MS);
}

const observer = new MutationObserver((mutations) => {
  for (const mutation of mutations) {
    for (const node of mutation.addedNodes) {
      if (node.nodeType === Node.ELEMENT_NODE && node.classList.contains("toast-item")) {
        armToast(node);
      }
    }
  }
});

function connectObserver() {
  const container = document.getElementById("toasts");
  if (!container) return;

  // Arm toasts already in the container (e.g. rendered inline on full page load)
  container.querySelectorAll(".toast-item").forEach(armToast);

  observer.disconnect();
  observer.observe(container, {childList: true});
}

// DOMContentLoaded for initial page load; htmx:afterSwap reconnects the
// observer to the new #toasts element after hx-boost replaces the body.
document.addEventListener("DOMContentLoaded", connectObserver);
document.addEventListener("htmx:afterSwap", connectObserver);
