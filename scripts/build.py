from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path
from string import Template
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PROJECT = json.loads((ROOT / "data/project.json").read_text(encoding="utf-8"))
TAXONOMY = json.loads((ROOT / "data/taxonomy.json").read_text(encoding="utf-8"))
BASE = PROJECT["base_path"].rstrip("/")
REPO = PROJECT["repository"]
STAGES = TAXONOMY["stages"]
INSIGHTS = TAXONOMY["insights"]
STAGE_MAP = {stage["id"]: stage for stage in STAGES}
TOPIC_MAP = {topic["id"]: topic for topic in INSIGHTS}
LABELS = {
    "en": {
        "overview": "Overview", "insights": "Insights", "papers": "Papers", "cite": "Cite",
        "read": "Read the paper", "explore": "Explore papers", "survey": "A systematic survey",
        "hero": "XR Software<br>Engineering.", "hero_description": "A life-cycle perspective on building, testing and maintaining virtual and augmented reality software.",
        "overview_heading": "The full life cycle.<br>A shared perspective.",
        "overview_description": "Follow software engineering research through the seven stages of VR/AR software.",
        "insights_heading": "What changes<br>when software becomes spatial?",
        "insights_description": "Five connections across the research landscape.",
        "view_topic": "Explore the papers", "paper_count": "papers", "stage_count": "life-cycle stages",
        "topic_count": "research themes", "library_heading": "Find your next<br>research direction.",
        "library_description": "Explore papers by life-cycle stage, research theme, year and venue.",
        "selected": "Across the life cycle", "all_papers": "Browse all papers",
        "year": "Year", "venue": "Venue", "title": "Title", "idea": "Key insight", "links": "Links",
        "search": "Search papers", "search_placeholder": "Title, method, topic or author",
        "stage": "Life-cycle stage", "theme": "Research theme", "all_stages": "All stages",
        "all_themes": "All themes", "all_years": "All years", "all_venues": "All venues",
        "sort": "Sort", "newest": "Newest first", "oldest": "Oldest first", "title_sort": "Title A–Z",
        "clear": "Clear filters", "empty": "No papers match these filters.",
        "citation_heading": "Build on the survey.", "citation_description": "Read the paper, explore the resources and connect the research.",
        "copy": "Copy BibTeX", "copied": "Copied", "contribute": "Suggest a paper",
        "resources": "Development resources", "resources_description": "Tools, platforms and design references discussed in the survey.",
        "resource": "Resource", "related": "Related surveys", "authors": "Authors", "skip": "Skip to content",
        "menu": "Open navigation", "footer": "Software Engineering Practice in the VR/AR Software Life Cycle",
        "maintenance_code": "Code", "maintenance_assets": "3D assets", "maintenance_config": "Engine settings",
        "code_detail": "Scripts & interactions", "assets_detail": "Meshes & materials", "config_detail": "Build & runtime configuration",
        "measure": "Measure", "experience": "Understand", "improve": "Improve",
        "measure_detail": "Runtime quality", "experience_detail": "User & developer experience", "improve_detail": "Engineering decisions",
        "figure": "Figure", "open_figure": "Open full-resolution figure", "contents": "Paper lists", "research_themes": "Insight-based reading lists",
        "contribution": "Add a paper or resource through an issue or pull request.", "website": "Website", "library": "Paper library",
    },
    "zh": {
        "overview": "总览", "insights": "研究洞察", "papers": "论文库", "cite": "引用",
        "read": "阅读论文", "explore": "探索论文库", "survey": "系统性综述",
        "hero": "XR 软件工程。<br>贯穿全生命周期。", "hero_description": "以生命周期视角，连接 VR/AR 软件的设计、开发、质量保证与用户体验。",
        "overview_heading": "完整的生命周期。<br>共同的研究视角。",
        "overview_description": "沿着七个阶段，探索 VR/AR 软件工程研究。",
        "insights_heading": "当软件进入三维空间，<br>工程方法如何演进？",
        "insights_description": "连接研究版图的五条线索。",
        "view_topic": "查看相关论文", "paper_count": "篇研究论文", "stage_count": "个生命周期阶段",
        "topic_count": "个研究专题", "library_heading": "寻找下一个<br>研究方向。",
        "library_description": "按生命周期阶段、研究专题、年份和发表场所探索论文。",
        "selected": "贯穿生命周期", "all_papers": "浏览全部论文",
        "year": "年份", "venue": "发表场所", "title": "论文标题", "idea": "核心工作", "links": "链接",
        "search": "搜索论文", "search_placeholder": "标题、方法、主题或作者",
        "stage": "生命周期阶段", "theme": "研究专题", "all_stages": "全部阶段",
        "all_themes": "全部专题", "all_years": "全部年份", "all_venues": "全部发表场所",
        "sort": "排序", "newest": "年份从新到旧", "oldest": "年份从旧到新", "title_sort": "标题 A–Z",
        "clear": "清除筛选", "empty": "当前筛选条件下没有论文。",
        "citation_heading": "从综述出发。", "citation_description": "阅读论文，探索资源，连接研究。",
        "copy": "复制 BibTeX", "copied": "已复制", "contribute": "推荐论文",
        "resources": "开发资源", "resources_description": "综述涉及的工具、平台与设计参考。",
        "resource": "资源", "related": "相关综述", "authors": "作者", "skip": "跳转到正文",
        "menu": "展开导航", "footer": "VR/AR 软件生命周期中的软件工程实践",
        "maintenance_code": "代码", "maintenance_assets": "三维资产", "maintenance_config": "引擎设置",
        "code_detail": "脚本与交互逻辑", "assets_detail": "网格与材质", "config_detail": "构建与运行配置",
        "measure": "测量", "experience": "理解", "improve": "改进",
        "measure_detail": "运行质量", "experience_detail": "用户与开发者体验", "improve_detail": "工程决策",
        "figure": "图", "open_figure": "查看原始尺寸图片", "contents": "分类论文列表", "research_themes": "专题阅读清单",
        "contribution": "通过 Issue 或 Pull Request 补充论文与资源。", "website": "项目网站", "library": "论文库",
    },
}


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def local_url(lang: str, library: bool = False) -> str:
    suffix = "zh/" if lang == "zh" else ""
    return f"{BASE}/{suffix}{'papers/' if library else ''}"


def absolute_url(lang: str, library: bool = False) -> str:
    return "https://tsingpig.github.io" + local_url(lang, library)


def unique_stage_papers(papers: list[dict], stage: str) -> list[dict]:
    return [paper for paper in papers if any(category["stage"] == stage for category in paper["categories"])]


def sorted_papers(papers: list[dict]) -> list[dict]:
    return sorted(papers, key=lambda paper: (-paper["year"], paper["title"].casefold()))


def validate(papers: list[dict], resources: list[dict]) -> None:
    ids = set()
    for paper in papers:
        for field in ("id", "title", "year", "venue", "summary", "categories", "insights", "links"):
            if not paper.get(field) and field != "insights":
                raise ValueError(f"Missing {field} in {paper.get('id', 'paper')}")
        if paper["id"] in ids:
            raise ValueError(f"Duplicate paper id {paper['id']}")
        ids.add(paper["id"])
        if not isinstance(paper["year"], int) or not 1970 <= paper["year"] <= PROJECT["year"]:
            raise ValueError(f"Invalid year in {paper['id']}")
        for lang in ("en", "zh"):
            if not paper["summary"].get(lang, "").strip():
                raise ValueError(f"Missing {lang} summary in {paper['id']}")
        for category in paper["categories"]:
            stage = STAGE_MAP.get(category["stage"])
            if not stage or category["subtopic"] not in {item["id"] for item in stage["subtopics"]}:
                raise ValueError(f"Invalid category in {paper['id']}: {category}")
        if not set(paper["insights"]).issubset(TOPIC_MAP):
            raise ValueError(f"Invalid topic in {paper['id']}")
        for link in paper["links"].values():
            if not link.startswith(("https://", "http://")) or re.search(r"[\s<>]", link):
                raise ValueError(f"Invalid link in {paper['id']}")
    for resource in resources:
        if not resource.get("title") or not resource.get("links"):
            raise ValueError(f"Invalid resource {resource.get('id')}")
        if not all(resource.get("summary", {}).get(lang) for lang in ("en", "zh")):
            raise ValueError(f"Missing resource translation {resource.get('id')}")


def paper_links(paper: dict, markdown: bool = False) -> str:
    labels = {"paper": "Paper", "doi": "DOI", "arxiv": "arXiv", "code": "Code", "project": "Project"}
    links = []
    seen = set()
    for key, label in labels.items():
        url = paper["links"].get(key)
        if url and url not in seen:
            seen.add(url)
            links.append(f"[{label}]({url})" if markdown else f'<a href="{escape(url)}">{label}</a>')
    return " · ".join(links) if markdown else " ".join(links)


def primary_link(paper: dict) -> str:
    return next(paper["links"][key] for key in ("paper", "doi", "arxiv", "project") if paper["links"].get(key))


def paper_search_text(paper: dict) -> str:
    terms = [
        paper["title"],
        paper.get("authors", ""),
        str(paper["year"]),
        paper["venue"],
        *paper["summary"].values(),
    ]
    for category in paper["categories"]:
        stage = STAGE_MAP[category["stage"]]
        subtopic = next(
            item for item in stage["subtopics"]
            if item["id"] == category["subtopic"]
        )
        terms.extend([
            stage["id"],
            *stage["title"].values(),
            subtopic["id"],
            subtopic["en"],
            subtopic["zh"],
        ])
    for identifier in paper["insights"]:
        topic = TOPIC_MAP[identifier]
        terms.extend([identifier, *topic["short"].values(), *topic["title"].values()])
    return " ".join(terms).casefold()


def paper_table(papers: list[dict], lang: str) -> str:
    labels = LABELS[lang]
    heads = [labels[key] for key in ("year", "venue", "title", "idea", "links")]
    rows = []
    for paper in sorted_papers(papers):
        stages = " ".join(sorted({item["stage"] for item in paper["categories"]}))
        values = [
            str(paper["year"]),
            escape(paper["venue"]),
            f'<a href="{escape(primary_link(paper))}">{escape(paper["title"])}</a>',
            escape(paper["summary"][lang]),
            f'<div class="paper-links">{paper_links(paper)}</div>',
        ]
        cells = "".join(
            f'<td class="paper-{column}" data-label="{escape(label)}">{value}</td>'
            for column, label, value in zip(
                ("year", "venue", "name", "summary", "resources"), heads, values
            )
        )
        rows.append(dedent(f'''
            <tr data-paper="{escape(paper["id"])}"
                data-search="{escape(paper_search_text(paper))}"
                data-stages="{escape(stages)}"
                data-topics="{escape(" ".join(paper["insights"]))}"
                data-year="{paper["year"]}"
                data-venue="{escape(paper["venue"])}"
                data-title="{escape(paper["title"])}">
              {cells}
            </tr>
        ''').strip())
    header = "".join(f'<th scope="col">{escape(head)}</th>' for head in heads)
    return dedent(f'''
        <div class="table-scroll">
          <table class="paper-table">
            <thead><tr>{header}</tr></thead>
            <tbody>{"".join(rows)}</tbody>
          </table>
        </div>
    ''').strip()


def header(lang: str, library: bool) -> str:
    labels = LABELS[lang]
    home = local_url(lang)
    peer = local_url("en" if lang == "zh" else "zh", library)
    links = [
        (home + "#overview", labels["overview"]),
        (home + "#insights", labels["insights"]),
        (local_url(lang, True), labels["papers"]),
        (home + "#cite", labels["cite"]),
    ]
    nav = "".join(f'<a href="{url}">{label}</a>' for url, label in links)
    return dedent(f'''
        <header class="site-header">
          <div class="nav-shell container">
            <a class="brand" href="{home}">XR Software Engineering</a>
            <nav id="site-nav" aria-label="{'Primary' if lang == 'en' else '主导航'}">{nav}</nav>
            <a class="lang-switch" data-peer="{peer}" href="{peer}"
               lang="{'en' if lang == 'zh' else 'zh-CN'}">{'EN' if lang == 'zh' else '中文'}</a>
            <button class="menu-toggle" type="button" aria-controls="site-nav"
                    aria-expanded="false" aria-label="{labels['menu']}">
              <span></span><span></span>
            </button>
          </div>
        </header>
    ''').strip()


def footer(lang: str) -> str:
    return dedent(f'''
        <footer class="site-footer">
          <div class="container footer-shell">
            <div>
              <a class="brand" href="{local_url(lang)}">XR Software Engineering</a>
              <p>{LABELS[lang]['footer']}</p>
            </div>
            <div class="footer-links">
              <a href="{PROJECT['paper']}">arXiv ↗</a>
              <a href="{REPO}">GitHub ↗</a>
            </div>
          </div>
        </footer>
    ''').strip()


def author_html() -> str:
    authors = []
    for author in PROJECT["authors"]:
        name = escape(author["name"])
        if author.get("url"):
            name = f'<a href="{escape(author["url"])}">{name}</a>'
        affiliations = ",".join(str(index) for index in author["affiliations"])
        authors.append(f'<span>{name}<sup>{affiliations}</sup></span>')
    institutions = "".join(
        f'<span><sup>{index}</sup>{escape(name)}</span>'
        for index, name in enumerate(PROJECT["affiliations"], 1)
    )
    return f'<div class="authors">{"".join(authors)}</div><div class="affiliations">{institutions}</div>'


def citation(lang: str) -> str:
    labels = LABELS[lang]
    return dedent(f'''
        <section class="citation" id="cite">
          <div class="container citation-grid">
            <div>
              <p class="eyebrow">{labels['cite']}</p>
              <h2>{labels['citation_heading']}</h2>
              <p>{labels['citation_description']}</p>
              <a class="text-link" href="{REPO}/issues/new/choose">{labels['contribute']} ↗</a>
            </div>
            <div class="citation-code">
              <div class="code-toolbar">
                <span>BibTeX</span>
                <button type="button" data-copy="bibtex" data-label="{labels['copy']}"
                        data-success="{labels['copied']}">{labels['copy']}</button>
                <span class="copy-status" aria-live="polite"></span>
              </div>
              <pre><code id="bibtex">{escape(PROJECT['bibtex'])}</code></pre>
            </div>
          </div>
        </section>
    ''').strip()


def visual(topic: dict, lang: str) -> str:
    labels = LABELS[lang]
    if topic.get("figure"):
        source = f'{BASE}/assets/{topic["figure"]}'
        description = escape(topic["figure_alt"][lang])
        return dedent(f'''
            <figure class="insight-visual">
              <a href="{source}" aria-label="{labels['open_figure']} · {description}">
                <img src="{source}" alt="{description}" loading="lazy">
              </a>
            </figure>
        ''').strip()
    if topic["id"] == "maintenance":
        entries = [
            ("{ }", "maintenance_code", "code_detail"),
            ("▧", "maintenance_assets", "assets_detail"),
            ("⌘", "maintenance_config", "config_detail"),
        ]
        blocks = "".join(dedent(f'''
            <div class="artifact">
              <span class="visual-symbol" aria-hidden="true">{symbol}</span>
              <strong>{labels[title]}</strong>
              <span>{labels[detail]}</span>
            </div>
        ''').strip() for symbol, title, detail in entries)
        return f'<div class="insight-visual artifact-flow">{blocks}</div>'
    entries = [
        ("↗", "measure", "measure_detail"),
        ("◎", "experience", "experience_detail"),
        ("↻", "improve", "improve_detail"),
    ]
    blocks = "".join(dedent(f'''
        <div class="feedback-step">
          <span class="visual-symbol" aria-hidden="true">{symbol}</span>
          <strong>{labels[title]}</strong>
          <span>{labels[detail]}</span>
        </div>
    ''').strip() for symbol, title, detail in entries)
    return f'<div class="insight-visual feedback-loop">{blocks}</div>'


def landing(papers: list[dict], lang: str) -> str:
    labels = LABELS[lang]
    library = local_url(lang, True)
    overview = PROJECT["overview"]
    hero_source = f"{BASE}/assets/{overview['image']}"
    hero_alt = escape(overview["alt"][lang])
    hero_caption = overview["caption"][lang]
    hero = dedent(f'''
        <section class="hero">
          <div class="container">
            <p class="eyebrow">{labels['survey']}</p>
            <h1>{labels['hero']}</h1>
            <p class="hero-description">{labels['hero_description']}</p>
            <p class="paper-title">{escape(PROJECT['title'])}</p>
            {author_html()}
            <div class="hero-actions">
              <a class="button primary" href="{PROJECT['paper']}">{labels['read']} ↗</a>
              <a class="button secondary" href="{REPO}">GitHub ↗</a>
              <a class="text-link" href="{library}">{labels['explore']} →</a>
            </div>
            <figure class="hero-figure">
              <a href="{hero_source}"
                 aria-label="{labels['open_figure']} · {hero_alt}">
                <img src="{hero_source}" width="{overview['width']}" height="{overview['height']}"
                     alt="{hero_alt}" fetchpriority="high">
              </a>
              <figcaption>{labels['figure']} {overview['number']} · {hero_caption}</figcaption>
            </figure>
            <div class="stats">
              <div class="stat"><strong>{len(papers)}</strong><span>{labels['paper_count']}</span></div>
              <div class="stat"><strong>7</strong><span>{labels['stage_count']}</span></div>
              <div class="stat"><strong>5</strong><span>{labels['topic_count']}</span></div>
            </div>
          </div>
        </section>
    ''').strip()
    cards = []
    for index, stage in enumerate(STAGES[:7], 1):
        count = len(unique_stage_papers(papers, stage["id"]))
        cards.append(dedent(f'''
            <a class="stage-card" href="{library}?stage={stage["id"]}">
              <span class="stage-number">{index:02d}</span>
              <h3>{stage["title"][lang]}</h3>
              <p>{stage["description"][lang]}</p>
              <span class="stage-count">
                {count} {labels["paper_count"]} <span aria-hidden="true">↗</span>
              </span>
            </a>
        ''').strip())
    overview = dedent(f'''
        <section class="overview" id="overview">
          <div class="container">
            <div class="section-heading">
              <p class="eyebrow">{labels['overview']}</p>
              <h2>{labels['overview_heading']}</h2>
              <p>{labels['overview_description']}</p>
            </div>
            <div class="stage-grid">{''.join(cards)}</div>
          </div>
        </section>
    ''').strip()
    stories = []
    paper_map = {paper["id"]: paper for paper in papers}
    for topic in INSIGHTS:
        reading_links = "".join(
            f'<li><a href="{escape(primary_link(paper_map[key]))}">'
            f'{escape(paper_map[key]["title"])}</a></li>'
            for key in topic["featured"]
        )
        stories.append(dedent(f'''
            <article class="insight-card" id="{topic["id"]}">
              <div class="insight-copy">
                <p class="eyebrow">{topic["short"][lang]}</p>
                <h3>{topic["title"][lang]}</h3>
                <p>{topic["description"][lang]}</p>
                <ul class="insight-papers">{reading_links}</ul>
                <a class="text-link" href="{library}?topic={topic["id"]}">{labels["view_topic"]} →</a>
              </div>
              {visual(topic, lang)}
            </article>
        ''').strip())
    insights = dedent(f'''
        <section class="insights" id="insights">
          <div class="container">
            <div class="section-heading">
              <p class="eyebrow">{labels['insights']}</p>
              <h2>{labels['insights_heading']}</h2>
              <p>{labels['insights_description']}</p>
            </div>
            <div class="insight-list">{''.join(stories)}</div>
          </div>
        </section>
    ''').strip()
    selected = []
    for stage in STAGES[:7]:
        candidates = sorted_papers(unique_stage_papers(papers, stage["id"]))
        candidate = next((paper for paper in candidates if paper not in selected), None)
        if candidate:
            selected.append(candidate)
    preview = dedent(f'''
        <section class="library paper-preview">
          <div class="container">
            <div class="section-heading">
              <p class="eyebrow">{labels['selected']}</p>
              <h2>{labels['library_heading']}</h2>
              <p>{labels['library_description']}</p>
            </div>
            {paper_table(selected, lang)}
            <div class="section-action">
              <a class="button primary" href="{library}">{labels['all_papers']} →</a>
            </div>
          </div>
        </section>
    ''').strip()
    return hero + overview + insights + preview + citation(lang)


def filter_select(name: str, label: str, options: list[tuple[str, str]]) -> str:
    choices = "".join(
        f'<option value="{escape(value)}">{escape(text)}</option>'
        for value, text in options
    )
    return dedent(f'''
        <label>
          <span>{escape(label)}</span>
          <select name="{name}">{choices}</select>
        </label>
    ''').strip()


def library_page(papers: list[dict], resources: list[dict], lang: str) -> str:
    labels = LABELS[lang]
    stage_options = [("", labels["all_stages"])] + [
        (stage["id"], stage["title"][lang]) for stage in STAGES
    ]
    topic_options = [("", labels["all_themes"])] + [
        (topic["id"], topic["short"][lang]) for topic in INSIGHTS
    ]
    year_options = [("", labels["all_years"])] + [
        (str(year), str(year))
        for year in sorted({paper["year"] for paper in papers}, reverse=True)
    ]
    venue_options = [("", labels["all_venues"])] + [
        (venue, venue)
        for venue in sorted({paper["venue"] for paper in papers}, key=str.casefold)
    ]
    sort_options = [
        ("year-desc", labels["newest"]),
        ("year-asc", labels["oldest"]),
        ("title", labels["title_sort"]),
    ]
    controls = [
        ("stage", "stage", stage_options),
        ("topic", "theme", topic_options),
        ("year", "year", year_options),
        ("venue", "venue", venue_options),
        ("sort", "sort", sort_options),
    ]
    selects = "".join(
        filter_select(name, labels[label], options)
        for name, label, options in controls
    )
    filters = dedent(f'''
        <form class="filters" id="paper-filters" role="search">
          <label class="search-field">
            <span>{labels["search"]}</span>
            <input type="search" name="q" placeholder="{labels["search_placeholder"]}"
                   autocomplete="off">
          </label>
          {selects}
        </form>
    ''').strip()
    resources_html = "".join(dedent(f'''
        <article class="resource-card">
          <h3><a href="{escape(primary_link(resource))}">{escape(resource["title"])} ↗</a></h3>
          <p>{escape(resource["summary"][lang])}</p>
        </article>
    ''').strip() for resource in resources)
    return dedent(f'''
        <section class="library-hero">
          <div class="container">
            <p class="eyebrow">{labels['library']}</p>
            <h1>{labels['library_heading']}</h1>
            <p>{labels['library_description']}</p>
          </div>
        </section>
        <section class="library full-library">
          <div class="container">
            {filters}
            <div class="library-toolbar">
              <p id="result-count" role="status" aria-live="polite">{len(papers)} {labels['paper_count']}</p>
              <button id="clear-filters" type="button">{labels['clear']}</button>
            </div>
            {paper_table(papers, lang)}
            <p class="empty-state" hidden>{labels['empty']}</p>
          </div>
        </section>
        <section class="resources" id="resources">
          <div class="container">
            <div class="section-heading">
              <h2>{labels['resources']}</h2>
              <p>{labels['resources_description']}</p>
            </div>
            <div class="resource-grid">{resources_html}</div>
          </div>
        </section>
    ''').strip()


def render_page(papers: list[dict], resources: list[dict], lang: str, library: bool) -> str:
    canonical = absolute_url(lang, library)
    title = PROJECT["name"] if not library else f"{LABELS[lang]['library']} · {PROJECT['name']}"
    structured_data = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "name": PROJECT["title"],
        "url": PROJECT["paper"],
        "datePublished": str(PROJECT["year"]),
        "author": [
            {"@type": "Person", "name": person["name"]}
            for person in PROJECT["authors"]
        ],
    }
    template = Template((ROOT / "site/templates/layout.html").read_text(encoding="utf-8"))
    return template.substitute(
        html_lang="zh-CN" if lang == "zh" else "en",
        lang=lang,
        page_title=escape(title),
        description=escape(PROJECT["description"][lang]),
        canonical=canonical,
        english_url=absolute_url("en", library),
        chinese_url=absolute_url("zh", library),
        social_image=PROJECT["website"] + "assets/" + PROJECT["overview"]["image"],
        base=BASE,
        structured_data=json.dumps(structured_data, ensure_ascii=False).replace("<", "\\u003c"),
        skip_label=LABELS[lang]["skip"],
        header=header(lang, library),
        footer=footer(lang),
        content=library_page(papers, resources, lang) if library else landing(papers, lang),
    )


def markdown_text(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def markdown_table(papers: list[dict], lang: str) -> str:
    labels = LABELS[lang]
    columns = [labels[key] for key in ("year", "venue", "title", "idea", "links")]
    lines = ["| " + " | ".join(columns) + " |", "| --- | --- | --- | --- | --- |"]
    for paper in sorted_papers(papers):
        title = markdown_text(paper["title"])
        cells = [str(paper["year"]), markdown_text(paper["venue"]), f"[{title}]({primary_link(paper)})", markdown_text(paper["summary"][lang]), paper_links(paper, True)]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def readme(papers: list[dict], resources: list[dict], lang: str) -> str:
    labels = LABELS[lang]
    website = absolute_url(lang)
    overview = PROJECT["overview"]
    lines = ["[English](README.md) · [中文](README.zh-CN.md)", "", "# XR Software Engineering Survey", "", PROJECT["title"], "", PROJECT["description"][lang], "", f"[arXiv]({PROJECT['paper']}) · [{labels['website']}]({website}) · [{labels['library']}]({absolute_url(lang, True)})", "", ", ".join(person["name"] for person in PROJECT["authors"]), "", f"![{overview['alt'][lang]}](site/assets/{overview['image']})", "", f"**{len(papers)} {labels['paper_count']} · 7 {labels['stage_count']} · 5 {labels['topic_count']}**", "", f"## {labels['research_themes']}", ""]
    for topic in INSIGHTS:
        path = f"lists/{'zh/' if lang == 'zh' else ''}{topic['id']}.md"
        lines.extend([f"### [{topic['title'][lang]}]({path})", "", topic["description"][lang], ""])
        if topic["id"] == "ai":
            lines.extend([f"![{topic['figure_alt'][lang]}](site/assets/{topic['figure']})", ""])
        paper_map = {paper["id"]: paper for paper in papers}
        for key in topic["featured"]:
            paper = paper_map[key]
            lines.append(f"- [{markdown_text(paper['title'])}]({primary_link(paper)})")
        lines.append("")
    lines.extend([f"## {labels['contents']}", ""])
    for stage in STAGES:
        count = len(unique_stage_papers(papers, stage["id"]))
        if count:
            lines.append(f"- [{stage['title'][lang]}](#{stage['id']}) · {count}")
    lines.append("")
    for stage in STAGES:
        stage_papers = unique_stage_papers(papers, stage["id"])
        if not stage_papers:
            continue
        lines.extend([f'<a id="{stage["id"]}"></a>', "", f"## {stage['title'][lang]}", "", stage["description"][lang], ""])
        for subtopic in stage["subtopics"]:
            subset = [paper for paper in stage_papers if any(category["stage"] == stage["id"] and category["subtopic"] == subtopic["id"] for category in paper["categories"])]
            if subset:
                lines.extend([f"### {subtopic[lang]}", "", markdown_table(subset, lang), ""])
    if resources:
        lines.extend([f"## {labels['resources']}", "", f"| {labels['resource']} | {labels['idea']} | {labels['links']} |", "| --- | --- | --- |"])
        for resource in resources:
            lines.append(f"| {markdown_text(resource['title'])} | {markdown_text(resource['summary'][lang])} | {paper_links(resource, True)} |")
        lines.append("")
    lines.extend([f"## {labels['cite']}", "", "```bibtex", PROJECT["bibtex"], "```", "", f"## {'Contribute' if lang == 'en' else '参与整理'}", "", labels["contribution"], "", f"[Issues]({REPO}/issues) · [Pull requests]({REPO}/pulls)", ""])
    return "\n".join(lines)


def topic_markdown(topic: dict, papers: list[dict], lang: str) -> str:
    peer = f"../{topic['id']}.md" if lang == "zh" else f"zh/{topic['id']}.md"
    home = "../../README.zh-CN.md" if lang == "zh" else "../README.md"
    subset = [paper for paper in papers if topic["id"] in paper["insights"]]
    lines = [f"[{'English' if lang == 'zh' else '中文'}]({peer}) · [XR Software Engineering Survey]({home})", "", f"# {topic['title'][lang]}", "", topic["description"][lang], "", f"[{LABELS[lang]['library']}]({absolute_url(lang, True)}?topic={topic['id']}) · [arXiv]({PROJECT['paper']})", "", markdown_table(subset, lang), ""]
    return "\n".join(lines)


def citation_file() -> str:
    lines = [
        'cff-version: 1.2.0',
        'message: "Cite the survey."',
        'type: dataset',
        f'title: "{PROJECT["name"]}"',
        f'url: "{PROJECT["website"]}"',
        f'repository-code: "{REPO}"',
        'authors:',
    ]
    for person in PROJECT["authors"]:
        given, family = person["name"].rsplit(" ", 1)
        lines.extend([f'  - family-names: "{family}"', f'    given-names: "{given}"'])
    lines.extend([
        'preferred-citation:',
        '  type: article',
        f'  title: "{PROJECT["title"]}"',
        f'  journal: "arXiv preprint arXiv:{PROJECT["arxiv"]}"',
        f'  year: {PROJECT["year"]}',
        f'  url: "{PROJECT["paper"]}"',
        '  authors:',
    ])
    for person in PROJECT["authors"]:
        given, family = person["name"].rsplit(" ", 1)
        lines.extend([f'    - family-names: "{family}"', f'      given-names: "{given}"'])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    papers = json.loads((ROOT / "data/papers.json").read_text(encoding="utf-8"))
    resources = json.loads((ROOT / "data/resources.json").read_text(encoding="utf-8"))
    validate(papers, resources)
    documents = {ROOT / "README.md": readme(papers, resources, "en"), ROOT / "README.zh-CN.md": readme(papers, resources, "zh"), ROOT / "CITATION.cff": citation_file()}
    for lang in ("en", "zh"):
        for topic in INSIGHTS:
            folder = ROOT / "lists" / ("zh" if lang == "zh" else "")
            documents[folder / f"{topic['id']}.md"] = topic_markdown(topic, papers, lang)
    if args.check:
        outdated = [str(path.relative_to(ROOT)) for path, content in documents.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
        if outdated:
            raise SystemExit("Regenerate: " + ", ".join(outdated))
    else:
        for path, content in documents.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
        for lang in ("en", "zh"):
            for library in (False, True):
                path = DIST / ("zh" if lang == "zh" else "") / ("papers" if library else "") / "index.html"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(render_page(papers, resources, lang, library), encoding="utf-8", newline="\n")
        shutil.copytree(ROOT / "site/assets", DIST / "assets", dirs_exist_ok=True)
        (DIST / ".nojekyll").touch()
        urls = [absolute_url(lang, library) for lang in ("en", "zh") for library in (False, True)]
        sitemap = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{url}</loc></url>" for url in urls) + "</urlset>\n"
        (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")
        (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {PROJECT['website']}sitemap.xml\n", encoding="utf-8")
    print(f"{'Checked' if args.check else 'Built'} {len(papers)} papers, {len(resources)} resources, 7 stages, 5 themes, 2 languages.")


if __name__ == "__main__":
    main()
