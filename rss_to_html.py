import feedparser

# Seznam RSS adres (můžeš přidat další)
rss_list = [
    "https://www.mediaguru.cz/rss/",
    "https://www.mediar.cz/feed/",
]

html = "<html><head><meta charset='utf-8'><title>Novinky z RSS</title></head><body>"
html += "<h1>Novinky z více zdrojů</h1>"

for rss_url in rss_list:
    feed = feedparser.parse(rss_url)
    html += f"<h2>{feed.feed.title}</h2><ul>"

    for entry in feed.entries:
        title = entry.title
        link = entry.link
        html += f"<li><a href='{link}' target='_blank'>{title}</a></li>"

    html += "</ul>"

html += "</body></html>"

# Uložení výsledku
with open("novinky.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Hotovo! Otevři soubor novinky.html v prohlížeči.")
