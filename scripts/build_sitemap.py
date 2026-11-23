"""Flatten the checked-in sitemap index for the production Pages artifact."""

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
S = f"{{{NS}}}"
ORIGIN = "https://twbronycon.org"


def build_sitemap(source: Path, target: Path) -> None:
    index = ET.parse(source).getroot()
    if index.tag != S + "sitemapindex":
        raise ValueError(f"{source} is not a sitemap index")

    ET.register_namespace("", NS)
    result = ET.Element(S + "urlset")
    seen = set()
    for location in index.findall(f"{S}sitemap/{S}loc"):
        sitemap = location.text or ""
        parts = urlsplit(sitemap)
        if (
            f"{parts.scheme}://{parts.netloc}" != ORIGIN
            or parts.query
            or parts.fragment
            or not parts.path.endswith("/sitemap.xml")
            or parts.path == "/sitemap.xml"
        ):
            raise ValueError(f"Unexpected child sitemap: {sitemap}")

        response = subprocess.check_output(
            ["curl", "--fail", "--silent", "--show-error", "--max-time", "15", sitemap],
        )
        child = ET.fromstring(response)
        entries = child.findall(S + "url")
        if child.tag != S + "urlset" or not entries:
            raise ValueError(f"Missing page URLs in {sitemap}")

        prefix = ORIGIN + parts.path.removesuffix("sitemap.xml")
        for entry in entries:
            url = entry.findtext(S + "loc", default="")
            if not url.startswith(prefix) or url in seen:
                raise ValueError(f"Unexpected or duplicate page URL: {url}")
            seen.add(url)
            result.append(entry)

    if not seen:
        raise ValueError("No page URLs found")
    ET.indent(result)
    ET.ElementTree(result).write(target, encoding="utf-8", xml_declaration=True)
    print(f"Wrote {len(seen)} page URLs to {target}")


if __name__ == "__main__":
    build_sitemap(Path(sys.argv[1]), Path(sys.argv[2]))
