# EpicBook frontend (October candidate)

Nginx serves the instructor static assets from public/ and proxies page rendering to the backend. Dockerfile copies only nginx.conf and public/. The retained server.js, views and package manifests document the September implementation and are not included in the October image. Cloud rollout of this candidate is pending.
