#!/usr/bin/env python3
"""Carry Kickstarter backers into the site as ordinary orders.

Backers have no order number, so after the campaign closes they cannot use
/portrait/ and would have nothing in hand until 2027. This reads the survey
responses, holds their places in oneheart-slots the same way the API does,
writes an order record, mints their certificates, uploads the portrait, and
sends the same receipt a site buyer gets.

  python3 import_backers.py backers.csv                 # show what would happen
  python3 import_backers.py backers.csv --apply         # write it
  python3 import_backers.py backers.csv --apply --send  # and send the emails

The CSV needs these columns, one row per backer:

  email        the backer's email address
  artworks     artwork numbers, comma separated, one entry per place
               a backer with three places in 05, 05 and 17 writes "5,5,17"
  name         optional, the name to engrave on the reverse (24 chars)
  photo        optional, path to their portrait file
  backer_id    optional, the Kickstarter backer number, kept for reference

A row is skipped if its email already has an imported order, so the script can
be run again as more surveys come back without duplicating anyone.
"""

import argparse
import csv
import mimetypes
import os
import sys
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

REGION = "ap-northeast-1"
ORDERS, SLOTS, CERTS = "oneheart-orders", "oneheart-slots", "oneheart-certs"
BUCKET = "oneheart-portraits"
SITE = "https://oneheart.tamjump.com"
FROM = "info@tamjump.com"

TITLES = [
    "ONE EARTH", "DIFFERENT", "WHO AM I?", "WONDER", "DREAMER", "MY VOICE",
    "LOVE INSIDE", "FACE TO FACE", "CONNECTED", "LIFELINE", "HEART KING",
    "KING OF ME", "BURNING SOUL", "COURAGE", "FADING AWAY", "ETERNAL",
    "TWO MINDS", "THE UNKNOWN", "HOPE STAR", "ANGEL WITHIN", "DEVIL WITHIN",
    "THE EYE", "ONE HEART",
]
COLS = 50
total = lambda i: 5000 if i == 23 else 2500
rows_of = lambda i: 100 if i == 23 else 50


def at(i, n):
    return {"row": -(-n // COLS), "col": (n - 1) % COLS + 1}


def pop_freed(ddb, art):
    """Take a released place back before opening a new one, as the API does."""
    try:
        it = ddb.get_item(TableName=SLOTS, Key={"artworkId": {"S": str(art)}},
                          ProjectionExpression="freed", ConsistentRead=True)
    except ClientError:
        return 0
    f = it.get("Item", {}).get("freed", {}).get("NS") or []
    if not f:
        return 0
    n = f[0]
    try:
        ddb.update_item(TableName=SLOTS, Key={"artworkId": {"S": str(art)}},
                        UpdateExpression="DELETE freed :s",
                        ConditionExpression="contains(freed,:n)",
                        ExpressionAttributeValues={":s": {"NS": [n]}, ":n": {"N": n}})
        return int(n)
    except ClientError:
        return 0


def reserve(ddb, art):
    """Hold one place. Returns the piece number, or -1 when the artwork is full."""
    f = pop_freed(ddb, art)
    if f:
        return f
    try:
        u = ddb.update_item(
            TableName=SLOTS, Key={"artworkId": {"S": str(art)}},
            UpdateExpression="SET tot = if_not_exists(tot,:t) ADD taken :one",
            ConditionExpression="attribute_not_exists(taken) OR taken < :t",
            ExpressionAttributeValues={":t": {"N": str(total(art))}, ":one": {"N": "1"}},
            ReturnValues="UPDATED_NEW")
        return int(u["Attributes"]["taken"]["N"])
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return -1
        raise


def release(ddb, art, piece):
    try:
        ddb.update_item(TableName=SLOTS, Key={"artworkId": {"S": str(art)}},
                        UpdateExpression="ADD freed :s",
                        ExpressionAttributeValues={":s": {"NS": [str(piece)]}})
    except ClientError as e:
        print("  could not release %02d:%d - %s" % (art, piece, e), file=sys.stderr)


def already_here(ddb, email):
    """True when this address already has an imported order."""
    k = None
    while True:
        kw = {"TableName": ORDERS,
              "FilterExpression": "email = :e AND #s = :s",
              "ExpressionAttributeNames": {"#s": "source"},
              "ExpressionAttributeValues": {":e": {"S": email}, ":s": {"S": "kickstarter"}}}
        if k:
            kw["ExclusiveStartKey"] = k
        q = ddb.scan(**kw)
        if q.get("Items"):
            return q["Items"][0]["orderId"]["S"]
        k = q.get("LastEvaluatedKey")
        if not k:
            return None


def read_rows(path):
    out = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for n, row in enumerate(csv.DictReader(fh), 2):
            email = (row.get("email") or "").strip().lower()
            arts = [a.strip() for a in (row.get("artworks") or "").split(",") if a.strip()]
            if not email or "@" not in email:
                print("line %d: no usable email, skipped" % n, file=sys.stderr)
                continue
            try:
                arts = [int(a) for a in arts]
            except ValueError:
                print("line %d: %s has a non-numeric artwork, skipped" % (n, email),
                      file=sys.stderr)
                continue
            if not arts or any(not 1 <= a <= 23 for a in arts):
                print("line %d: %s has no valid artwork, skipped" % (n, email),
                      file=sys.stderr)
                continue
            out.append({"email": email, "arts": arts,
                        "name": (row.get("name") or "").strip(),
                        "photo": (row.get("photo") or "").strip(),
                        "backer": (row.get("backer_id") or "").strip()})
    return out


def receipt_text(places, oid, name):
    lines = "\n".join("%02d %s piece %d (r%d,c%d)"
                      % (p["artwork"], TITLES[p["artwork"] - 1], p["piece"],
                         p["row"], p["col"]) for p in places)
    return (
        "WE ARE ALL ONE HEART\n\n"
        "Your places are held.\n\n"
        "Thank you for backing the project on Kickstarter. Your places are now "
        "recorded on the site under the order number below, exactly as they are "
        "for anyone who takes a place here.\n\n"
        "YOUR PLACES\n" + lines + "\n\n"
        + ("Name on the reverse: " + name + "\n\n" if name else "")
        + "Order: " + oid + "\n\n"
        "Your piece is yours to look at whenever you like. Open "
        + SITE + "/portrait/?id=" + oid + " with this order number and this email "
        "address, and it comes back. If you sent the wrong photograph, send another "
        "one the same way and it replaces this one.\n\n"
        "Places close on 30 June 2027. The artworks are rendered as they stand on "
        "that date, and everything reaches you by 30 September 2027.\n\n"
        + SITE + "\nTAmJ Inc., Tokyo - " + FROM + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--apply", action="store_true", help="write to DynamoDB and S3")
    ap.add_argument("--send", action="store_true", help="also email each backer")
    args = ap.parse_args()

    rows = read_rows(args.csv)
    ddb = boto3.client("dynamodb", region_name=REGION)
    s3 = boto3.client("s3", region_name=REGION)
    ses = boto3.client("ses", region_name=REGION)

    print("%d backers read from %s\n" % (len(rows), args.csv))
    if not args.apply:
        for r in rows:
            print("%-34s %d place(s) in %s%s"
                  % (r["email"], len(r["arts"]),
                     ",".join("%02d" % a for a in r["arts"]),
                     "  + photo" if r["photo"] else ""))
        print("\nnothing written. Run again with --apply.")
        return 0

    done = skipped = failed = 0
    for r in rows:
        prior = already_here(ddb, r["email"])
        if prior:
            print("%-34s already imported as %s" % (r["email"], prior[:8]))
            skipped += 1
            continue

        held = []
        full = None
        for a in r["arts"]:
            piece = reserve(ddb, a)
            if piece < 0:
                full = a
                break
            held.append((a, piece))
        if full:
            for a, p in held:
                release(ddb, a, p)
            print("%-34s artwork %02d is full - nothing held" % (r["email"], full),
                  file=sys.stderr)
            failed += 1
            continue

        oid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        positions = ",".join("%d:%d" % (a, p) for a, p in held)

        item = {"orderId": {"S": oid}, "email": {"S": r["email"]},
                "artworks": {"S": ",".join(str(a) for a in r["arts"])},
                "pieces": {"N": str(len(held))},
                "amount": {"N": str(len(held) * 500)},
                "paymentId": {"S": "kickstarter:" + (r["backer"] or "-")},
                "status": {"S": "paid"}, "portrait": {"S": ""},
                "positions": {"S": positions}, "createdAt": {"S": now},
                "ip": {"S": ""}, "source": {"S": "kickstarter"}}
        if r["name"]:
            item["reverseName"] = {"S": r["name"]}

        # the portrait first, so the order record is never written pointing at
        # a file that failed to upload
        if r["photo"]:
            if not os.path.exists(r["photo"]):
                print("%-34s photo not found: %s" % (r["email"], r["photo"]),
                      file=sys.stderr)
                for a, p in held:
                    release(ddb, a, p)
                failed += 1
                continue
            ext = "png" if r["photo"].lower().endswith(".png") else "jpg"
            key = "portraits/%s.%s" % (oid, ext)
            ctype = mimetypes.guess_type(r["photo"])[0] or "image/jpeg"
            s3.upload_file(r["photo"], BUCKET, key, ExtraArgs={"ContentType": ctype})
            item["portrait"] = {"S": key}
            item["portraitAt"] = {"S": now}

        ddb.put_item(TableName=ORDERS, Item=item)

        places = []
        for a, p in held:
            g = at(a, p)
            places.append({"artwork": a, "piece": p, "row": g["row"], "col": g["col"]})
            cid = "OHP%02d-%04d-%s" % (a, p, uuid.uuid4().hex[:8].upper())
            try:
                ddb.put_item(TableName=CERTS, Item={
                    "certId": {"S": cid}, "orderId": {"S": oid},
                    "artworkId": {"N": str(a)}, "piece": {"N": str(p)},
                    "row": {"N": str(g["row"])}, "col": {"N": str(g["col"])},
                    "status": {"S": "held"}, "issuedAt": {"S": now}},
                    ConditionExpression="attribute_not_exists(certId)")
            except ClientError as e:
                print("  certificate for %02d:%d failed - %s" % (a, p, e), file=sys.stderr)

        if args.send:
            try:
                ses.send_email(
                    Source=FROM, Destination={"ToAddresses": [r["email"]]},
                    Message={"Subject": {"Data": "Your places are held - ONE HEART order "
                                                 + oid[:8]},
                             "Body": {"Text": {"Data": receipt_text(places, oid, r["name"])}}})
            except ClientError as e:
                print("  email to %s failed - %s" % (r["email"], e), file=sys.stderr)

        print("%-34s %s  %s" % (r["email"], oid[:8],
                                " ".join("%02d:%d" % (a, p) for a, p in held)))
        done += 1

    print("\n%d imported, %d already there, %d could not be held"
          % (done, skipped, failed))
    print("Check the counters with:  curl -s %s/slots" % (
        "https://7xw0uwnpra.execute-api.ap-northeast-1.amazonaws.com"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
