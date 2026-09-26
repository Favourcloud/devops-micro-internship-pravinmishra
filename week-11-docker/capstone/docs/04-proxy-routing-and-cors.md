# Reverse proxy, HTTPS and CORS

Nginx routes `/api/` to the backend and `/` to the frontend through Docker DNS. Variable upstreams with the Docker resolver let it discover replacement containers. Only the proxy publishes an application port. The proxy restricts request bodies, applies an API rate limit, suppresses its version, rejects dotfiles, and sends nosniff, frame-denial and referrer-policy headers. JSON logs omit cookies and request bodies.

CloudFront provides the AWS HTTPS hostname with HTTP-to-HTTPS redirection. Its dynamic cache TTL is zero and cookies/query strings/headers are forwarded. The distribution adds a viewer-scheme header so the origin can set Secure cookies for HTTPS requests. The backend permits exactly the direct origin and CloudFront origins. Foreign Origin headers are rejected with 403; signed HttpOnly SameSite=Strict cart cookies separate independent clients. Tests cover rejected origins and missing/invalid book IDs.

The direct origin remains public to satisfy the public-IP exercise. The origin hop is HTTP. Before handling real accounts, payments or personal data, use a certificate-backed HTTPS origin, restrict origin access, and review the complete threat model. This deployment accepts synthetic orders only and never takes payment.
