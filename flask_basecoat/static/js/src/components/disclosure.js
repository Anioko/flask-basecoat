/* Accordion, Collapsible and Trace collapsible: expand/collapse regions with data-state and aria-expanded. */
(function (FB) {
  'use strict';

  function heightVar(content, name) {
    content.style.setProperty(name, `${content.scrollHeight}px`);
  }

  function toggleContent(trigger, content, open, varName) {
    const item = trigger.closest('[data-slot$="-item"], [data-slot="collapsible"], [data-slot="trace-collapsible"]');
    if (open) {
      content.removeAttribute('hidden');
      FB.setState(content, 'open');
      heightVar(content, varName);
    } else {
      heightVar(content, varName);
      FB.setState(content, 'closed');
      content.setAttribute('data-fb-animating', '');
      setTimeout(() => { if (content.getAttribute('data-state') === 'closed') { content.setAttribute('hidden', ''); content.removeAttribute('data-fb-animating'); } }, 220);
    }
    FB.setState(trigger, open ? 'open' : 'closed');
    trigger.setAttribute('aria-expanded', String(open));
    if (item) FB.setState(item, open ? 'open' : 'closed');
  }

  FB.register('accordion', {
    init(root) {
      const type = root.getAttribute('data-type') || 'single';
      const collapsible = root.getAttribute('data-collapsible') !== 'false';
      const items = FB.qsa(root, '[data-slot="accordion-item"]').filter((i) => i.closest('[data-slot="accordion"]') === root);
      const pairs = items.map((item) => {
        const trigger = FB.qs(item, '[data-slot="accordion-trigger"]');
        const content = FB.qs(item, '[data-slot="accordion-content"]');
        if (!trigger || !content) return null;
        trigger.setAttribute('aria-controls', FB.ensureId(content, 'accordion-content'));
        content.setAttribute('aria-labelledby', FB.ensureId(trigger, 'accordion-trigger'));
        return { item, trigger, content };
      }).filter(Boolean);
      const triggers = () => pairs.map((p) => p.trigger);
      const nav = FB.roving(triggers, { orientation: root.getAttribute('data-orientation') === 'horizontal' ? 'horizontal' : 'vertical', loop: true, typeahead: false });
      pairs.forEach((p) => {
        p.trigger.addEventListener('click', (e) => {
          e.preventDefault();
          const isOpen = p.trigger.getAttribute('aria-expanded') === 'true';
          if (type === 'single') {
            pairs.forEach((o) => { if (o !== p && o.trigger.getAttribute('aria-expanded') === 'true') toggleContent(o.trigger, o.content, false, '--radix-accordion-content-height'); });
            if (isOpen && !collapsible) return;
          }
          toggleContent(p.trigger, p.content, !isOpen, '--radix-accordion-content-height');
          FB.emit(root, 'change', { value: p.item.getAttribute('data-value'), open: !isOpen });
        });
        p.trigger.addEventListener('keydown', nav);
      });
    },
  });

  function collapsible(kind) {
    return {
      init(root) {
        const trigger = FB.qs(root, `[data-slot="${kind}-trigger"]`);
        const content = FB.qs(root, `[data-slot="${kind}-content"]`);
        if (!trigger || !content) return;
        trigger.setAttribute('aria-controls', FB.ensureId(content, `${kind}-content`));
        trigger.addEventListener('click', (e) => {
          e.preventDefault();
          const isOpen = trigger.getAttribute('aria-expanded') === 'true';
          toggleContent(trigger, content, !isOpen, '--radix-collapsible-content-height');
          FB.emit(root, 'change', { open: !isOpen });
        });
      },
    };
  }
  FB.register('collapsible', collapsible('collapsible'));
  FB.register('trace-collapsible', collapsible('trace-collapsible'));
})(window.FlaskBasecoat);
