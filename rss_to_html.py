import feedparser
import locale
from datetime import datetime

# Nastavení českého locale (pokud nefunguje, nastaví fallback)
try:
    locale.setlocale(locale.LC_TIME, 'cs_CZ.UTF-8')
except locale.Error:
    print("⚠️ Locale cs_CZ.UTF-8 není dostupné, používám výchozí.")
    locale.setlocale(locale.LC_TIME, '')

# URL RSS kanálu
RSS_URL = "https://www.example.com/rss.xml"

# Stažení a parsování feedu
feed = feedparser.parse(RSS_URL)

# CSS styl
CSS = """
<style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: auto; padding: 20px; background: #fdfdfd; }
    h1 { text-align: center; color: #333; }
    .article { border-bottom: 1px solid #ddd; padding: 10px 0; }
    h2 { margin-bottom: 5px; }
    a { color: #1a73e8; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .date { color: #888; font-size: 0.9em; }
</style>
"""

# Vytvoření HTML obsahu
html_content = f"""<html>
<head>
<meta charset="UTF-8">
<title>{feed.feed.get('title', 'RSS Feed')}</title>
{CSS}
</head>
<body>
<h1>{feed.feed.get('title', 'RSS Feed')}</h1>
"""

for entry in feed.entries:
    date_str = ""
    if "published_parsed" in entry and entry.published_parsed:
        date_str = datetime(*entry.published_parsed[:6]).strftime("%d. %B %Y")

    html_content += f"""
    <div class="article">
        <h2><a href="{entry.link}">{entry.title}</a></h2>
        <div class="date">{date_str}</div>
        <p>{entry.get('summary', '')}</p>
    </div>
    """

html_content += "</body></html>"

# Uložení do souboru
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ HTML soubor vygenerován: index.html")
