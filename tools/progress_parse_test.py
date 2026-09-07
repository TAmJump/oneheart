#!/usr/bin/env python3
"""Offline check of the Kickstarter reward parser and the artwork mapping.

The container cannot reach kickstarter.com, so this builds pages in both of the
shapes update_progress.py knows how to read and asserts that every reward lands
on the right artwork. It does not prove the live page still has these shapes -
only that the mapping is sound once the rewards are found.

  python3 tools/progress_parse_test.py
"""

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import update_progress as up  # noqa: E402


def reward_titles():
    """The 23 artwork rewards, the founding tier and the add-on."""
    out = ["BECOME A PIECE OF ONE HEART - %s" % t for t in up.TITLES]
    out.append("FOUNDING HOLDER - ALL 24 PLACES")
    out.append("ADDITIONAL PIECE - ADD-ON")
    return out


def as_embedded_json(counts):
    rewards = [{"title": t, "backers_count": n} for t, n in counts.items()]
    blob = {"project": {"rewards": rewards}}
    attr = html.escape(json.dumps(blob), quote=True)
    return ('<html><body><div data-project="%s"></div>'
            '<script type="application/json">%s</script></body></html>'
            % (attr, json.dumps(blob)))


def as_markup(counts):
    parts = ['<html><body>']
    for t, n in counts.items():
        parts.append(
            '<li class="pledge-card" data-reward-id="1">'
            '<h3>%s</h3><span>%s backers</span></li>' % (html.escape(t), n))
    parts.append('</body></html>')
    return "".join(parts)


def check(name, page, counts):
    rewards = up.parse([page])
    if rewards != counts:
        missing = set(counts) - set(rewards)
        extra = set(rewards) - set(counts)
        sys.exit("%s: rewards do not round-trip\n  missing %s\n  extra %s"
                 % (name, sorted(missing), sorted(extra)))

    mapping, matched, loose = up.classify(rewards)
    gaps = [i for i in range(1, 24) if i not in matched]
    if gaps:
        sys.exit("%s: no reward matched artwork(s) %s" % (name, gaps))

    for i, title in enumerate(up.TITLES, 1):
        key = "BECOME A PIECE OF ONE HEART - %s" % title
        if mapping[key] != i:
            sys.exit("%s: %r mapped to %r, expected %d" % (name, key, mapping[key], i))
    if mapping["FOUNDING HOLDER - ALL 24 PLACES"] != "founding":
        sys.exit("%s: the founding tier was not recognised" % name)
    if mapping["ADDITIONAL PIECE - ADD-ON"] is not None:
        sys.exit("%s: the add-on should stay unassigned" % name)
    if loose != ["ADDITIONAL PIECE - ADD-ON"]:
        sys.exit("%s: unexpected unassigned rewards %s" % (name, loose))

    taken, unassigned = up.tally(rewards)
    print("  %-14s %d rewards, %d places, %d unassigned"
          % (name, len(rewards), sum(taken.values()), unassigned))
    return taken, unassigned


def main():
    titles = reward_titles()

    print("all rewards at zero, as on launch day")
    zero = {t: 0 for t in titles}
    for name, page in (("embedded json", as_embedded_json(zero)), ("markup", as_markup(zero))):
        taken, un = check(name, page, zero)
        assert sum(taken.values()) == 0 and un == 0

    print("\nrewards with backers")
    counts = {t: i + 1 for i, t in enumerate(titles)}
    counts["FOUNDING HOLDER - ALL 24 PLACES"] = 10
    counts["ADDITIONAL PIECE - ADD-ON"] = 7
    for name, page in (("embedded json", as_embedded_json(counts)),
                       ("markup", as_markup(counts))):
        taken, un = check(name, page, counts)
        # artwork 1 gets its own backers plus one per founding holder
        assert taken[1] == 1 + 10, taken[1]
        # artwork 23 gets its own backers plus two per founding holder
        assert taken[23] == 23 + 20, taken[23]
        assert un == 7

    print("\ntitle shapes that should still map")
    variants = {
        "BECOME A PIECE OF ONE HEART \u2014 TWO MINDS": 17,   # em dash
        "Become a piece of One Heart - The Eye": 22,          # sentence case
        "BECOME A PIECE OF ONE HEART &ndash; HOPE STAR": 19,  # html entity
        "FOUNDING HOLDER": "founding",
        "ADD-ON: ONE MORE PLACE": None,
        "EXTRA PLACE": None,
    }
    for title, want in variants.items():
        got = up.artwork_of(title)
        flag = "ok " if got == want else "BAD"
        print("  %s %-52s -> %r" % (flag, title, got))
        if got != want:
            sys.exit("mapping changed for %r" % title)

    print("\nthe guard fires when an artwork has no reward")
    short = {t: 0 for t in titles if "ETERNAL" not in t}
    rewards = up.parse([as_embedded_json(short)])
    _, matched, _ = up.classify(rewards)
    if 16 in matched:
        sys.exit("artwork 16 should not have matched")
    print("  ok  artwork 16 ETERNAL reported as missing")

    print("\nall checks passed")


if __name__ == "__main__":
    main()
