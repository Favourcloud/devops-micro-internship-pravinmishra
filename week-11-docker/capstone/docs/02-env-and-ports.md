# Environment, ports and persistence

Eze Favour · 15 October 2026 candidate, verified locally; cloud rollout pending.

The instructor's EpicBook catalogue, signed cart and demo checkout remain. The candidate serves static assets from Nginx in the frontend container and renders application pages in the Express backend. This meets the current static-Nginx frontend requirement while preserving the existing Handlebars pages. There are no background workers.

| Component | Container port | Host exposure | Configuration | Persistence |
|---|---|---|---|---|
| reverse-proxy | 8080 | 80 by default; localhost 3180 during local tests | proxy/nginx.conf | logs/nginx bind mount |
| frontend Nginx | 8080 | none | frontend/nginx.conf; /usr/share/nginx/html | static files in image |
| backend Express | 8080 | none | ALLOWED_ORIGINS; file-mounted secrets | database only |
| database MySQL | 3306 | none | MYSQL_DATABASE; MYSQL_USER; *_PASSWORD_FILE | db_data external named volume |

`HTTP_BIND`/`HTTP_PORT` select the proxy host listener; `DATABASE_VOLUME_NAME` defaults to the existing `week11-epicbook_database-data` cloud volume. The logical Compose key is `db_data`, with `external: true`, so a rename does not silently create an empty replacement database. Create a separate named volume explicitly for a new environment; never point a local test at production data.

The backend reads `/run/secrets/db_password` and `/run/secrets/session`; MySQL also receives `/run/secrets/db_root`. Values remain in untracked host files. No database credential is sent to the frontend or included in a Dockerfile ARG. Standalone Compose secret files are not an encrypted secret-management service.

MySQL readiness uses authenticated SELECT 1, backend /health authenticates to MySQL, frontend /health confirms Nginx is serving, and the public /health route forwards to backend readiness.
