import feedparser
from datetime import datetime, date
import locale

# Nastavení českého formátu dat
locale.setlocale(locale.LC_TIME, 'cs_CZ.UTF-8')

# RSS zdroje
rss_list = [
    ("https://www.mediar.cz/feed/", "#ff6f61"),   # Mediar.cz - červená
    ("https://mam.cz/feed/", "#1db954"),         # MAM.cz - zelená
    ("https://www.mediaguru.cz/rss", "#3b82f6")  # MediaGuru - modrá
]

feeds = []
for url, color in rss_list:
    feed = feedparser.parse(url)
    for entry in feed.entries:
        pub_date = None
        if "published_parsed" in entry and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6])
        elif "updated_parsed" in entry and entry.updated_parsed:
            pub_date = datetime(*entry.updated_parsed[:6])

        feeds.append({
            "title": entry.title,
            "link": entry.link,
            "date": pub_date,
            "source": feed.feed.title,
            "color": color
        })

# Seřadit podle data (novější nahoře)
feeds = sorted(feeds, key=lambda x: x["date"] or datetime.min, reverse=True)

# Funkce na odstín podle stáří
def date_brightness(pub_date):
    if not pub_date:
        return "#999999"
    days_diff = (date.today() - pub_date.date()).days
    if days_diff == 0:
        return "#ffffff"
    elif days_diff == 1:
        return "#cccccc"
    elif days_diff == 2:
        return "#aaaaaa"
    else:
        return "#888888"

# HTML výstup
html = """
<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Marketing & Media RSS</title>
<style>
    body {
        background-color: #121212;
        color: #fff;
        font-family: Arial, Helvetica, sans-serif;
        margin: 0;
        padding: 20px;
    }
    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 30px;
    }
    .card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .card:hover {
        transform: translateY(-5px);
    }
    .title {
        font-family: 'Segoe UI', sans-serif;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 1.1em;
        margin-bottom: 10px;
        text-decoration: none;
    }
    .meta {
        font-family: Georgia, serif;
        font-style: italic;
        font-size: 0.9em;
        margin-top: auto;
    }
    .source {
        font-style: normal;
        font-weight: bold;
    }
</style>
</head>
<body>
<div class="grid">
"""

for item in feeds:
    date_color = date_brightness(item["date"])
    date_str = item["date"].strftime("%-d. %B %Y, %H:%M") if item["date"] else ""
    html += f"""
    <div class="card">
        <a class="title" href="{item['link']}" target="_blank" style="color: {item['color']};">{item['title']}</a>
        <div class="meta">
            <span style="color: {date_color};">{date_str}</span> |
            <span class="source" style="color: #ffcc00;">{item['source']}</span>
        </div>
    </div>
    """

html += """
</div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("HTML stránka byla vygenerována jako index.html")
