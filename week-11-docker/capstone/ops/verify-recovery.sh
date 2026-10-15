#!/usr/bin/env bash
# Eze Favour: run only against this teaching stack. No application rows are deleted.
set -euo pipefail
cd "${1:?Usage: verify-recovery.sh COMPOSE_DIRECTORY BASE_URL}"
base=${2:?Provide the tested HTTP base URL}
export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-week11-epicbook}
umask 077
stamp=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p backups
sql() { docker compose exec -T database sh -c 'MYSQL_PWD=$(cat /run/secrets/db_password) mysql -u epicapp bookstore --batch -e "$1"' sh "$1"; }
assert_probe_count() {
  local actual
  actual=$(sql "SELECT COUNT(*) FROM dmi_restore_probe WHERE id=1 AND owner='Eze Favour - isolated restore probe';" | tail -n 1)
  test "$actual" = "$1" || { printf 'FAIL: expected %s probe rows, got %s\n' "$1" "$actual" >&2; return 1; }
}
recover() { docker compose up -d --wait --wait-timeout 180 >/dev/null; }
trap recover EXIT
printf 'Eze Favour | Week 11 A7 | Actual persistence, backup and failure drill | %s\n' "$stamp"
docker compose config --quiet
docker compose ps
sql "CREATE TABLE IF NOT EXISTS dmi_restore_probe (id INT PRIMARY KEY, owner VARCHAR(100)); INSERT INTO dmi_restore_probe VALUES (1, 'Eze Favour - isolated restore probe') ON DUPLICATE KEY UPDATE owner=VALUES(owner); SELECT * FROM dmi_restore_probe;"
assert_probe_count 1
archive="backups/rubric-probe-$stamp.sql"
docker compose exec -T database sh -c 'MYSQL_PWD=$(cat /run/secrets/db_password) mysqldump -u epicapp --no-tablespaces --set-gtid-purged=OFF bookstore dmi_restore_probe' > "$archive"
test -s "$archive"
echo 'Backup created:'
ls -lh "$archive"
echo 'Controlled deletion: only the synthetic dmi_restore_probe row'
sql 'DELETE FROM dmi_restore_probe WHERE id=1; SELECT COUNT(*) AS probe_rows_after_delete FROM dmi_restore_probe;'
assert_probe_count 0
docker compose exec -T database sh -c 'MYSQL_PWD=$(cat /run/secrets/db_password) mysql -u epicapp bookstore' < "$archive"
sql 'SELECT * FROM dmi_restore_probe;'
assert_probe_count 1
echo 'PASS: synthetic probe restored'
echo '$ docker compose down (no volume removal)'
docker compose down
echo '$ docker compose up -d --wait'
recover
sql 'SELECT * FROM dmi_restore_probe;'
assert_probe_count 1
echo 'PASS: same row persists after down/up'
for path in / /api/catalog /assets/img/1.png /health; do
 status=$(curl -sS -o /dev/null -w '%{http_code}' "$base$path")
 printf '%s -> %s\n' "$path" "$status"
 test "$status" = 200
done
echo 'Backend failure test'
docker compose stop backend
status=$(curl -sS --max-time 15 -o /dev/null -w '%{http_code}' "$base/api/catalog")
[[ "$status" =~ ^50[234]$ ]]
echo "Expected unavailable response: $status"
recover
curl -fsS "$base/health"
echo 'Database failure test'
docker compose stop database
status=$(curl -sS --max-time 20 -o /dev/null -w '%{http_code}' "$base/api/catalog")
[[ "$status" =~ ^50[234]$ ]]
echo "Expected database-dependent failure: $status"
recover
curl -fsS "$base/api/catalog" >/dev/null
curl -fsS "$base/health"
echo 'PASS: both dependency failures recovered'
docker compose restart reverse-proxy
recover
echo 'Persistent proxy log entries after proxy restart:'
tail -3 logs/nginx/access.log
echo 'Backend recent structured logs:'
docker compose logs --no-color --tail 3 backend
docker compose ps
trap - EXIT
