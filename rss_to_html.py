import feedparser
from datetime import datetime

# Seznam RSS zdrojů (oddělené čárkou)
rss_list = [
    "https://www.mediar.cz/feed/",
    "https://mam.cz/feed/",
    "https://www.mediaguru.cz/rss/"
]

# Načtení dat
articles = []
for rss_url in rss_list:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries:
        published = ""
        if hasattr(entry, "published"):
            try:
                published = datetime(*entry.published_parsed[:6]).strftime("%d.%m.%Y")
            except:
                published = ""
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": getattr(entry, "summary", ""),
            "source": feed.feed.title,
            "published": published
        })

# Seřadit podle data (pokud je k dispozici)
articles.sort(key=lambda x: x["published"], reverse=True)

# HTML výstup s designem
html_content = """<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Marketing Novinky RSS</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
  <style>
    body {
      font-family: 'Inter', sans-serif;
      background-color: #f9fafb;
      color: #1f2937;
      margin: 0;
      padding: 2rem;
    }
    h1 {
      text-align: center;
      font-size: 2rem;
      margin-bottom: 2rem;
    }
    .container {
      max-width: 900px;
      margin: 0 auto;
      display: grid;
      gap: 1.5rem;
    }
    .card {
      background: white;
      padding: 1.5rem;
      border-radius: 0.75rem;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover {
      transform: translateY(-4px);
      box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
    }
    .card a {
      text-decoration: none;
      color: #2563eb;
      font-weight: 600;
    }
    .card p {
      margin: 0.5rem 0 0;
      color: #4b5563;
    }
    .meta {
      font-size: 0.85rem;
      color: #6b7280;
      margin-bottom: 0.5rem;
    }
  </style>
</head>
<body>
  <h1>Marketing Novinky RSS</h1>
  <div class="container">
"""

# Přidání článků
for article in articles:
    html_content += f"""
    <div class="card">
      <div class="meta">{article["source"]} • {article["published"]}</div>
      <a href="{article["link"]}" target="_blank">{article["title"]}</a>
      <p>{article["summary"][:150]}...</p>
    </div>
    """

# Uzavření HTML
html_content += """
  </div>
</body>
</html>
"""

# Uložení souboru
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
