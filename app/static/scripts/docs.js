(function () {
  const root = document.documentElement;
  const storageKey = "basecoat-docs-theme";

  function applyTheme(theme) {
    root.setAttribute("data-color-theme", theme);
  }

  function toggleTheme() {
    const current = root.getAttribute("data-color-theme") === "dark" ? "dark" : "light";
    const next = current === "dark" ? "light" : "dark";
    applyTheme(next);
    try {
      localStorage.setItem(storageKey, next);
    } catch (err) {
      console.warn("Unable to persist theme preference", err);
    }
  }

  function hydrateTheme() {
    let stored = null;
    try {
      stored = localStorage.getItem(storageKey);
    } catch (err) {
      stored = null;
    }
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const theme = stored || (prefersDark ? "dark" : "light");
    applyTheme(theme);
  }

  function slugify(text) {
    return (text || "")
      .toString()
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)+/g, "")
      .substring(0, 60);
  }

  function initThemeToggle() {
    const toggle = document.querySelector("[data-theme-toggle]");
    if (!toggle) return;
    toggle.addEventListener("click", toggleTheme);
  }

  function initMobileNav() {
    const trigger = document.querySelector("[data-mobile-toggle]");
    const sidebar = document.querySelector("[data-sidebar]");
    if (!trigger || !sidebar) return;

    trigger.addEventListener("click", function () {
      sidebar.classList.toggle("is-open");
    });

    sidebar.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        sidebar.classList.remove("is-open");
      });
    });
  }

  function initCopyButtons() {
    const blocks = document.querySelectorAll("[data-code]");
    if (!blocks.length) return;

    blocks.forEach(function (block) {
      const button = block.querySelector("[data-copy]");
      const code = block.querySelector("pre code");
      if (!button || !code) return;

      button.addEventListener("click", function () {
        const text = code.innerText;
        if (!navigator.clipboard) {
          try {
            const textarea = document.createElement("textarea");
            textarea.style.position = "fixed";
            textarea.style.opacity = "0";
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand("copy");
            document.body.removeChild(textarea);
            button.classList.add("is-success");
            button.textContent = "Copied";
          } catch (err) {
            button.textContent = "Failed";
          }
          setTimeout(function () {
            button.classList.remove("is-success");
            button.textContent = "Copy";
          }, 1600);
          return;
        }

        navigator.clipboard.writeText(text).then(
          function () {
            button.classList.add("is-success");
            button.textContent = "Copied";
            setTimeout(function () {
              button.classList.remove("is-success");
              button.textContent = "Copy";
            }, 1600);
          },
          function () {
            button.textContent = "Failed";
            setTimeout(function () {
              button.textContent = "Copy";
            }, 1600);
          }
        );
      });
    });
  }

  function initTableOfContents() {
    const tocRoot = document.querySelector("[data-docs-toc]");
    const article = document.querySelector(".docs-article");
    if (!tocRoot || !article) return;

    const headings = Array.from(article.querySelectorAll("h2, h3")).filter(function (heading) {
      return Boolean(heading.textContent && heading.textContent.trim().length);
    });

    if (!headings.length) {
      tocRoot.hidden = true;
      tocRoot.setAttribute("aria-hidden", "true");
      return;
    }

    tocRoot.hidden = false;
    tocRoot.removeAttribute("aria-hidden");
    tocRoot.innerHTML = "";

    const title = document.createElement("p");
    title.className = "docs-toc__title";
    title.textContent = "On this page";
    tocRoot.appendChild(title);

    const list = document.createElement("ul");
    list.className = "docs-toc__list";
    tocRoot.appendChild(list);

    const headingMap = new Map();
    let currentMainItem = null;

    headings.forEach(function (heading) {
      if (!heading.id) {
        const base = slugify(heading.textContent || heading.innerText || "");
        if (base) {
          let candidate = base;
          let index = 1;
          while (candidate && document.getElementById(candidate)) {
            candidate = base + "-" + index;
            index += 1;
          }
          heading.id = candidate || base;
        }
      }

      if (!heading.id) return;

      const link = document.createElement("a");
      link.className = "docs-toc__link";
      link.href = "#" + heading.id;
      link.textContent = heading.textContent.trim();
      link.dataset.tocTarget = heading.id;

      const item = document.createElement("li");
      item.appendChild(link);

      link.addEventListener("click", function () {
        setActive(heading.id);
      });

      if (heading.tagName.toLowerCase() === "h3") {
        if (currentMainItem) {
          let nested = currentMainItem.querySelector("ul");
          if (!nested) {
            nested = document.createElement("ul");
            nested.className = "docs-toc__nested";
            currentMainItem.appendChild(nested);
          }
          nested.appendChild(item);
        } else {
          list.appendChild(item);
        }
      } else {
        currentMainItem = item;
        list.appendChild(item);
      }

      headingMap.set(heading.id, link);
    });

    if (!headingMap.size) {
      tocRoot.hidden = true;
      return;
    }

    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            setActive(entry.target.id);
          }
        });
      },
      { rootMargin: "0px 0px -60% 0px", threshold: 0.2 }
    );

    function setActive(id) {
      headingMap.forEach(function (link, key) {
        if (key === id) {
          link.classList.add("is-active");
        } else {
          link.classList.remove("is-active");
        }
      });
    }

    headingMap.forEach(function (_, id) {
      const target = document.getElementById(id);
      if (target) {
        observer.observe(target);
      }
    });

    const firstId = headings.length ? headings[0].id : null;
    if (firstId) {
      setActive(firstId);
    }
  }

  function initSearch() {
    const input = document.querySelector("[data-docs-search]");
    const results = document.querySelector("[data-docs-search-results]");
    const sidebar = document.querySelector("[data-sidebar]");
    if (!input || !results || !sidebar) return;

    const entries = Array.from(sidebar.querySelectorAll(".docs-nav__link")).map(function (link) {
      const titleNode = link.querySelector(".docs-nav__title");
      const descriptionNode = link.querySelector(".docs-nav__description");
      const sectionNode = link.closest(".docs-nav__section");
      const sectionHeading = sectionNode ? sectionNode.querySelector(".docs-nav__heading") : null;
      return {
        title: titleNode ? titleNode.textContent.trim() : link.textContent.trim(),
        description: descriptionNode ? descriptionNode.textContent.trim() : "",
        section: sectionHeading ? sectionHeading.textContent.trim() : "",
        href: link.getAttribute("href") || "#"
      };
    });

    function clearResults() {
      results.innerHTML = "";
      results.classList.remove("is-visible");
    }

    function render(query) {
      const value = query.trim().toLowerCase();
      if (value.length < 2) {
        clearResults();
        return;
      }

      const matches = entries
        .filter(function (entry) {
          return (
            entry.title.toLowerCase().includes(value) ||
            entry.description.toLowerCase().includes(value) ||
            entry.section.toLowerCase().includes(value)
          );
        })
        .slice(0, 8);

      results.innerHTML = "";

      if (!matches.length) {
        const empty = document.createElement("p");
        empty.className = "docs-search__empty";
        empty.textContent = "No matches yet. Try another keyword.";
        results.appendChild(empty);
        results.classList.add("is-visible");
        return;
      }

      matches.forEach(function (entry) {
        const link = document.createElement("a");
        link.href = entry.href;
        if (entry.section) {
          const meta = document.createElement("span");
          meta.className = "docs-search__result-meta";
          meta.textContent = entry.section;
          link.appendChild(meta);
        }

        const title = document.createElement("span");
        title.className = "docs-search__result-title";
        title.textContent = entry.title;
        link.appendChild(title);

        if (entry.description) {
          const description = document.createElement("span");
          description.className = "docs-search__result-description";
          description.textContent = entry.description;
          link.appendChild(description);
        }
        results.appendChild(link);
      });

      results.classList.add("is-visible");
    }

    input.addEventListener("input", function (event) {
      render(event.target.value || "");
    });

    input.addEventListener("focus", function (event) {
      render(event.target.value || "");
    });

    document.addEventListener("click", function (event) {
      if (event.target === input || results.contains(event.target)) {
        return;
      }
      clearResults();
    });

    input.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        clearResults();
        input.blur();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    hydrateTheme();
    initThemeToggle();
    initMobileNav();
    initCopyButtons();
    initTableOfContents();
    initSearch();
  });
})();
