// Behaviour for the shadcn checkbox macro (role="checkbox" button).
// Click and Space toggle; Enter does nothing, as in Radix; an indeterminate box becomes checked.
(function () {
  var CHECK = '<svg class="size-3.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>';

  function sync(box, state) {
    box.setAttribute('data-state', state);
    box.setAttribute('aria-checked', state === 'indeterminate' ? 'mixed' : String(state === 'checked'));
    var indicator = box.querySelector('[data-slot="checkbox-indicator"]');
    if (indicator) indicator.innerHTML = state === 'unchecked' ? '' : CHECK;
    var field = box.nextElementSibling;
    if (field && field.tagName === 'INPUT' && field.type === 'checkbox') field.checked = state === 'checked';
  }

  function toggle(box) {
    if (box.disabled) return;
    sync(box, box.getAttribute('data-state') === 'checked' ? 'unchecked' : 'checked');
    box.dispatchEvent(new CustomEvent('checkedchange', { bubbles: true }));
  }

  document.addEventListener('click', function (e) {
    var box = e.target.closest('[data-slot="checkbox"]');
    if (box) toggle(box);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.target.closest && e.target.closest('[data-slot="checkbox"]')) e.preventDefault();
  });
})();
