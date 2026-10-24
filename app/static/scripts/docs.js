/* Documentation shell enhancements: the "On this page" table of contents and the sidebar search.
   Theme switching, the collapsible sidebar, copy buttons and every interactive component come from the
   flask-basecoat runtime; this file only adds what is specific to the docs pages. */
(function () {
  function slugify(text) {
    return (text || "")
      .toString()
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)+/g, "")
      .substring(0, 60);
  }

  function initTableOfContents() {
    const tocRoot = document.querySelector("[data-docs-toc]");
    const article = document.querySelector("[data-docs-article]");
    if (!tocRoot || !article) return;

    const headings = Array.from(article.querySelectorAll("h2, h3")).filter(function (heading) {
      if (heading.closest("[data-preview]")) return false;
      return Boolean(heading.textContent && heading.textContent.trim().length);
    });

    if (!headings.length) {
      tocRoot.hidden = true;
      return;
    }

    tocRoot.innerHTML = "";
    const title = document.createElement("p");
    title.className = "text-sm font-medium";
    title.textContent = "On this page";
    tocRoot.appendChild(title);

    const list = document.createElement("ul");
    list.className = "mt-2 flex flex-col gap-1 border-l text-sm";
    tocRoot.appendChild(list);

    const links = new Map();

    headings.forEach(function (heading) {
      if (!heading.id) {
        const base = slugify(heading.textContent);
        let candidate = base;
        let index = 1;
        while (candidate && document.getElementById(candidate)) {
          candidate = base + "-" + index;
          index += 1;
        }
        heading.id = candidate || base;
      }
      if (!heading.id) return;

      const link = document.createElement("a");
      link.href = "#" + heading.id;
      link.textContent = heading.textContent.trim();
      link.className =
        "-ml-px block border-l border-transparent py-1 text-muted-foreground transition-colors hover:text-foreground " +
        "data-[active=true]:border-foreground data-[active=true]:font-medium data-[active=true]:text-foreground " +
        (heading.tagName.toLowerCase() === "h3" ? "pl-8" : "pl-4");
      link.addEventListener("click", function () {
        setActive(heading.id);
      });

      const item = document.createElement("li");
      item.appendChild(link);
      list.appendChild(item);
      links.set(heading.id, link);
    });

    function setActive(id) {
      links.forEach(function (link, key) {
        if (key === id) link.setAttribute("data-active", "true");
        else link.removeAttribute("data-active");
      });
    }

    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) setActive(entry.target.id);
          });
        },
        { rootMargin: "0px 0px -60% 0px", threshold: 0.2 }
      );
      headings.forEach(function (heading) {
        observer.observe(heading);
      });
    }
    setActive(headings[0].id);
  }

  function initSearch() {
    const input = document.querySelector("[data-docs-search]");
    const results = document.querySelector("[data-docs-search-results]");
    if (!input || !results) return;

    const entries = Array.from(document.querySelectorAll("[data-docs-nav]")).map(function (link) {
      return {
        title: link.textContent.trim(),
        description: link.getAttribute("data-description") || "",
        section: link.getAttribute("data-section") || "",
        href: link.getAttribute("href") || "#",
      };
    });

    function hide() {
      results.innerHTML = "";
      results.classList.add("hidden");
      results.classList.remove("flex");
    }

    function show() {
      results.classList.remove("hidden");
      results.classList.add("flex");
    }

    function render(query) {
      const value = query.trim().toLowerCase();
      if (value.length < 2) {
        hide();
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
        empty.className = "px-2 py-1.5 text-sm text-muted-foreground";
        empty.textContent = "No matches yet. Try another keyword.";
        results.appendChild(empty);
        show();
        return;
      }

      matches.forEach(function (entry) {
        const link = document.createElement("a");
        link.href = entry.href;
        link.className =
          "flex flex-col gap-0.5 rounded-sm px-2 py-1.5 text-sm outline-hidden hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground";
        if (entry.section) {
          const meta = document.createElement("span");
          meta.className = "text-xs text-muted-foreground";
          meta.textContent = entry.section;
          link.appendChild(meta);
        }
        const title = document.createElement("span");
        title.className = "font-medium";
        title.textContent = entry.title;
        link.appendChild(title);
        if (entry.description) {
          const description = document.createElement("span");
          description.className = "text-xs text-muted-foreground line-clamp-2";
          description.textContent = entry.description;
          link.appendChild(description);
        }
        results.appendChild(link);
      });
      show();
    }

    input.addEventListener("input", function (event) {
      render(event.target.value || "");
    });
    input.addEventListener("focus", function (event) {
      render(event.target.value || "");
    });
    input.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        hide();
        input.blur();
      }
    });
    document.addEventListener("click", function (event) {
      if (event.target === input || results.contains(event.target)) return;
      hide();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTableOfContents();
    initSearch();
  });
})();
