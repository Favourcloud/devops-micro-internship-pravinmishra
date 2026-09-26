#!/usr/bin/env bash
# Consistent cold-volume snapshot; restore into a separate named volume and isolated container.
set -euo pipefail
cd /opt/week11/capstone
umask 077
stamp=$(date -u +%Y%m%dT%H%M%SZ)
archive="database-$stamp.tar.gz"
restore_volume="week11-restore-$stamp"
restore_container="week11-restore-$stamp"
source_volume=week11-epicbook_database-data
mkdir -p backups
query='SELECT "books",COUNT(*) FROM Book UNION ALL SELECT "carts",COUNT(*) FROM Cart UNION ALL SELECT "orders",COUNT(*) FROM Checkout; SELECT id,CartId,subTotal FROM Checkout ORDER BY id;'
recover() { docker compose up -d --wait --wait-timeout 180 >/dev/null; }
trap recover EXIT
printf 'Eze Favour | Database snapshot / restore drill | %s\n' "$stamp"
docker compose stop reverse-proxy frontend backend database
# The database is stopped before reading the data files.
docker run --rm --network none -v "$source_volume:/source:ro" -v "$PWD/backups:/backup" node:22-bookworm-slim tar -czf "/backup/$archive" -C /source .
sha256sum "backups/$archive"
docker volume create "$restore_volume"
docker run --rm --network none -v "$restore_volume:/restore" -v "$PWD/backups:/backup:ro" node:22-bookworm-slim tar -xzf "/backup/$archive" -C /restore
# Same image digest/version, no published port, and no networking.
mysql_image=$(docker inspect week11-epicbook-database-1 --format '{{.Image}}')
docker run -d --name "$restore_container" --network none -v "$restore_volume:/var/lib/mysql" -v "$PWD/secrets/db_password:/run/secrets/db_password:ro" "$mysql_image"
for i in $(seq 1 60); do
 if docker exec "$restore_container" sh -c 'MYSQL_PWD=$(cat /run/secrets/db_password) mysql -u epicapp bookstore -e "SELECT 1"' >/dev/null 2>&1;then break;fi
 sleep 2
done
docker exec "$restore_container" sh -c 'MYSQL_PWD=$(cat /run/secrets/db_password) mysql -u epicapp bookstore --batch --skip-column-names -e "$1"' sh "$query" > "backups/$stamp-restored.tsv"
recover
docker compose exec -T --interactive=false database sh -c 'MYSQL_PWD=$(cat /run/secrets/db_password) mysql -u epicapp bookstore --batch --skip-column-names -e "$1"' sh "$query" > "backups/$stamp-original.tsv"
diff -u "backups/$stamp-original.tsv" "backups/$stamp-restored.tsv"
cat "backups/$stamp-original.tsv"
echo 'PASS: isolated restored database matches original catalogue/cart/order counts and order rows'
docker stop "$restore_container"
# Preserve the restore volume and snapshot for operator inspection; no published port remains.
printf 'Archive: %s\nRestore volume: %s\nStopped restore container: %s\n' "$archive" "$restore_volume" "$restore_container"
trap - EXIT
