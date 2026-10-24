(() => {
  // Basecoat's select.js preselects the first option; shadcn's placeholder state has no value.
  // Runs after Basecoat's DOMContentLoaded initialiser and restores the placeholder until the user chooses.
  const restorePlaceholder = (root) => {
    const trigger = root.querySelector(':scope > button');
    const label = trigger && trigger.querySelector('[data-slot="select-value"]');
    const input = root.querySelector(':scope > input[type="hidden"]');
    if (!label || !input) return;
    label.textContent = root.dataset.placeholderText;
    input.value = '';
    root.querySelectorAll('[role="option"][aria-selected="true"]').forEach((opt) => opt.removeAttribute('aria-selected'));
    trigger.setAttribute('data-placeholder', '');
    root.addEventListener('change', () => trigger.removeAttribute('data-placeholder'), { once: true });
  };

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-slot="select"][data-placeholder-text]').forEach(restorePlaceholder);
  });
})();
