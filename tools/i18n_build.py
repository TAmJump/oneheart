#!/usr/bin/env python3
"""Build /i18n/<page>.json from ordered translation lists.

Usage:
    python3 tools/i18n_build.py keys <page>            # print the numbered key list
    python3 tools/i18n_build.py make <page> <ja.txt> <ko.txt>

The translation files carry one line per key, in the same order as `keys`
prints them. An empty line means "leave this string as it is".
Multi-line source strings are collapsed to single spaces on both sides,
so every key is one line.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = {
    "index": "index.html",
    "verify": "verify/index.html",
    "holders": "holders/index.html",
    "join": "join/index.html",
    "participate": "participate/index.html",
    "portrait": "portrait/index.html",
    "terms": "terms.html",
    "ceo": "ceo.html",
}

SKIP = {"script", "style"}
VOID = {"img", "input", "br", "hr", "link", "meta", "source", "col", "area"}
ATTRS = ("placeholder", "title", "alt", "aria-label")


class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.text = []
        self.attrs = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        for k in ATTRS:
            if d.get(k):
                self.attrs.append(d[k])
        if tag == "meta" and d.get("name") == "description" and d.get("content"):
            self.attrs.append(d["content"])
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass

    def handle_data(self, data):
        if any(t in SKIP for t in self.stack):
            return
        s = " ".join(data.split())
        if s and not re.fullmatch(r"[\s\W\d]+", s):
            self.text.append(s)


def keys_for(page):
    path = os.path.join(ROOT, PAGES[page])
    src = open(path, encoding="utf-8").read()
    p = Extract()
    p.feed(src)
    out = []
    for s in p.text + p.attrs:
        if s not in out:
            out.append(s)
    return out


def read_lines(path, n, label):
    raw = open(path, encoding="utf-8").read().split("\n")
    while raw and raw[-1] == "":
        raw.pop()
    if len(raw) > n:
        sys.exit("%s has %d lines, expected %d" % (label, len(raw), n))
    while len(raw) < n:
        raw.append("")
    return raw


def main():
    if len(sys.argv) < 3 or sys.argv[2] not in PAGES:
        sys.exit(__doc__)
    cmd, page = sys.argv[1], sys.argv[2]
    ks = keys_for(page)

    if cmd == "keys":
        for i, k in enumerate(ks, 1):
            print("%3d|%s" % (i, k))
        print("total %d" % len(ks), file=sys.stderr)
        return

    if cmd == "make":
        ja = read_lines(sys.argv[3], len(ks), "ja")
        ko = read_lines(sys.argv[4], len(ks), "ko")
        out = {"ja": {}, "ko": {}}
        for k, j, o in zip(ks, ja, ko):
            if j.strip():
                out["ja"][k] = j.strip()
            if o.strip():
                out["ko"][k] = o.strip()
        d = os.path.join(ROOT, "i18n")
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, page + ".json")
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=False)
            fh.write("\n")
        print("%s  ja %d / ko %d of %d keys" % (f, len(out["ja"]), len(out["ko"]), len(ks)))
        return

    sys.exit(__doc__)


if __name__ == "__main__":
    main()
