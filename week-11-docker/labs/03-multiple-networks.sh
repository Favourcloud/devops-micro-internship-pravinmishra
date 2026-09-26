#!/usr/bin/env bash
set -euo pipefail
cd /opt/week11
mkdir -p private
chmod 700 private
test -s private/mongo_password || openssl rand -hex 32 > private/mongo_password
chmod 444 private/mongo_password
docker network create --internal backend-network
docker network create frontend-network
find networking/multi -maxdepth 2 -type f
cat networking/multi/{database,backend,frontend}/Dockerfile
docker build --progress=plain -t lab-mongo:1.0 networking/multi/database
docker build --progress=plain -t multi-backend:1.0 networking/multi/backend
docker build --progress=plain -t multi-frontend:1.0 networking/multi/frontend
docker run -d --name database --network backend-network -e MONGO_INITDB_ROOT_USERNAME=labuser -e MONGO_INITDB_ROOT_PASSWORD_FILE=/run/secrets/mongo_password -v /opt/week11/private/mongo_password:/run/secrets/mongo_password:ro lab-mongo:1.0
docker run -d --name api --network backend-network -v /opt/week11/private/mongo_password:/run/secrets/mongo_password:ro multi-backend:1.0
docker network connect frontend-network api
docker run -d --name frontend --network frontend-network -p 80:8080 multi-frontend:1.0
docker ps
docker network inspect backend-network frontend-network
for i in $(seq 1 40); do docker exec database mongosh --quiet --eval 'db.getSiblingDB("admin").auth("labuser",require("fs").readFileSync("/run/secrets/mongo_password","utf8").trim());db.getSiblingDB("lab").messages.findOne()' >/dev/null 2>&1 && break || sleep 2; done
docker exec database mongosh --quiet --eval 'db.getSiblingDB("admin").auth("labuser",require("fs").readFileSync("/run/secrets/mongo_password","utf8").trim());db.getSiblingDB("lab").messages.insertOne({owner:"Eze Favour",message:"Docker networks verified",exercise:"Week 11"});printjson(db.getSiblingDB("lab").messages.find().toArray())'
docker exec frontend curl -fsS http://api:8080/
curl -fsS http://127.0.0.1/
if docker exec frontend node -e 'require("dns").lookup("database",(e)=>process.exit(e?1:0))'; then echo 'FAIL: frontend resolves database'; exit 1; else echo 'PASS: frontend cannot resolve the database on its network'; fi
