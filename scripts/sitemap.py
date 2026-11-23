"""Write the production sitemap from the assembled Nuxt pages."""

import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


class PageHead(HTMLParser):
    canonical = None
    noindex = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonical = attrs.get("href")
        if tag == "meta" and attrs.get("name", "").lower() in {"robots", "googlebot"}:
            directives = attrs.get("content", "").lower().replace(",", " ").split()
            self.noindex |= bool({"noindex", "none"}.intersection(directives))


output = Path(sys.argv[1])
urls = set()
for year in sorted(output.iterdir()):
    if not year.is_dir() or len(year.name) != 4 or not year.name.isdecimal():
        continue
    prefix = f"/{year.name}"
    for html in year.rglob("index.html"):
        head = PageHead()
        head.feed(html.read_text(encoding="utf-8").split("</head>", 1)[0])
        if not head.canonical or head.noindex:
            continue
        url = urlsplit(head.canonical)
        if (
            url.scheme == "https"
            and url.netloc == "twbronycon.org"
            and (url.path == prefix or url.path.startswith(f"{prefix}/"))
            and not url.query
            and not url.fragment
        ):
            urls.add(head.canonical)

if not urls:
    raise SystemExit("No canonical event pages found for the sitemap")

root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
for url in sorted(urls):
    ET.SubElement(ET.SubElement(root, "url"), "loc").text = url
ET.indent(root)
ET.ElementTree(root).write(output / "sitemap.xml", encoding="utf-8", xml_declaration=True)
