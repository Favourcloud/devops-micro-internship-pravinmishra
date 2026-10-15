# Proxy routing and CORS

Eze Favour · 15 October candidate, local verification; cloud rollout pending.

The reverse proxy is the only published capstone service. `/api/` goes to backend:8080; `/health` goes to its database-aware health endpoint; other requests go to frontend:8080. Frontend Nginx serves `/assets/` from `/usr/share/nginx/html` and sends application pages to the backend's Handlebars routes. Docker DNS resolution has a five-second cache so replaced service IPs are rediscovered.

The browser sees a single origin for pages and APIs, so browser CORS permissions are not necessary for this capstone. The explicit backend origin allowlist is retained as a defence on write requests; it is not a substitute for authentication. The separate Assignment 6 app intentionally uses two public ports and therefore has an actual cross-origin CORS requirement.

The proxy keeps bounded timeouts, small request bodies, no dotfile access, security headers, and API request limits. JSON logs include timestamp, method, path, status and duration; they exclude cookies, authorization headers, query strings and database connection strings.

[Local route and checkout checks](../../evidence/2026-10-15-rubric/capstone-http-tests.json) · [proxy configuration](../proxy/nginx.conf) · [frontend routing](../frontend/nginx.conf).
