FROM node:22-bookworm-slim AS build
WORKDIR /app
COPY app/package*.json ./
RUN npm ci --no-audit --no-fund
COPY app/ ./
RUN npm run build
FROM nginx:stable-alpine AS runtime
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/build /usr/share/nginx/html
USER 101:101
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s CMD wget -q -O /dev/null http://127.0.0.1:8080/health || exit 1
CMD ["nginx", "-g", "daemon off;"]
