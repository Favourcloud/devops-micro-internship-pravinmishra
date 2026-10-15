'use strict';
const express=require('express'),{engine}=require('express-handlebars'),accounting=require('accounting');
module.exports = function addPages(app) {app.disable('x-powered-by');app.engine('handlebars',engine({defaultLayout:'main'}));app.set('view engine','handlebars');

app.use((req,res,next)=>{const at=Date.now();res.on('finish',()=>console.log(JSON.stringify({service:'frontend',method:req.method,path:req.path,status:res.statusCode,duration_ms:Date.now()-at})));next();});

async function api(req,route){const r=await fetch('http://127.0.0.1:8080'+route,{headers:{cookie:req.headers.cookie||''},signal:AbortSignal.timeout(5500)});if(!r.ok)throw new Error('Backend unavailable');return r.json();}
function wrap(row){const v={...row,price:accounting.formatMoney(row.price),modalhref:'#modal-book-'+row.id,modalId:'modal-book-'+row.id};if(row.Author)v.Author={dataValues:row.Author};if(row.Books)v.Books=row.Books.map(b=>({dataValues:b}));return {dataValues:v};}
function unavailable(res){res.status(503).type('html').send('<!doctype html><html lang="en"><meta charset="utf-8"><title>EpicBook temporarily unavailable</title><body style="font:20px system-ui;max-width:48rem;margin:8vh auto;padding:2rem"><h1>We could not load the bookstore</h1><p>Your cart has not been cleared. Please try again shortly.</p><a href="/">Try again</a><hr><p>Eze Favour · DMI Week 11 · EpicBook</p></body></html>');}
async function catalog(req,res){try{const genre=req.body&&req.body.genre;const d=await api(req,'/api/catalog'+(genre?'?genre='+encodeURIComponent(genre):''));res.render(genre?'category':'index',{...d,books:d.books.map(wrap)});}catch{unavailable(res);}}
app.get('/',catalog);app.post('/category/:categoryName',catalog);
app.get('/cart',async(req,res)=>{try{const[a,b]=await Promise.all([api(req,'/api/cart'),api(req,'/api/catalog')]);res.render('cart',{cart:a.cart.map(wrap),cartCount:a.cart.length,categories:b.categories,subTotal:a.cart.reduce((n,c)=>n+Number(c.price)*c.quantity,0).toFixed(2)});}catch{unavailable(res);}});
app.get('/gallery',(_req,res)=>res.render('gallery'));
};
