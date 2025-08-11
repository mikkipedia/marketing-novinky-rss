import feedparser
from datetime import datetime

# URL RSS feedu
RSS_URL = "https://www.mujweb.cz/rss.xml"

# Výstupní HTML soubor
OUTPUT_FILE = "index.html"

# Načtení RSS
feed = feedparser.parse(RSS_URL)

# Začátek HTML
html_content = """
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSS Feed</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 0;
        }
        header {
            background: linear-gradient(90deg, #4e73df, #1cc88a);
            color: white;
            padding: 20px;
            text-align: center;
        }
        main {
            padding: 20px;
            max-width: 900px;
            margin: auto;
        }
        article {
            background: white;
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h2 {
            color: #333;
            margin-top: 0;
        }
        a {
            text-decoration: none;
            color: #4e73df;
        }
        a:hover {
            text-decoration: underline;
        }
        .date {
            font-size: 0.9em;
            color: #888;
        }
    </style>
</head>
<body>
    <header>
        <h1>RSS Feed</h1>
    </header>
    <main>
"""

# Přidání položek z RSS
for entry in feed.entries:
    title = entry.title
    link = entry.link
    published = entry.get("published", "")
    if published:
        try:
            published = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
            published = published.strftime("%d.%m.%Y %H:%M")
        except:
            pass

    summary = entry.get("summary", "")

    html_content += f"""
        <article>
            <h2><a href="{link}" target="_blank">{title}</a></h2>
            <div class="date">{published}</div>
            <p>{summary}</p>
        </article>
    """

# Konec HTML
html_content += """
    </main>
</body>
</html>
"""

# Uložení souboru
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML stránka byla vygenerována do {OUTPUT_FILE}")
