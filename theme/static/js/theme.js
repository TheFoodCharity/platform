function setupPasswordInput(el) {
  const input = el.querySelector("input");
  const btn = el.querySelector("button");
  const icon = btn.querySelector(".material-symbols-rounded");

  btn.addEventListener("click", () => {
    const visible = input.type === "text";
    input.type = visible ? "password" : "text";
    icon.textContent = visible ? "visibility_off" : "visibility";
  });
}

function findPasswordInputs(root) {
  const results = [];
  if (root.matches?.(".password-input")) results.push(root);
  root.querySelectorAll?.(".password-input").forEach((el) => results.push(el));
  return results;
}

const observer = new MutationObserver((mutations) => {
  for (const mutation of mutations) {
    for (const node of mutation.addedNodes) {
      if (node.nodeType !== Node.ELEMENT_NODE) continue;
      findPasswordInputs(node).forEach(setupPasswordInput);
    }
  }
});

observer.observe(document.body, {subtree: true, childList: true});
document.querySelectorAll(".password-input").forEach(setupPasswordInput);
