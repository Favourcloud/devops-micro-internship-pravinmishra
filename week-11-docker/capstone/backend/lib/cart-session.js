"use strict";
const crypto = require("crypto");
const secret = process.env.EPICBOOK_SESSION_SECRET;
if (!secret || secret.length < 32) throw new Error("A strong EPICBOOK_SESSION_SECRET is required");
const cookieName = "epicbook_cart";
function signature(text) { return crypto.createHmac("sha256", secret).update(text).digest("base64url"); }
function read(req) {
  const raw = (req.headers.cookie || "").split(";").map(x => x.trim()).find(x => x.startsWith(cookieName + "="));
  if (!raw || raw.length > 2048) return [];
  const [payload, signed, extra] = raw.slice(cookieName.length + 1).split(".");
  if (!payload || !signed || extra) return [];
  const expected = Buffer.from(signature(payload)), actual = Buffer.from(signed);
  if (actual.length !== expected.length || !crypto.timingSafeEqual(actual, expected)) return [];
  try {
    const data = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    if (!Number.isSafeInteger(data.expires) || data.expires < Date.now() || data.expires > Date.now() + 86400001) return [];
    if (!Array.isArray(data.ids) || data.ids.length > 20 || !data.ids.every(x => Number.isSafeInteger(x) && x > 0)) return [];
    return [...new Set(data.ids)];
  } catch (_) { return []; }
}
function write(req, res, ids) {
  const payload = Buffer.from(JSON.stringify({ids, expires: Date.now() + 86400000})).toString("base64url");
  res.cookie(cookieName, payload + "." + signature(payload), {httpOnly: true, sameSite: "strict", secure: req.secure, maxAge: 86400000, path: "/"});
}
function sameOrigin(req, res) {
  if (req.headers.origin) {
    try { if (new URL(req.headers.origin).host !== req.get("host")) { res.status(403).json({error: "Cross-origin request rejected"}); return false; } }
    catch (_) { res.status(403).json({error: "Invalid origin"}); return false; }
  }
  return true;
}
async function pending(db, req) {
  const ids = read(req);
  if (!ids.length) return [];
  const rows = await db.Cart.findAll({where: {id: ids}, include: [db.Book, db.Checkout]});
  return rows.filter(row => !row.Checkout);
}
module.exports = {read, write, sameOrigin, pending};
