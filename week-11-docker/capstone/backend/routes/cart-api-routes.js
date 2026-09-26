"use strict";
const db = require("../models");
const session = require("../lib/cart-session");
module.exports = function (app) {
  app.post("/api/cart", async (req, res) => {
    if (!session.sameOrigin(req, res)) return;
    const bookId = Number(req.body.bookId);
    if (!Number.isSafeInteger(bookId) || bookId < 1) return res.status(400).json({error: "Invalid book"});
    const ids = session.read(req);
    if (ids.length >= 20) return res.status(400).json({error: "Demo cart limit reached"});
    try {
      const book = await db.Book.findByPk(bookId);
      if (!book) return res.status(404).json({error: "Book not found"});
      const cart = await db.sequelize.transaction(async transaction => {
        const row = await db.Cart.create({quantity: 1, price: book.price}, {transaction});
        await row.addBook(book, {transaction});
        return row;
      });
      session.write(req, res, [...ids, cart.id]);
      return res.status(201).json({id: cart.id, quantity: cart.quantity, price: cart.price, book});
    } catch (_) { return res.status(500).json({error: "Cart could not be saved"}); }
  });
  app.get("/api/cart", async (req, res) => {
    try { return res.json({cart: await session.pending(db, req)}); }
    catch (_) { return res.status(500).json({error: "Cart could not be loaded"}); }
  });
  app.post("/api/checkout", async (req, res) => {
    if (!session.sameOrigin(req, res)) return;
    const ids = session.read(req).sort((a,b) => a-b);
    if (!ids.length) return res.status(400).json({error: "Cart is empty"});
    try {
      const orders = await db.sequelize.transaction(async transaction => {
        const rows = await db.Cart.findAll({where: {id: ids}, order: [["id", "ASC"]], transaction, lock: transaction.LOCK.UPDATE});
        if (rows.length !== ids.length) throw new Error("Cart no longer exists");
        const saved = [];
        for (const cart of rows) {
          let order = await db.Checkout.findOne({where: {CartId: cart.id}, transaction});
          if (!order) order = await db.Checkout.create({CartId: cart.id,
            addressLine1: "DMI demonstration - no shipment", addressLine2: "Synthetic test order",
            city: "Demo", state: "Demo", zipCode: "00000", subTotal: Number(cart.price) * cart.quantity}, {transaction});
          saved.push({id: order.id, cartId: cart.id, subTotal: Number(order.subTotal).toFixed(2)});
        }
        return saved;
      });
      session.write(req, res, []);
      return res.status(201).json({demo: true, paymentTaken: false, orders});
    } catch (_) { return res.status(500).json({error: "Order could not be saved; your cart is retained"}); }
  });
  app.delete("/api/cart/delete", (_req, res) => res.status(405).json({error: "Use the demo checkout action"}));
};
