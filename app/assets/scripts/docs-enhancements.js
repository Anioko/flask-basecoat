/**
 * Documentation Enhancement Components JavaScript
 * Provides interactive functionality for documentation and learning tools
 */

class DocumentationEnhancements {
  constructor() {
    this.init();
  }

  init() {
    this.initCodeExamples();
    this.initSearchFilter();
    this.initVersionHistory();
    this.initApiDocs();
  }

  /**
   * Code Examples functionality
   */
  initCodeExamples() {
    // Basic code examples
    document.querySelectorAll('[data-code-examples]').forEach(container => {
      const mode = container.querySelector('.examples-basic, .examples-playground, .examples-tutorial') ? 
                   (container.querySelector('.examples-basic') ? 'basic' : 
                    container.querySelector('.examples-playground') ? 'playground' : 'tutorial') : 'basic';

      switch (mode) {
        case 'basic':
          this.initBasicCodeExamples(container);
          break;
        case 'playground':
          this.initPlaygroundExamples(container);
          break;
        case 'tutorial':
          this.initTutorialExamples(container);
          break;
      }
    });
  }

  initBasicCodeExamples(container) {
    // Copy functionality
    container.querySelectorAll('[data-action="copy"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const codeContent = container.querySelector('.code-content');
        if (codeContent) {
          navigator.clipboard.writeText(codeContent.textContent).then(() => {
            this.showToast('Code copied to clipboard!');
          });
        }
      });
    });

    // Run functionality
    container.querySelectorAll('[data-action="run"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const codeContent = container.querySelector('.code-content');
        const resultContent = container.querySelector('[data-result]');
        
        if (codeContent && resultContent) {
          try {
            // For HTML content, update the result display
            if (codeContent.dataset.language === 'html') {
              resultContent.innerHTML = codeContent.textContent;
            }
            // For other languages, show execution feedback
            else {
              this.showToast('Code executed successfully!');
            }
          } catch (error) {
            this.showToast('Error executing code: ' + error.message, 'error');
          }
        }
      });
    });

    // Live editing
    container.querySelectorAll('.code-content[contenteditable]').forEach(editor => {
      editor.addEventListener('input', this.debounce(() => {
        const resultContent = container.querySelector('[data-result]');
        if (resultContent && editor.dataset.language === 'html') {
          try {
            resultContent.innerHTML = editor.textContent;
          } catch (error) {
            console.error('Live preview error:', error);
          }
        }
      }, 300));
    });
  }

  initPlaygroundExamples(container) {
    // Example library interaction
    container.querySelectorAll('[data-example]').forEach(item => {
      item.addEventListener('click', () => {
        const exampleType = item.dataset.example;
        const editor = container.querySelector('.code-editor-full');
        
        if (editor) {
          const templates = {
            button: `<button class="btn btn-primary">Click Me</button>`,
            card: `<div class="card">
  <div class="card-header">
    <h3>Card Title</h3>
  </div>
  <div class="card-content">
    <p>Card content goes here.</p>
  </div>
</div>`
          };
          
          editor.value = templates[exampleType] || '';
          this.updatePlaygroundPreview(container);
        }
      });
    });

    // Live preview updates
    const editor = container.querySelector('.code-editor-full');
    if (editor) {
      editor.addEventListener('input', this.debounce(() => {
        this.updatePlaygroundPreview(container);
      }, 500));
    }
  }

  updatePlaygroundPreview(container) {
    const editor = container.querySelector('.code-editor-full');
    const preview = container.querySelector('.preview-frame');
    
    if (editor && preview) {
      const html = `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body { padding: 20px; font-family: system-ui; }
            .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }
            .btn-primary { background: #3b82f6; color: white; }
            .card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; }
            .card-header { margin-bottom: 12px; }
            .card-content { color: #6b7280; }
          </style>
        </head>
        <body>
          ${editor.value}
        </body>
        </html>
      `;
      
      // Update iframe content
      preview.srcdoc = html;
    }
  }

  initTutorialExamples(container) {
    // Progress tracking
    const progressBar = container.querySelector('.progress-fill');
    const progressText = container.querySelector('.progress-text');
    
    // Task validation
    container.querySelectorAll('.task-input').forEach(input => {
      input.addEventListener('input', () => {
        this.validateTutorialTask(container, input);
      });
    });

    // Navigation
    container.querySelectorAll('.tutorial-nav').forEach(nav => {
      nav.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (action === 'next' || action === 'prev') {
          this.navigateTutorial(container, action);
        }
      });
    });
  }

  validateTutorialTask(container, input) {
    const value = input.value.trim();
    const step = input.closest('[data-step]');
    
    if (step) {
      const stepNumber = parseInt(step.dataset.step);
      
      // Simple validation examples
      const validations = {
        2: (code) => code.includes('.btn') && code.includes('padding'),
        3: (code) => code.includes('border-radius'),
        4: (code) => code.includes('hover')
      };
      
      const isValid = validations[stepNumber] ? validations[stepNumber](value) : value.length > 0;
      
      if (isValid) {
        input.style.borderColor = '#22c55e';
        this.showToast('Task completed!', 'success');
      } else {
        input.style.borderColor = '#ef4444';
      }
    }
  }

  /**
   * Search Filter functionality
   */
  initSearchFilter() {
    document.querySelectorAll('[data-search-filter]').forEach(container => {
      const type = container.querySelector('.global-search') ? 'global' :
                   container.querySelector('.faceted-search') ? 'faceted' : 'visual';

      switch (type) {
        case 'global':
          this.initGlobalSearch(container);
          break;
        case 'faceted':
          this.initFacetedSearch(container);
          break;
        case 'visual':
          this.initVisualSearch(container);
          break;
      }
    });
  }

  initGlobalSearch(container) {
    const searchInput = container.querySelector('[data-global-search]');
    const searchResults = container.querySelector('[data-search-results]');
    
    if (searchInput && searchResults) {
      searchInput.addEventListener('input', this.debounce(() => {
        const query = searchInput.value.toLowerCase();
        this.performGlobalSearch(query, searchResults);
      }, 300));
    }
  }

  performGlobalSearch(query, resultsContainer) {
    // Mock search results
    const mockResults = [
      { icon: '🔘', title: 'Button', description: 'Interactive button component' },
      { icon: '📄', title: 'Card', description: 'Content container component' },
      { icon: '📝', title: 'Form', description: 'Form input components' },
      { icon: '🎨', title: 'Theme', description: 'Theme customization tools' }
    ];

    const filtered = mockResults.filter(item => 
      item.title.toLowerCase().includes(query) || 
      item.description.toLowerCase().includes(query)
    );

    resultsContainer.innerHTML = filtered.map(item => `
      <div class="result-item">
        <div class="result-icon">${item.icon}</div>
        <div class="result-content">
          <h5>${item.title}</h5>
          <p>${item.description}</p>
        </div>
      </div>
    `).join('');
  }

  initFacetedSearch(container) {
    const searchInput = container.querySelector('[data-faceted-search]');
    const filters = container.querySelectorAll('.filter-option input[type="checkbox"]');
    const resultsGrid = container.querySelector('.search-results-grid');

    // Search input
    if (searchInput) {
      searchInput.addEventListener('input', this.debounce(() => {
        this.performFacetedSearch(container);
      }, 300));
    }

    // Filter checkboxes
    filters.forEach(filter => {
      filter.addEventListener('change', () => {
        this.performFacetedSearch(container);
      });
    });
  }

  performFacetedSearch(container) {
    const query = container.querySelector('[data-faceted-search]').value.toLowerCase();
    const activeFilters = Array.from(container.querySelectorAll('.filter-option input:checked')).map(cb => cb.value);
    const resultsGrid = container.querySelector('.search-results-grid');

    // Mock filtering logic
    const mockData = [
      { type: 'component', icon: '🔘', title: 'Button Component', description: 'Interactive button with variants' },
      { type: 'docs', icon: '📖', title: 'Button Documentation', description: 'How to use button components' },
      { type: 'component', icon: '📄', title: 'Card Component', description: 'Content container with flexible layout' }
    ];

    const filtered = mockData.filter(item => {
      const matchesQuery = item.title.toLowerCase().includes(query) || item.description.toLowerCase().includes(query);
      const matchesFilter = activeFilters.length === 0 || activeFilters.includes(item.type);
      return matchesQuery && matchesFilter;
    });

    resultsGrid.innerHTML = filtered.map(item => `
      <div class="result-card">
        <div class="card-icon">${item.icon}</div>
        <div class="card-content">
          <h4>${item.title}</h4>
          <p>${item.description}</p>
        </div>
      </div>
    `).join('');
  }

  initVisualSearch(container) {
    const componentOptions = container.querySelectorAll('[data-component]');
    const visualResults = container.querySelector('.visual-results');

    componentOptions.forEach(option => {
      option.addEventListener('click', () => {
        // Remove active state from all options
        componentOptions.forEach(opt => opt.classList.remove('active'));
        option.classList.add('active');

        const componentType = option.dataset.component;
        this.updateVisualResults(visualResults, componentType);
      });
    });
  }

  updateVisualResults(resultsContainer, componentType) {
    const previews = {
      button: [
        '<button class="btn btn-primary">Primary Button</button>',
        '<button class="btn btn-secondary">Secondary Button</button>',
        '<button class="btn btn-outline">Outline Button</button>'
      ],
      card: [
        '<div class="card"><div class="card-content">Basic Card</div></div>',
        '<div class="card elevated"><div class="card-content">Elevated Card</div></div>'
      ]
    };

    const items = previews[componentType] || [];
    
    resultsContainer.innerHTML = items.map(html => `
      <div class="preview-item">${html}</div>
    `).join('');
  }

  /**
   * Version History functionality
   */
  initVersionHistory() {
    document.querySelectorAll('[data-version-history]').forEach(container => {
      const type = container.querySelector('.changelog-view') ? 'changelog' :
                   container.querySelector('.timeline-view') ? 'timeline' : 'migration';

      switch (type) {
        case 'changelog':
          this.initChangelog(container);
          break;
        case 'timeline':
          this.initTimeline(container);
          break;
        case 'migration':
          this.initMigration(container);
          break;
      }
    });
  }

  initChangelog(container) {
    const versionSelect = container.querySelector('.version-select');
    
    if (versionSelect) {
      versionSelect.addEventListener('change', (e) => {
        const version = e.target.value;
        this.loadChangelogVersion(container, version);
      });
    }
  }

  loadChangelogVersion(container, version) {
    // Mock version data
    const versionData = {
      'v2.1.0': {
        date: 'December 15, 2024',
        features: ['Added dark mode support', 'New animation library', 'Component playground'],
        fixes: ['Fixed button focus states', 'Resolved card overflow issues']
      },
      'v2.0.0': {
        date: 'November 1, 2024',
        features: ['Complete redesign', 'New component system'],
        fixes: ['Performance improvements', 'Accessibility enhancements']
      }
    };

    const data = versionData[version];
    const entriesContainer = container.querySelector('.changelog-entries');

    if (data && entriesContainer) {
      entriesContainer.innerHTML = `
        <div class="changelog-entry">
          <div class="entry-header">
            <h4>Version ${version}</h4>
            <span class="entry-date">${data.date}</span>
          </div>
          <div class="entry-content">
            <h5>✨ New Features</h5>
            <ul>
              ${data.features.map(feature => `<li>${feature}</li>`).join('')}
            </ul>
            <h5>🐛 Bug Fixes</h5>
            <ul>
              ${data.fixes.map(fix => `<li>${fix}</li>`).join('')}
            </ul>
          </div>
        </div>
      `;
    }
  }

  initTimeline(container) {
    const timelineItems = container.querySelectorAll('.timeline-item');
    
    timelineItems.forEach(item => {
      item.addEventListener('click', () => {
        const version = item.dataset.version;
        this.showVersionDetails(version);
      });
    });
  }

  initMigration(container) {
    const fromSelect = container.querySelector('.version-from');
    const toSelect = container.querySelector('.version-to');

    if (fromSelect && toSelect) {
      [fromSelect, toSelect].forEach(select => {
        select.addEventListener('change', () => {
          this.updateMigrationSteps(container, fromSelect.value, toSelect.value);
        });
      });
    }
  }

  updateMigrationSteps(container, fromVersion, toVersion) {
    // Mock migration steps
    const migrationSteps = {
      'v2.0.0-v2.1.0': [
        {
          title: 'Update Button Classes',
          before: '<button class="btn btn-large">',
          after: '<button class="btn btn-lg">'
        },
        {
          title: 'Update Card Structure',
          before: '<div class="card-body">',
          after: '<div class="card-content">'
        }
      ]
    };

    const key = `${fromVersion}-${toVersion}`;
    const steps = migrationSteps[key] || [];
    const stepsContainer = container.querySelector('.migration-steps');

    if (stepsContainer) {
      stepsContainer.innerHTML = steps.map(step => `
        <div class="migration-step">
          <h5>${step.title}</h5>
          <div class="code-comparison">
            <div class="code-before">
              <label>Before</label>
              <pre>${step.before}</pre>
            </div>
            <div class="code-after">
              <label>After</label>
              <pre>${step.after}</pre>
            </div>
          </div>
        </div>
      `).join('');
    }
  }

  /**
   * API Documentation functionality
   */
  initApiDocs() {
    document.querySelectorAll('[data-api-docs]').forEach(container => {
      const type = container.querySelector('.api-reference') ? 'reference' :
                   container.querySelector('.api-explorer') ? 'explorer' : 'examples';

      switch (type) {
        case 'reference':
          this.initApiReference(container);
          break;
        case 'explorer':
          this.initApiExplorer(container);
          break;
        case 'examples':
          this.initApiExamples(container);
          break;
      }
    });
  }

  initApiReference(container) {
    const navLinks = container.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = link.getAttribute('href').substring(1);
        this.scrollToApiSection(container, target);
      });
    });
  }

  scrollToApiSection(container, sectionId) {
    const section = container.querySelector(`#${sectionId}`);
    if (section) {
      section.scrollIntoView({ behavior: 'smooth' });
    }
  }

  initApiExplorer(container) {
    const tryButton = container.querySelector('.try-btn');
    const methodSelect = container.querySelector('.method-select');
    const endpointInput = container.querySelector('.endpoint-input');
    const responseViewer = container.querySelector('.response-content');

    if (tryButton) {
      tryButton.addEventListener('click', () => {
        const method = methodSelect ? methodSelect.value : 'GET';
        const endpoint = endpointInput ? endpointInput.value : '/api/components';
        
        this.simulateApiCall(method, endpoint, responseViewer);
      });
    }
  }

  simulateApiCall(method, endpoint, responseViewer) {
    // Mock API responses
    const responses = {
      'GET /api/components': {
        components: [
          { name: 'Button', variants: ['primary', 'secondary', 'outline'] },
          { name: 'Card', variants: ['default', 'elevated', 'outlined'] }
        ]
      },
      'POST /api/components': {
        message: 'Component created successfully',
        id: 'comp_123'
      }
    };

    const key = `${method} ${endpoint}`;
    const response = responses[key] || { error: 'Endpoint not found' };

    if (responseViewer) {
      responseViewer.textContent = JSON.stringify(response, null, 2);
    }
  }

  initApiExamples(container) {
    const tabButtons = container.querySelectorAll('.tab-btn');
    const codeExamples = container.querySelectorAll('.code-example');

    tabButtons.forEach(button => {
      button.addEventListener('click', () => {
        const language = button.dataset.lang;
        
        // Update active tab
        tabButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');

        // Show corresponding example
        codeExamples.forEach(example => {
          example.style.display = example.dataset.example === language ? 'block' : 'none';
        });
      });
    });
  }

  /**
   * Utility methods
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  showToast(message, type = 'info') {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Style the toast
    Object.assign(toast.style, {
      position: 'fixed',
      top: '20px',
      right: '20px',
      padding: '12px 16px',
      backgroundColor: type === 'error' ? '#ef4444' : type === 'success' ? '#22c55e' : '#3b82f6',
      color: 'white',
      borderRadius: '6px',
      zIndex: '10000',
      fontSize: '14px',
      fontWeight: '500',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
      transform: 'translateX(100%)',
      transition: 'transform 0.3s ease'
    });

    document.body.appendChild(toast);

    // Animate in
    setTimeout(() => {
      toast.style.transform = 'translateX(0)';
    }, 10);

    // Remove after delay
    setTimeout(() => {
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 300);
    }, 3000);
  }

  showVersionDetails(version) {
    this.showToast(`Showing details for ${version}`);
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new DocumentationEnhancements();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DocumentationEnhancements;
}