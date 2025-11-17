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

  // Enable sortable tables (if tablesort.min.js is loaded)
  if (typeof Tablesort !== 'undefined') {
    document.querySelectorAll('table.sortable').forEach(function(table) {
      new Tablesort(table);
    });
  }
});
