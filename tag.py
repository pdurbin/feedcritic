#!/usr/bin/env python3
"""Tag episodes in episodes.json with the movies they cover; write data.js.

Recognized episode title patterns, tried in order:
  "123: Movie"      (numbered; also "123: Live Episode: Movie")
  "'Movie' With …"  (first quoted title anywhere: 'Movie' Live From …, The Re-'Movie')
  "Guest on Movie"  (optionally prefixed "Flashback - " or "Someone RIP - ")

Podcasts listed under "list_style" in overrides.json are parsed differently.
Their titles are just movie names, possibly several, with extras around them:
  "123 - Movie / Movie (w/ Guest)", "Movie + Our Top 10 …", "BONUS - Movie",
  "Movie, Part 1 of 2", "Movie: Bonus Episode!", "#028: Movie / Movie (Pt. 2)",
  "Theme, Pt. 1 — Movie", "Episode 557: Movie (Patreon Pick by …)",
  "315 - Movie (1991) PT 2 | Subtitle"
The title is split into movies on " / ", " + ", " plus " and commas, and
segments that look like lists or specials ("Our Top 10 …", "Oscars Recap")
are dropped.

Years: "Movie (1984)" and "Movie (2016)" are different movies. A title without
a year joins "Movie (YYYY)" when that episode's description mentions YYYY near
the title. If
only one year is known for the title, it also joins when the episode came out
after that year, its description names no other year, and the year didn't come
from overrides.json (overrides add years to tell remakes from originals).

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
QUOTED = re.compile(r"(?:^|[\s\-])[‘'“\"](.+?)[’'”\"](?=[\s.,(:|]|$)(\s*\(\d{4}\))?")
NUMBERED = re.compile(r"^(\d+):\s+(?:([\w ]*\bEpisode):\s+)?(.+)$")
YEAR = re.compile(r"\s*\((\d{4})\)$")

# list style
LIST_NUMBER = re.compile(  # "123 - ", "07b – ", "#028: ", "Episode 557: ", "Episode 500!!! - "
    r"^(?:Episode\s+(\d+)[!:]*\s*-?\s*|#(\d+):\s*|(\d+[ab]?)\s*[-–—]\s*)", re.I)
LIST_LEAD = re.compile(r"^(?:[^\w(#{'\"‘“]+|\((?:Pt|Part)\.?\s*\d+\)\s*)")  # emoji, "(Pt. 1) "
LIST_SECTION = re.compile(  # "BONUS - ", "Patron Preview: ", "Spooktober Special II: ", "Magic May (Part I): "
    r"^(?:\{?BONUS\}?(?: Episode)?|Patreon Pour[- ]?Up|The Worst and Forgotten|Side[- ]?Eye Side ?Quest"
    r"|[\w’' ]*?(?:Special(?: [IVX]+)?|SPECTACULAR|Retrospective|Mass Debate|Patron Preview)"
    r"|[\w ]+\(Part [IVX\d]+\))\s*[-–—:]\s*", re.I)
LIST_PARENS = re.compile(
    r"\s*\((?:w/|AUDIO VERSION|SPOILER|LIVE|The (?:New )?Drunkest|plus |Patre?on|[^)]*Bonus Episode)[^)]*(?:\)|$)",
    re.I)
# "Theme, Pt. 1 — Movie", "Theme Pt. 2: Movie", "Theme, Pt 1 - Movie"
LIST_THEME = re.compile(r"^.*?\bPt[ .,]*\d+\.?\s*[-–—:]\s*", re.I)
# guest credits and picks: "Movie w/ Guest", "Movie with guests …", "Movie - Patreon Pick from …"
LIST_GUEST = re.compile(
    r"\s*(?:[-–]\s*)?(?:\(\s*)?(?:Pat(?:re|er)on (?:pick|pour)|picked by|w/|with guests?\b|frm\b).*$"
    r"|\s*with\s+\S.*\b(?:from|of)\b.*$|\s+aka\s.*$", re.I)
LIST_SPLIT = re.compile(r"\s+/\s+|\s+\+\s+|\s+plus\s+", re.I)
# split on commas only for real lists: "A, B, and C" or "A, B, C" (not "What's Up, Doc?")
LIST_COMMAS = re.compile(r",\s+(?:and\s+)?")
# whole titles that are never about specific movies
LIST_SKIP = re.compile(
    r"perfect album|mix-?tape|spooktacular|interview (?:special|with a 3)|bachelorette|behind the reel"
    r"|tier list|cinematic showdown|behind the scenes|how we graded|announcement|interruption in service"
    r"|state of streaming|introducing |let's talk about|live at the|^short:|if we picked"
    r"|podcasting 101|post show|preshow|pregame|clip show|round ?table|#podcast|comicpalooza x", re.I)
LIST_JUNK = re.compile(
    r"^(?:our |the |my |billy’s )?(?:all[- ]time |ultimate )?(?:top (?:\d|ten|five)"
    r"|(?:best|worst|favou?rite) (?:\d+ |five |ten )?(?:films|movies|of\b)|most (?:anticipated|underrated))"
    r"|oscar|golden globes|mixtape|perfect album|required viewing|what (?:else|have|do) we"
    r"|movie draft|trivia|interview|ranking|recap|wrap[- ]up|the one where|lists of|top 10s"
    r"|and more|^more\b|cinema releases|random flicks|^\d{4} movie|bumper|re-?watch|\bpromo\b"
    r"|retrospective|year in review|\bintro\b|missing movies|side.?eye|top films", re.I)
# trailing extras: "Fargo, Part 2", "No Country for Old Men, Part 1 of 2", "A Serious Man: Bonus Episode!",
# "Barton Fink (Pt. 2)", "Tombstone PT1"
_PART = r"(?:Part|Pt\.?)\s*(?:\d+|[IVX]+|One|Two|Three)(?: of \d+)?"
LIST_EXTRA = re.compile(
    r"(?:,\s*" + _PART + r"|\s*\(" + _PART + r"\)|\s+(?-i:PT)\.?\s*\d*|:\s*Bonus Episode!?)$", re.I)


def parse_list_title(ep):
    """Return the movies in a list-style title (may be empty)."""
    t = ep["title"]
    if LIST_SKIP.search(t):
        return []
    m = LIST_NUMBER.match(t)
    if m:
        ep["number"] = next(g for g in m.groups() if g)
        t = t[m.end():]
    t = LIST_LEAD.sub("", t)
    while m := LIST_SECTION.match(t):  # may be nested: "BONUS - Spooktober Special II: "
        ep["tag"] = m.group(0).strip(" -–—:")
        t = t[m.end():]
        t = LIST_LEAD.sub("", t)
    t = t.split(" | ")[0]               # "Movie (1991) PT 2 | Subtitle"
    t = LIST_PARENS.sub("", t)
    # drop anything after a year unless another movie follows: "Congo (1995) PT 1 - Spoiler-Free Review"
    t = re.sub(r"(\(\d{4}\))(?!\s*(?:/|\+|,|and\b)).*$", r"\1", t)
    t = LIST_THEME.sub("", t)
    if " — " in t:                      # "What's In a Name — The Last Picture Show"
        t = t.rsplit(" — ", 1)[1]
    segs = []
    for seg in re.split(r"(?<=\(\d{4}\))\s+and\s+|" + LIST_SPLIT.pattern, t, flags=re.I):
        if seg.count(",") >= 2 or ", and " in seg:
            segs.extend(LIST_COMMAS.split(seg))
        else:
            segs.append(seg)
    movies = []
    for seg in segs:
        if len(segs) > 1 and re.fullmatch(r"\s*\d{4}\s*", seg):  # "Best of 2024 / 2014"
            continue
        seg = LIST_GUEST.sub("", seg.strip())
        seg = re.sub(r"(?:\s*\((?!\d{4}\))[^()]*(?:\)|$))+$", "", seg)   # "(Picked by …)", "(Revisited)"
        seg = re.sub(r"\s*\)+$", "", seg) if seg.count(")") > seg.count("(") else seg
        seg = re.sub(r"\s+PT\.?\s*\d+(?=\s*\(\d{4}\)$)", "", seg, flags=re.I)  # "Movie PT1 (2023)"
        q = re.search(r"[\"“](.+?)[\"”]$", seg)                         # Steve McQueen's "Widows"
        if q:
            seg = q.group(1)
        seg = re.sub(r"\s*(?:and more|review)\W*$", "", seg, flags=re.I).strip(" .")
        seg = LIST_EXTRA.sub("", seg).strip(" -–")
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


def split_year(title):
    """"Halloween (1978)" -> ("Halloween", 1978); "Halloween" -> ("Halloween", None)."""
    m = YEAR.search(title)
    return (title[:m.start()].strip(), int(m.group(1))) if m else (title, None)


def years_near(title, text, window=80):
    """Years (1800–2099) within `window` characters of a mention of `title` in `text`."""
    t, x = norm(title), norm(text)
    found = set()
    if not t:
        return found
    for m in re.finditer(r"\b" + re.escape(t) + r"\b", x):
        near = x[max(0, m.start() - window):m.end() + window]
        found |= {int(y) for y in re.findall(r"\b(1[89]\d\d|20\d\d)\b", near)}
    return found


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
        return (m.group(1).strip() + (m.group(2) or "")).strip()
    t = PREFIX.sub("", ep["title"])
    if " on " in t:
        guest, movie = t.split(" on ", 1)
        ep["guest"] = guest.strip()
        if PREFIX.match(ep["title"]):
            ep["tag"] = PREFIX.match(ep["title"]).group(0).strip(" -")
        return movie.strip()
    return None


def movies_for(ep, ov):
    """Return [(movie title, came from overrides?)]."""
    if ep["title"] in ov["by_title"]:
        return [(m, True) for m in ov["by_title"][ep["title"]]]
    parsed = parse_list_title(ep) if ep["podcast"] in ov["list_style"] else [parse_title(ep)]
    out = []
    for movie in parsed:
        if movie is None:
            continue
        if movie in ov["by_movie"]:
            out.extend((m, True) for m in ov["by_movie"][movie])
        else:
            out.append((movie, False))
    return out


def main():
    data = json.loads((HERE / "episodes.json").read_text())
    ov_path = HERE / "overrides.json"  # optional; see overrides.json.example
    ov = json.loads(ov_path.read_text()) if ov_path.exists() else {}
    ov.setdefault("by_movie", {})
    ov.setdefault("by_title", {})
    ov.setdefault("list_style", [])

    # pass 1: raw movie titles per episode, and the explicit years seen for each title
    raw = []          # (episode index, base title, year or None)
    years = {}        # norm(base) -> set of years
    parsed_years = {} # norm(base) -> years that came from titles, not overrides
    for i, ep in enumerate(data["episodes"]):
        ep["n"] = i
        for m, from_ov in movies_for(ep, ov):
            base, year = split_year(m)
            raw.append((i, base, year))
            if year:
                years.setdefault(norm(base), set()).add(year)
                if not from_ov:
                    parsed_years.setdefault(norm(base), set()).add(year)
    explicit = {}     # episode index -> keys it names with a year
    for i, base, year in raw:
        if year:
            explicit.setdefault(i, set()).add(f"{norm(base)} {year}")

    # pass 2: decide which year a title without one belongs to (see docstring)
    movies = {}  # key -> {"title", "episodes": [ids]}
    for ep in data["episodes"]:
        ep["movies"] = []
    for i, base, year in raw:
        ep = data["episodes"][i]
        b = norm(base)
        if year is None and b in years:
            mentioned = years_near(base, ep["description"])
            ep_year = int(ep["date"][:4]) if ep["date"] else 9999
            mentioned = {y for y in mentioned if y <= ep_year and str(y) not in base}  # "1917"
            cands = years[b] & mentioned
            if len(cands) == 1:
                year = cands.pop()
            elif not cands and len(years[b]) == 1 and parsed_years.get(b) == years[b]:
                y = next(iter(years[b]))
                if y <= ep_year and not (mentioned - {y}):
                    year = y
            if year and f"{b} {year}" in explicit.get(i, ()):  # episode names both versions
                year = None
        key = f"{b} {year}" if year else b
        title = f"{base} ({year})" if year else base
        entry = movies.setdefault(key, {"title": title, "episodes": []})
        if year and not YEAR.search(entry["title"]):  # prefer "Suspiria (2018)" over "Suspiria 2018"
            entry["title"] = title
        if i not in entry["episodes"]:
            entry["episodes"].append(i)
            ep["movies"].append(key)

    untagged = [ep["title"] for ep in data["episodes"] if not ep["movies"]]
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
