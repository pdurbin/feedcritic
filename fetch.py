#!/usr/bin/env python3
"""Download the podcast feeds listed in feeds.txt and write episodes.json.

Usage: python3 fetch.py
"""
import email.utils
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
FEEDS = HERE / "feeds.txt"
CACHE = HERE / "cache"
OUT = HERE / "episodes.json"

ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}"


def strip_html(s):
    s = re.sub(r"<br\s*/?>|</p>", "\n", s or "", flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"Hosted by Simplecast.*?advertising\.", "", s, flags=re.S)
    s = re.sub(r"We love hearing from listeners!.*?Tumblr!", "", s, flags=re.S)
    s = re.sub(r"Learn more about your ad choices\. Visit \S+", "", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def parse_date(s):
    try:
        return email.utils.parsedate_to_datetime(s).date().isoformat()
    except (TypeError, ValueError):
        return ""


def feed_urls():
    if not FEEDS.exists():
        sys.exit("feeds.txt not found: copy feeds.txt.example to feeds.txt and add your feeds")
    for line in FEEDS.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            yield line.split()[-1]


def download(url):
    CACHE.mkdir(exist_ok=True)
    name = re.sub(r"[^A-Za-z0-9]+", "_", url).strip("_") + ".xml"
    path = CACHE / name
    req = urllib.request.Request(url, headers={"User-Agent": "feedcritic/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        path.write_bytes(r.read())
    return path


def parse(path, url):
    channel = ET.parse(path).getroot().find("channel")
    podcast = {
        "title": channel.findtext("title", "").strip(),
        "link": channel.findtext("link", "").strip(),
        "feed": url,
    }
    img = channel.find(f"{ITUNES}image")
    podcast["image"] = img.get("href") if img is not None else ""
    episodes = []
    for item in channel.findall("item"):
        enc = item.find("enclosure")
        desc = item.findtext(f"{CONTENT}encoded") or item.findtext("description") or ""
        episodes.append({
            "id": (item.findtext("guid") or item.findtext("link") or "").strip(),
            "podcast": podcast["title"],
            "title": strip_html(item.findtext("title", "")),
            "date": parse_date(item.findtext("pubDate")),
            "link": (item.findtext("link") or "").strip(),
            "audio": enc.get("url") if enc is not None else "",
            "description": strip_html(desc),
        })
    return podcast, episodes


def main():
    podcasts, episodes = [], []
    for url in feed_urls():
        print("fetching", url, file=sys.stderr)
        p, eps = parse(download(url), url)
        print(f"  {p['title']}: {len(eps)} episodes", file=sys.stderr)
        podcasts.append(p)
        episodes.extend(eps)
    OUT.write_text(json.dumps({"podcasts": podcasts, "episodes": episodes}, indent=1))
    print(f"wrote {OUT.name}: {len(episodes)} episodes", file=sys.stderr)


if __name__ == "__main__":
    main()
