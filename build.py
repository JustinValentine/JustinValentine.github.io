#!/usr/bin/env python3
"""Build the site from src/.

Each post is src/posts/<slug>.html: a few `key: value` lines, a line with
three dashes, then the post body as HTML. The body is published at
posts/<slug>/index.html, so its links and images are written relative to
that folder (images are ../../images/..., other posts are ../<slug>/index.html).

Header keys:
  title     required
  date      2023-12-08, 2026-10 or 2024 (shown at that precision)
  topics    comma-separated slugs from TOPICS below
  summary   one or two sentences for the lists
  image     thumbnail, path from the site root (optional)
  video     thumbnail video instead of an image (optional, mp4; plays like a GIF)
  thumb_fit contain, to show the whole thumbnail image instead of cropping it
  thumb_position  CSS object-position for the thumbnail crop, e.g. 50% 30%
  thumb_zoom      scale factor for a thumbnail, e.g. 1.8
  featured  1, 2, 3...: show the post in the homepage's Featured row, in that order
  series    a key from SERIES, to list the other posts in that series
  series_order  position in the series (otherwise date order)
  math      yes, to load KaTeX for \\( ... \\) and \\[ ... \\]
  home      no, to leave a post off the homepage

The homepage, the topic pages, the post archive, the About page and the RSS
feed are all generated. Run:  python3 build.py
"""
import datetime
import html
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://justinvalentine.ca/"
EMAIL = "justin@justinvalentine.ca"
GITHUB = "https://github.com/JustinValentine"
DEFAULT_IMAGE = "images/wrist-front.jpg"  # link-preview image for pages without their own
SCHOLAR = "https://scholar.google.com/citations?user=Dwp3tBEAAAAJ&amp;hl=en"

TOPICS = [
    ("haptics", "Haptics"),
    ("teleoperation", "Teleoperation"),
    ("mechanisms", "Mechanisms"),
    ("legged-robots", "Legged robots"),
    ("control", "Control"),
    ("electronics", "Electronics"),
    ("machining", "Machining"),
    ("simulation", "Simulation"),
    ("learning", "Machine learning"),
    ("vision", "Computer vision"),
    ("software", "Software"),
    ("games", "Games"),
]
TOPIC_NAMES = dict(TOPICS)
SERIES = {"haptic-wrist": {
    "title": "Finding a haptic wrist design",
    "intro": "Before I leave for Barrett, I&rsquo;m trying to settle on a wrist design for our WAM teleoperation setup, so I build and test one idea after another. These are the designs in the order I try them.",
}}
# Comments with giscus (GitHub Discussions). Turned on once category_id is filled in.
GISCUS = {
    "repo": "JustinValentine/JustinValentine.github.io",
    "repo_id": "R_kgDOVkY93w",
    "category": "Announcements",
    "category_id": "DIC_kwDOVkY9384DKtdl",
}
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
KATEX = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/"


def esc(s):
    return html.escape(s, quote=True)


# ---------- posts ----------

class Post:
    def __init__(self, path):
        text = open(path, encoding="utf-8").read()
        head, body = re.split(r"^---\s*$", text, maxsplit=1, flags=re.M)
        meta = {}
        for line in head.strip().splitlines():
            if line.strip():
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        self.slug = os.path.splitext(os.path.basename(path))[0]
        self.title = meta["title"]
        self.date = meta["date"]
        self.topics = [t.strip() for t in meta.get("topics", "").split(",") if t.strip()]
        for t in self.topics:
            if t not in TOPIC_NAMES:
                raise SystemExit(f"{path}: unknown topic {t!r}")
        self.summary = meta.get("summary", "")
        self.image = meta.get("image", "")
        self.video = meta.get("video", "")
        self.series = meta.get("series", "")
        self.series_order = int(meta.get("series_order", "0") or 0)
        self.thumb_fit = meta.get("thumb_fit", "")
        self.featured = int(meta.get("featured", "0") or 0)
        self.thumb_position = meta.get("thumb_position", "")
        self.thumb_zoom = meta.get("thumb_zoom", "")
        self.math = meta.get("math", "no") == "yes"
        self.home = meta.get("home", "yes") != "no"
        self.body = body.strip()
        parts = [int(p) for p in self.date.split("-")]
        self.y, self.m, self.d = (parts + [None, None])[:3]
        self.sort = (self.y, self.m or 6, self.d or (15 if self.m else 30))

    @property
    def date_text(self):
        if self.d:
            return f"{MONTHS[self.m - 1]} {self.d}, {self.y}"
        if self.m:
            return f"{MONTHS[self.m - 1]} {self.y}"
        return str(self.y)

    @property
    def date_short(self):
        if self.d:
            return f"{MONTHS[self.m - 1][:3]} {self.d}, {self.y}"
        if self.m:
            return f"{MONTHS[self.m - 1][:3]} {self.y}"
        return str(self.y)

    @property
    def iso(self):
        return "-".join(f"{p:02d}" if i else str(p) for i, p in enumerate(x for x in (self.y, self.m, self.d) if x))


def load_posts():
    folder = os.path.join(ROOT, "src", "posts")
    posts = [Post(os.path.join(folder, f)) for f in os.listdir(folder) if f.endswith(".html")]
    return sorted(posts, key=lambda p: p.sort, reverse=True)


# ---------- page shell ----------

def page(title, body, depth, current="", description="", head_extra="", tail="", path="", image="", og_type="website"):
    r = "../" * depth
    nav = [("topics", "Topics", f"{r}topics/index.html"), ("papers", "Papers", f"{r}about/index.html#papers"),
           ("about", "About", f"{r}about/index.html"), ("cv", "CV", f"{r}cv.pdf")]
    cur = ' aria-current="page"'
    links = "\n".join(
        f'          <a href="{href}"{cur if key == current else ""}>{label}</a>'
        for key, label, href in nav)
    full_title = "Justin Valentine" if not title else f"{title} | Justin Valentine"
    description = html.unescape(description)
    desc = f'\n    <meta name="description" content="{esc(description)}">' if description else ""
    og_title = html.unescape(title or "Justin Valentine")
    preview = f"""
    <link rel="canonical" href="{SITE_URL}{path}">
    <meta property="og:site_name" content="Justin Valentine">
    <meta property="og:type" content="{og_type}">
    <meta property="og:title" content="{esc(og_title)}">
    <meta property="og:description" content="{esc(description)}">
    <meta property="og:url" content="{SITE_URL}{path}">
    <meta property="og:image" content="{SITE_URL}{image or DEFAULT_IMAGE}">
    <meta name="twitter:card" content="summary_large_image">"""
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{esc(full_title)}</title>{desc}{preview}
    <link rel="icon" href="{r}favicon.ico" sizes="any">
    <link rel="icon" href="{r}favicon-32.png" sizes="32x32" type="image/png">
    <link rel="apple-touch-icon" href="{r}apple-touch-icon.png">
    <link rel="stylesheet" href="{r}css/style.css">
    <link rel="alternate" type="application/rss+xml" title="Justin Valentine" href="{r}index.xml">{head_extra}
  </head>
  <body>
    <header class="site-header">
      <nav class="site-nav" aria-label="Main navigation">
        <a class="site-title" href="{r}index.html">Justin Valentine</a>
        <div class="nav-links">
{links}
        </div>
      </nav>
    </header>

    <main>
{body}
    </main>

    <footer class="site-footer">
      <p><a href="mailto:{EMAIL}">{EMAIL}</a> &middot; <a href="{GITHUB}">GitHub</a> &middot; <a href="{SCHOLAR}">Google Scholar</a> &middot; <a href="{r}index.xml">RSS</a></p>
    </footer>
{REDUCED_MOTION}{FILE_PREVIEW}{tail}
  </body>
</html>
"""


FILE_PREVIEW = """
    <script>
      // YouTube won't play embeds on a page opened from disk (file://), so there each
      // embed becomes its thumbnail, linking to the video on YouTube.
      if (location.protocol === "file:") {
        document.querySelectorAll('iframe[src*="youtube"]').forEach(function (f) {
          var id = f.src.split("/embed/")[1].split("?")[0];
          var a = document.createElement("a");
          a.href = "https://www.youtube.com/watch?v=" + id; a.target = "_blank"; a.rel = "noopener";
          a.className = "yt-link";
          a.innerHTML = '<img src="https://i.ytimg.com/vi/' + id + '/hqdefault.jpg" alt=""><span>Watch on YouTube</span>';
          f.replaceWith(a);
        });
      }
    </script>"""


REDUCED_MOTION = """    <script>
      // With reduced motion on, hold autoplaying clips on their first frame.
      if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        document.querySelectorAll("video[autoplay]").forEach(function (v) { v.removeAttribute("autoplay"); v.pause(); });
      }
    </script>"""


def topic_links(topics, r):
    return ", ".join(f'<a href="{r}topics/{t}/index.html">{TOPIC_NAMES[t]}</a>' for t in topics)


def thumb_html(p, r, href):
    style = ""
    if p.thumb_position:
        style += f"object-position: {p.thumb_position};"
    if p.thumb_zoom:
        style += f"transform: scale({p.thumb_zoom});"
    style = f' style="{style}"' if style else ""
    cls = "thumb contain" if p.thumb_fit == "contain" else "thumb"
    if p.video:
        return (f'<a class="{cls}" href="{href}" tabindex="-1" aria-hidden="true"><video autoplay muted loop '
                f'playsinline preload="auto"{style}><source src="{r}{p.video}" type="video/mp4"></video></a>')
    if p.image:
        return f'<a class="{cls}" href="{href}" tabindex="-1" aria-hidden="true"><img src="{r}{p.image}" alt="" loading="lazy"{style}></a>'
    return '<span class="thumb empty" aria-hidden="true"></span>'


def entry(p, r):
    """One post in a list: thumbnail (if any), title, date, summary, topics."""
    href = f"{r}posts/{p.slug}/index.html"
    thumb = thumb_html(p, r, href)
    meta = p.date_short + (f" &middot; {topic_links(p.topics, r)}" if p.topics else "")
    summary = f"\n            <p>{p.summary}</p>" if p.summary else ""
    return f"""        <li>
          {thumb}
          <div>
            <h3><a href="{href}">{p.title}</a></h3>
            <p class="entry-meta">{meta}</p>{summary}
          </div>
        </li>"""


def entry_list(posts, r):
    return '      <ul class="work">\n' + "\n".join(entry(p, r) for p in posts) + "\n      </ul>"


# ---------- pages ----------

def build_post(p, posts):
    r = "../../"
    meta = p.date_text + (f" &middot; {topic_links(p.topics, r)}" if p.topics else "")
    series = ""
    if p.series:
        members = sorted([q for q in posts if q.series == p.series], key=lambda q: (q.series_order or 99, q.sort))
        part = members.index(p) + 1
        items = "\n".join(
            f"          <li><strong>{q.title}</strong></li>" if q is p else
            f'          <li><a href="../{q.slug}/index.html">{q.title}</a></li>'
            for q in members)
        series = f"""
        <aside class="series">
          <p><strong>{SERIES[p.series]['title']}</strong>, part {part} of {len(members)}. {SERIES[p.series]['intro']}</p>
          <ol>
{items}
          </ol>
        </aside>"""
    i = posts.index(p)
    newer, older = (posts[i - 1] if i > 0 else None), (posts[i + 1] if i + 1 < len(posts) else None)
    nav = ""
    if newer or older:
        a = f'<a href="../{older.slug}/index.html">&larr; {older.title}</a>' if older else "<span></span>"
        b = f'<a href="../{newer.slug}/index.html">{newer.title} &rarr;</a>' if newer else "<span></span>"
        nav = f'\n        <nav class="post-nav" aria-label="Older and newer posts">{a}{b}</nav>'
    body = f"""      <article class="post">
        <header class="post-header">
          <h1>{p.title}</h1>
          <p class="post-meta">{meta}</p>
        </header>{series}
        <div class="post-content">
{p.body}
        </div>
        <p class="post-contact">Questions or comments? Email me at <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>{nav}{comments_block()}
      </article>"""
    head = ""
    if p.math:
        head = f"""
    <link rel="stylesheet" href="{KATEX}katex.min.css">
    <script defer src="{KATEX}katex.min.js"></script>
    <script defer src="{KATEX}contrib/auto-render.min.js" onload="renderMathInElement(document.body, {{delimiters: [{{left: '\\\\[', right: '\\\\]', display: true}}, {{left: '\\\\(', right: '\\\\)', display: false}}]}})"></script>"""
    out = os.path.join(ROOT, "posts", p.slug)
    os.makedirs(out, exist_ok=True)
    write(os.path.join(out, "index.html"), page(p.title, body, 2, description=re.sub("<[^>]+>", "", p.summary), head_extra=head, path=f"posts/{p.slug}/", image=p.image, og_type="article"))


def comments_block():
    if not GISCUS["category_id"]:
        return ""
    g = GISCUS
    return f"""
        <section class="comments" id="comments">
          <h2>Comments</h2>
          <script src="https://giscus.app/client.js" data-repo="{g['repo']}" data-repo-id="{g['repo_id']}"
            data-category="{g['category']}" data-category-id="{g['category_id']}" data-mapping="pathname" data-strict="1"
            data-reactions-enabled="1" data-emit-metadata="0" data-input-position="top" data-theme="light" data-lang="en"
            data-loading="lazy" crossorigin="anonymous" async></script>
        </section>"""


def featured_row(posts):
    feat = sorted([p for p in posts if p.featured], key=lambda p: p.featured)
    if not feat:
        return ""
    cards = "\n".join(f"""        <li>
          {thumb_html(p, "", f"posts/{p.slug}/index.html")}
          <h3><a href="posts/{p.slug}/index.html">{p.title}</a></h3>
          <p class="entry-meta">{p.date_short}</p>
        </li>""" for p in feat)
    return f"""      <h2>Featured</h2>
      <ul class="featured">
{cards}
      </ul>
"""


def build_home(posts):
    intro = open(os.path.join(ROOT, "src", "home.html"), encoding="utf-8").read().strip()
    counts = {t: sum(t in p.topics for p in posts) for t, _ in TOPICS}
    topics = " &middot; ".join(f'<a href="topics/{t}/index.html">{name}</a>' for t, name in TOPICS if counts[t])
    body = f"""{intro}

      <p class="topic-line">Topics: {topics}</p>

{featured_row(posts)}
      <h2>{"More posts" if any(p.featured for p in posts) else "Recent posts"}</h2>
{entry_list([p for p in posts if p.home and not p.featured], "")}"""
    write(os.path.join(ROOT, "index.html"), page("", body, 0, description="Justin Valentine builds robots and other machines in Edmonton, from the mechanism and machined parts to the electronics, firmware and control code."))


def build_topics(posts):
    sections = []
    for t, name in TOPICS:
        tp = [p for p in posts if t in p.topics]
        if not tp:
            continue
        body = f"""      <p class="crumb"><a href="../index.html">Topics</a></p>
      <h1>{name}</h1>
{entry_list(tp, "../../")}"""
        os.makedirs(os.path.join(ROOT, "topics", t), exist_ok=True)
        write(os.path.join(ROOT, "topics", t, "index.html"), page(name, body, 2, current="topics", description=f"Posts by Justin Valentine about {name.lower()}.", path=f"topics/{t}/"))
        items = "\n".join(f'          <li><a href="../posts/{p.slug}/index.html">{p.title}</a> <span class="year">{p.date_short}</span></li>' for p in tp)
        sections.append(f"""      <section class="topic">
        <h2><a href="{t}/index.html">{name}</a></h2>
        <ul>
{items}
        </ul>
      </section>""")
    body = "      <h1>Topics</h1>\n" + "\n".join(sections)
    write(os.path.join(ROOT, "topics", "index.html"), page("Topics", body, 1, current="topics", description="Posts by Justin Valentine, by topic.", path="topics/"))


def build_archive(posts):
    years = []
    for y in sorted({p.y for p in posts}, reverse=True):
        items = "\n".join(f'        <li><time datetime="{p.iso}">{p.date_short}</time><a href="{p.slug}/index.html">{p.title}</a></li>' for p in posts if p.y == y)
        years.append(f"      <h2>{y}</h2>\n      <ul class=\"dated\">\n{items}\n      </ul>")
    body = "      <h1>All posts</h1>\n" + "\n".join(years)
    write(os.path.join(ROOT, "posts", "index.html"), page("All posts", body, 1, description="Every post on the site, newest first.", path="posts/"))


def build_about():
    body = open(os.path.join(ROOT, "src", "about.html"), encoding="utf-8").read().rstrip()
    write(os.path.join(ROOT, "about", "index.html"), page("About", body, 1, current="about", description="About Justin Valentine, who builds robots and other machines in Edmonton.", path="about/"))


def build_redirect(path, target, label):
    write(os.path.join(ROOT, path, "index.html"), f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Moved | Justin Valentine</title>
    <meta http-equiv="refresh" content="0; url={target}">
    <link rel="canonical" href="{target}">
  </head>
  <body>
    <p>This page moved to <a href="{target}">{label}</a>.</p>
  </body>
</html>
""")


def build_feed(posts):
    items = []
    for p in posts:
        d = datetime.datetime(p.y, p.m or 1, p.d or 1, 12, tzinfo=datetime.timezone.utc)
        link = f"{SITE_URL}posts/{p.slug}/"
        items.append(f"""    <item>
      <title>{esc(p.title)}</title>
      <link>{link}</link>
      <guid>{link}</guid>
      <pubDate>{d.strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
      <description>{esc(re.sub("<[^>]+>", "", p.summary))}</description>
    </item>""")
    write(os.path.join(ROOT, "index.xml"), f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>Justin Valentine</title>
    <link>{SITE_URL}</link>
    <description>Robots and the tools around them, by Justin Valentine.</description>
    <language>en</language>
{chr(10).join(items)}
  </channel>
</rss>
""")


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    posts = load_posts()
    for p in posts:
        build_post(p, posts)
    build_home(posts)
    build_topics(posts)
    build_archive(posts)
    build_about()
    build_feed(posts)
    build_redirect("projects", "../index.html", "the homepage")
    build_redirect("categories", "../topics/index.html", "Topics")
    print(f"Built {len(posts)} posts.")


if __name__ == "__main__":
    main()
