/* Sidebar: expanded/collapsed state on the sidebar root (offcanvas or icon mode), trigger and rail toggles,
   keyboard shortcut Ctrl/Cmd+B, state remembered in a cookie like upstream, and a mobile sheet below 768px. */
(function (FB) {
  'use strict';

  const COOKIE = 'sidebar_state';
  const MOBILE = 768;

  FB.register('sidebar-wrapper', {
    init(wrapper) {
      const sidebars = FB.qsa(wrapper, '[data-slot="sidebar"]').filter((s) => s.closest('[data-slot="sidebar-wrapper"]') === wrapper);
      const sidebar = sidebars[0];
      if (!sidebar) return;
      const collapsible = sidebar.getAttribute('data-collapsible-mode') || (sidebar.hasAttribute('data-collapsible') ? 'offcanvas' : 'none');
      let open = sidebar.getAttribute('data-state') !== 'collapsed';
      const match = document.cookie.match(new RegExp(`(?:^|; )${COOKIE}=(true|false)`));
      if (match) open = match[1] === 'true';
      let mobileOpen = false;
      const isMobile = () => window.innerWidth < MOBILE;

      function apply() {
        if (collapsible === 'none') return;
        sidebar.setAttribute('data-state', open ? 'expanded' : 'collapsed');
        sidebar.setAttribute('data-collapsible', open ? '' : collapsible);
        FB.emit(wrapper, 'sidebar', { open });
      }
      function toggle() {
        if (isMobile()) { mobileOpen = !mobileOpen; applyMobile(); return; }
        open = !open;
        document.cookie = `${COOKIE}=${open}; path=/; max-age=${60 * 60 * 24 * 7}`;
        apply();
      }
      // Mobile: the sidebar content is shown inside a sheet-like overlay on small screens.
      let mobileSheet = null;
      function applyMobile() {
        if (!mobileSheet) {
          mobileSheet = document.createElement('div');
          mobileSheet.setAttribute('data-fb-sidebar-mobile', '');
          mobileSheet.className = 'fixed inset-0 z-50 hidden';
          mobileSheet.innerHTML = '<div data-slot="sheet-overlay" data-state="open" class="cn-sheet-overlay fixed inset-0 z-50 bg-black/50"></div>' +
            '<div data-slot="sheet-content" data-state="open" data-side="left" role="dialog" aria-modal="true" data-sidebar="sidebar" data-mobile="true" class="cn-sheet-content fixed inset-y-0 left-0 z-50 flex h-full w-(--sidebar-width) flex-col bg-sidebar p-0 text-sidebar-foreground"><div class="flex h-full w-full flex-col" data-fb-mobile-slot></div></div>';
          mobileSheet.style.setProperty('--sidebar-width', '18rem');
          document.body.appendChild(mobileSheet);
          mobileSheet.firstElementChild.addEventListener('click', () => { mobileOpen = false; applyMobile(); });
        }
        const slot = FB.qs(mobileSheet, '[data-fb-mobile-slot]');
        const inner = FB.qs(sidebar, '[data-slot="sidebar-inner"]');
        if (mobileOpen) {
          mobileSheet.classList.remove('hidden');
          if (inner && inner.parentNode !== slot) { inner.fbHome = inner.parentNode; slot.appendChild(inner); }
          FB.lockScroll();
          FB.pushLayer(mobileSheet.fbLayer = { content: mobileSheet.lastElementChild, modal: true, onDismiss: () => { mobileOpen = false; applyMobile(); } });
        } else {
          mobileSheet.classList.add('hidden');
          if (inner && inner.fbHome) { inner.fbHome.appendChild(inner); }
          FB.unlockScroll();
          if (mobileSheet.fbLayer) { FB.removeLayer(mobileSheet.fbLayer); mobileSheet.fbLayer = null; }
        }
      }
      wrapper.addEventListener('click', (e) => {
        const t = e.target.closest('[data-slot="sidebar-trigger"], [data-slot="sidebar-rail"]');
        if (t && wrapper.contains(t)) { e.preventDefault(); toggle(); }
      });
      document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'b') { e.preventDefault(); toggle(); }
      });
      // Menu buttons marked data-active reflect the current page; links with the current path get it too.
      FB.qsa(wrapper, '[data-slot="sidebar-menu-button"][href], [data-slot="sidebar-menu-sub-button"][href]').forEach((a) => {
        try {
          const url = new URL(a.getAttribute('href'), location.href);
          if (url.pathname === location.pathname && a.getAttribute('data-active') === null) a.setAttribute('data-active', 'true');
        } catch (e) { /* ignore */ }
      });
      // Collapsible groups inside the sidebar use the generic collapsible module.
      apply();
      wrapper.fbToggle = toggle;
    },
  });
})(window.FlaskBasecoat);
