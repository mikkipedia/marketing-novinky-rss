import feedparser
from datetime import datetime, date, timedelta
from urllib.parse import urlparse

# ====== NASTAVENÍ ======
FEEDS = {
    "https://www.mediar.cz/feed/": ("mediar.cz", "#facc15"),
    "https://mam.cz/feed/": ("mam.cz", "#ef4444"),
    "https://www.mediaguru.cz/rss": ("mediaguru.cz", "#67e8f9"),
}
OUTPUT_FILE = "index.html"
PAGE_TITLE = "Marketing & Media – novinky"
BUILD_STAMP = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

# ====== POMOCNÉ FUNKCE ======
CZ_MONTHS = [
    "ledna", "února", "března", "dubna", "května", "června",
    "července", "srpna", "září", "října", "listopadu", "prosince",
]

def to_datetime(entry):
    for key in ("published_parsed", "updated_parsed"):
        val = getattr(entry, key, None)
        if val:
            try:
                return datetime(*val[:6])
            except Exception:
                pass
    return None

def format_cz(dt):
    if not dt:
        return ""
    return f"{dt.day}. {CZ_MONTHS[dt.month - 1]} {dt.year}, {dt:%H:%M}"

def date_tone(dt):
    if not dt:
        return "#9ca3af"
    diff = (date.today() - dt.date()).days
    if diff <= 0:
        return "#ffffff"
    if diff == 1:
        return "#d1d5db"
    if diff == 2:
        return "#bfc5cc"
    if diff == 3:
        return "#a1a7ae"
    return "#6b7280"

# ====== SBĚR DAT ======
items = []
source_counts = {name: 0 for name, _ in FEEDS.values()}
cutoff_date = date.today() - timedelta(days=3)

for feed_url, (source_name, source_color) in FEEDS.items():
    feed = feedparser.parse(feed_url)
    source_title = feed.feed.get("title", source_name)
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
            "title_color": "#e5e7eb",
        })
        if dt and dt.date() >= cutoff_date:
            source_counts[source_name] += 1

# Řazení
items.sort(key=lambda x: x["dt"] or datetime.min, reverse=True)

# ====== HTML ======
HTML_HEAD = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{PAGE_TITLE}</title>
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
<meta http-equiv="Pragma" content="no-cache" />
<meta http-equiv="Expires" content="0" />
<style>
  :root {{
    --bg:#0b0d10;
    --card:#14181d;
    --card-border:#1f2730;
    --text:#e5e7eb;
    --muted:#94a3b8;
  }}
  * {{ box-sizing: border-box; }}
  html,body {{
    margin:0;
    padding:0;
    background:var(--bg);
    color:var(--text);
    font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  }}
  .wrap {{
    max-width:1200px;
    margin:0 auto;
    padding:20px;
  }}
  .legend {{
    display:flex;
    gap:16px;
    flex-wrap:wrap;
    margin-bottom:20px;
    font-size:0.9rem;
  }}
  .legend-item {{
    display:flex;
    align-items:center;
    gap:6px;
  }}
  .legend-color {{
    width:14px;
    height:14px;
    border-radius:3px;
    flex-shrink:0;
  }}
  .grid {{
    display:grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap:22px;
  }}
  .card {{
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
  }}
  .card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 10px 22px rgba(0,0,0,.32);
    border-color:#2a3542;
  }}
  .title {{
    text-decoration:none;
    text-transform:uppercase;
    font-weight:800;
    letter-spacing:.02em;
    line-height:1.25;
    font-size:1.02rem;
    color:#e5e7eb;
  }}
  .meta {{
    margin-top:auto;
    font-family: Georgia, 'Times New Roman', serif;
    font-style: italic;
    font-size:.88rem;
    display:flex;
    gap:.4rem;
    flex-wrap:wrap;
  }}
  .dot::before {{
    content:"•";
    opacity:.45;
    margin:0 .35rem;
  }}
</style>
</head>
<body>
<div class="wrap">
  <!-- build: {BUILD_STAMP} -->

  <div class="legend">
"""

# Legend items with counts
legend_html = []
for feed_url, (source_name, source_color) in FEEDS.items():
    count = source_counts[source_name]
    legend_html.append(
        f'<div class="legend-item"><div class="legend-color" style="background:{source_color};"></div>{source_name} ({count})</div>'
    )

HTML_LEGEND = "\n    ".join(legend_html) + "\n  </div>\n  <div class=\"grid\">"

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
      <a class="title" href="{it['link']}" target="_blank" rel="noopener">{it['title']}</a>
      <div class="meta">
        <span style="color:{it['date_color']};">{it['date_text']}</span>
        <span class="dot"></span>
        <span style="color:{it['source_color']};">{it['source']}</span>
      </div>
    </div>""")

html = HTML_HEAD + HTML_LEGEND + "\n".join(cards) + HTML_FOOT

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Vygenerováno: {OUTPUT_FILE} (počet článků: {len(items)})")
