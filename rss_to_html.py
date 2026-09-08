import json
import re
import requests
import feedparser
from datetime import datetime, date, timedelta
from urllib.parse import urlparse, quote

# ====== NASTAVENÍ ======
FEEDS = {
    "https://www.mediar.cz/feed/": ("mediar.cz", "#facc15"),
    "https://www.mam.cz/feed/": ("mam.cz", "#ef4444"),
    "https://www.mediaguru.cz/rss": ("mediaguru.cz", "#67e8f9"),
    "https://cc.cz/feed/": ("czechcrunch.cz", "#4ade80"),  # CzechCrunch – světle zelená
}

# URL stránky s nasazeným HTML – kvůli načtení archivu
ARCHIVE_URL = "https://mikkipedia.github.io/marketing-novinky-rss/"

OUTPUT_FILE = "index.html"
PAGE_TITLE = "Marketing & Media – novinky"
BUILD_STAMP = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

# Hlavičky pro stahování feedů (feedparser sám posílá UA, který některé weby blokují)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.7",
    "Accept-Language": "cs,en;q=0.8",
}

# ====== POMOCNÉ FUNKCE ======
CZ_MONTHS = [
    "ledna", "února", "března", "dubna", "května", "června",
    "července", "srpna", "září", "října", "listopadu", "prosince",
]


SESSION = requests.Session()


def _get(url, referer=None, timeout=25):
    h = dict(HEADERS)
    if referer:
        h["Referer"] = referer
    return SESSION.get(url, headers=h, timeout=timeout, allow_redirects=True)


def _try_direct(url):
    """Přímé stažení se session (cookies z homepage). Jeden pokus, bez retry."""
    base = f"https://{urlparse(url).netloc}/"
    try:
        SESSION.get(base, headers=HEADERS, timeout=20)
    except Exception:
        pass
    try:
        r = _get(url, referer=base)
    except Exception as e:
        print(f"   · primo: chyba – {e}")
        return None
    print(f"   · primo: HTTP {r.status_code}, {len(r.content)} B")
    return r.content if r.status_code == 200 else None


def _try_proxy(label, target):
    try:
        r = _get(target)
    except Exception as e:
        print(f"   · {label}: chyba – {e}")
        return None
    print(f"   · {label}: HTTP {r.status_code}, {len(r.content)} B")
    return r.content if r.status_code == 200 else None


def _try_google_news(domain):
    q = (
        "https://news.google.com/rss/search?q=site:"
        + domain
        + "+when:7d&hl=cs&gl=CZ&ceid=CZ:cs"
    )
    return _try_proxy("google-news", q)


def fetch_feed(url, domain):
    """
    Stáhne feed. Zkusí postupně:
      1) přímo (session + cookies + retry na 429)
      2) codetabs proxy
      3) allorigins proxy
      4) r.jina.ai
      5) Google News RSS (site:domena) – nouzová varianta
    Vrací (parsed_feed, label_zdroje).
    """
    attempts = [
        ("primo", lambda: _try_direct(url)),
        ("codetabs", lambda: _try_proxy(
            "codetabs", "https://api.codetabs.com/v1/proxy/?quest=" + quote(url, safe=""))),
        ("allorigins", lambda: _try_proxy(
            "allorigins", "https://api.allorigins.win/raw?url=" + quote(url, safe=""))),
        ("r.jina.ai", lambda: _try_proxy("r.jina.ai", "https://r.jina.ai/" + url)),
        ("google-news", lambda: _try_google_news(domain)),
    ]
    for label, fn in attempts:
        raw = fn()
        if not raw:
            continue
        parsed = feedparser.parse(raw)
        if getattr(parsed, "entries", []):
            return parsed, label
        print(f"   · {label}: 0 položek po parsování")
    raise RuntimeError("žádná z cest nevrátila použitelný feed")


def to_datetime(entry):
    """Vrátí datetime z published/updated, jinak None."""
    for key in ("published_parsed", "updated_parsed"):
        val = getattr(entry, key, None)
        if val:
            try:
                return datetime(*val[:6])
            except Exception:
                pass
    return None


def format_cz(dt):
    """Datum ve formátu '11. srpna 2025, 08:15'."""
    if not dt:
        return ""
    return f"{dt.day}. {CZ_MONTHS[dt.month - 1]} {dt.year}, {dt:%H:%M}"


def date_tone(dt):
    """Barva datumu podle stáří."""
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
    """Počet hodin od publikace (pro filtr stáří)."""
    if not dt:
        return 10_000
    return int((datetime.utcnow() - dt).total_seconds() // 3600)


def build_item(title, link, dt, source_title, source_slug, source_color):
    """Normovaný záznam článku."""
    return {
        "title": title,
        "link": link,
        "dt": dt,
        "age_h": hours_since(dt),
        "date_text": format_cz(dt),
        "date_color": date_tone(dt),
        "source": source_title,
        "source_slug": source_slug,
        "source_color": source_color,
    }


# ====== ARCHIV V HTML ======
def load_archive():
    """
    Načte archiv z předchozího HTML (script#archive-json) a vrátí list položek build_item().
    Pokud nic nenajde nebo se nepodaří stáhnout, vrací [].
    """
    try:
        resp = requests.get(ARCHIVE_URL, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ Archiv: HTTP {resp.status_code}")
            return []
        m = re.search(
            r'<script id="archive-json"[^>]*>(.*?)</script>',
            resp.text,
            re.DOTALL,
        )
        if not m:
            return []
        raw = m.group(1).strip()
        if not raw:
            return []
        data = json.loads(raw)
        items = []
        for entry in data:
            dt = None
            dt_str = entry.get("dt")
            if dt_str:
                try:
                    dt = datetime.fromisoformat(dt_str)
                except Exception:
                    pass
            if not dt:
                continue
            items.append(
                build_item(
                    entry.get("title", "Bez názvu"),
                    entry.get("link", "#"),
                    dt,
                    entry.get("source", entry.get("source_slug", "Neznámý zdroj")),
                    entry.get("source_slug", "neznamy"),
                    entry.get("source_color", "#94a3b8"),
                )
            )
        print(f"ℹ️ Načteno z archivu: {len(items)} položek")
        return items
    except Exception as e:
        print("⚠️ Nepodařilo se načíst archiv:", e)
        return []


def build_archive_json(items, cutoff_date):
    """
    Vytvoří JSON pro uložení do <script id=archive-json>.
    Drží jen položky, které jsou >= cutoff_date (7 dní historie).
    """
    data = []
    for it in items:
        dt = it.get("dt")
        if not dt or dt.date() < cutoff_date:
            continue
        data.append(
            {
                "title": it["title"],
                "link": it["link"],
                "dt": it["dt"].isoformat(),
                "source": it["source"],
                "source_slug": it["source_slug"],
                "source_color": it["source_color"],
            }
        )
    return json.dumps(data, ensure_ascii=False, indent=2)


# ====== SBĚR DAT (ARCHIV + RSS, POSLEDNÍCH 7 DNŮ) ======
cutoff_date = date.today() - timedelta(days=7)

archive_items = load_archive()

rss_items = []
for feed_url, (source_name, source_color) in FEEDS.items():
    print(f"→ {source_name}")
    try:
        feed, via = fetch_feed(feed_url, source_name)
    except Exception as e:
        print(f"❌ {source_name}: stažení selhalo – {e}")
        continue

    entries = getattr(feed, "entries", [])
    print(f"ℹ️ {source_name}: {len(entries)} položek (zdroj: {via})")
    if not entries:
        continue

    if via == "google-news":
        source_title = source_name
    else:
        source_title = feed.feed.get("title", source_name)

    for entry in entries:
        dt = to_datetime(entry)
        if not dt:
            continue
        title = entry.get("title", "Bez názvu")
        if via == "google-news" and " - " in title:
            title = title.rsplit(" - ", 1)[0]
        rss_items.append(
            build_item(
                title,
                entry.get("link", "#"),
                dt,
                source_title,
                source_name,
                source_color,
            )
        )

# Sloučení archivu a RSS podle linku (unikátní článek podle URL)
merged_by_link = {}

for it in archive_items:
    dt = it.get("dt")
    if dt and dt.date() >= cutoff_date:
        merged_by_link[it["link"]] = it

for it in rss_items:
    dt = it.get("dt")
    if dt and dt.date() >= cutoff_date:
        merged_by_link[it["link"]] = it

items = list(merged_by_link.values())

# Řazení (nejnovější nahoře)
items.sort(key=lambda x: x["dt"] or datetime.min, reverse=True)

# Souhrny
source_counts = {name: 0 for name, _ in FEEDS.values()}
for it in items:
    slug = it["source_slug"]
    if slug not in source_counts:
        source_counts[slug] = 0
    source_counts[slug] += 1

total_count = len(items)
last7_total = len(items)

# ====== HTML ŠABLONA (HEAD) ======
HTML_HEAD_TEMPLATE = """<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>%%TITLE%%</title>
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
<meta http-equiv="Pragma" content="no-cache" />
<meta http-equiv="Expires" content="0" />
<style>
  :root {
    --bg:#0b0d10;
    --card:#14181d;
    --card-border:#1f2730;
    --text:#e5e7eb;
    --muted:#94a3b8;
    --accent:#2a3542;
    --btn-bg:#0f1317;
    --btn-active:#64748b;
  }
  * { box-sizing: border-box; }
  html,body {
    margin:0; padding:0; background:var(--bg); color:var(--text);
    font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  }
  .wrap { max-width:1200px; margin:0 auto; padding:20px; }

  .topbar {
    display:flex; gap:16px; flex-wrap:wrap; align-items:center; justify-content:space-between;
    margin-bottom:10px; color:var(--muted); font-size:.92rem;
  }
  .summary { display:flex; gap:.75rem; flex-wrap:wrap; }
  .controls { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
  select {
    background:var(--btn-bg); color:var(--text); border:1px solid var(--accent);
    border-radius:10px; padding:8px 10px; font-size:.92rem;
  }

  .legend { display:flex; gap:10px; flex-wrap:wrap; margin:.35rem 0 12px; }
  .legend-btn {
    background:var(--btn-bg); color:var(--text); border:1px solid var(--accent);
    border-radius:999px; padding:6px 10px; font-size:.88rem; display:flex; align-items:center; gap:8px;
    cursor:pointer; user-select:none; transition: border-color .15s, transform .12s;
  }
  .legend-btn .dot { width:10px; height:10px; border-radius:999px; display:inline-block; }
  .legend-btn:hover { border-color:#3a4858; transform: translateY(-1px); }
  .legend-btn.active { border-color:var(--btn-active); box-shadow:0 0 0 2px rgba(100,116,139,.25) inset; }

  .bulk {
    display:flex; gap:8px; flex-wrap:wrap; margin-bottom:18px;
  }
  .bulk button {
    background:var(--btn-bg); color:var(--text); border:1px solid var(--accent);
    border-radius:10px; padding:6px 10px; font-size:.88rem; cursor:pointer;
  }
  .bulk button:hover { border-color:#3a4858; }

  .grid {
    display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap:22px;
  }
  .card {
    background:var(--card); border:1px solid var(--card-border); border-radius:14px;
    padding:18px 16px; min-height:160px; display:flex; flex-direction:column; gap:10px;
    box-shadow: 0 6px 16px rgba(0,0,0,.25);
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
  }
  .card:hover { transform: translateY(-4px); box-shadow: 0 10px 22px rgba(0,0,0,.32); border-color:#2a3542; }
  .title {
    text-decoration:none; text-transform:uppercase; font-weight:800; letter-spacing:.02em; line-height:1.25;
    font-size:1.02rem; color:#e5e7eb;
  }
  .meta {
    margin-top:auto; font-family: Georgia, 'Times New Roman', serif; font-style: italic; font-size:.88rem;
    display:flex; gap:.4rem; flex-wrap:wrap;
  }
  .dotsep::before { content:"•"; opacity:.45; margin:0 .35rem; }

  .hidden { display:none !important; }
</style>
</head>
<body>
<div class="wrap">
  <!-- build: %%BUILD%% -->

  <div class="topbar">
    <div class="summary">
      <span>Celkem: %%TOTAL%% článků</span>
      <span>·</span>
      <span>Posledních 7 dní: %%LAST7%%</span>
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

HTML_HEAD = (
    HTML_HEAD_TEMPLATE.replace("%%TITLE%%", PAGE_TITLE)
    .replace("%%BUILD%%", BUILD_STAMP)
    .replace("%%TOTAL%%", str(total_count))
    .replace("%%LAST7%%", str(last7_total))
)

# ====== LEGENDA (TLAČÍTKA) ======
legend_parts = []
for feed_url, (source_name, source_color) in FEEDS.items():
    count = source_counts.get(source_name, 0)
    legend_parts.append(
        f'<button class="legend-btn active" type="button" data-source="{source_name}">'
        f'<span class="dot" style="background:{source_color};"></span>{source_name} ({count})'
        f"</button>"
    )

HTML_LEGEND = "\n    ".join(legend_parts)

# ====== OTEVŘENÍ BULK OVLÁDÁNÍ A GRIDU ======
BULK_AND_GRID_OPEN = """
  </div>

  <div class="bulk">
    <button id="selectAll" type="button">Vybrat vše</button>
    <button id="clearAll" type="button">Zrušit vše</button>
  </div>

  <div class="grid">
"""

# ====== KARTY ======
card_parts = []
for it in items:
    card_parts.append(
        f"""
    <div class="card" data-source="{it['source_slug']}" data-ageh="{it['age_h']}">
      <a class="title" href="{it['link']}" target="_blank" rel="noopener">{it['title']}</a>
      <div class="meta">
        <span style="color:{it['date_color']};">{it['date_text']}</span>
        <span class="dotsep"></span>
        <span style="color:{it['source_color']};">{it['source']}</span>
      </div>
    </div>"""
    )

CARDS_HTML = "\n".join(card_parts)

# ====== ARCHIV JSON BLOK ======
archive_json = build_archive_json(items, cutoff_date)
ARCHIVE_SCRIPT = f"""
<script id="archive-json" type="application/json">
{archive_json}
</script>
"""

# ====== FOOTER S JS ======
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
      if (matchSource && matchAge) {
        card.classList.remove('hidden');
      } else {
        card.classList.add('hidden');
      }
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

# ====== SLOŽENÍ CELÉHO HTML ======
html = HTML_HEAD + HTML_LEGEND + BULK_AND_GRID_OPEN + CARDS_HTML + ARCHIVE_SCRIPT + HTML_FOOT

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Vygenerováno: {OUTPUT_FILE} (počet článků: {len(items)})")
