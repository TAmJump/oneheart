/* Exercises the reservation logic in the Lambda against an in-memory
   stand-in for DynamoDB that honours the conditional writes we rely on. */
const Module = require("module");
const fs = require("fs");

const slots = new Map();          // artworkId -> {taken, tot, freed:Set}
const orders = [];
let squareShouldFail = false;

function item(id) {
  if (!slots.has(id)) slots.set(id, { taken: undefined, tot: undefined, freed: new Set() });
  return slots.get(id);
}

class Cmd { constructor(i) { Object.assign(this, i); } }

const ddbStub = {
  DynamoDBClient: class {
    async send(c) {
      const k = c.Key && c.Key.artworkId && c.Key.artworkId.S;
      if (c.__t === "get") {
        const s = item(k);
        return { Item: s.freed.size ? { freed: { NS: [...s.freed] } } : {} };
      }
      if (c.__t === "update") {
        const s = item(k);
        const ex = c.UpdateExpression;
        if (ex.startsWith("DELETE freed")) {
          const n = c.ExpressionAttributeValues[":n"].N;
          if (!s.freed.has(n)) { const e = new Error("cc"); e.name = "ConditionalCheckFailedException"; throw e; }
          s.freed.delete(n);
          return {};
        }
        if (ex.startsWith("ADD freed")) {
          for (const n of c.ExpressionAttributeValues[":s"].NS) s.freed.add(n);
          return {};
        }
        if (ex.startsWith("SET tot")) {
          const t = parseInt(c.ExpressionAttributeValues[":t"].N, 10);
          const ok = s.taken === undefined || s.taken < t;
          if (!ok) { const e = new Error("cc"); e.name = "ConditionalCheckFailedException"; throw e; }
          if (s.tot === undefined) s.tot = t;
          s.taken = (s.taken || 0) + 1;
          return { Attributes: { taken: { N: String(s.taken) } } };
        }
      }
      if (c.__t === "put") { orders.push(c.Item); return {}; }
      if (c.__t === "scan") {
        return {
          Items: [...slots.entries()].map(([id, s]) => ({
            artworkId: { S: id },
            taken: { N: String(s.taken || 0) },
            tot: { N: String(s.tot || 2500) },
            ...(s.freed.size ? { freed: { NS: [...s.freed] } } : {})
          }))
        };
      }
      throw new Error("unhandled " + c.__t);
    }
  },
  PutItemCommand: class extends Cmd { constructor(i) { super(i); this.__t = "put"; } },
  UpdateItemCommand: class extends Cmd { constructor(i) { super(i); this.__t = "update"; } },
  GetItemCommand: class extends Cmd { constructor(i) { super(i); this.__t = "get"; } },
  ScanCommand: class extends Cmd { constructor(i) { super(i); this.__t = "scan"; } }
};

const stubs = {
  "@aws-sdk/client-dynamodb": ddbStub,
  "@aws-sdk/client-ses": { SESClient: class { async send() { } }, SendEmailCommand: class { } },
  "@aws-sdk/client-ssm": {
    SSMClient: class { async send() { return { Parameter: { Value: "tok" } }; } },
    GetParameterCommand: class { }
  }
};

const realLoad = Module._load;
Module._load = (req, parent, isMain) => stubs[req] || realLoad(req, parent, isMain);

global.fetch = async () => squareShouldFail
  ? { ok: false, json: async () => ({ errors: [{ detail: "CARD_DECLINED" }] }) }
  : { ok: true, json: async () => ({ payment: { id: "pay_" + Math.random().toString(36).slice(2) } }) };

process.env.SLOTS = "slots";
process.env.ORDERS = "orders";
process.env.TABLE = "signups";
process.env.ORIGIN = "https://oneheart.tamjump.com";
process.env.SQ_LOCATION = "L";
process.env.TOKEN_PARAM = "/p";

fs.writeFileSync("/tmp/fn_mod.js", fs.readFileSync("/tmp/fn.js", "utf8"));
const fn = require("/tmp/fn_mod.js");

const call = (body, method = "POST", path = "/order") =>
  fn.handler({ rawPath: path, body: JSON.stringify(body), requestContext: { http: { sourceIp: "1.2.3.4", method } } });

function assert(c, m) { if (!c) { console.error("FAIL " + m); process.exitCode = 1; } else console.log("ok   " + m); }

(async () => {
  // 1. a normal order gets one place in each artwork it asked for
  let res = await call({ email: "a@b.com", artworks: [1, 7, 23, 23], sourceId: "cnon" });
  let b = JSON.parse(res.body);
  assert(res.statusCode === 200, "a valid order is accepted");
  assert(b.places.length === 4, "four places are returned");
  assert(b.places[2].piece === 1 && b.places[3].piece === 2, "the two ONE HEART places are 1 and 2");
  assert(b.places[0].row === 1 && b.places[0].col === 1, "piece 1 sits at row 1, col 1");

  // 2. positions never repeat
  const seen = new Set();
  for (let i = 0; i < 60; i++) {
    const r = await call({ email: "x" + i + "@b.com", artworks: [2], sourceId: "cnon" });
    const p = JSON.parse(r.body).places[0];
    const key = p.artwork + ":" + p.piece;
    if (seen.has(key)) { assert(false, "position reuse at " + key); break; }
    seen.add(key);
  }
  assert(seen.size === 60, "sixty orders produce sixty distinct positions");

  // 3. a declined card gives the place back, and it is handed to the next buyer
  squareShouldFail = true;
  res = await call({ email: "d@b.com", artworks: [2], sourceId: "cnon" });
  assert(res.statusCode === 402, "a declined card returns 402");
  squareShouldFail = false;
  res = await call({ email: "e@b.com", artworks: [2], sourceId: "cnon" });
  const reused = JSON.parse(res.body).places[0].piece;
  assert(reused === 61, "the freed place is reissued rather than burned");

  // 4. an artwork cannot be oversold
  const s = item("5"); s.taken = 2499; s.tot = 2500;
  res = await call({ email: "f@b.com", artworks: [5], sourceId: "cnon" });
  assert(res.statusCode === 200 && JSON.parse(res.body).places[0].piece === 2500, "the last place is sold");
  res = await call({ email: "g@b.com", artworks: [5], sourceId: "cnon" });
  assert(res.statusCode === 409 && JSON.parse(res.body).error === "artwork_full", "the 2,501st is refused");

  // 5. a mixed order that hits a full artwork keeps nothing
  const before = item("9").taken;
  res = await call({ email: "h@b.com", artworks: [9, 5], sourceId: "cnon" });
  assert(res.statusCode === 409, "an order touching a full artwork is refused");
  const after = item("9");
  assert((after.taken || 0) - (before || 0) === 1 && after.freed.size === 1,
    "the place taken in the other artwork is released again");

  // 6. ONE HEART holds 5,000 places on a 50 x 100 grid
  const o = item("23"); o.taken = 4999; o.tot = 5000; o.freed.clear();
  res = await call({ email: "i@b.com", artworks: [23], sourceId: "cnon" });
  const last = JSON.parse(res.body).places[0];
  assert(last.piece === 5000 && last.rows === 100 && last.cols === 50, "ONE HEART runs to 5,000 on 50 x 100");
  res = await call({ email: "j@b.com", artworks: [23], sourceId: "cnon" });
  assert(res.statusCode === 409, "ONE HEART also stops at its limit");

  // 7. the public count endpoint reports what has actually been taken
  res = await call({}, "GET", "/slots");
  const sl = JSON.parse(res.body).artworks;
  assert(res.statusCode === 200 && sl["5"].taken === 2500 && sl["5"].total === 2500, "GET /slots reports live counts");
  assert(sl["12"].taken === 0 && sl["12"].total === 2500, "untouched artworks report zero");
})();
