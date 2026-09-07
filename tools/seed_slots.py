#!/usr/bin/env python3
"""Seed oneheart-slots with the Kickstarter result, once.

From 9 October the DynamoDB counter is what decides whether a place is still
free. Before that the places sold on Kickstarter exist only on Kickstarter, so
they have to be carried over by hand exactly once: this script sets `taken` on
each artwork to the number of places already sold, which holds pieces 1..N for
the backers and starts the site's own numbering after them.

Input is a JSON file of counts, artwork number to places sold:

    {
      "1": 42, "2": 17, ... "23": 128,
      "unassigned": 34
    }

`unassigned` is read only to be reported; add-on places whose artwork is not
known yet are not written anywhere until the survey comes back.

    python3 seed_slots.py counts.json              # show what would change
    python3 seed_slots.py counts.json --apply      # write it
    python3 seed_slots.py counts.json --apply --overwrite   # write over a seed

Without --overwrite the script refuses to touch an artwork whose counter is
already above zero, so running it twice cannot double-count.
"""

import argparse
import json
import sys

import boto3
from botocore.exceptions import ClientError

TABLE = "oneheart-slots"
REGION = "ap-northeast-1"
TITLES = [
    "ONE EARTH", "DIFFERENT", "WHO AM I?", "WONDER", "DREAMER", "MY VOICE",
    "LOVE INSIDE", "FACE TO FACE", "CONNECTED", "LIFELINE", "HEART KING",
    "KING OF ME", "BURNING SOUL", "COURAGE", "FADING AWAY", "ETERNAL",
    "TWO MINDS", "THE UNKNOWN", "HOPE STAR", "ANGEL WITHIN", "DEVIL WITHIN",
    "THE EYE", "ONE HEART",
]


def total(i):
    return 5000 if i == 23 else 2500


def read_counts(path):
    doc = json.load(open(path))
    # accept the shape update_progress.py writes, as well as a plain mapping
    if "artworks" in doc:
        counts = {int(k): int(v["taken"]) for k, v in doc["artworks"].items()}
        unassigned = int(doc.get("unassigned", 0))
    else:
        counts = {int(k): int(v) for k, v in doc.items() if k != "unassigned"}
        unassigned = int(doc.get("unassigned", 0))
    for i, n in counts.items():
        if not 1 <= i <= 23:
            sys.exit("artwork %r is not between 1 and 23" % i)
        if n < 0 or n > total(i):
            sys.exit("artwork %d: %d places is outside 0..%d" % (i, n, total(i)))
    return counts, unassigned


def current(ddb):
    out = {}
    k = None
    while True:
        kw = {"TableName": TABLE}
        if k:
            kw["ExclusiveStartKey"] = k
        q = ddb.scan(**kw)
        for it in q.get("Items", []):
            i = int(it["artworkId"]["S"])
            taken = int(it["taken"]["N"]) if "taken" in it else 0
            freed = len(it["freed"]["NS"]) if "freed" in it else 0
            out[i] = (taken, freed)
        k = q.get("LastEvaluatedKey")
        if not k:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("counts", help="JSON file of places sold per artwork")
    ap.add_argument("--apply", action="store_true", help="write to DynamoDB")
    ap.add_argument("--overwrite", action="store_true",
                    help="write even where a counter is already above zero")
    args = ap.parse_args()

    counts, unassigned = read_counts(args.counts)
    ddb = boto3.client("dynamodb", region_name=REGION)
    now = current(ddb)

    blocked = []
    plan = []
    for i in range(1, 24):
        want = counts.get(i, 0)
        taken, freed = now.get(i, (0, 0))
        if taken and not args.overwrite:
            blocked.append(i)
        if want != taken:
            plan.append((i, taken, want, freed))

    print("%-4s %-14s %8s %8s" % ("", "artwork", "now", "after"))
    for i, taken, want, freed in plan:
        mark = "  refuses" if i in blocked else ""
        print("%02d   %-14s %8d %8d%s" % (i, TITLES[i - 1], taken, want, mark))
    if not plan:
        print("nothing to change")
    print("\nplaces to carry over: %d" % sum(counts.values()))
    if unassigned:
        print("add-on places with no artwork yet: %d  (held until the survey returns)"
              % unassigned)

    if blocked:
        print("\n%d artwork(s) already have a counter above zero. Nothing was written. "
              "If this seed is meant to replace them, run again with --overwrite."
              % len(blocked), file=sys.stderr)
        return 1

    if not args.apply:
        print("\nnothing written. Run again with --apply to write it.")
        return 0

    for i, taken, want, freed in plan:
        try:
            ddb.update_item(
                TableName=TABLE,
                Key={"artworkId": {"S": str(i)}},
                UpdateExpression="SET taken = :n, tot = :t",
                ExpressionAttributeValues={":n": {"N": str(want)}, ":t": {"N": str(total(i))}},
            )
            print("%02d set to %d" % (i, want))
        except ClientError as e:
            print("%02d failed: %s" % (i, e), file=sys.stderr)
            return 1
    print("\ndone. Check it with:  curl -s "
          "https://7xw0uwnpra.execute-api.ap-northeast-1.amazonaws.com/slots")
    return 0


if __name__ == "__main__":
    sys.exit(main())
