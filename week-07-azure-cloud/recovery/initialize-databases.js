// Run once by the authorized operator, never by the runtime application user.
const {Sequelize} = require('/opt/week07/book/backend/node_modules/sequelize');
const fs = require('fs');
const {spawnSync} = require('child_process');
const host=process.env.DB_HOST;
const password=process.env.ADMIN_PASSWORD;
const admin=new Sequelize('bookreview','week07admin',password,{host,dialect:'mysql',logging:false,dialectOptions:{ssl:{rejectUnauthorized:true}}});
async function main(){
  await admin.authenticate();
  const models=['User','Book','Review'].map(n=>require('/opt/week07/book/backend/src/models/'+n)(admin));
  for(const model of models) await model.sync();
  if(await models[1].count()===0)await models[1].bulkCreate([
    {title:'The Pragmatic Programmer',author:'Andrew Hunt',rating:4.8},
    {title:'Clean Code',author:'Robert C. Martin',rating:4.7},
    {title:'JavaScript: The Good Parts',author:'Douglas Crockford',rating:4.5}
  ]);
  process.env.NODE_ENV='production';
  process.env.EPICBOOK_DB_TLS='true';
  process.env.JAWSDB_URL='mysql://week07admin:'+encodeURIComponent(password)+'@'+host+':3306/bookstore';
  const epic=require('/opt/week07/epic/models');
  epic.sequelize.options.logging=false;
  await epic.sequelize.sync();
  if(await epic.Author.count()===0){
    const sql=['author_seed.sql','books_seed.sql'].map(n=>fs.readFileSync('/opt/week07/epic/db/'+n,'utf8')).join(';\n');
    const result=spawnSync('mysql',['--ssl-mode=VERIFY_IDENTITY','--ssl-ca=/etc/ssl/certs/ca-certificates.crt','--host='+host,'--user=week07admin','bookstore'],{input:sql,encoding:'utf8',env:{...process.env,MYSQL_PWD:password}});
    if(result.status!==0)throw new Error('Seed import failed: '+result.stderr);
  }
  for(const [user,source,database,pass] of [
    ['bookapp','10.0.4.%','bookreview',process.env.APP_PASSWORD],
    ['epicapp','10.0.1.10','bookstore',process.env.EPIC_PASSWORD]
  ]){
    const account=admin.escape(user)+'@'+admin.escape(source);
    await admin.query('CREATE USER IF NOT EXISTS '+account+' IDENTIFIED BY :pass REQUIRE SSL',{replacements:{pass}});
    await admin.query('GRANT SELECT,INSERT,UPDATE,DELETE ON `'+database+'`.* TO '+account);
  }
  const [tls]=await admin.query("SHOW STATUS LIKE 'Ssl_cipher'");
  console.log(JSON.stringify({bookreviewBooks:await models[1].count(),epicAuthors:await epic.Author.count(),epicBooks:await epic.Book.count(),tls:tls,applicationPrivileges:'SELECT, INSERT, UPDATE, DELETE; source-restricted and TLS required'},null,2));
  await epic.sequelize.close();await admin.close();
}
main().catch(e=>{console.error('Database initialization failed: '+e.message);process.exitCode=1;});
