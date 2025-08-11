import feedparser
from datetime import datetime

# RSS zdroje
rss_list = [
    "https://www.mediar.cz/feed/",
    "https://mam.cz/feed/",
    "https://www.mediaguru.cz/rss"
]

feeds = []
for url in rss_list:
    feed = feedparser.parse(url)
    for entry in feed.entries:
        feeds.append({
            "title": entry.title,
            "link": entry.link,
            "date": entry.published if "published" in entry else "",
            "source": feed.feed.title
        })

# Seřadit podle data (novější nahoře)
feeds.sort(key=lambda x: x["date"], reverse=True)

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
        gap: 20px;
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
        color: #ffffff;
        text-decoration: none;
    }
    .title:hover {
        color: #1db954;
    }
    .meta {
        font-family: Georgia, serif;
        font-style: italic;
        color: #bbbbbb;
        font-size: 0.9em;
        margin-top: auto;
    }
</style>
</head>
<body>
<div class="grid">
"""

for item in feeds:
    html += f"""
    <div class="card">
        <a class="title" href="{item['link']}" target="_blank">{item['title']}</a>
        <div class="meta">{item['date']} | {item['source']}</div>
    </div>
    """

html += """
</div>
</body>
</html>
"""

# Uložení souboru
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("HTML stránka byla vygenerována jako index.html")
