/**
 * Sidebar Component - JavaScript state management
 * Implements collapsible sidebar with shadcn/ui-inspired behavior
 */

class Sidebar {
  constructor(sidebarElement) {
    this.sidebar = sidebarElement;
    this.id = sidebarElement.id;
    this.state = sidebarElement.dataset.state || 'expanded';
    this.spacer = document.getElementById(`${this.id}-spacer`);

    this.init();
  }

  init() {
    // Toggle button
    const toggleBtn = this.sidebar.querySelector('.sidebar-toggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => this.toggle());
    }

    // Collapsible groups
    const groupTriggers = this.sidebar.querySelectorAll('.sidebar-group-trigger');
    groupTriggers.forEach(trigger => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggleGroup(trigger.closest('.sidebar-group'));
      });
    });

    // User menu (placeholder for future dropdown)
    const userMenuBtn = this.sidebar.querySelector('.sidebar-user-menu');
    if (userMenuBtn) {
      userMenuBtn.addEventListener('click', () => {
        console.log('User menu clicked - implement dropdown here');
      });
    }

    // Restore state from localStorage
    const savedState = localStorage.getItem(`sidebar-${this.id}-state`);
    if (savedState) {
      this.setState(savedState);
    }
  }

  toggle() {
    const newState = this.state === 'expanded' ? 'collapsed' : 'expanded';
    this.setState(newState);
  }

  setState(state) {
    this.state = state;
    this.sidebar.dataset.state = state;

    if (state === 'collapsed') {
      this.sidebar.style.width = '4rem';
      if (this.spacer) {
        this.spacer.style.marginLeft = '4rem';
      }

      // Hide labels and user info
      this.sidebar.querySelectorAll('.sidebar-label').forEach(el => {
        el.classList.add('opacity-0', 'w-0', 'overflow-hidden');
      });
      this.sidebar.querySelectorAll('.sidebar-user-info').forEach(el => {
        el.classList.add('hidden');
      });
      this.sidebar.querySelectorAll('.sidebar-chevron').forEach(el => {
        el.classList.add('hidden');
      });

      // Collapse all groups
      this.sidebar.querySelectorAll('.sidebar-group').forEach(group => {
        this.collapseGroup(group);
      });

    } else {
      this.sidebar.style.width = '16rem';
      if (this.spacer) {
        this.spacer.style.marginLeft = '16rem';
      }

      // Show labels and user info
      this.sidebar.querySelectorAll('.sidebar-label').forEach(el => {
        el.classList.remove('opacity-0', 'w-0', 'overflow-hidden');
      });
      this.sidebar.querySelectorAll('.sidebar-user-info').forEach(el => {
        el.classList.remove('hidden');
      });
      this.sidebar.querySelectorAll('.sidebar-chevron').forEach(el => {
        el.classList.remove('hidden');
      });
    }

    // Save state to localStorage
    localStorage.setItem(`sidebar-${this.id}-state`, state);
  }

  toggleGroup(group) {
    if (this.state === 'collapsed') return; // Don't allow group toggle when sidebar is collapsed

    const currentState = group.dataset.state || 'collapsed';
    const newState = currentState === 'collapsed' ? 'expanded' : 'collapsed';

    if (newState === 'expanded') {
      this.expandGroup(group);
    } else {
      this.collapseGroup(group);
    }
  }

  expandGroup(group) {
    group.dataset.state = 'expanded';
    const content = group.querySelector('.sidebar-group-content');
    const chevron = group.querySelector('.sidebar-chevron');

    if (content) {
      content.classList.remove('hidden');
    }
    if (chevron) {
      chevron.style.transform = 'rotate(90deg)';
    }
  }

  collapseGroup(group) {
    group.dataset.state = 'collapsed';
    const content = group.querySelector('.sidebar-group-content');
    const chevron = group.querySelector('.sidebar-chevron');

    if (content) {
      content.classList.add('hidden');
    }
    if (chevron) {
      chevron.style.transform = 'rotate(0deg)';
    }
  }
}

// Initialize all sidebars on page load
document.addEventListener('DOMContentLoaded', function() {
  const sidebars = document.querySelectorAll('.sidebar');
  sidebars.forEach(sidebar => {
    new Sidebar(sidebar);
  });
});

// Mobile responsiveness - auto-collapse on small screens
window.addEventListener('resize', function() {
  const sidebars = document.querySelectorAll('.sidebar');
  if (window.innerWidth < 768) {
    sidebars.forEach(sidebar => {
      // On mobile, could implement overlay behavior
      // For now, just hide the sidebar
      sidebar.classList.add('hidden');
      const spacer = document.getElementById(`${sidebar.id}-spacer`);
      if (spacer) {
        spacer.style.marginLeft = '0';
      }
    });
  } else {
    sidebars.forEach(sidebar => {
      sidebar.classList.remove('hidden');
    });
  }
});
