import feedparser
from datetime import datetime, date
from urllib.parse import urlparse

# ====== NASTAVENÍ ======
# RSS zdroje (URL -> barva nadpisu)
FEEDS = {
    "https://www.mediar.cz/feed/": "#ef4444",     # červená
    "https://mam.cz/feed/": "#22c55e",            # zelená
    "https://www.mediaguru.cz/rss": "#3b82f6",    # modrá
}
OUTPUT_FILE = "index.html"
PAGE_TITLE = "Marketing & Media – novinky"

# ====== POMOCNÉ FUNKCE ======
CZ_MONTHS = [
    "ledna", "února", "března", "dubna", "května", "června",
    "července", "srpna", "září", "října", "listopadu", "prosince",
]

def to_datetime(entry):
    """Zkus published, pak updated; vrať datetime nebo None."""
    for key in ("published_parsed", "updated_parsed"):
        val = getattr(entry, key, None)
        if val:
            return datetime(*val[:6])
    return None

def format_cz(dt: datetime | None) -> str:
    """Vrať '11. srpna 2025, 08:15' (bez závislosti na OS locale)."""
    if not dt:
        return ""
    d = dt.day
    m = CZ_MONTHS[dt.month - 1]
    return f"{d}. {m} {dt.year}, {dt:%H:%M}"

def date_tone(dt: datetime | None) -> str:
    """Barva datumu podle stáří: dnešní nejjasnější, starší tmavší (na dark pozadí)."""
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

def title_color_for(source_title: str, feed_url: str) -> str:
    """Vyber barvu nadpisu podle známého feedu; fallback podle domény."""
    for url, color in FEEDS.items():
        if url in feed_url:
            return color
    host = urlparse(feed_url).hostname or ""
    # fallback barvy podle domény, ať je to stabilní
    palette = ["#ea]()
