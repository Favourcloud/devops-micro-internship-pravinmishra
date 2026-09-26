# Components, configuration and persistence

Eze Favour — DMI Week 11. The pinned instructor source began as a single Express/Handlebars application. This submission separates view rendering and static assets into a frontend service, and database operations into the backend. There are no background workers. The upstream book catalogue and disclosed Week 10 signed-cart/demo-checkout patch are retained; this week's explicit SQL migration adds the missing join/checkout tables.

| Component | Container port | Host exposure | Configuration | Persistent data |
|---|---|---|---|---|
| Nginx proxy | 8080 | 80 | proxy/nginx.conf | logs/nginx bind mount |
| Frontend | 8080 | none | internal backend URL | none |
| Backend | 8080 | none | ALLOWED_ORIGINS; secret files | MySQL via internal network |
| MySQL | 3306 | none | MYSQL_DATABASE, MYSQL_USER, *_FILE passwords | database-data named volume |
| CloudFront | HTTPS 443 | AWS edge address | origin, forwarded cookies/headers, TTL 0 | none |

The backend reads `/run/secrets/db_password` and `/run/secrets/session`. Database root and application passwords are distinct. No database password is a Dockerfile ARG or baked into an image. Compose mounts operator-owned files; this standalone Compose setup is not an encrypted secret-management service. Keep the private secret directory out of Git and restrict host access. Neither the frontend nor the proxy receives database credentials.

HTTPS: https://d209ibroel8p0b.cloudfront.net/ . Direct teaching origin: http://98.86.65.226/ . Browser-to-edge traffic uses TLS; the CloudFront-to-VM hop is HTTP. The internal Docker database link is also unencrypted and confined to one host. These are disclosed production limitations, not end-to-end encryption claims.
