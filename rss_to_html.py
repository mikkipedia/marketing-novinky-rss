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

def hours_since(dt):
    if not dt:
        return 10_000
    return int((datetime.utcnow() - dt).total_seconds() // 3600)

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
            "age_h": hours_since(dt),
            "date_text": format_cz(dt),
            "date_color": date_tone(dt),
            "source": source_title,
            "source_slug": source_name,
            "source_color": source_color,
        })
        if dt and dt.date() >= cutoff_date:
            source_counts[source_name] += 1

# Řazení (nejnovější nahoře)
items.sort(key=lambda x: x["dt"] or datetime.min, reverse=True)

# Souhrny
total_count = len(items)
last3_total = sum(source_counts.values())

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
    --accent:#2a3542;
    --btn-bg:#0f1317;
    --btn-active:#64748b;
  }}
  * {{ box-sizing: border-box; }}
  html,body {{
    margin:0; padding:0; background:var(--bg); color:var(--text);
    font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  }}
  .wrap {{ max-width:1200px; margin:0 auto; padding:20px; }}

  .topbar {{
    display:flex; gap:16px; flex-wrap:wrap; align-items:center; justify-content:space-between;
    margin-bottom:10px; color:var(--muted); font-size:.92rem;
  }}
  .summary {{ display:flex; gap:.75rem; flex-wrap:wrap; }}
  .controls {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; }}
  select {{
    background:var(--btn-bg); color:var(--text); border:1px solid var(--accent);
    border-radius:10px; padding:8px 10px; font-size:.92rem;
  }}

  .legend {{ display:flex; gap:10px; flex-wrap:wrap; margin:.35rem 0 12px; }}
  .legend-btn {{
    background:var(--btn-bg); color:var(--text); border:1px solid var(--accent);
    border-radius:999px; padding:6px 10px; font-size:.88rem; display:flex; align-items:center; gap:8px;
    cursor:pointer; user-select:none; transition: border-color .15s, transform .12s;
  }}
  .legend-btn .dot {{ width:10px; height:10px; border-radius:999px; display:inline-block; }}
  .legend-btn:hover {{ border-color:#3a4858; transform: translateY(-1px); }}
  .legend-btn.active {{ border-color:var(--btn-active); box-shadow:0 0 0 2px rgba(100,116,139,.25) inset; }}

  .bulk {{
    display:flex; gap:8px; flex-wrap:wrap; margin-bottom:18px;
  }}
  .bulk button {{
    background:var(--btn-bg); color:var(--text); border:1px solid var(--accent);
    border-radius:10px; padding:6px 10px; font-size:.88rem; cursor:pointer;
  }}
  .bulk button:hover {{ border-color:#3a4858; }}

  .grid {{
    display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap:22px;
  }}
  .card {{
    background:var(--card); border:1px solid var(--card-border); border-radius:14px;
    padding:18px 16px; min-height:160px; display:flex; flex-direction:column; gap:10px;
    box-shadow: 0 6px 16px rgba(0,0,0,.25);
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
  }}
  .card:hover {{ transform: translateY(-4px); box-shadow: 0 10px 22px rgba(0,0,0,.32); border-color:#2a3542; }}
  .title {{
    text-decoration:none; text-transform:uppercase; font-weight:800; letter-spacing:.02em; line-height:1.25;
    font-size:1.02rem; color:#e5e7eb;
  }}
  .meta {{
    margin-top:auto; font-family: Georgia, 'Times New Roman', serif; font-style: italic; font-size:.88rem;
    display:flex; gap:.4rem; flex-wrap:wrap;
  }}
  .dotsep::before {{ content:"•"; opacity:.45; margin:0 .35rem; }}

  .hidden {{ display:none !important; }}
</style>
</head>
<body>
<div class="wrap">
  <!-- build: {BUILD_STAMP} -->

  <div class="topbar">
    <div class="summary">
      <span>Celkem: {total_count} článků</span>
      <span>·</span>
      <span>Poslední 3 dny: {last3_total}</span>
    </div>

    <div class="controls">
      <label for="ageFilter">Zobrazit:</label>
      <select id="ageFilter" aria-label="Filtr dle stáří">
        <option value="all" selected>Vše</option>
        <option value="24">Posledních 24 h</option>
        <option value="72">Poslední 3 dny</option>
        <option value="168">Poslední týden</option>
      </select>
    </div>
  </div>

  <div class="legend" role="group" aria-label="Filtr podle zdroje">
"""

# Legenda (tlačítka)
legend_html = []
for feed_url, (source_name, source_color) in FEEDS.items():
    legend_html.append(
        f'<button class="legend-btn active" type="button" data-source="{source_name}">'
        f'<span class="dot" style="background:{source_color};"></span>{source_name}'
        f'</button>'
    )
HTML_LEGEND = "\n    ".join(legend_html) + """
  </div>

  <div class="bulk">
    <button id="selectAll" type="button">Vybrat vše</button>
    <button id="clearAll" type="button">Zrušit vše</button>
  </div>

  <div class="grid">
"""

HTML_FOOT = """
  </div>
</div>

<script>
(function() {
  const cards = Array.from(document.querySelectorAll('.card'));
  const legendButtons = Array.from(document.querySelectorAll('.legend-btn'));
  const ageFilter = document.getElementById('ageFilter');
  const btnSelectAll = document.getElementById('selectAll');
  const btnClearAll = document.getElementById('clearAll');

  function getActiveSources() {
    const active = legendButtons.filter(b => b.classList.contains('active')).map(b => b.dataset.source);
    return active.length ? active : legendButtons.map(b => b.dataset.source);
  }

  function getAgeLimitHours() {
    const val = ageFilter.value;
    if (val === 'all') return Infinity;
    const n = parseInt(val, 10);
    return isNaN(n) ? Infinity : n;
  }

  function applyFilter() {
    const activeSources = new Set(getActiveSources());
    const limitH = getAgeLimitHours();

    cards.forEach(card => {
      const src = card.dataset.source;
      const ageH = parseInt(card.dataset.ageh, 10) || 999999;
      const matchSource = activeSources.has(src);
      const matchAge = ageH <= limitH;
      if (matchSource && matchAge) {{
        card.classList.remove('hidden');
      }} else {{
        card.classList.add('hidden');
      }}
    });
  }

  legendButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      btn.classList.toggle('active');
      applyFilter();
    });
  });

  btnSelectAll.addEventListener('click', () => {
    legendButtons.forEach(b => b.classList.add('active'));
    applyFilter();
  });

  btnClearAll.addEventListener('click', () => {
    legendButtons.forEach(b => b.classList.remove('active'));
    applyFilter();
  });

  ageFilter.addEventListener('change', applyFilter);

  // inicializace
  applyFilter();
})();
</script>

</body>
</html>
"""

# ====== GENEROVÁNÍ KARET ======
cards = []
for it in items:
    cards.append(f"""
    <div class="card" data-source="{it['source_slug']}" data-ageh="{it['age_h']}">
      <a class="title" href="{it['link']}" target="_blank" rel="noopener">{it['title']}</a>
      <div class="meta">
        <span style="color:{it['date_color']};">{it['date_text']}</span>
        <span class="dotsep"></span>
        <span style="color:{it['source_color']};">{it['source']}</span>
      </div>
    </div>""")

html = HTML_HEAD + HTML_LEGEND + "\n".join(cards) + HTML_FOOT

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Vygenerováno: {OUTPUT_FILE} (počet článků: {len(items)})")
