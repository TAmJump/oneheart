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
  python scripts/update_progress.py --check          # print the mapping, write nothing
  python scripts/update_progress.py --html FILE      # parse a saved page

The mapping is checked before anything is written. Kickstarter carries one
reward per artwork, so all 23 have to be matched by a reward title; if any is
missing the reward names have moved and the run stops without writing, rather
than publishing a number that is quietly wrong. --force writes anyway.
"""

import argparse
import datetime
import html
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "progress.json"

# The workflow passes KS_PROJECT_URL through even when the repository variable
# is not set, which arrives as an empty string rather than as a missing key -
# so fall back on anything falsy, not just on the key being absent.
PROJECT_URL = (os.environ.get("KS_PROJECT_URL") or
               "https://www.kickstarter.com/projects/tamj/"
               "we-are-all-one-heart-23-pieces-one-world").strip().rstrip("/")
if not PROJECT_URL.startswith("http"):
    raise SystemExit("KS_PROJECT_URL is not a URL: %r" % PROJECT_URL)

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


def _why(resp):
    """A short, readable line from a non-200 body.

    Kickstarter's block pages carry the reason in the text - a rate limit
    notice, a captcha, a Cloudflare interstitial. Print enough of it to tell
    those apart without dumping the whole page into the log.
    """
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", resp.text[:4000])
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return text[:300] or "(empty body)"


def fetch_rewards():
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                  "image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    })

    # Land on the home page first. A session that arrives straight at a project
    # page with no cookies looks like a scraper and is refused more often.
    try:
        home = s.get("https://www.kickstarter.com/", timeout=30)
        print("GET / -> %d, %d cookies" % (home.status_code, len(s.cookies)),
              file=sys.stderr)
    except requests.RequestException as e:
        print("GET / failed (%s)" % e, file=sys.stderr)

    pages = []
    for url in (PROJECT_URL + "/rewards", PROJECT_URL):
        for attempt in (1, 2, 3):
            try:
                r = s.get(url, timeout=30,
                          headers={"Referer": "https://www.kickstarter.com/",
                                   "Sec-Fetch-Site": "same-origin"})
            except requests.RequestException as e:
                print("fetch failed: %s (%s)" % (url, e), file=sys.stderr)
                break

            print("GET %s -> %d, %d bytes" % (url, r.status_code, len(r.content)),
                  file=sys.stderr)
            if r.status_code == 200:
                pages.append(r.text)
                break

            print("  %s" % _why(r), file=sys.stderr)
            # A hard block does not clear on the second try, so 403 gets one
            # retry only; a rate limit or a hiccup is worth waiting out.
            limit = 2 if r.status_code == 403 else 3
            if r.status_code in (403, 429, 500, 502, 503) and attempt < limit:
                wait = 8 * attempt
                print("  retrying in %ds" % wait, file=sys.stderr)
                time.sleep(wait)
                continue
            break

    if not pages:
        raise SystemExit(
            "could not fetch the project page - see the status codes above. "
            "If Kickstarter is refusing this network, save the /rewards page "
            "in a browser and run again with --html FILE.")
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

def classify(rewards):
    """Return (mapping, matched artwork numbers, titles that matched nothing)."""
    mapping, matched, loose = {}, set(), []
    for title in sorted(rewards):
        key = artwork_of(title)
        mapping[title] = key
        if isinstance(key, int):
            matched.add(key)
        elif key is None:
            loose.append(title)
    return mapping, matched, loose


def report(rewards):
    mapping, matched, loose = classify(rewards)
    width = max((len(t) for t in mapping), default=10)
    for title in sorted(mapping):
        key = mapping[title]
        if key == "founding":
            where = "FOUNDING HOLDER -> every artwork"
        elif key is None:
            where = "unassigned"
        else:
            where = "%02d %s" % (key, TITLES[key - 1])
        print("  %-*s  %6d backers  ->  %s" % (width, title, rewards[title], where))
    missing = [i for i in range(1, 24) if i not in matched]
    if missing:
        print("\nno reward title matched: " + ", ".join(
            "%02d %s" % (i, TITLES[i - 1]) for i in missing), file=sys.stderr)
    if loose:
        print("\ncounted as unassigned: " + ", ".join(loose), file=sys.stderr)
    return missing


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
    ap.add_argument("--check", action="store_true",
                    help="print how every reward title maps, and write nothing")
    ap.add_argument("--force", action="store_true",
                    help="write even when some artworks have no matching reward")
    ap.add_argument("--html", help="parse a saved HTML file instead of fetching")
    args = ap.parse_args()

    pages = [Path(args.html).read_text()] if args.html else fetch_rewards()
    rewards = parse(pages)

    missing = report(rewards)
    if args.check:
        return 1 if missing else 0
    if missing and not args.force:
        print("\nstopping without writing: %d of 23 artworks have no reward title. "
              "Check the reward names on Kickstarter, then run again."
              % len(missing), file=sys.stderr)
        return 1

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

    try:
        was = json.loads(OUT.read_text())
        before = sum(a["taken"] for a in was["artworks"].values())
        if sum(taken.values()) < before:
            print("note: the total went down, %d -> %d. Cancelled pledges do this, "
                  "so it is written as it stands." % (before, sum(taken.values())),
                  file=sys.stderr)
    except Exception:
        pass

    if args.dry_run:
        print(json.dumps(doc, indent=2))
        return 0

    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print("wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
