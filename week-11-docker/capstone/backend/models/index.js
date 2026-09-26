'use strict';
const fs=require('fs'),path=require('path'),Sequelize=require('sequelize');
const password=fs.readFileSync('/run/secrets/db_password','utf8').trim();
const sequelize=new Sequelize('bookstore','epicapp',password,{host:'database',dialect:'mysql',logging:false,pool:{max:5,min:0,acquire:5000,idle:10000},dialectOptions:{connectTimeout:3000}});
const db={};
for(const file of fs.readdirSync(__dirname).filter(f=>f.endsWith('.js')&&f!=='index.js')){const model=require(path.join(__dirname,file))(sequelize,Sequelize.DataTypes);db[model.name]=model;}
for(const model of Object.values(db))if(model.associate)model.associate(db);
db.sequelize=sequelize;db.Sequelize=Sequelize;module.exports=db;
