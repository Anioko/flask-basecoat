// Component interactions for shadcn/ui components

// Tabs functionality
document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabs = document.querySelectorAll('.tabs');
    tabs.forEach(tabContainer => {
        const triggers = tabContainer.querySelectorAll('.tabs-trigger');
        const contents = tabContainer.querySelectorAll('.tabs-content');
        
        triggers.forEach(trigger => {
            trigger.addEventListener('click', () => {
                const tabId = trigger.dataset.tab;
                
                // Remove active classes
                triggers.forEach(t => t.classList.remove('tabs-active'));
                contents.forEach(c => c.classList.remove('tabs-content-active'));
                
                // Add active classes
                trigger.classList.add('tabs-active');
                const targetContent = tabContainer.querySelector(`[data-tab="${tabId}"]`);
                if (targetContent && targetContent.classList.contains('tabs-content')) {
                    targetContent.classList.add('tabs-content-active');
                }
            });
        });
    });

    // Dialog functionality
    const dialogTriggers = document.querySelectorAll('.dialog-trigger');
    const dialogs = document.querySelectorAll('.dialog');
    const dialogCloses = document.querySelectorAll('.dialog-close');
    const dialogOverlays = document.querySelectorAll('.dialog-overlay');

    dialogTriggers.forEach(trigger => {
        trigger.addEventListener('click', () => {
            const dialogId = trigger.dataset.dialog;
            const dialog = document.getElementById(dialogId);
            if (dialog) {
                dialog.setAttribute('aria-hidden', 'false');
                document.body.style.overflow = 'hidden';
            }
        });
    });

    dialogCloses.forEach(close => {
        close.addEventListener('click', () => {
            const dialog = close.closest('.dialog');
            if (dialog) {
                dialog.setAttribute('aria-hidden', 'true');
                document.body.style.overflow = '';
            }
        });
    });

    dialogOverlays.forEach(overlay => {
        overlay.addEventListener('click', () => {
            const dialog = overlay.closest('.dialog');
            if (dialog) {
                dialog.setAttribute('aria-hidden', 'true');
                document.body.style.overflow = '';
            }
        });
    });

    // Escape key to close dialogs
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const openDialog = document.querySelector('.dialog[aria-hidden="false"]');
            if (openDialog) {
                openDialog.setAttribute('aria-hidden', 'true');
                document.body.style.overflow = '';
            }
        }
    });

    // Popover functionality
    const popoverTriggers = document.querySelectorAll('.popover-trigger');
    popoverTriggers.forEach(trigger => {
        let timeout;
        
        trigger.addEventListener('mouseenter', () => {
            clearTimeout(timeout);
            const popoverId = trigger.dataset.popover;
            const popover = document.getElementById(popoverId);
            if (popover) {
                popover.style.opacity = '1';
                popover.style.visibility = 'visible';
            }
        });

        trigger.addEventListener('mouseleave', () => {
            timeout = setTimeout(() => {
                const popoverId = trigger.dataset.popover;
                const popover = document.getElementById(popoverId);
                if (popover) {
                    popover.style.opacity = '0';
                    popover.style.visibility = 'hidden';
                }
            }, 200);
        });
    });

    // Tooltip functionality
    const tooltipTriggers = document.querySelectorAll('.tooltip-trigger');
    tooltipTriggers.forEach(trigger => {
        let timeout;
        
        trigger.addEventListener('mouseenter', () => {
            clearTimeout(timeout);
            const tooltip = trigger.nextElementSibling;
            if (tooltip && tooltip.classList.contains('tooltip')) {
                tooltip.style.opacity = '1';
                tooltip.style.visibility = 'visible';
            }
        });

        trigger.addEventListener('mouseleave', () => {
            timeout = setTimeout(() => {
                const tooltip = trigger.nextElementSibling;
                if (tooltip && tooltip.classList.contains('tooltip')) {
                    tooltip.style.opacity = '0';
                    tooltip.style.visibility = 'hidden';
                }
            }, 100);
        });
    });

    // Progress bar animation
    const progressBars = document.querySelectorAll('.progress-bar[data-value]');
    progressBars.forEach(bar => {
        const value = bar.dataset.value;
        setTimeout(() => {
            bar.style.width = `${value}%`;
        }, 100);
    });

    // Toggle functionality
    const toggles = document.querySelectorAll('.toggle');
    toggles.forEach(toggle => {
        toggle.addEventListener('change', () => {
            const slider = toggle.nextElementSibling;
            if (slider && slider.classList.contains('toggle-slider')) {
                if (toggle.checked) {
                    slider.style.transform = 'translateX(1.25rem)';
                } else {
                    slider.style.transform = 'translateX(0)';
                }
            }
        });
    });

    // Sheet functionality
    const sheetTriggers = document.querySelectorAll('.sheet-trigger');
    const sheets = document.querySelectorAll('.sheet');
    const sheetCloses = document.querySelectorAll('.sheet-close');
    const sheetOverlays = document.querySelectorAll('.sheet-overlay');

    sheetTriggers.forEach(trigger => {
        trigger.addEventListener('click', () => {
            const sheetId = trigger.dataset.sheet;
            const sheet = document.getElementById(sheetId);
            if (sheet) {
                sheet.setAttribute('aria-hidden', 'false');
                document.body.style.overflow = 'hidden';
            }
        });
    });

    sheetCloses.forEach(close => {
        close.addEventListener('click', () => {
            const sheet = close.closest('.sheet');
            if (sheet) {
                sheet.setAttribute('aria-hidden', 'true');
                document.body.style.overflow = '';
            }
        });
    });

    sheetOverlays.forEach(overlay => {
        overlay.addEventListener('click', () => {
            const sheet = overlay.closest('.sheet');
            if (sheet) {
                sheet.setAttribute('aria-hidden', 'true');
                document.body.style.overflow = '';
            }
        });
    });

    // Escape key to close sheets and dialogs
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const openDialog = document.querySelector('.dialog[aria-hidden="false"]');
            const openSheet = document.querySelector('.sheet[aria-hidden="false"]');
            
            if (openDialog) {
                openDialog.setAttribute('aria-hidden', 'true');
                document.body.style.overflow = '';
            }
            
            if (openSheet) {
                openSheet.setAttribute('aria-hidden', 'true');
                document.body.style.overflow = '';
            }
        }
    });

    // Switch functionality
    const switches = document.querySelectorAll('.switch-input');
    switches.forEach(switchInput => {
        switchInput.addEventListener('change', () => {
            const slider = switchInput.nextElementSibling;
            const thumb = slider.querySelector('.switch-thumb');
            if (thumb) {
                if (switchInput.checked) {
                    thumb.style.transform = 'translateX(1.25rem)';
                } else {
                    thumb.style.transform = 'translateX(0)';
                }
            }
        });
    });

    // Dropdown functionality
    const dropdownTriggers = document.querySelectorAll('.dropdown-trigger');
    dropdownTriggers.forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            const dropdown = trigger.parentElement;
            const content = dropdown.querySelector('.dropdown-content');
            
            // Close all other dropdowns
            document.querySelectorAll('.dropdown-content').forEach(c => {
                if (c !== content) {
                    c.style.opacity = '0';
                    c.style.visibility = 'hidden';
                }
            });
            
            // Toggle current dropdown
            if (content.style.opacity === '1') {
                content.style.opacity = '0';
                content.style.visibility = 'hidden';
            } else {
                content.style.opacity = '1';
                content.style.visibility = 'visible';
            }
        });
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', () => {
        document.querySelectorAll('.dropdown-content').forEach(content => {
            content.style.opacity = '0';
            content.style.visibility = 'hidden';
        });
    });

    // Command palette functionality
    const commandSearches = document.querySelectorAll('.command-search');
    commandSearches.forEach(search => {
        search.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const items = search.closest('.command').querySelectorAll('.command-item');
            
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(query)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });

    // Table row highlighting
    const hoverableRows = document.querySelectorAll('.table-hoverable .table-row');
    hoverableRows.forEach(row => {
        row.addEventListener('mouseenter', () => {
            row.style.backgroundColor = 'var(--docs-muted-background)';
        });
        
        row.addEventListener('mouseleave', () => {
            row.style.backgroundColor = '';
        });
    });

    // Data table functionality
    const datatableSortHeaders = document.querySelectorAll('.datatable-header-cell.sortable');
    datatableSortHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const sortColumn = header.dataset.sort;
            const table = header.closest('.datatable');
            const tbody = table.querySelector('.datatable-body');
            const rows = Array.from(tbody.querySelectorAll('.datatable-row'));
            
            // Simple sorting implementation
            rows.sort((a, b) => {
                const aText = a.querySelector('.datatable-cell').textContent.trim();
                const bText = b.querySelector('.datatable-cell').textContent.trim();
                return aText.localeCompare(bText);
            });
            
            rows.forEach(row => tbody.appendChild(row));
            
            // Update sort indicator
            datatableSortHeaders.forEach(h => h.querySelector('.sort-indicator').textContent = '↕');
            header.querySelector('.sort-indicator').textContent = '↑';
        });
    });

    // Search functionality
    const searchInputs = document.querySelectorAll('.datatable-search-input');
    searchInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const table = input.closest('.datatable-container').querySelector('.datatable');
            const rows = table.querySelectorAll('.datatable-body .datatable-row');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });

    // Accordion functionality
    const accordionTriggers = document.querySelectorAll('.accordion-trigger');
    accordionTriggers.forEach(trigger => {
        trigger.addEventListener('click', () => {
            const accordion = trigger.closest('.accordion');
            const isMultiple = accordion.dataset.multiple === 'true';
            const content = document.getElementById(trigger.dataset.target);
            const isOpen = trigger.classList.contains('accordion-open');
            
            // Close other items if not multiple
            if (!isMultiple && !isOpen) {
                accordion.querySelectorAll('.accordion-trigger.accordion-open').forEach(otherTrigger => {
                    if (otherTrigger !== trigger) {
                        otherTrigger.classList.remove('accordion-open');
                        const otherContent = document.getElementById(otherTrigger.dataset.target);
                        otherContent.classList.remove('accordion-content-open');
                    }
                });
            }
            
            // Toggle current item
            trigger.classList.toggle('accordion-open');
            content.classList.toggle('accordion-content-open');
        });
    });

    // Carousel functionality
    const carousels = document.querySelectorAll('.carousel');
    carousels.forEach(carousel => {
        let currentSlide = 0;
        const slides = carousel.querySelectorAll('.carousel-slide');
        const prevBtn = carousel.querySelector('.carousel-prev');
        const nextBtn = carousel.querySelector('.carousel-next');
        const dots = carousel.querySelectorAll('.carousel-dot');
        const thumbnails = carousel.querySelectorAll('.carousel-thumb');
        
        function showSlide(index) {
            slides.forEach((slide, i) => {
                slide.classList.toggle('carousel-slide-active', i === index);
            });
            
            dots.forEach((dot, i) => {
                dot.classList.toggle('carousel-dot-active', i === index);
            });
            
            thumbnails.forEach((thumb, i) => {
                thumb.classList.toggle('carousel-thumb-active', i === index);
            });
            
            currentSlide = index;
        }
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                const newIndex = currentSlide > 0 ? currentSlide - 1 : slides.length - 1;
                showSlide(newIndex);
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                const newIndex = currentSlide < slides.length - 1 ? currentSlide + 1 : 0;
                showSlide(newIndex);
            });
        }
        
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => showSlide(index));
        });
        
        thumbnails.forEach((thumb, index) => {
            thumb.addEventListener('click', () => showSlide(index));
        });
        
        // Autoplay
        if (carousel.dataset.autoplay === 'true') {
            setInterval(() => {
                const nextIndex = currentSlide < slides.length - 1 ? currentSlide + 1 : 0;
                showSlide(nextIndex);
            }, 3000);
        }
    });

    // Calendar functionality
    const calendarNavBtns = document.querySelectorAll('.calendar-nav-btn');
    calendarNavBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const calendar = btn.closest('.calendar, .datepicker-popup');
            const title = calendar.querySelector('.calendar-title');
            // Simple month navigation simulation
            const isNext = btn.textContent.includes('›');
            const currentText = title.textContent;
            title.textContent = isNext ? 'December 2025' : 'October 2025';
        });
    });

    const calendarDays = document.querySelectorAll('.calendar-day');
    calendarDays.forEach(day => {
        day.addEventListener('click', () => {
            const calendar = day.closest('.calendar, .datepicker-popup');
            const datepickerInput = calendar.closest('.datepicker')?.querySelector('.datepicker-input');
            
            // Remove previous selection
            calendar.querySelectorAll('.calendar-day-selected').forEach(d => 
                d.classList.remove('calendar-day-selected'));
            
            // Select new day
            day.classList.add('calendar-day-selected');
            
            // Update input if it's a datepicker
            if (datepickerInput) {
                datepickerInput.value = `November ${day.textContent}, 2025`;
            }
        });
    });

    // Chart animations
    const charts = document.querySelectorAll('.chart');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const chart = entry.target;
                chart.style.opacity = '0';
                chart.style.transform = 'scale(0.8)';
                chart.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                
                setTimeout(() => {
                    chart.style.opacity = '1';
                    chart.style.transform = 'scale(1)';
                }, 100);
            }
        });
    });
    
    charts.forEach(chart => observer.observe(chart));

    // Wizard functionality
    initWizards();
    
    // Rich Text Editor functionality
    initRichEditor();
    
    // File Upload functionality
    initFileUpload();
    
    // Autocomplete functionality
    initAutocomplete();
    
    // Form Validation functionality
    initFormValidation();
    
    // Theme System functionality
    initThemeToggle();
    initColorGenerator();
    initTypographyEditor();
    initVariantBuilder();
    
    // Animation Library functionality
    initAnimationKit();
    initLoadingStates();
    initTransitions();
    initScrollAnimations();
});

// Animation Kit functionality
function initAnimationKit() {
  document.querySelectorAll('[data-animation-kit]').forEach(kit => {
    const triggers = kit.querySelectorAll('.demo-trigger');
    
    triggers.forEach(trigger => {
      trigger.addEventListener('click', () => {
        const animationType = trigger.dataset.trigger;
        const element = kit.querySelector(`[data-animation="${animationType}"]`);
        
        if (element) {
          // Remove any existing animation classes
          element.className = element.className.replace(/animate-[\w-]+/g, '');
          
          // Force reflow to ensure class removal takes effect
          element.offsetHeight;
          
          // Add the animation class
          element.classList.add(`animate-${animationType}`);
          
          // Remove animation class after animation completes
          setTimeout(() => {
            element.classList.remove(`animate-${animationType}`);
          }, 1000);
        }
      });
    });
  });
}

// Loading States functionality
function initLoadingStates() {
  document.querySelectorAll('[data-loading-states]').forEach(states => {
    // Progress animation functionality
    const progressBars = states.querySelectorAll('.progress-animated');
    progressBars.forEach(bar => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += 1;
        if (progress > 100) progress = 0;
        bar.style.width = progress + '%';
        
        const percentageText = states.querySelector('.progress-percentage');
        if (percentageText) {
          percentageText.textContent = progress + '%';
        }
      }, 50);
      
      // Store interval for cleanup
      bar._progressInterval = interval;
    });
    
    // Circular progress functionality
    const circularProgress = states.querySelectorAll('.circle-progress');
    circularProgress.forEach(circle => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += 1;
        if (progress > 100) progress = 0;
        
        const circumference = 2 * Math.PI * 15.9155;
        const strokeDasharray = (progress / 100) * circumference;
        circle.style.strokeDasharray = `${strokeDasharray}, ${circumference}`;
        
        const progressText = states.querySelector('.progress-circular .progress-text');
        if (progressText) {
          progressText.textContent = progress + '%';
        }
      }, 50);
      
      circle._progressInterval = interval;
    });
  });
}

// Transitions functionality
function initTransitions() {
  document.querySelectorAll('[data-transitions]').forEach(transitions => {
    const triggers = transitions.querySelectorAll('.transition-trigger');
    
    triggers.forEach(trigger => {
      trigger.addEventListener('click', () => {
        const targetId = trigger.dataset.target;
        const target = document.getElementById(targetId);
        
        if (target) {
          target.classList.toggle('active');
          
          const isActive = target.classList.contains('active');
          trigger.textContent = isActive ? 
            trigger.textContent.replace('Toggle', 'Hide') : 
            trigger.textContent.replace('Hide', 'Toggle');
        }
      });
    });
  });
}

// Scroll Animations functionality
function initScrollAnimations() {
  // Intersection Observer for reveal animations
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const delay = parseInt(entry.target.dataset.delay) || 0;
        setTimeout(() => {
          entry.target.classList.add('revealed');
        }, delay);
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '-50px'
  });

  // Observe reveal items
  document.querySelectorAll('[data-reveal]').forEach(item => {
    revealObserver.observe(item);
  });

  // Parallax effect
  function updateParallax() {
    document.querySelectorAll('[data-parallax-speed]').forEach(layer => {
      const speed = parseFloat(layer.dataset.parallaxSpeed);
      const rect = layer.getBoundingClientRect();
      const scrolled = window.pageYOffset;
      const parallaxOffset = scrolled * (1 - speed);
      
      layer.style.transform = `translateY(${parallaxOffset}px)`;
    });
  }

  // Stagger animations
  function initStaggerAnimations() {
    document.querySelectorAll('[data-stagger]').forEach(container => {
      const items = container.querySelectorAll('.stagger-item');
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            items.forEach((item, index) => {
              setTimeout(() => {
                item.classList.add('stagger-animate');
              }, index * 100);
            });
          }
        });
      }, { threshold: 0.5 });
      
      observer.observe(container);
    });
  }

  // Timeline animations
  function initTimelineAnimations() {
    document.querySelectorAll('[data-timeline]').forEach(timeline => {
      const sections = document.querySelectorAll('[data-timeline-section]');
      const progressBar = timeline.querySelector('.timeline-bar');
      
      function updateTimeline() {
        const scrollPercent = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
        
        if (progressBar) {
          progressBar.style.width = Math.min(scrollPercent, 100) + '%';
        }
        
        sections.forEach(section => {
          const sectionProgress = parseInt(section.dataset.timelineSection);
          if (scrollPercent >= sectionProgress) {
            section.classList.add('timeline-active');
          } else {
            section.classList.remove('timeline-active');
          }
        });
      }
      
      window.addEventListener('scroll', updateTimeline);
      updateTimeline(); // Initial call
    });
  }

  // Initialize parallax on scroll
  window.addEventListener('scroll', updateParallax);
  updateParallax(); // Initial call
  
  // Initialize other scroll animations
  initStaggerAnimations();
  initTimelineAnimations();

  // Cleanup function for intervals
  window.addEventListener('beforeunload', () => {
    document.querySelectorAll('[data-loading-states]').forEach(states => {
      const progressElements = states.querySelectorAll('[_progressInterval]');
      progressElements.forEach(element => {
        if (element._progressInterval) {
          clearInterval(element._progressInterval);
        }
      });
    });
  });
}

// Theme Toggle functionality
function initThemeToggle() {
  document.querySelectorAll('[data-theme-toggle]').forEach(toggle => {
    const options = toggle.querySelectorAll('[data-theme]');
    let currentTheme = localStorage.getItem('theme') || 'auto';

    function updateTheme(theme) {
      currentTheme = theme;
      localStorage.setItem('theme', theme);
      
      options.forEach(option => {
        option.classList.toggle('theme-option-active', option.dataset.theme === theme);
      });

      // Apply theme to document
      if (theme === 'auto') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
      } else {
        document.documentElement.setAttribute('data-theme', theme);
      }
    }

    options.forEach(option => {
      option.addEventListener('click', () => {
        updateTheme(option.dataset.theme);
      });
    });

    // Initialize theme
    updateTheme(currentTheme);

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (currentTheme === 'auto') {
        updateTheme('auto');
      }
    });
  });
}

// Color Generator functionality
function initColorGenerator() {
  document.querySelectorAll('[data-color-generator]').forEach(generator => {
    const wheelCanvas = generator.querySelector('.wheel-canvas');
    const preview = generator.querySelector('.color-preview');
    const hexInput = generator.querySelector('.color-hex');
    const rgbInput = generator.querySelector('.color-rgb');
    const hslInput = generator.querySelector('.color-hsl');
    const swatches = generator.querySelectorAll('.color-swatch');
    const colorInputs = generator.querySelectorAll('.color-input');

    if (wheelCanvas) {
      initColorWheel(wheelCanvas, preview, hexInput, rgbInput, hslInput);
    }

    swatches.forEach(swatch => {
      swatch.addEventListener('click', () => {
        swatches.forEach(s => s.classList.remove('swatch-active'));
        swatch.classList.add('swatch-active');
        
        const color = swatch.dataset.color;
        const display = generator.querySelector('.color-display');
        const code = generator.querySelector('.color-code');
        
        if (display && code) {
          display.style.background = color;
          code.textContent = color;
        }
      });
    });

    colorInputs.forEach(input => {
      const colorBlock = input.parentElement.querySelector('.color-block');
      
      input.addEventListener('change', () => {
        if (colorBlock) {
          colorBlock.style.background = input.value;
        }
      });
    });

    // Palette builder functionality
    const addColorBtn = generator.querySelector('[data-action="add-color"]');
    const generateBtn = generator.querySelector('[data-action="generate"]');
    const exportBtn = generator.querySelector('[data-action="export"]');
    const paletteColors = generator.querySelector('.palette-colors');

    if (addColorBtn) {
      addColorBtn.addEventListener('click', () => {
        const newItem = document.createElement('div');
        newItem.className = 'palette-item';
        newItem.innerHTML = `
          <div class="color-block" style="background: #6366f1;"></div>
          <input type="text" class="color-input" value="#6366f1">
          <button type="button" class="remove-color">×</button>
        `;
        
        paletteColors.appendChild(newItem);
        
        // Add event listeners to new elements
        const input = newItem.querySelector('.color-input');
        const block = newItem.querySelector('.color-block');
        const remove = newItem.querySelector('.remove-color');
        
        input.addEventListener('change', () => {
          block.style.background = input.value;
        });
        
        remove.addEventListener('click', () => {
          newItem.remove();
        });
      });
    }

    if (generateBtn) {
      generateBtn.addEventListener('click', () => {
        // Generate complementary colors
        const items = paletteColors.querySelectorAll('.palette-item');
        items.forEach(item => {
          const input = item.querySelector('.color-input');
          const block = item.querySelector('.color-block');
          const randomColor = '#' + Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0');
          input.value = randomColor;
          block.style.background = randomColor;
        });
      });
    }

    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        const colors = Array.from(colorInputs).map(input => input.value);
        const css = colors.map((color, index) => `--color-${index + 1}: ${color};`).join('\n');
        
        navigator.clipboard.writeText(`:root {\n${css}\n}`).then(() => {
          alert('Palette CSS copied to clipboard!');
        });
      });
    }
  });

  function initColorWheel(canvas, preview, hexInput, rgbInput, hslInput) {
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 10;

    function drawColorWheel() {
      for (let angle = 0; angle < 360; angle++) {
        const startAngle = (angle - 1) * Math.PI / 180;
        const endAngle = angle * Math.PI / 180;
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, startAngle, endAngle);
        ctx.lineWidth = radius;
        ctx.strokeStyle = `hsl(${angle}, 100%, 50%)`;
        ctx.stroke();
      }
    }

    function updateColor(hue, saturation, lightness) {
      const hsl = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
      const rgb = hslToRgb(hue / 360, saturation / 100, lightness / 100);
      const hex = rgbToHex(rgb.r, rgb.g, rgb.b);

      if (preview) preview.style.background = hex;
      if (hexInput) hexInput.value = hex;
      if (rgbInput) rgbInput.value = `${rgb.r}, ${rgb.g}, ${rgb.b}`;
      if (hslInput) hslInput.value = `${hue}, ${saturation}%, ${lightness}%`;
    }

    canvas.addEventListener('click', (e) => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left - centerX;
      const y = e.clientY - rect.top - centerY;
      const distance = Math.sqrt(x * x + y * y);
      
      if (distance <= radius) {
        const angle = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
        const saturation = Math.min(distance / radius * 100, 100);
        updateColor(Math.round(angle), Math.round(saturation), 50);
      }
    });

    drawColorWheel();
  }

  function hslToRgb(h, s, l) {
    let r, g, b;
    if (s === 0) {
      r = g = b = l;
    } else {
      const hue2rgb = (p, q, t) => {
        if (t < 0) t += 1;
        if (t > 1) t -= 1;
        if (t < 1/6) return p + (q - p) * 6 * t;
        if (t < 1/2) return q;
        if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
        return p;
      };
      const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
      const p = 2 * l - q;
      r = hue2rgb(p, q, h + 1/3);
      g = hue2rgb(p, q, h);
      b = hue2rgb(p, q, h - 1/3);
    }
    return {
      r: Math.round(r * 255),
      g: Math.round(g * 255),
      b: Math.round(b * 255)
    };
  }

  function rgbToHex(r, g, b) {
    return "#" + [r, g, b].map(x => {
      const hex = x.toString(16);
      return hex.length === 1 ? "0" + hex : hex;
    }).join("");
  }
}

// Typography Editor functionality
function initTypographyEditor() {
  document.querySelectorAll('[data-typography-editor]').forEach(editor => {
    const baseSizeControl = editor.querySelector('[data-control="base-size"]');
    const scaleRatioControl = editor.querySelector('[data-control="scale-ratio"]');
    const typeSamples = editor.querySelectorAll('.type-sample');
    const fontOptions = editor.querySelectorAll('.font-option');
    const categoryBtns = editor.querySelectorAll('.category-btn');
    const styleControls = editor.querySelectorAll('[data-style]');
    const styleTarget = editor.querySelector('[data-style-target]');

    if (baseSizeControl && scaleRatioControl) {
      function updateTypeScale() {
        const baseSize = parseInt(baseSizeControl.value);
        const scaleRatio = parseFloat(scaleRatioControl.value);
        const sizes = {
          'xs': Math.round(baseSize / (scaleRatio * scaleRatio)),
          'sm': Math.round(baseSize / scaleRatio),
          'base': baseSize,
          'lg': Math.round(baseSize * scaleRatio),
          'xl': Math.round(baseSize * scaleRatio * scaleRatio),
          '2xl': Math.round(baseSize * Math.pow(scaleRatio, 3))
        };

        typeSamples.forEach(sample => {
          const size = sample.dataset.size;
          if (sizes[size]) {
            sample.style.fontSize = sizes[size] + 'px';
            sample.textContent = `Text ${size.toUpperCase()} (${sizes[size]}px)`;
          }
        });

        editor.querySelector('.value').textContent = baseSize + 'px';
      }

      baseSizeControl.addEventListener('input', updateTypeScale);
      scaleRatioControl.addEventListener('change', updateTypeScale);
      updateTypeScale();
    }

    fontOptions.forEach(option => {
      option.addEventListener('click', () => {
        fontOptions.forEach(opt => opt.classList.remove('font-option-active'));
        option.classList.add('font-option-active');
        
        const fontName = option.dataset.font;
        if (styleTarget) {
          styleTarget.style.fontFamily = fontName;
        }
      });
    });

    categoryBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        categoryBtns.forEach(b => b.classList.remove('category-btn-active'));
        btn.classList.add('category-btn-active');
      });
    });

    styleControls.forEach(control => {
      control.addEventListener('input', () => {
        const property = control.dataset.style;
        let value = control.value;
        
        if (property === 'font-weight') {
          styleTarget.style.fontWeight = value;
        } else if (property === 'letter-spacing') {
          styleTarget.style.letterSpacing = value + 'em';
        } else if (property === 'line-height') {
          styleTarget.style.lineHeight = value;
        }
      });
    });
  });
}

// Variant Builder functionality
function initVariantBuilder() {
  document.querySelectorAll('[data-variant-builder]').forEach(builder => {
    const baseColorPicker = builder.querySelector('[data-base-color]');
    const variantCheckboxes = builder.querySelectorAll('[data-variant]');
    const variantItems = builder.querySelectorAll('[data-variant-type]');
    const baseSizeControl = builder.querySelector('[data-base-size]');
    const scaleFactorControl = builder.querySelector('[data-scale-factor]');
    const sizeVariants = builder.querySelectorAll('.size-variants .btn');
    const styleControls = builder.querySelectorAll('[data-style]');
    const styleTarget = builder.querySelector('[data-style-target]');

    if (baseColorPicker) {
      function updateColorVariants() {
        const baseColor = baseColorPicker.value;
        const hsl = hexToHsl(baseColor);
        
        variantItems.forEach(item => {
          const type = item.dataset.variantType;
          const sample = item.querySelector('.color-sample');
          const code = item.querySelector('.color-code');
          
          if (sample && code) {
            let newColor = baseColor;
            
            if (type === 'light') {
              newColor = hslToHex(hsl.h, hsl.s, Math.min(hsl.l + 30, 90));
            } else if (type === 'dark') {
              newColor = hslToHex(hsl.h, hsl.s, Math.max(hsl.l - 30, 10));
            }
            
            sample.style.background = newColor;
            code.textContent = newColor;
          }
        });
      }

      baseColorPicker.addEventListener('change', updateColorVariants);
      updateColorVariants();
    }

    if (baseSizeControl && scaleFactorControl) {
      function updateSizeVariants() {
        const baseSize = parseInt(baseSizeControl.value);
        const scaleFactor = parseFloat(scaleFactorControl.value);
        
        const sizes = [
          baseSize / (scaleFactor * scaleFactor), // xs
          baseSize / scaleFactor, // sm
          baseSize, // md
          baseSize * scaleFactor, // lg
          baseSize * scaleFactor * scaleFactor // xl
        ];

        sizeVariants.forEach((btn, index) => {
          if (sizes[index]) {
            btn.style.fontSize = Math.round(sizes[index]) + 'px';
          }
        });

        builder.querySelector('.size-value').textContent = baseSize + 'px';
        builder.querySelector('.scale-value').textContent = scaleFactor;
      }

      baseSizeControl.addEventListener('input', updateSizeVariants);
      scaleFactorControl.addEventListener('input', updateSizeVariants);
      updateSizeVariants();
    }

    if (styleTarget) {
      styleControls.forEach(control => {
        control.addEventListener('input', () => {
          const property = control.dataset.style;
          const value = control.value;
          
          if (property === 'border-radius') {
            styleTarget.style.borderRadius = value + 'px';
          } else if (property === 'border-width') {
            styleTarget.style.borderWidth = value + 'px';
          } else if (property === 'shadow') {
            const shadows = [
              'none',
              '0 1px 3px rgba(0, 0, 0, 0.1)',
              '0 4px 6px rgba(0, 0, 0, 0.1)',
              '0 10px 25px rgba(0, 0, 0, 0.1)'
            ];
            styleTarget.style.boxShadow = shadows[value] || shadows[0];
          }
        });
      });
    }
  });

  function hexToHsl(hex) {
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;

    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h, s, l = (max + min) / 2;

    if (max === min) {
      h = s = 0;
    } else {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = (g - b) / d + (g < b ? 6 : 0); break;
        case g: h = (b - r) / d + 2; break;
        case b: h = (r - g) / d + 4; break;
      }
      h /= 6;
    }

    return { h: h * 360, s: s * 100, l: l * 100 };
  }

  function hslToHex(h, s, l) {
    h /= 360; s /= 100; l /= 100;
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1/6) return p + (q - p) * 6 * t;
      if (t < 1/2) return q;
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
      return p;
    };
    
    let r, g, b;
    if (s === 0) {
      r = g = b = l;
    } else {
      const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
      const p = 2 * l - q;
      r = hue2rgb(p, q, h + 1/3);
      g = hue2rgb(p, q, h);
      b = hue2rgb(p, q, h - 1/3);
    }

    return "#" + [r, g, b].map(x => {
      const hex = Math.round(x * 255).toString(16);
      return hex.length === 1 ? "0" + hex : hex;
    }).join("");
  }

// Wizard functionality
function initWizards() {
  document.querySelectorAll('.wizard').forEach(wizard => {
    const steps = wizard.querySelectorAll('.wizard-step');
    const progressBar = wizard.querySelector('.progress-fill');
    const indicators = wizard.querySelectorAll('.step-indicator');
    const prevBtn = wizard.querySelector('.wizard-prev');
    const nextBtn = wizard.querySelector('.wizard-next');
    let currentStep = 0;

    function updateProgress() {
      const progress = ((currentStep + 1) / steps.length) * 100;
      progressBar.style.width = progress + '%';
      
      indicators.forEach((indicator, index) => {
        indicator.classList.remove('step-active', 'step-completed');
        if (index < currentStep) {
          indicator.classList.add('step-completed');
        } else if (index === currentStep) {
          indicator.classList.add('step-active');
        }
      });

      steps.forEach((step, index) => {
        step.classList.toggle('wizard-step-active', index === currentStep);
      });

      prevBtn.disabled = currentStep === 0;
      if (currentStep === steps.length - 1) {
        nextBtn.textContent = 'Finish';
      } else {
        nextBtn.textContent = 'Next';
      }
    }

    prevBtn?.addEventListener('click', () => {
      if (currentStep > 0) {
        currentStep--;
        updateProgress();
      }
    });

    nextBtn?.addEventListener('click', () => {
      if (currentStep < steps.length - 1) {
        currentStep++;
        updateProgress();
      } else {
        // Handle form submission
        console.log('Wizard completed!');
      }
    });

    updateProgress();
  });
}

// Rich Text Editor functionality
function initRichEditor() {
  document.querySelectorAll('.rich-editor').forEach(editor => {
    const toolbar = editor.querySelector('.editor-toolbar');
    const content = editor.querySelector('.editor-content');
    
    if (!toolbar || !content) return;

    toolbar.addEventListener('click', (e) => {
      const btn = e.target.closest('.toolbar-btn');
      if (!btn) return;

      const command = btn.dataset.command;
      if (!command) return;

      e.preventDefault();
      
      if (command === 'createLink') {
        const url = prompt('Enter URL:');
        if (url) {
          document.execCommand(command, false, url);
        }
      } else if (command === 'insertImage') {
        const url = prompt('Enter image URL:');
        if (url) {
          document.execCommand('insertImage', false, url);
        }
      } else if (command === 'foreColor') {
        const color = prompt('Enter color (hex):');
        if (color) {
          document.execCommand(command, false, color);
        }
      } else {
        document.execCommand(command, false, null);
      }

      updateToolbarState();
    });

    toolbar.addEventListener('change', (e) => {
      if (e.target.classList.contains('toolbar-select')) {
        const command = e.target.dataset.command;
        const value = e.target.value;
        if (command && value) {
          document.execCommand(command, false, value);
          updateToolbarState();
        }
      }
    });

    function updateToolbarState() {
      toolbar.querySelectorAll('.toolbar-btn').forEach(btn => {
        const command = btn.dataset.command;
        if (command && document.queryCommandState(command)) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    }

    content.addEventListener('keyup', updateToolbarState);
    content.addEventListener('mouseup', updateToolbarState);
  });
}

// File Upload functionality
function initFileUpload() {
  document.querySelectorAll('.file-upload').forEach(uploader => {
    const area = uploader.querySelector('.upload-area');
    const input = uploader.querySelector('.upload-input');
    const previews = uploader.querySelector('.upload-previews');
    let files = [];

    area.addEventListener('dragover', (e) => {
      e.preventDefault();
      area.classList.add('dragover');
    });

    area.addEventListener('dragleave', () => {
      area.classList.remove('dragover');
    });

    area.addEventListener('drop', (e) => {
      e.preventDefault();
      area.classList.remove('dragover');
      handleFiles(e.dataTransfer.files);
    });

    input.addEventListener('change', (e) => {
      handleFiles(e.target.files);
    });

    function handleFiles(newFiles) {
      Array.from(newFiles).forEach(file => {
        files.push(file);
        createPreview(file);
      });
    }

    function createPreview(file) {
      const preview = document.createElement('div');
      preview.className = 'preview-item';
      preview.innerHTML = `
        <div class="preview-info">
          <div class="preview-name">${file.name}</div>
          <div class="preview-size">${formatFileSize(file.size)}</div>
        </div>
        <div class="preview-progress">
          <div class="progress-bar">
            <div class="progress-fill" style="width: 0%"></div>
          </div>
          <span class="progress-text">0%</span>
        </div>
        <button type="button" class="preview-remove">×</button>
      `;

      previews.appendChild(preview);

      // Simulate upload progress
      const progressBar = preview.querySelector('.progress-fill');
      const progressText = preview.querySelector('.progress-text');
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 20;
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
        }
        progressBar.style.width = progress + '%';
        progressText.textContent = Math.round(progress) + '%';
      }, 200);

      preview.querySelector('.preview-remove').addEventListener('click', () => {
        const index = files.indexOf(file);
        if (index > -1) {
          files.splice(index, 1);
        }
        preview.remove();
      });
    }

    function formatFileSize(bytes) {
      if (bytes === 0) return '0 B';
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(1024));
      return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i];
    }
  });
}

// Autocomplete functionality
function initAutocomplete() {
  document.querySelectorAll('.autocomplete').forEach(autocomplete => {
    const input = autocomplete.querySelector('.autocomplete-input');
    const dropdown = autocomplete.querySelector('.autocomplete-dropdown');
    const tagsContainer = autocomplete.querySelector('.autocomplete-tags');
    let selectedTags = [];
    let highlightedOption = -1;

    const options = [
      { value: 'javascript', label: 'JavaScript', description: 'Programming language' },
      { value: 'python', label: 'Python', description: 'Programming language' },
      { value: 'react', label: 'React', description: 'JavaScript library' },
      { value: 'vue', label: 'Vue.js', description: 'JavaScript framework' },
      { value: 'angular', label: 'Angular', description: 'TypeScript framework' },
      { value: 'nodejs', label: 'Node.js', description: 'JavaScript runtime' },
      { value: 'css', label: 'CSS', description: 'Styling language' },
      { value: 'html', label: 'HTML', description: 'Markup language' }
    ];

    input.addEventListener('input', handleInput);
    input.addEventListener('keydown', handleKeydown);

    function handleInput() {
      const query = input.value.toLowerCase();
      dropdown.innerHTML = '';

      if (query.length === 0) {
        dropdown.style.display = 'none';
        return;
      }

      const filtered = options.filter(option => 
        option.label.toLowerCase().includes(query) &&
        !selectedTags.some(tag => tag.value === option.value)
      );

      if (filtered.length > 0) {
        filtered.forEach((option, index) => {
          const optionEl = document.createElement('div');
          optionEl.className = 'autocomplete-option';
          optionEl.innerHTML = `
            ${option.label}
            <span class="option-description">${option.description}</span>
          `;
          optionEl.addEventListener('click', () => selectOption(option));
          dropdown.appendChild(optionEl);
        });
        dropdown.style.display = 'block';
        highlightedOption = -1;
      } else {
        dropdown.style.display = 'none';
      }
    }

    function handleKeydown(e) {
      const options = dropdown.querySelectorAll('.autocomplete-option');
      
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          highlightedOption = Math.min(highlightedOption + 1, options.length - 1);
          updateHighlight();
          break;
        case 'ArrowUp':
          e.preventDefault();
          highlightedOption = Math.max(highlightedOption - 1, -1);
          updateHighlight();
          break;
        case 'Enter':
          e.preventDefault();
          if (highlightedOption >= 0 && options[highlightedOption]) {
            const optionValue = options[highlightedOption].textContent.split('\n')[0].trim();
            const option = filtered.find(opt => opt.label === optionValue);
            if (option) selectOption(option);
          }
          break;
        case 'Escape':
          dropdown.style.display = 'none';
          highlightedOption = -1;
          break;
      }
    }

    function updateHighlight() {
      const options = dropdown.querySelectorAll('.autocomplete-option');
      options.forEach((opt, index) => {
        opt.classList.toggle('autocomplete-option-highlighted', index === highlightedOption);
      });
    }

    function selectOption(option) {
      selectedTags.push(option);
      renderTags();
      input.value = '';
      dropdown.style.display = 'none';
      highlightedOption = -1;
    }

    function renderTags() {
      tagsContainer.innerHTML = '';
      selectedTags.forEach((tag, index) => {
        const tagEl = document.createElement('span');
        tagEl.className = 'autocomplete-tag';
        tagEl.innerHTML = `
          ${tag.label}
          <button type="button" class="tag-remove">×</button>
        `;
        tagEl.querySelector('.tag-remove').addEventListener('click', () => {
          selectedTags.splice(index, 1);
          renderTags();
        });
        tagsContainer.appendChild(tagEl);
      });
    }
  });
}

// Form Validation functionality
function initFormValidation() {
  document.querySelectorAll('.form-validation').forEach(form => {
    const inputs = form.querySelectorAll('input, textarea, select');
    const submitBtn = form.querySelector('button[type="submit"]');
    let validationState = {};

    inputs.forEach(input => {
      input.addEventListener('input', () => validateField(input));
      input.addEventListener('blur', () => validateField(input));
    });

    function validateField(input) {
      const group = input.closest('.input-group');
      const feedback = group.querySelector('.input-feedback');
      const rules = input.dataset.validation ? JSON.parse(input.dataset.validation) : {};
      
      let isValid = true;
      let message = '';

      // Required validation
      if (rules.required && !input.value.trim()) {
        isValid = false;
        message = 'This field is required';
      }
      
      // Email validation
      else if (rules.email && input.value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(input.value)) {
          isValid = false;
          message = 'Please enter a valid email address';
        }
      }
      
      // Min length validation
      else if (rules.minLength && input.value.length < rules.minLength) {
        isValid = false;
        message = `Minimum ${rules.minLength} characters required`;
      }
      
      // Password strength validation
      else if (input.type === 'password' && input.value) {
        const strength = calculatePasswordStrength(input.value);
        updatePasswordStrength(group, strength);
        if (strength.score < 2) {
          isValid = false;
          message = 'Password is too weak';
        } else {
          message = `Password strength: ${strength.label}`;
        }
      }

      // Update visual state
      group.classList.remove('has-error', 'has-success');
      if (input.value) {
        if (isValid) {
          group.classList.add('has-success');
          feedback.className = 'input-feedback success';
          feedback.textContent = message || 'Looks good!';
        } else {
          group.classList.add('has-error');
          feedback.className = 'input-feedback error';
          feedback.textContent = message;
        }
      } else {
        feedback.className = 'input-feedback';
        feedback.textContent = '';
      }

      validationState[input.name] = isValid;
      updateFormState();
    }

    function calculatePasswordStrength(password) {
      let score = 0;
      let feedback = [];

      if (password.length >= 8) score++;
      if (password.match(/[a-z]/)) score++;
      if (password.match(/[A-Z]/)) score++;
      if (password.match(/[0-9]/)) score++;
      if (password.match(/[^A-Za-z0-9]/)) score++;

      let label = 'Weak';
      if (score >= 4) label = 'Strong';
      else if (score >= 3) label = 'Medium';

      return { score, label, total: 5 };
    }

    function updatePasswordStrength(group, strength) {
      const indicator = group.querySelector('.strength-indicator');
      const text = group.querySelector('.strength-text');
      
      if (indicator && text) {
        const bars = indicator.querySelectorAll('.strength-bar');
        bars.forEach((bar, index) => {
          bar.classList.remove('strength-weak', 'strength-medium', 'strength-strong');
          if (index < strength.score) {
            if (strength.score <= 2) bar.classList.add('strength-weak');
            else if (strength.score <= 3) bar.classList.add('strength-medium');
            else bar.classList.add('strength-strong');
          }
        });
        text.textContent = strength.label;
      }
    }

    function updateFormState() {
      const summary = form.querySelector('.form-summary');
      if (summary) {
        const totalFields = Object.keys(validationState).length;
        const validFields = Object.values(validationState).filter(Boolean).length;
        const errorFields = totalFields - validFields;

        summary.querySelector('.summary-count').textContent = `${validFields}/${totalFields}`;
        const errorCount = summary.querySelector('.error-count');
        if (errorCount) {
          errorCount.textContent = errorFields;
        }
      }

      // Update submit button state
      const allValid = Object.values(validationState).every(Boolean) && 
                      Object.keys(validationState).length > 0;
      if (submitBtn) {
        submitBtn.disabled = !allValid;
      }
    }

    // Initialize validation for existing values
    inputs.forEach(input => {
      if (input.value) {
        validateField(input);
      }
    });
  });
}

// Component Playground Functionality
function initComponentPreview() {
  // Tab switching
  document.querySelectorAll('[data-component-preview]').forEach(preview => {
    const tabs = preview.querySelectorAll('[data-tab]');
    const tabContents = preview.querySelectorAll('[data-tab-content]');
    
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const targetTab = tab.dataset.tab;
        
        // Remove active classes
        tabs.forEach(t => t.classList.remove('toolbar-btn-active'));
        tabContents.forEach(content => content.classList.remove('editor-tab-active'));
        
        // Add active classes
        tab.classList.add('toolbar-btn-active');
        const targetContent = preview.querySelector(`[data-tab-content="${targetTab}"]`);
        if (targetContent) {
          targetContent.classList.add('editor-tab-active');
        }
      });
    });
    
    // Property controls
    const propInputs = preview.querySelectorAll('[data-prop]');
    const previewTarget = preview.querySelector('[data-preview-target]');
    
    propInputs.forEach(input => {
      input.addEventListener('input', () => {
        updatePreviewComponent(preview, propInputs, previewTarget);
        updateCodeOutput(preview, propInputs);
      });
    });
    
    // Device switching for responsive preview
    const deviceButtons = preview.querySelectorAll('[data-device]');
    const responsiveFrame = preview.querySelector('[data-device-frame]');
    const sizeIndicator = preview.querySelector('.size-indicator');
    
    deviceButtons.forEach(button => {
      button.addEventListener('click', () => {
        const device = button.dataset.device;
        
        // Update button states
        deviceButtons.forEach(btn => btn.classList.remove('device-btn-active'));
        button.classList.add('device-btn-active');
        
        // Update frame
        if (responsiveFrame) {
          responsiveFrame.dataset.deviceFrame = device;
          
          // Update size indicator
          if (sizeIndicator) {
            const sizes = {
              desktop: '1200px × 800px',
              tablet: '768px × 1024px',
              mobile: '375px × 667px'
            };
            sizeIndicator.textContent = sizes[device] || sizes.desktop;
          }
        }
      });
    });
  });
}

function updatePreviewComponent(preview, propInputs, target) {
  if (!target) return;
  
  const props = {};
  propInputs.forEach(input => {
    const prop = input.dataset.prop;
    if (input.type === 'checkbox') {
      props[prop] = input.checked;
    } else {
      props[prop] = input.value;
    }
  });
  
  // Update button example
  if (target.tagName === 'BUTTON') {
    if (props.text) target.textContent = props.text;
    if (props.variant) {
      target.className = target.className.replace(/btn-\w+/, `btn-${props.variant}`);
    }
    if (props.size) {
      target.className = target.className.replace(/btn-(sm|md|lg)/, `btn-${props.size}`);
    }
    target.disabled = props.disabled || false;
  }
}

function updateCodeOutput(preview, propInputs) {
  const codeOutput = preview.querySelector('[data-output]');
  if (!codeOutput) return;
  
  const props = {};
  propInputs.forEach(input => {
    const prop = input.dataset.prop;
    if (input.type === 'checkbox') {
      props[prop] = input.checked;
    } else {
      props[prop] = input.value;
    }
  });
  
  // Generate HTML
  const classes = ['btn'];
  if (props.variant) classes.push(`btn-${props.variant}`);
  if (props.size) classes.push(`btn-${props.size}`);
  
  const attributes = [];
  if (props.disabled) attributes.push('disabled');
  
  const html = `<button class="${classes.join(' ')}"${attributes.length ? ' ' + attributes.join(' ') : ''}>${props.text || 'Sample Button'}</button>`;
  codeOutput.textContent = html;
}

function initCodeGenerator() {
  document.querySelectorAll('[data-code-generator]').forEach(generator => {
    const generateBtn = generator.querySelector('[data-action="generate"]');
    const copyBtn = generator.querySelector('[data-action="copy"]');
    const output = generator.querySelector('[data-output]');
    
    if (generateBtn) {
      generateBtn.addEventListener('click', () => {
        generateCode(generator, output);
      });
    }
    
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        copyToClipboard(output.textContent);
        showCopyFeedback(copyBtn);
      });
    }
    
    // Auto-generate on input change
    const settings = generator.querySelectorAll('[data-setting]');
    settings.forEach(setting => {
      setting.addEventListener('input', () => {
        generateCode(generator, output);
      });
    });
  });
}

function generateCode(generator, output) {
  if (!output) return;
  
  const format = generator.closest('[data-code-generator]').querySelector('[data-setting="component"]')?.value || 
                generator.closest('[data-code-generator]').querySelector('h4')?.textContent.toLowerCase() || 'html';
  
  const settings = {};
  generator.querySelectorAll('[data-setting]').forEach(setting => {
    settings[setting.dataset.setting] = setting.value;
  });
  
  let code = '';
  
  if (format.includes('html') || settings.component) {
    // HTML Generator
    const component = settings.component || 'button';
    const classes = settings.classes || 'btn btn-primary';
    
    switch (component) {
      case 'button':
        code = `<button class="${classes}">Click Me</button>`;
        break;
      case 'card':
        code = `<div class="card">
  <div class="card-header">Card Title</div>
  <div class="card-content">
    <p>Card content goes here.</p>
    <button class="btn btn-primary">Action</button>
  </div>
</div>`;
        break;
      case 'form':
        code = `<form class="form">
  <div class="form-group">
    <label class="label">Email</label>
    <input type="email" class="input" placeholder="Enter email">
  </div>
  <button type="submit" class="${classes}">Submit</button>
</form>`;
        break;
      case 'nav':
        code = `<nav class="navbar">
  <div class="navbar-brand">Brand</div>
  <div class="navbar-menu">
    <a href="#" class="navbar-item">Home</a>
    <a href="#" class="navbar-item">About</a>
  </div>
</nav>`;
        break;
    }
  } else if (format.includes('jsx') || format.includes('react')) {
    // React JSX Generator
    const name = settings.name || 'MyButton';
    const props = settings.props || 'variant="primary"\nsize="md"';
    
    code = `<${name} ${props.replace(/\n/g, '\n  ')}>
  Click Me
</${name}>`;
  } else if (format.includes('vue')) {
    // Vue Template Generator
    const tag = settings.tag || 'v-button';
    const directives = settings.directives || ':variant="buttonVariant"';
    
    code = `<${tag} 
  ${directives.replace(/\n/g, '\n  ')}>
  {{ buttonText }}
</${tag}>`;
  } else if (format.includes('angular')) {
    // Angular Generator
    const selector = settings.selector || 'app-button';
    const inputs = settings.inputs || '[variant]="\'primary\'"';
    
    code = `<${selector} 
  ${inputs.replace(/\n/g, '\n  ')}
  (click)="onClick()">
  Click Me
</${selector}>`;
  }
  
  output.textContent = code;
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    console.log('Code copied to clipboard');
  }).catch(err => {
    console.error('Failed to copy: ', err);
  });
}

function showCopyFeedback(button) {
  const originalText = button.textContent;
  button.textContent = 'Copied!';
  button.style.background = '#059669';
  button.style.color = '#fff';
  
  setTimeout(() => {
    button.textContent = originalText;
    button.style.background = '';
    button.style.color = '';
  }, 2000);
}

function initComponentBuilder() {
  document.querySelectorAll('[data-component-builder]').forEach(builder => {
    // Tool selection
    const toolBtns = builder.querySelectorAll('[data-tool]');
    let activeTool = 'select';
    
    toolBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        toolBtns.forEach(b => b.classList.remove('tool-btn-active'));
        btn.classList.add('tool-btn-active');
        activeTool = btn.dataset.tool;
      });
    });
    
    // Canvas interactions
    const canvas = builder.querySelector('[data-canvas]');
    const components = canvas?.querySelectorAll('.canvas-component');
    
    if (canvas && components) {
      // Make components draggable
      components.forEach(component => {
        makeComponentDraggable(component);
        
        component.addEventListener('click', () => {
          // Select component
          components.forEach(c => c.classList.remove('selected'));
          component.classList.add('selected');
          
          // Update properties panel
          updatePropertiesPanel(builder, component);
        });
      });
      
      // Add new components on canvas click
      canvas.addEventListener('click', (e) => {
        if (e.target === canvas && activeTool !== 'select') {
          addComponent(canvas, activeTool, e.offsetX, e.offsetY);
        }
      });
    }
    
    // Layer tree interactions
    const layerItems = builder.querySelectorAll('[data-layer]');
    layerItems.forEach(item => {
      const toggle = item.querySelector('.layer-toggle');
      const content = item.querySelector('.layer-content');
      
      if (toggle) {
        toggle.addEventListener('click', (e) => {
          e.stopPropagation();
          toggleLayerExpansion(item);
        });
      }
      
      if (content) {
        content.addEventListener('click', () => {
          selectLayerComponent(builder, item.dataset.layer);
        });
      }
    });
    
    // Property panel updates
    const propertyInputs = builder.querySelectorAll('.property-input, .property-select, .property-color, .property-range');
    propertyInputs.forEach(input => {
      input.addEventListener('input', () => {
        updateSelectedComponent(builder, input);
      });
    });
  });
}

function makeComponentDraggable(component) {
  let isDragging = false;
  let startX, startY, startLeft, startTop;
  
  component.addEventListener('mousedown', (e) => {
    isDragging = true;
    startX = e.clientX;
    startY = e.clientY;
    startLeft = parseInt(component.style.left || '0');
    startTop = parseInt(component.style.top || '0');
    
    component.style.cursor = 'grabbing';
  });
  
  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    
    const deltaX = e.clientX - startX;
    const deltaY = e.clientY - startY;
    
    component.style.left = `${startLeft + deltaX}px`;
    component.style.top = `${startTop + deltaY}px`;
  });
  
  document.addEventListener('mouseup', () => {
    if (isDragging) {
      isDragging = false;
      component.style.cursor = '';
    }
  });
}

function addComponent(canvas, type, x, y) {
  const component = document.createElement('div');
  component.className = 'canvas-component';
  component.dataset.component = type;
  component.style.position = 'absolute';
  component.style.left = `${x}px`;
  component.style.top = `${y}px`;
  
  let content = '';
  switch (type) {
    case 'text':
      content = '<p>New text element</p>';
      break;
    case 'button':
      content = '<button class="btn btn-primary">New Button</button>';
      break;
    case 'card':
      content = `<div class="card" style="width: 200px;">
                  <div class="card-header">New Card</div>
                  <div class="card-content">Content</div>
                </div>`;
      break;
    default:
      content = `<div>New ${type}</div>`;
  }
  
  component.innerHTML = content;
  makeComponentDraggable(component);
  canvas.appendChild(component);
}

function toggleLayerExpansion(item) {
  const toggle = item.querySelector('.layer-toggle');
  const children = item.querySelector('.layer-children');
  
  if (children) {
    const isExpanded = item.classList.contains('layer-item-expanded');
    if (isExpanded) {
      item.classList.remove('layer-item-expanded');
      toggle.textContent = '▶';
      children.style.display = 'none';
    } else {
      item.classList.add('layer-item-expanded');
      toggle.textContent = '▼';
      children.style.display = 'block';
    }
  }
}

function selectLayerComponent(builder, layerId) {
  const canvas = builder.querySelector('[data-canvas]');
  const components = canvas?.querySelectorAll('.canvas-component');
  
  if (components) {
    components.forEach(component => {
      component.classList.remove('selected');
      if (component.dataset.component === layerId) {
        component.classList.add('selected');
        updatePropertiesPanel(builder, component);
      }
    });
  }
}

function updatePropertiesPanel(builder, component) {
  const selectedElement = builder.querySelector('.selected-element');
  if (selectedElement) {
    selectedElement.textContent = component.dataset.component || 'Component';
  }
  
  // Update property values based on component
  const rect = component.getBoundingClientRect();
  const inputs = builder.querySelectorAll('.property-input');
  
  inputs.forEach(input => {
    const label = input.previousElementSibling?.textContent.toLowerCase();
    if (label === 'x') input.value = parseInt(component.style.left || '0');
    if (label === 'y') input.value = parseInt(component.style.top || '0');
    if (label === 'width') input.value = Math.round(rect.width);
    if (label === 'height') input.value = Math.round(rect.height);
  });
}

function updateSelectedComponent(builder, input) {
  const selectedComponent = builder.querySelector('.canvas-component.selected');
  if (!selectedComponent) return;
  
  const label = input.previousElementSibling?.textContent.toLowerCase();
  const value = input.value;
  
  switch (label) {
    case 'x':
      selectedComponent.style.left = `${value}px`;
      break;
    case 'y':
      selectedComponent.style.top = `${value}px`;
      break;
    case 'width':
      selectedComponent.style.width = `${value}px`;
      break;
    case 'height':
      selectedComponent.style.height = `${value}px`;
      break;
    case 'text':
      const textEl = selectedComponent.querySelector('p, button, span');
      if (textEl) textEl.textContent = value;
      break;
    case 'background':
      selectedComponent.style.backgroundColor = value;
      break;
  }
}

function initExportTools() {
  document.querySelectorAll('[data-export-tools]').forEach(exportTool => {
    // Export actions
    const exportBtns = exportTool.querySelectorAll('[data-action^="export-"]');
    exportBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        handleExportAction(exportTool, action);
      });
    });
    
    // Download actions
    const downloadBtns = exportTool.querySelectorAll('[data-action="download-zip"], [data-action="copy"]');
    downloadBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        handleDownloadAction(exportTool, action);
      });
    });
    
    // Option changes
    const options = exportTool.querySelectorAll('[data-option]');
    options.forEach(option => {
      option.addEventListener('change', () => {
        updateExportPreview(exportTool);
      });
    });
  });
}

function handleExportAction(exportTool, action) {
  const format = exportTool.querySelector('h4')?.textContent.toLowerCase() || 'figma';
  
  // Show loading state
  const btn = exportTool.querySelector(`[data-action="${action}"]`);
  const originalText = btn.textContent;
  btn.textContent = 'Exporting...';
  btn.disabled = true;
  
  // Simulate export process
  setTimeout(() => {
    btn.textContent = 'Export Complete!';
    btn.style.background = '#059669';
    btn.style.color = '#fff';
    
    setTimeout(() => {
      btn.textContent = originalText;
      btn.style.background = '';
      btn.style.color = '';
      btn.disabled = false;
    }, 3000);
  }, 2000);
  
  console.log(`Exporting to ${format} with action: ${action}`);
}

function handleDownloadAction(exportTool, action) {
  if (action === 'download-zip') {
    // Simulate ZIP download
    const link = document.createElement('a');
    link.href = '#';
    link.download = 'components-export.zip';
    link.click();
  } else if (action === 'copy') {
    // Copy export URL or data
    const mockUrl = 'https://export.example.com/components/abc123';
    copyToClipboard(mockUrl);
    showCopyFeedback(exportTool.querySelector('[data-action="copy"]'));
  }
}

function updateExportPreview(exportTool) {
  const format = exportTool.querySelector('[data-option="format"]')?.value;
  const scale = exportTool.querySelector('[data-option="scale"]')?.value;
  const includeVariants = exportTool.querySelector('[data-option="include-variants"]')?.checked;
  
  console.log('Export options updated:', { format, scale, includeVariants });
  
  // Update preview based on options
  const preview = exportTool.querySelector('.export-preview, .figma-preview, .asset-grid');
  if (preview) {
    // Add visual feedback for option changes
    preview.style.opacity = '0.7';
    setTimeout(() => {
      preview.style.opacity = '1';
    }, 300);
  }
}

// Initialize Component Playground features
document.addEventListener('DOMContentLoaded', function() {
  initComponentPreview();
  initCodeGenerator();
  initComponentBuilder();
  initExportTools();
});