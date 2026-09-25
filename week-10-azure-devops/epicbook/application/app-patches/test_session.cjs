"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const path = require("node:path");
process.env.EPICBOOK_SESSION_SECRET = crypto.randomBytes(32).toString("hex");
const session = require(path.resolve(process.env.DMI_EPICBOOK_SOURCE, "lib/cart-session.js"));
function cookie(ids) {
  let value;
  session.write({secure: false}, {cookie: (name, text, options) => {
    assert.equal(options.httpOnly, true); assert.equal(options.sameSite, "strict");
    value = name + "=" + text;
  }}, ids);
  return value;
}
test("signed cart IDs round-trip with HttpOnly and SameSite", () => {
  assert.deepEqual(session.read({headers: {cookie: cookie([1,2])}}), [1,2]);
});
test("separate browsers retain separate cart membership", () => {
  const a=cookie([10]), b=cookie([20]);
  assert.deepEqual(session.read({headers:{cookie:a}}),[10]);
  assert.deepEqual(session.read({headers:{cookie:b}}),[20]);
  assert.deepEqual(session.read({headers:{}}),[]);
});
test("tampering and malformed cookies cannot select another cart", () => {
  const valid=cookie([10]);
  const payload=Buffer.from(JSON.stringify({ids:[999],expires:Date.now()+60000})).toString("base64url");
  for (const c of ["epicbook_cart="+payload+"."+valid.split(".")[1],valid+".extra","epicbook_cart=invalid", "epicbook_cart="+"x".repeat(3000)]) {
    assert.deepEqual(session.read({headers:{cookie:c}}),[]);
  }
});
test("expired, oversized and invalid signed IDs are rejected", () => {
  const data=[{ids:[1],expires:Date.now()-10},{ids:[-1],expires:Date.now()+60000},{ids:Array.from({length:21},(_,i)=>i+1),expires:Date.now()+60000}];
  for (const x of data) {
    const p=Buffer.from(JSON.stringify(x)).toString("base64url");
    const sig=crypto.createHmac("sha256",process.env.EPICBOOK_SESSION_SECRET).update(p).digest("base64url");
    assert.deepEqual(session.read({headers:{cookie:"epicbook_cart="+p+"."+sig}}),[]);
  }
});
test("cross-origin writes are refused", () => {
  let code;
  const res={status:c=>{code=c;return res;},json:()=>{}};
  assert.equal(session.sameOrigin({headers:{origin:"https://attacker.invalid"},get:()=>"example.test"},res),false);
  assert.equal(code,403);
  assert.equal(session.sameOrigin({headers:{origin:"https://example.test"},get:()=>"example.test"},res),true);
});
test("pending query is restricted to signed IDs and hides completed orders", async () => {
  let where;
  const db={Book:{},Checkout:{},Cart:{findAll:async opts=>{where=opts.where;return [{id:1,Checkout:null},{id:2,Checkout:{id:9}}];}}};
  assert.deepEqual(await session.pending(db,{headers:{cookie:cookie([1,2])}}),[{id:1,Checkout:null}]);
  assert.deepEqual(where,{id:[1,2]});
});
