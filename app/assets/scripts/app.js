// Responsive breakpoints
var mobileBreakpoint = '768px';
var tabletBreakpoint = '992px';
var smallMonitorBreakpoint = '1200px';

document.addEventListener('DOMContentLoaded', function () {
  // Enable dismissable flash messages
  document.querySelectorAll('.message .close').forEach(function(closeBtn) {
    closeBtn.addEventListener('click', function() {
      this.closest('.message').style.display = 'none';
    });
  });

  // Enable mobile navigation
  const openNav = document.getElementById('open-nav');
  if (openNav) {
    openNav.addEventListener('click', function() {
      const mobileMenu = document.querySelector('.mobile.only .vertical.menu');
      if (mobileMenu) {
        mobileMenu.style.display = mobileMenu.style.display === 'none' ? 'block' : 'none';
      }
    });
  }

  // Enable sortable tables (if tablesort.min.js is loaded)
  if (typeof Tablesort !== 'undefined') {
    document.querySelectorAll('table.sortable').forEach(function(table) {
      new Tablesort(table);
    });
  }
});


// Mobile dropdown menu state change
var currentState = [];

function changeMenu(e) {
  var children = e.children[1].innerHTML;
  children += '<a class="item" onClick="back()">Back</a><i class="back icon"></i>';
  const mobileMenu = document.querySelector('.mobile.only .vertical.menu');
  if (mobileMenu) {
    currentState.push(mobileMenu.innerHTML);
    mobileMenu.innerHTML = children;
  }
}

function back() {
  const mobileMenu = document.querySelector('.mobile.only .vertical.menu');
  if (mobileMenu && currentState.length > 0) {
    mobileMenu.innerHTML = currentState.pop();
  }
}

// Load Documentation Enhancement components
// Note: This would typically be loaded as a separate module
// For demo purposes, included inline

// Initialize docs enhancements when available
if (document.querySelector('[data-code-examples], [data-search-filter], [data-version-history], [data-api-docs]')) {
  // Load docs-enhancements.js functionality
  const script = document.createElement('script');
  script.src = '/static/scripts/docs-enhancements.js';
  script.async = true;
  document.head.appendChild(script);
}
