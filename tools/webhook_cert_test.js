// Local check for the Square webhook receiver and the certificate routes.
// Run with the AWS SDK stubbed:  node tools/webhook_cert_test.js
// The stub answers every DynamoDB / SES call from a small in-memory store,
// so this exercises signature checking, the application_id filter, the
// orphan-payment alert, certificate minting and /verify without touching AWS.

const {createHmac} = require("crypto");
const assert = require("assert");

const URL = "https://example.execute-api.ap-northeast-1.amazonaws.com/square-webhook";
const KEY = "test-webhook-signature-key";
const APP = "sq0idp-TESTAPPID";

Object.assign(process.env, {
  ORIGIN: "https://oneheart.tamjump.com",
  TABLE: "signups", ORDERS: "orders", SLOTS: "slots",
  CERTS: "certs", PAYMENTS: "payments",
  BUCKET: "bucket", NOTIFY_TO: "info@example.com", NOTIFY_FROM: "info@example.com",
  SQ_LOCATION: "LOC", TOKEN_PARAM: "/t", WEBHOOK_PARAM: "/w",
  WEBHOOK_URL: URL, SQ_APP_ID: APP
});

const db = {certs: {}, payments: {}, orders: {}};
const mails = [];

global.__AWS = (c) => {
  const n = c.__n, i = c.input || {};
  if (n === "GetParameterCommand") return {Parameter: {Value: KEY}};
  if (n === "SendEmailCommand") {
    mails.push({to: i.Destination.ToAddresses[0], subject: i.Message.Subject.Data});
    return {};
  }
  const t = (i.TableName || "").replace(/^oneheart-/, "");
  if (n === "PutItemCommand") {
    const k = i.Item.certId ? i.Item.certId.S : (i.Item.paymentId ? i.Item.paymentId.S : i.Item.orderId.S);
    if (i.ConditionExpression && db[t][k]) { const e = new Error("exists"); e.name = "ConditionalCheckFailedException"; throw e; }
    db[t][k] = i.Item;
    return {};
  }
  if (n === "GetItemCommand") {
    const k = i.Key.certId ? i.Key.certId.S : (i.Key.paymentId ? i.Key.paymentId.S : i.Key.orderId.S);
    return db[t][k] ? {Item: db[t][k]} : {};
  }
  if (n === "UpdateItemCommand") return {};
  return {};
};

const fn = require("../lambda/index.js");

const ev = (path, body, headers) => ({
  rawPath: path, body, headers: headers || {},
  requestContext: {http: {method: "POST", sourceIp: "203.0.113.7"}}
});

const sign = (body) => createHmac("sha256", KEY).update(URL + body).digest("base64");

const payment = (over) => JSON.stringify({
  type: "payment.updated",
  data: {object: {payment: Object.assign({
    id: "PAY_TEST_1", status: "COMPLETED",
    amount_money: {amount: 1500, currency: "JPY"},
    buyer_email_address: "buyer@example.com",
    note: "ONE HEART 3 places [1,5,23]",
    created_at: "2026-10-20T04:05:06Z",
    application_details: {application_id: APP}
  }, over || {})}}
});

(async () => {
  // 1. a body with no signature is refused
  let res = await fn.handler(ev("/square-webhook", payment(), {}));
  assert.strictEqual(res.statusCode, 401, "unsigned body must be refused");

  // 2. a body signed with the wrong key is refused
  const bad = createHmac("sha256", "wrong").update(URL + payment()).digest("base64");
  res = await fn.handler(ev("/square-webhook", payment(), {"x-square-hmacsha256-signature": bad}));
  assert.strictEqual(res.statusCode, 401, "wrong key must be refused");

  // 3. a payment from another application is let through and ignored
  const other = payment({application_details: {application_id: "sq0idp-SOMEONEELSE"}});
  res = await fn.handler(ev("/square-webhook", other, {"x-square-hmacsha256-signature": sign(other)}));
  assert.strictEqual(res.statusCode, 200);
  assert.strictEqual(res.body, "other app", "another app's payment must be ignored");
  assert.strictEqual(mails.length, 0, "another app's payment must not raise an alert");

  // 4. base64 transport is decoded before the signature is checked
  const b = payment();
  res = await fn.handler(Object.assign(ev("/square-webhook", Buffer.from(b).toString("base64"),
    {"x-square-hmacsha256-signature": sign(b)}), {isBase64Encoded: true}));
  assert.strictEqual(res.statusCode, 200, "base64 body must verify");
  assert.strictEqual(res.body, "orphan recorded", "unknown payment must be recorded as an orphan");
  assert.ok(db.payments.PAY_TEST_1.orphan.BOOL, "orphan flag must be stored");
  assert.strictEqual(mails.length, 1, "an orphan must raise one alert");
  assert.ok(/payment without an order record/.test(mails[0].subject));

  // 5. once the order exists, the same event is quiet
  db.payments.PAY_TEST_1 = {paymentId: {S: "PAY_TEST_1"}, ordered: {BOOL: true}};
  mails.length = 0;
  res = await fn.handler(ev("/square-webhook", b, {"x-square-hmacsha256-signature": sign(b)}));
  assert.strictEqual(res.body, "ok", "a reconciled payment must be quiet");
  assert.strictEqual(mails.length, 0, "a reconciled payment must not raise an alert");

  // 6. /verify rejects a malformed id
  res = await fn.handler(ev("/verify", JSON.stringify({certId: "nope"})));
  assert.strictEqual(res.statusCode, 400);

  // 7. /verify on an id that was never issued
  res = await fn.handler(ev("/verify", JSON.stringify({certId: "OHP17-0042-ABCDEF01"})));
  assert.strictEqual(res.statusCode, 404);

  // 8. a stored certificate comes back with its artwork, piece and position
  db.certs["OHP17-0042-ABCDEF01"] = {
    certId: {S: "OHP17-0042-ABCDEF01"}, orderId: {S: "ord"}, artworkId: {N: "17"},
    piece: {N: "42"}, row: {N: "1"}, col: {N: "42"}, status: {S: "held"},
    issuedAt: {S: "2026-10-20T04:05:06.000Z"}
  };
  res = await fn.handler(ev("/verify", JSON.stringify({certId: " ohp17-0042-abcdef01 "})));
  const v = JSON.parse(res.body);
  assert.strictEqual(res.statusCode, 200);
  assert.strictEqual(v.title, "TWO MINDS", "artwork 17 is TWO MINDS");
  assert.strictEqual(v.piece, 42);
  assert.strictEqual(v.col, 42);
  assert.strictEqual(v.heldOn, "2026-10-20", "only the date is returned");
  assert.ok(!("email" in v) && !("orderId" in v), "no personal detail is returned");

  console.log("all checks passed");
})().catch(e => { console.error(e); process.exit(1); });
