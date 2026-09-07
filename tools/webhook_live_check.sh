#!/usr/bin/env bash
# ONE HEART - check that the live Square webhook receiver accepts our signature.
#
# Square's own "Send test event" carries an application_id that is not ours, so
# the receiver ignores it and the result tells us nothing about the signature.
# This signs a body the same way Square does, using the key that is actually in
# SSM, and reads the answer.
#
#   bash webhook_live_check.sh          # signature checks only, no side effects
#   bash webhook_live_check.sh --alert  # also prove the orphan alert fires
#
# --alert posts a payment that looks like ours but has no order behind it. That
# is the condition the receiver exists to catch, so it writes a row in
# oneheart-payments and sends a notice to info@. The row is removed again at the
# end, and the notice is expected - it is the proof.

set -euo pipefail

URL=https://7xw0uwnpra.execute-api.ap-northeast-1.amazonaws.com/square-webhook
APP=sq0idp-DDvfI0E05acVUIYXHZimkQ
PARAM=/oneheart/square/webhook-key
REGION=ap-northeast-1
ALERT=0
[ "${1:-}" = "--alert" ] && ALERT=1

KEY="$(aws ssm get-parameter --name "$PARAM" --with-decryption --region "$REGION" \
        --query Parameter.Value --output text)"
if [ -z "$KEY" ] || [ "$KEY" = "None" ]; then
  echo "the signature key is not in SSM at $PARAM" >&2
  exit 1
fi
echo "key      read from $PARAM (${#KEY} characters)"
echo "url      $URL"
echo

PAYID="CHECK-$(date +%s)"

body() {
  python3 -c '
import json, sys
app, pid = sys.argv[1], sys.argv[2]
print(json.dumps({
  "merchant_id": "CHECK",
  "type": "payment.updated",
  "event_id": "check-" + pid,
  "created_at": "2026-09-07T00:00:00Z",
  "data": {"type": "payment", "id": pid, "object": {"payment": {
    "id": pid, "status": "COMPLETED",
    "amount_money": {"amount": 1500, "currency": "JPY"},
    "buyer_email_address": "check@tamjump.com",
    "note": "webhook_live_check.sh",
    "created_at": "2026-09-07T00:00:00Z",
    "application_details": {"application_id": app}}}}}, separators=(",", ":")))
' "$1" "$2"
}

sign() {
  python3 -c '
import base64, hashlib, hmac, sys
key, url, body = sys.argv[1].encode(), sys.argv[2], sys.argv[3]
print(base64.b64encode(hmac.new(key, (url + body).encode(), hashlib.sha256).digest()).decode())
' "$KEY" "$URL" "$1"
}

post() {
  curl -s -o /tmp/wh.out -w "%{http_code}" -X POST "$URL" \
    -H "content-type: application/json" \
    -H "x-square-hmacsha256-signature: $2" \
    --data-binary "$1"
}

check() {
  local label="$1" want_code="$2" want_body="$3" code
  code="$(post "$4" "$5")"
  local got; got="$(cat /tmp/wh.out)"
  if [ "$code" = "$want_code" ] && [ "$got" = "$want_body" ]; then
    printf '  ok   %-34s -> %s %s\n' "$label" "$code" "$got"
  else
    printf '  BAD  %-34s -> %s %s   (expected %s %s)\n' \
      "$label" "$code" "$got" "$want_code" "$want_body"
    return 1
  fi
}

fail=0

# 1. a body signed with the real key, from an application that is not ours.
#    A 401 here would mean the key in SSM does not match the one in Square.
B="$(body sq0idp-SOMEONEELSE "$PAYID")"
check "signed, another application" 200 "other app" "$B" "$(sign "$B")" || fail=1

# 2. the same body with a signature made from the wrong key
check "signed with the wrong key" 401 "bad signature" "$B" \
  "$(KEY=not-the-key python3 -c '
import base64, hashlib, hmac, sys
print(base64.b64encode(hmac.new(b"not-the-key", (sys.argv[1] + sys.argv[2]).encode(), hashlib.sha256).digest()).decode())
' "$URL" "$B")" || fail=1

# 3. no signature at all
code="$(curl -s -o /tmp/wh.out -w "%{http_code}" -X POST "$URL" \
  -H "content-type: application/json" --data-binary "$B")"
if [ "$code" = "401" ]; then
  printf '  ok   %-34s -> %s %s\n' "unsigned" "$code" "$(cat /tmp/wh.out)"
else
  printf '  BAD  %-34s -> %s %s   (expected 401)\n' "unsigned" "$code" "$(cat /tmp/wh.out)"
  fail=1
fi

if [ "$ALERT" = "1" ]; then
  echo
  echo "posting a payment that looks like ours, with no order behind it."
  echo "the receiver waits six seconds before it decides, so this is slow."
  B2="$(body "$APP" "$PAYID")"
  check "signed, our application, no order" 200 "orphan recorded" "$B2" "$(sign "$B2")" || fail=1
  echo "  a notice for $PAYID should be in info@tamjump.com"
  aws dynamodb delete-item --table-name oneheart-payments \
    --key "{\"paymentId\":{\"S\":\"$PAYID\"}}" --region "$REGION"
  echo "  test row $PAYID removed from oneheart-payments"
fi

echo
if [ "$fail" = "0" ]; then
  echo "the receiver accepts our signature and refuses everything else."
else
  echo "something did not answer as expected - see the BAD lines above." >&2
fi
exit "$fail"
