#!/usr/bin/env python3
"""
Update data/progress.json from the live Kickstarter project page.

Reads the backer count of every reward, maps each reward to one of the 23
artworks, and writes the result to data/progress.json.

Mapping rules
  "BECOME A PIECE OF ONE HEART - <TITLE>"  -> +backers to that artwork
  "FOUNDING HOLDER" (24 places)            -> +backers to artworks 1-22,
                                              +2 x backers to artwork 23
  add-on / extra place rewards             -> counted in "unassigned"
                                              (the artwork is chosen later)

Usage
  python scripts/update_progress.py                  # fetch and write
  python scripts/update_progress.py --dry-run        # fetch and print only
  python scripts/update_progress.py --html FILE      # parse a saved page
"""

import argparse
import datetime
import html
import json
import os
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "progress.json"

PROJECT_URL = os.environ.get(
    "KS_PROJECT_URL",
    "https://www.kickstarter.com/projects/tamj/we-are-all-one-heart-23-pieces-one-world",
).rstrip("/")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

TITLES = [
    "ONE EARTH", "DIFFERENT", "WHO AM I?", "WONDER", "DREAMER", "MY VOICE",
    "LOVE INSIDE", "FACE TO FACE", "CONNECTED", "LIFELINE", "HEART KING",
    "KING OF ME", "BURNING SOUL", "COURAGE", "FADING AWAY", "ETERNAL",
    "TWO MINDS", "THE UNKNOWN", "HOPE STAR", "ANGEL WITHIN", "DEVIL WITHIN",
    "THE EYE", "ONE HEART",
]
TOTALS = {i: (5000 if i == 23 else 2500) for i in range(1, 24)}


def norm(s):
    s = html.unescape(s or "")
    s = re.sub(r"[\u2010-\u2015\u2212]", "-", s)   # dashes to hyphen
    s = re.sub(r"[^A-Z0-9?\- ]", " ", s.upper())
    return re.sub(r"\s+", " ", s).strip()


def artwork_of(title):
    """Return artwork number for a reward title, "founding", or None.

    Every reward title contains the words ONE HEART, so the artwork name is
    read from the part after the separator, never from the whole string.
    """
    t = norm(title)
    if "FOUNDING" in t:
        return "founding"
    if "ADD-ON" in t or "ADD ON" in t or "EXTRA PLACE" in t:
        return None

    tail = re.split(r"\s+-\s+", t)[-1].strip()
    names = sorted(enumerate(TITLES, 1), key=lambda p: -len(p[1]))
    for i, name in names:
        if norm(name) == tail:
            return i
    for i, name in names:
        if norm(name) in tail:
            return i
    return None


# ---------------------------------------------------------------- extraction

def _walk(node, found):
    """Collect any list that looks like a reward list."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("rewards", "items") and isinstance(v, list):
                for r in v:
                    if isinstance(r, dict) and "title" in r and (
                        "backers_count" in r or "backersCount" in r
                    ):
                        found.append(r)
            _walk(v, found)
    elif isinstance(node, list):
        for v in node:
            _walk(v, found)


def from_embedded_json(page):
    """Strategy A: reward data embedded in a data-* attribute."""
    out = []
    for m in re.finditer(r'data-(?:initial|project|react-props|rewards)="([^"]{200,})"', page):
        try:
            blob = json.loads(html.unescape(m.group(1)))
        except Exception:
            continue
        _walk(blob, out)
    for m in re.finditer(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', page, re.S):
        try:
            blob = json.loads(m.group(1))
        except Exception:
            continue
        _walk(blob, out)

    rewards = {}
    for r in out:
        title = r.get("title") or ""
        n = r.get("backers_count", r.get("backersCount"))
        if title and isinstance(n, int):
            rewards[title] = max(n, rewards.get(title, 0))
    return rewards


def from_markup(page):
    """Strategy B: server-rendered reward cards."""
    rewards = {}
    blocks = re.split(r'(?=<(?:li|div)[^>]*(?:class="[^"]*pledge|data-reward-id))', page)
    for b in blocks:
        tm = (re.search(r'BECOME A PIECE OF ONE HEART[^<]{0,80}|FOUNDING HOLDER[^<]{0,60}', b)
              or re.search(r'<h[1-4][^>]*>\s*([^<]{3,120}?)\s*</h[1-4]>', b))
        nm = re.search(r'([\d,]+)\s*(?:backers?|支援者)', b)
        if tm and nm:
            title = (tm.group(1) if tm.re.groups else tm.group(0)).strip()
            n = int(nm.group(1).replace(",", ""))
            rewards[title] = max(n, rewards.get(title, 0))
    return rewards


def fetch_rewards():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    pages = []
    for url in (PROJECT_URL + "/rewards", PROJECT_URL):
        try:
            r = s.get(url, timeout=30)
            if r.status_code == 200:
                pages.append(r.text)
        except requests.RequestException as e:
            print("fetch failed: %s (%s)" % (url, e), file=sys.stderr)
    if not pages:
        raise SystemExit("could not fetch the project page")
    return pages


def parse(pages):
    for page in pages:
        for fn in (from_embedded_json, from_markup):
            rewards = fn(page)
            if rewards:
                print("parsed %d rewards via %s" % (len(rewards), fn.__name__))
                return rewards
    raise SystemExit("no reward data found - Kickstarter markup has changed")


# ------------------------------------------------------------------- mapping

def tally(rewards):
    taken = {i: 0 for i in range(1, 24)}
    unassigned = 0
    for title, n in rewards.items():
        key = artwork_of(title)
        if key == "founding":
            for i in range(1, 23):
                taken[i] += n
            taken[23] += n * 2
        elif key is None:
            unassigned += n
        else:
            taken[key] += n
    return taken, unassigned


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--html", help="parse a saved HTML file instead of fetching")
    args = ap.parse_args()

    pages = [Path(args.html).read_text()] if args.html else fetch_rewards()
    rewards = parse(pages)
    taken, unassigned = tally(rewards)

    jst = datetime.timezone(datetime.timedelta(hours=9))
    doc = {
        "updated": datetime.datetime.now(jst).strftime("%Y-%m-%d"),
        "source": "kickstarter",
        "unassigned": unassigned,
        "artworks": {
            str(i): {"taken": min(taken[i], TOTALS[i]), "total": TOTALS[i]}
            for i in range(1, 24)
        },
    }

    print("total taken: %d  unassigned: %d" % (sum(taken.values()), unassigned))
    if args.dry_run:
        print(json.dumps(doc, indent=2))
        return

    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
