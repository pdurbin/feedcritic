#!/usr/bin/env python3
"""Tag episodes in episodes.json with the movies they cover; write data.js.

Recognized episode title patterns, tried in order:
  "123: Movie"      (numbered; also "123: Live Episode: Movie")
  "'Movie' With …"  (first quoted title anywhere: 'Movie' Live From …, The Re-'Movie')
  "Guest on Movie"  (optionally prefixed "Flashback - " or "Someone RIP - ")

Podcasts listed under "list_style" in overrides.json are parsed differently:
  "123 - Movie / Movie (w/ Guest)", "Movie + Our Top 10 …", "BONUS - Movie"
The title is split into movies on " / ", " + ", " plus " and commas, and
segments that look like lists or specials ("Our Top 10 …", "Oscars Recap")
are dropped.

Optional fix-ups live in overrides.json (copy overrides.json.example to start one).

Usage: python3 tag.py
"""
import json
import re
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = re.compile(r"^(?:Flashback|[^-]*\bRIP)\s+-+\s+", re.I)
# opening quote at start or after space/hyphen; closing quote followed by space/punct/end
QUOTED = re.compile(r"(?:^|[\s\-])[‘'“\"](.+?)[’'”\"](?=[\s.,(:|]|$)")
NUMBERED = re.compile(r"^(\d+):\s+(?:([\w ]*\bEpisode):\s+)?(.+)$")

# list style
LIST_NUMBER = re.compile(r"^(\d+)\s*-\s*")
LIST_SECTION = re.compile(  # "BONUS - ", "Patron Preview: ", "Spooktober Special II: ", "Magic May (Part I): "
    r"^(?:BONUS|[\w’' ]*?(?:SPECIAL|SPECTACULAR|Special(?: [IVX]+)?|Retrospective|Mass Debate|Patron Preview)"
    r"|[\w ]+\(Part [IVX\d]+\))\s*[-:]\s*")
LIST_PARENS = re.compile(
    r"\s*\((?:w/|AUDIO VERSION|SPOILER|LIVE|The (?:New )?Drunkest|plus )[^)]*(?:\)|$)", re.I)
LIST_SPLIT = re.compile(r"\s+/\s+|\s+\+\s+|\s+plus\s+", re.I)
# split on commas only for real lists: "A, B, and C" or "A, B, C" (not "What's Up, Doc?")
LIST_COMMAS = re.compile(r",\s+(?:and\s+)?")
# whole titles that are never about specific movies
LIST_SKIP = re.compile(r"perfect album|mix-?tape|spooktacular|interview (?:special|with a 3)", re.I)
LIST_JUNK = re.compile(
    r"^(?:our |the |my |billy’s )?(?:all[- ]time |ultimate )?(?:top (?:\d|ten|five)|best |worst |most )"
    r"|oscar|golden globes|mixtape|perfect album|required viewing|what (?:else|have|do) we"
    r"|movie draft|trivia|interview|ranking|recap|wrap[- ]up|the one where|lists of"
    r"|and more|^more\b|cinema releases|random flicks|^\d{4} movie|bumper|re-?watch", re.I)


def parse_list_title(ep):
    """Return the movies in a list-style title (may be empty)."""
    t = ep["title"]
    if LIST_SKIP.search(t):
        return []
    m = LIST_NUMBER.match(t)
    if m:
        ep["number"] = m.group(1)
        t = t[m.end():]
    while m := LIST_SECTION.match(t):  # may be nested: "BONUS - Spooktober Special II: "
        ep["tag"] = m.group(0).strip(" -:")
        t = t[m.end():]
    t = LIST_PARENS.sub("", t)
    segs = []
    for seg in LIST_SPLIT.split(t):
        if seg.count(",") >= 2 or ", and " in seg:
            segs.extend(LIST_COMMAS.split(seg))
        else:
            segs.append(seg)
    movies = []
    for seg in segs:
        if len(segs) > 1 and re.fullmatch(r"\s*\d{4}\s*", seg):  # "Best of 2024 / 2014"
            continue
        seg = re.sub(r"\s*(?:and more|review)\W*$", "", seg.strip(), flags=re.I).strip(" .")
        if seg and not LIST_JUNK.search(seg):
            movies.append(seg)
    return movies


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
    m = QUOTED.search(ep["title"])
    if m:
        return m.group(1).strip()
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
    if ep["podcast"] in ov["list_style"]:
        out = []
        for movie in parse_list_title(ep):
            out.extend(ov["by_movie"].get(movie, [movie]))
        return out
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
    ov.setdefault("list_style", [])
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
