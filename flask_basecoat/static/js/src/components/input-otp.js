/* Input OTP: a visually hidden input drives the slot cells; typing, paste, Backspace and arrow keys update the
   active slot (data-active) and the rendered characters, with a fake caret in the active empty slot. */
(function (FB) {
  'use strict';

  FB.register('input-otp', {
    init(input) {
      const container = input.closest('[data-input-otp-container]') || input.parentElement;
      const slots = () => FB.qsa(container, '[data-slot="input-otp-slot"]');
      const maxLength = Number(input.getAttribute('maxlength') || slots().length || 6);
      input.setAttribute('maxlength', String(maxLength));
      const pattern = input.getAttribute('pattern') ? new RegExp(input.getAttribute('pattern')) : null;
      function render() {
        const value = input.value;
        const focused = document.activeElement === input;
        const caret = Math.min(value.length, maxLength - 1);
        slots().forEach((s, i) => {
          const ch = value[i] || '';
          let text = FB.qs(s, '[data-fb-otp-char]');
          if (!text) { text = document.createElement('span'); text.setAttribute('data-fb-otp-char', ''); s.insertBefore(text, s.firstChild); }
          text.textContent = ch;
          const active = focused && (i === caret || (value.length === maxLength && i === maxLength - 1));
          s.setAttribute('data-active', String(active));
          let fake = FB.qs(s, '[data-fb-otp-caret]');
          if (active && !ch) {
            if (!fake) { fake = document.createElement('div'); fake.setAttribute('data-fb-otp-caret', ''); fake.className = 'pointer-events-none absolute inset-0 flex items-center justify-center'; fake.innerHTML = '<div class="h-4 w-px bg-foreground animate-caret-blink duration-1000"></div>'; s.appendChild(fake); }
          } else if (fake) fake.remove();
        });
        input.setAttribute('data-input-otp-placeholder-shown', String(!value.length));
        if (value.length === maxLength) FB.emit(input, 'complete', { value });
      }
      input.addEventListener('input', () => {
        let v = input.value.replace(/\s+/g, '');
        if (pattern) v = v.split('').filter((c) => pattern.test(c)).join('');
        input.value = v.slice(0, maxLength);
        render();
        FB.emit(input, 'change', { value: input.value });
      });
      input.addEventListener('focus', render);
      input.addEventListener('blur', render);
      container.addEventListener('click', () => input.focus());
      render();
    },
  });
})(window.FlaskBasecoat);
