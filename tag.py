#!/usr/bin/env python3
"""Tag episodes in episodes.json with the movies they cover; write data.js.

Recognized episode title patterns, tried in order:
  "123: Movie"      (numbered; also "123: Live Episode: Movie")
  "Guest on Movie"  (optionally prefixed "Flashback - " or "Someone RIP - ") Optional fix-ups live in overrides.json
(copy overrides.json.example to start one).

Usage: python3 tag.py
"""
import json
import re
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = re.compile(r"^(?:Flashback|[^-]*\bRIP)\s+-+\s+", re.I)
NUMBERED = re.compile(r"^(\d+):\s+(?:([\w ]*\bEpisode):\s+)?(.+)$")


def norm(title):
    """Key used to merge different spellings of the same movie."""
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def sort_key(title):
    key = re.sub(r"^(the|a|an) ", "", norm(title)) or title
    return re.sub(r"\d+", lambda m: m.group(0).zfill(6), key)


def parse_title(ep):
    """Return the movie text in an episode title, or None."""
    m = NUMBERED.match(ep["title"])
    if m:
        ep["number"] = m.group(1)
        if m.group(2):
            ep["tag"] = m.group(2)
        return m.group(3).strip()
    t = PREFIX.sub("", ep["title"])
    if " on " in t:
        guest, movie = t.split(" on ", 1)
        ep["guest"] = guest.strip()
        if PREFIX.match(ep["title"]):
            ep["tag"] = PREFIX.match(ep["title"]).group(0).strip(" -")
        return movie.strip()
    return None


def movies_for(ep, ov):
    if ep["title"] in ov["by_title"]:
        return ov["by_title"][ep["title"]]
    movie = parse_title(ep)
    if movie is None:
        return []
    return ov["by_movie"].get(movie, [movie])


def main():
    data = json.loads((HERE / "episodes.json").read_text())
    ov_path = HERE / "overrides.json"  # optional; see overrides.json.example
    ov = json.loads(ov_path.read_text()) if ov_path.exists() else {}
    ov.setdefault("by_movie", {})
    ov.setdefault("by_title", {})
    movies = {}  # norm key -> {"title", "episodes": [ids]}
    untagged = []
    for i, ep in enumerate(data["episodes"]):
        ep["n"] = i
        ep["movies"] = []
        for m in movies_for(ep, ov):
            key = norm(m)
            entry = movies.setdefault(key, {"title": m, "episodes": []})
            entry["episodes"].append(i)
            ep["movies"].append(key)
        if not ep["movies"]:
            untagged.append(ep["title"])
    data["movies"] = movies
    # explicit order: JS objects put integer-like keys ("1917") first
    data["movie_order"] = sorted(movies, key=lambda k: sort_key(movies[k]["title"]))
    (HERE / "data.js").write_text(
        "window.FEEDCRITIC = " + json.dumps(data, ensure_ascii=False) + ";\n")
    print(f"{len(movies)} movies across {len(data['episodes'])} episodes")
    for t in untagged:
        print("  untagged:", t)
    shared = [m for m in movies.values()
              if len({data["episodes"][i]["podcast"] for i in m["episodes"]}) > 1]
    print(f"{len(shared)} movies on more than one podcast:")
    for m in sorted(shared, key=lambda m: sort_key(m["title"])):
        print("  ", m["title"])


if __name__ == "__main__":
    main()
