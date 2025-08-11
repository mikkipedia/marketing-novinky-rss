import feedparser
from datetime import datetime, date
from urllib.parse import urlparse

FEEDS = {
    "https://www.mediar.cz/feed/": "#ef4444",
    "https://mam.cz/feed/": "#22c55e",
    "https://www.mediaguru.cz/rss": "#3b82f6",
}
OUTPUT_FILE = "index.html"
PAGE_TITLE = "Marketing & Media – novinky"
BUILD_STAMP = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

CZ_MONTHS = [
    "ledna","února","března","dubna","května","června",
    "července","srpna","září","října","listopadu","prosince",
]

def to_datetime(entry):
    for key in ("published_parsed","updated_parsed"):
        val = getattr(entry, key, None)
        if val:
            try: return datetime(*val[:6])
            except: pass
    return None

def format_cz(dt):
    if not dt: return ""
    return f"{dt.day}. {CZ_MONTHS[dt.month-1]} {dt.year}, {dt:%H:%M}"

def date_tone(dt):
    if not dt: return "#9ca3af"
    diff = (date.today() - dt.date()).days
    return "#ffffff" if diff<=0 else "#d1d5db" if diff==1 else "#bfc5cc" if diff==2 else "#a1a7ae" if diff==3 else "#6b7280"

def title_color_for(feed_url):
    for url, color in FEEDS.items():
        if url in feed_url:
            return color
    host = urlparse(feed_url).hostname or ""
    palette = ["#eab308","#22c55e","#3b82f6","#a855f7","#f97316","#ef4444"]
    return palette[hash(host) % len(palette)]

items = []
for feed_url in FEEDS.keys():
    feed = feedparser.parse(feed_url)
    source_title = feed.feed.get("title", urlparse(feed_url).hostname or "Neznámý zdroj")
    for entry in getattr(feed, "entries", []):
        dt = to_datetime(entry)
        items.append({
            "title": entry.get("title","Bez názvu"),
            "link": entry.get("link","#"),
            "dt": dt,
            "date_text": format_cz(dt),
            "date_color": date_tone(dt),
            "source": source_title,
            "source_color": "#facc15",
            "title_color": title_color_for(feed_url),
        })

items.sort(key=lambda x: x["dt"] or datetime.min, reverse=True)

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
  :root {{ --bg:#0b0d10; --card:#14181d; --card-border:#1f2730; --text:#e5e7eb; --muted:#94a3b8; --source:#facc15; }}
  * {{ box-sizing: border-box; }}
  html,body {{ margin:0; padding:0; background:var(--bg); color:var(--text); font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }}
  .wrap {{ max-width:1200px; margin:0 auto; padding:20px; }}
  .grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:22px; }}
  .card {{ background:var(--card); border:1px solid var(--card-border); border-radius:14px; padding:18px 16px; min-height:160px;
          display:flex; flex-direction:column; gap:10px; box-shadow:0 6px 16px rgba(0,0,0,.25); transition: transform .18s, box-shadow .18s, border-color .18s; }}
  .card:hover {{ transform: translateY(-4px); box-shadow:0 10px 22px rgba(0,0,0,.32); border-color:#2a3542; }}
  .title {{ text-decoration:none; text-transform:uppercase; font-weight:800; letter-spacing:.02em; line-height:1.25; font-size:1.02rem; }}
  .meta {{ margin-top:auto; font-family: Georgia, 'Times New Roman', serif; font-style: italic; font-size:.88rem; display:flex; gap:.4rem; flex-wrap:wrap; }}
  .dot::before {{ content:"•"; opacity:.45; margin:0 .35rem; }}
</style>
</head>
<body>
<div class="wrap">
  <!-- build: {BUILD_STAMP} -->
  <div class="grid">
"""

HTML_FOOT = """
  </div>
</div>
</body>
</html>
"""

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

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(HTML_HEAD + "\n".join(cards) + HTML_FOOT)

print(f"✅ Vygenerováno: {OUTPUT_FILE} (počet článků: {len(items)})")
