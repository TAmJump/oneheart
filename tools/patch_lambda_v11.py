#!/usr/bin/env python3
"""Add certificate issuing, /verify and the Square webhook receiver to lambda/index.js."""
import io, sys, re

P = "/home/claude/oneheart/lambda/index.js"
s = io.open(P, encoding="utf-8").read()


def sub1(old, new):
    global s
    if s.count(old) != 1:
        sys.exit("not unique: " + old[:70])
    s = s.replace(old, new)


# 1. crypto imports
sub1('const {randomUUID}=require("crypto");',
     'const {randomUUID,createHmac,timingSafeEqual}=require("crypto");')

# 2. certificate + payment helpers, inserted just before "async function order"
HELPERS = r'''const CERTS=process.env.CERTS;
const PAYMENTS=process.env.PAYMENTS;
const P4=n=>String(n).padStart(4,"0");
const CERT_RE=/^OHP\d{2}-\d{4}-[0-9A-F]{8}$/;
const newCertId=(a,i)=>"OHP"+P2(a)+"-"+P4(i)+"-"+randomUUID().replace(/-/g,"").slice(0,8).toUpperCase();
async function issueCerts(id,held,now){
  const out=[];
  for(const t of held){
    const g=at(t.id,t.i);
    for(let n=0;n<3;n++){
      const c=newCertId(t.id,t.i);
      try{
        await ddb.send(new PutItemCommand({TableName:CERTS,
          Item:{certId:{S:c},orderId:{S:id},artworkId:{N:String(t.id)},piece:{N:String(t.i)},
            row:{N:String(g.row)},col:{N:String(g.col)},status:{S:"held"},issuedAt:{S:now}},
          ConditionExpression:"attribute_not_exists(certId)"}));
        out.push({artwork:t.id,piece:t.i,certId:c});
        break;
      }catch(e){
        if(e.name!=="ConditionalCheckFailedException"){console.error("cert",e.name);break}
      }
    }
  }
  if(out.length){
    try{await ddb.send(new UpdateItemCommand({TableName:process.env.ORDERS,Key:{orderId:{S:id}},
      UpdateExpression:"SET certs = :c",
      ExpressionAttributeValues:{":c":{S:out.map(o=>o.artwork+":"+o.piece+":"+o.certId).join(",")}}}))}
    catch(e){console.error("ddb",e)}
  }
  return out;
}
async function verify(d){
  const c=String(d.certId||"").trim().toUpperCase().replace(/[\s\u3000]+/g,"");
  if(!CERT_RE.test(c))return r(400,{ok:false,error:"bad_id"});
  let it;
  try{it=await ddb.send(new GetItemCommand({TableName:CERTS,Key:{certId:{S:c}}}))}
  catch(e){console.error("ddb",e);return r(500,{ok:false,error:"lookup_failed"})}
  if(!it.Item)return r(404,{ok:false,error:"not_found"});
  const a=parseInt(it.Item.artworkId.N,10);
  return r(200,{ok:true,certId:c,artwork:a,title:TT(a),
    piece:parseInt(it.Item.piece.N,10),
    row:parseInt(it.Item.row.N,10),col:parseInt(it.Item.col.N,10),
    status:(it.Item.status&&it.Item.status.S)||"held",
    heldOn:((it.Item.issuedAt&&it.Item.issuedAt.S)||"").slice(0,10)});
}
async function notePayment(pid,id,email,amt,now,ordered){
  if(!pid)return;
  try{await ddb.send(new PutItemCommand({TableName:PAYMENTS,Item:{
    paymentId:{S:pid},orderId:{S:id},email:{S:email},amount:{N:String(amt)},
    ordered:{BOOL:!!ordered},createdAt:{S:now}}}))}catch(e){console.error("pay",e.name)}
}
let WKEY;
async function wkey(){
  if(WKEY===undefined){
    try{const p=await ssm.send(new GetParameterCommand({Name:process.env.WEBHOOK_PARAM,WithDecryption:true}));
      WKEY=p.Parameter.Value}
    catch(e){console.error("wkey",e.name);WKEY=null}
  }
  return WKEY;
}
const raw200=b=>({statusCode:200,headers:{"content-type":"text/plain"},body:b});
async function squareHook(body,sig){
  const k=await wkey();
  if(!k)return {statusCode:503,headers:{"content-type":"text/plain"},body:"no key"};
  const mine=createHmac("sha256",k).update(process.env.WEBHOOK_URL+body).digest("base64");
  const a=Buffer.from(mine,"utf8"),b=Buffer.from(String(sig||""),"utf8");
  if(a.length!==b.length||!timingSafeEqual(a,b))
    return {statusCode:401,headers:{"content-type":"text/plain"},body:"bad signature"};
  let ev={};try{ev=JSON.parse(body||"{}")}catch(x){return raw200("bad json")}
  const pay=ev&&ev.data&&ev.data.object&&ev.data.object.payment;
  if(!pay)return raw200("ignored");
  const app=(pay.application_details&&pay.application_details.application_id)||"";
  if(app!==process.env.SQ_APP_ID)return raw200("other app");
  if(String(pay.status||"")!=="COMPLETED")return raw200("not completed");
  const pid=String(pay.id||"");
  if(!pid)return raw200("no id");
  if(await paired(pid))return raw200("ok");
  await new Promise(z=>setTimeout(z,6000));
  if(await paired(pid))return raw200("ok");
  const amt=(pay.amount_money&&pay.amount_money.amount)||0;
  const buyer=String(pay.buyer_email_address||"-");
  const note=String(pay.note||"-");
  try{await ddb.send(new PutItemCommand({TableName:PAYMENTS,Item:{
    paymentId:{S:pid},orderId:{S:""},email:{S:buyer},amount:{N:String(amt)},
    ordered:{BOOL:false},orphan:{BOOL:true},note:{S:note},
    createdAt:{S:String(pay.created_at||new Date().toISOString())}}}))}catch(e){console.error("pay",e.name)}
  await mail("ONE HEART - payment without an order record - "+pid,
    "A Square payment completed but no order record was written.\n\n"
    +"payment  "+pid+"\namount   "+YEN(amt)+"\nbuyer    "+buyer+"\nnote     "+note
    +"\ntime     "+String(pay.created_at||"-")
    +"\n\nThe places for this payment may not be held in oneheart-slots, and the buyer has not been sent a receipt with an order number. Check oneheart-orders and oneheart-payments for "+pid+" before contacting the buyer.\n");
  return raw200("orphan recorded");
}
async function paired(pid){
  try{
    const it=await ddb.send(new GetItemCommand({TableName:PAYMENTS,Key:{paymentId:{S:pid}}}));
    return !!(it.Item&&it.Item.ordered&&it.Item.ordered.BOOL===true);
  }catch(e){console.error("ddb",e);return false}
}
'''
sub1("async function order(d,ip){", HELPERS + "async function order(d,ip){")

# 3. order(): record the payment, then the order, then mint certificates
sub1('''  try{
    await ddb.send(new PutItemCommand({TableName:process.env.ORDERS,Item:{
      orderId:{S:id},email:{S:email},artworks:{S:ls},pieces:{N:String(n)},
      amount:{N:String(amt)},paymentId:{S:(pay.payment&&pay.payment.id)||""},
      status:{S:"paid"},portrait:{S:""},positions:{S:ps},createdAt:{S:now},ip:{S:ip}}}));
  }catch(e){console.error("ddb",e)}''',
'''  const pid=(pay.payment&&pay.payment.id)||"";
  await notePayment(pid,id,email,amt,now,false);
  let stored=false;
  try{
    await ddb.send(new PutItemCommand({TableName:process.env.ORDERS,Item:{
      orderId:{S:id},email:{S:email},artworks:{S:ls},pieces:{N:String(n)},
      amount:{N:String(amt)},paymentId:{S:pid},
      status:{S:"paid"},portrait:{S:""},positions:{S:ps},createdAt:{S:now},ip:{S:ip}}}));
    stored=true;
  }catch(e){console.error("ddb",e)}
  if(stored){await notePayment(pid,id,email,amt,now,true);await issueCerts(id,held,now)}''')

# 4. office notification: paymentId variable is now in scope
sub1('''\\n\\norder "+id+"\\npayment "+((pay.payment&&pay.payment.id)||"-")+"\\n"''',
     '''\\n\\norder "+id+"\\npayment "+(pid||"-")+"\\n"''')

# 5. handler: raw body, webhook branch, /verify route
sub1('''exports.handler=async(e)=>{
  const p=(e.rawPath||"").replace(/\\/+$/,"")||"/";
  const hx=(e.requestContext&&e.requestContext.http)||{};
  const ip=hx.sourceIp||"";
  if(p==="/slots"&&hx.method==="GET")return slots();
  let d={};try{d=JSON.parse(e.body||"{}")}catch(x){return r(400,{error:"bad_json"})}
  if(p==="/notify")return notify(d,ip);
  if(p==="/order")return order(d,ip);
  if(p==="/portrait")return portrait(d,ip);
  if(p==="/piece")return piece(d);
  return r(404,{error:"not_found"});
};''',
'''exports.handler=async(e)=>{
  const p=(e.rawPath||"").replace(/\\/+$/,"")||"/";
  const hx=(e.requestContext&&e.requestContext.http)||{};
  const ip=hx.sourceIp||"";
  if(p==="/slots"&&hx.method==="GET")return slots();
  const body=e.isBase64Encoded?Buffer.from(e.body||"","base64").toString("utf8"):(e.body||"");
  if(p==="/square-webhook"){
    const hd=e.headers||{};
    return squareHook(body,hd["x-square-hmacsha256-signature"]||hd["X-Square-HmacSha256-Signature"]||"");
  }
  let d={};try{d=JSON.parse(body||"{}")}catch(x){return r(400,{error:"bad_json"})}
  if(p==="/notify")return notify(d,ip);
  if(p==="/order")return order(d,ip);
  if(p==="/portrait")return portrait(d,ip);
  if(p==="/piece")return piece(d);
  if(p==="/verify")return verify(d);
  return r(404,{error:"not_found"});
};''')

io.open(P, "w", encoding="utf-8").write(s)
print("patched", len(s), "bytes")
