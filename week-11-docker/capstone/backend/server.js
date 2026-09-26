'use strict';
const fs = require('fs');
process.env.EPICBOOK_SESSION_SECRET = fs.readFileSync('/run/secrets/session', 'utf8').trim();
const express = require('express'), db = require('./models'), session = require('./lib/cart-session');
const app = express();
app.disable('x-powered-by'); app.set('trust proxy', 1);
app.use(express.json({limit:'16kb'})); app.use(express.urlencoded({extended:false,limit:'16kb'}));
app.use((req,res,next) => {
 const started=Date.now();res.on('finish',()=>console.log(JSON.stringify({at:new Date().toISOString(),service:'backend',method:req.method,path:req.path,status:res.statusCode,duration_ms:Date.now()-started})));
 const allowed=(process.env.ALLOWED_ORIGINS||'').split(',');
 if(req.headers.origin&&!allowed.includes(req.headers.origin))return res.status(403).json({error:'Origin is not allowed'});
 if(req.headers.origin){res.setHeader('Access-Control-Allow-Origin',req.headers.origin);res.setHeader('Vary','Origin');res.setHeader('Access-Control-Allow-Credentials','true');}
 if(req.method==='OPTIONS'){res.setHeader('Access-Control-Allow-Methods','GET,POST,OPTIONS');res.setHeader('Access-Control-Allow-Headers','Content-Type');return res.sendStatus(204);}next();
});
app.get('/health',async(_req,res)=>{try{await db.sequelize.authenticate();res.json({status:'ready',database:'reachable'});}catch{res.status(503).json({status:'unavailable',database:'unreachable'});}});
app.get('/api/catalog',async(req,res)=>{try{
 const where=req.query.genre?{genre:String(req.query.genre).slice(0,100)}:{};
 const books=await db.Book.findAll({where,limit:req.query.genre?50:9,include:[db.Author],order:[['id','ASC']]});
 const categories=await db.Book.aggregate('genre','DISTINCT',{plain:false});const cart=await session.pending(db,req);
 res.json({books,categories,cartCount:cart.length});
}catch{res.status(503).json({error:'Catalogue temporarily unavailable'});}});
require('./routes/cart-api-routes')(app);
app.use((_req,res)=>res.status(404).json({error:'Not found'}));app.use((_err,_req,res,_next)=>res.status(500).json({error:'Request could not be completed'}));
const server=app.listen(8080,'0.0.0.0',()=>console.log(JSON.stringify({service:'backend',event:'listening',port:8080})));
process.on('SIGTERM',()=>server.close(()=>db.sequelize.close().finally(()=>process.exit(0))));
