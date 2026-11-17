(() => {
  const language = document.body.dataset.lang === "zh" ? "zh" : "en";
  const locale = language === "zh" ? "zh-CN" : "en";
  const languageLinks = [...document.querySelectorAll("a.lang-switch[data-peer]")];

  function syncLanguageLinks() {
    languageLinks.forEach(link => {
      const target = new URL(link.dataset.peer, window.location.href);
      target.search = window.location.search;
      target.hash = window.location.hash;
      link.href = target.href;
    });
  }

  const header = document.querySelector(".site-header");
  const menuToggle = document.querySelector(".menu-toggle");

  if (header && menuToggle) {
    const navigation = document.getElementById(menuToggle.getAttribute("aria-controls") || "site-nav");

    function setMenu(open) {
      menuToggle.setAttribute("aria-expanded", String(open));
      header.classList.toggle("menu-open", open);
    }

    menuToggle.addEventListener("click", () => {
      setMenu(menuToggle.getAttribute("aria-expanded") !== "true");
    });

    navigation?.addEventListener("click", event => {
      if (event.target.closest("a")) setMenu(false);
    });

    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && menuToggle.getAttribute("aria-expanded") === "true") {
        setMenu(false);
        menuToggle.focus();
      }
    });

    window.matchMedia("(min-width: 901px)").addEventListener("change", event => {
      if (event.matches) setMenu(false);
    });
  }

  const form = document.getElementById("paper-filters");
  const tableBody = document.querySelector(".paper-table tbody");

  if (form && tableBody) {
    const fields = ["q", "stage", "topic", "year", "venue", "sort"];
    const controls = Object.fromEntries(fields.map(name => [name, form.elements.namedItem(name)]));
    const rows = [...tableBody.querySelectorAll("tr[data-paper]")];
    const resultCount = document.getElementById("result-count");
    const emptyState = document.querySelector(".empty-state");
    const clearButton = document.getElementById("clear-filters");
    const collator = new Intl.Collator(locale, { sensitivity: "base", numeric: true });
    let searchTimeout;

    function normalize(value) {
      return String(value || "")
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLocaleLowerCase(locale)
        .trim();
    }

    const searchText = new Map(rows.map(row => [row, normalize(row.dataset.search || row.textContent)]));

    function readQuery() {
      const query = new URLSearchParams(window.location.search);

      fields.forEach(name => {
        const control = controls[name];
        if (!control) return;

        const value = query.get(name) || (name === "sort" ? "year-desc" : "");
        if (control.tagName === "SELECT") {
          const allowed = [...control.options].some(option => option.value === value);
          control.value = allowed ? value : (name === "sort" ? "year-desc" : "");
        } else {
          control.value = value;
        }
      });
    }

    function applyFilters(writeUrl = true) {
      const values = Object.fromEntries(fields.map(name => [name, controls[name]?.value || ""]));
      const terms = normalize(values.q).split(/\s+/).filter(Boolean);
      let visible = 0;

      rows.forEach(row => {
        const stages = (row.dataset.stages || "").split(/\s+/);
        const topics = (row.dataset.topics || "").split(/\s+/);
        const matches = terms.every(term => searchText.get(row).includes(term))
          && (!values.stage || stages.includes(values.stage))
          && (!values.topic || topics.includes(values.topic))
          && (!values.year || row.dataset.year === values.year)
          && (!values.venue || row.dataset.venue === values.venue);

        row.hidden = !matches;
        if (matches) visible += 1;
      });

      const sortedRows = [...rows].sort((left, right) => {
        const byTitle = collator.compare(left.dataset.title || "", right.dataset.title || "");
        if (values.sort === "title") return byTitle;

        const byYear = Number(left.dataset.year || 0) - Number(right.dataset.year || 0);
        return (values.sort === "year-asc" ? byYear : -byYear) || byTitle;
      });

      const fragment = document.createDocumentFragment();
      sortedRows.forEach(row => fragment.append(row));
      tableBody.append(fragment);

      if (resultCount) {
        resultCount.textContent = language === "zh"
          ? `显示 ${visible} / ${rows.length} 篇论文`
          : `${visible} of ${rows.length} papers`;
      }

      if (emptyState) emptyState.hidden = visible !== 0;

      if (writeUrl) {
        const url = new URL(window.location.href);

        fields.forEach(name => {
          const value = values[name].trim();
          if (value && !(name === "sort" && value === "year-desc")) {
            url.searchParams.set(name, value);
          } else {
            url.searchParams.delete(name);
          }
        });

        window.history.replaceState(null, "", url);
      }

      syncLanguageLinks();
    }

    form.addEventListener("submit", event => {
      event.preventDefault();
      window.clearTimeout(searchTimeout);
      applyFilters();
    });

    controls.q?.addEventListener("input", () => {
      window.clearTimeout(searchTimeout);
      searchTimeout = window.setTimeout(applyFilters, 160);
    });

    fields.filter(name => name !== "q").forEach(name => {
      controls[name]?.addEventListener("change", () => {
        window.clearTimeout(searchTimeout);
        applyFilters();
      });
    });

    clearButton?.addEventListener("click", event => {
      event.preventDefault();
      window.clearTimeout(searchTimeout);
      fields.forEach(name => {
        if (controls[name]) controls[name].value = name === "sort" ? "year-desc" : "";
      });
      applyFilters();
    });

    window.addEventListener("popstate", () => {
      window.clearTimeout(searchTimeout);
      readQuery();
      applyFilters(false);
    });

    readQuery();
    applyFilters(false);
  }

  document.querySelectorAll("button[data-copy]").forEach(button => {
    const source = document.getElementById(button.dataset.copy);
    if (!source) return;

    const label = button.dataset.label || button.textContent;
    const success = button.dataset.success || (language === "zh" ? "已复制" : "Copied");
    const status = button.closest(".citation-code")?.querySelector(".copy-status");
    let resetTimeout;

    button.addEventListener("click", async () => {
      window.clearTimeout(resetTimeout);

      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(source.textContent.trim());
        } else {
          const field = document.createElement("textarea");
          const activeElement = document.activeElement;
          field.value = source.textContent.trim();
          field.style.cssText = "position:fixed;left:-9999px;top:0;opacity:0";
          document.body.append(field);
          field.select();
          const copied = document.execCommand("copy");
          field.remove();
          activeElement?.focus({ preventScroll: true });
          if (!copied) throw new Error("Clipboard copy failed");
        }

        button.textContent = success;
        if (status) status.textContent = success;
      } catch {
        const range = document.createRange();
        range.selectNodeContents(source);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        button.textContent = language === "zh" ? "已选中文本" : "Text selected";
        if (status) status.textContent = button.textContent;
      }

      resetTimeout = window.setTimeout(() => {
        button.textContent = label;
        if (status) status.textContent = "";
      }, 2000);
    });
  });

  window.addEventListener("hashchange", syncLanguageLinks);
  syncLanguageLinks();
})();
