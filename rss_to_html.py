import feedparser
from datetime import datetime, date
from urllib.parse import urlparse

# ====== NASTAVENÍ ======
# RSS zdroje: URL -> barva nadpisu (můžeš upravit hex kódy)
FEEDS = {
    "https://www.mediar.cz/feed/": "#ef4444",     # Mediar - červená
    "https://mam.cz/feed/": "#22c55e",            # MAM - zelená
    "https://www.mediaguru.cz/rss": "#3b82f6",    # MediaGuru - modrá
}
OUTPUT_FILE = "index.html"
PAGE_TITLE = "Marketing & Media – novinky"

# ====== POMOCNÉ FUNKCE ======
CZ_MONTHS = [
    "ledna", "února", "března", "dubna", "května", "června",
    "července", "srpna", "září", "října", "listopadu", "prosince",
]

def to_datetime(entry):
    """Vrať datetime z published/updated, jinak None."""
    for key in ("published_parsed", "updated_parsed"):
        val = getattr(entry, key, None)
        if val:
            try:
                return datetime(*val[:6])
            except Exception:
                pass
    return None

def format_cz(dt):
    """Formát: '11. srpna 2025, 08:15' bez OS locale."""
    if not dt:
        return ""
    return f"{dt.day}. {CZ_MONTHS[dt.month - 1]} {dt.year}, {dt:%H:%M}"

def date_tone(dt):
    """Barva datumu podle stáří (na dark pozadí)."""
    if not dt:
        return "#9ca3af"
    diff = (date.today() - dt.date()).days
    if diff <= 0:
        return "#ffffff"   # dnes
    if diff == 1:
        return "#d1d5db"
    if diff == 2:
        return "#bfc5cc"
    if diff == 3:
        return "#a1a7ae"
    return "#6b7280"       # 4+ dnů

def title_color_for(feed_url):
    """Barva nadpisu podle známého feedu; fallback podle domény."""
    for url, color in FEEDS.items():
        if url in feed_url:
            return color
    host = urlparse(feed_url).hostname or ""
    palette = ["#eab308", "#22c55e", "#3b82f6", "#a855f7", "#f97316", "#ef4444"]
    return palette[hash(host) % len(palette)]

# ====== SBĚR DAT ======
items = []
for feed_url in FEEDS.keys():
    feed = feedparser.parse(feed_url)
    source_title = feed.feed.get("title", urlparse(feed_url).hostname or "Neznámý zdroj")
    source_color = "#facc15"  # žlutá pro zdroj (lze změnit)
    tcolor = title_color_for(feed_url)

    for entry in getattr(feed, "entries", []):
        dt = to_datetime(entry)
        items.append({
            "title": entry.get("title", "Bez názvu"),
            "link": entry.get("link", "#"),
            "dt": dt,
            "date_text": format_cz(dt),
            "date_color": date_tone(dt),
            "source": source_title,
            "source_color": source_color,
            "title_color": tcolor,
        })

# Řazení (nejnovější nahoře)
items.sort(key=lambda x: x["dt"] or datetime.min, reverse=True)

# ====== HTML (HEAD + STYL) ======
HTML_HEAD = """<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>%%TITLE%%</title>
<style>
  :root {
    --bg:#0b0d10;         /* hlavní pozadí */
    --card:#14181d;       /* dlaždice */
    --card-border:#1f2730;/* rámeček karet */
    --text:#e5e7eb;       /* primární text */
    --muted:#94a3b8;      /* popisky */
    --source:#facc15;     /* žlutá pro zdroj */
  }
  * { box-sizing: border-box; }
  html,body { margin:0; padding:0; background:var(--bg); color:var(--text);
              font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
  .wrap { max-width:1200px; margin:0 auto; padding:20px; }

  /* responzivní mřížka */
  .grid {
    display:grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap:22px; /* výrazné oddělení vertikálně i horizontálně */
  }

  .card {
    background:var(--card);
    border:1px solid var(--card-border);
    border-radius:14px;
    padding:18px 16px;
    min-height:160px;
    display:flex;
    flex-direction:column;
    gap:10px;
    box-shadow: 0 6px 16px rgba(0,0,0,.25);
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
  }
  .card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 22px rgba(0,0,0,.32);
    border-color:#2a3542;
  }

  /* nadpis článku */
  .title {
    text-decoration:none;
    text-transform:uppercase;
    font-weight:800;
    letter-spacing:.02em;
    line-height:1.25;
    font-size:1.02rem;
  }

  /* meta: datum + zdroj (patkové, kurzíva) */
  .meta {
    margin-top:auto;
    font-family: "Georgia", "Times New Roman", serif;
    font-style: italic;
    font-size:.88rem;
    display:flex;
    gap:.4rem;
    flex-wrap:wrap;
  }
  .dot::before { content:"•"; opacity:.45; margin:0 .35rem; }

  /* přístupnost: focus */
  .title:focus-visible { outline:2px dashed currentColor; outline-offset:3px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="grid">
""".replace("%%TITLE%%", PAGE_TITLE)

HTML_FOOT = """
  </div>
</div>
</body>
</html>
"""

# ====== GENEROVÁNÍ KARET ======
cards = []
for it in items:
    cards.append(f"""
    <div class="card">
      <a class="title" href="{it['link']}" target="_blank" rel="noopener" style="color:{it['title_color']};">{it['title']}</a>
      <div class="meta">
        <span style="color:{it['date_color']};">{it['date_text']}</span>
        <span class="dot"></span>
        <span style="color:{it['source_color']};">{it['source']}</span>
      </div>
    </div>""")

html = HTML_HEAD + "\n".join(cards) + HTML_FOOT

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Vygenerováno: {OUTPUT_FILE} (počet článků: {len(items)})")
