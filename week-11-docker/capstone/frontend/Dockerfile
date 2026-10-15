FROM nginx@sha256:985220252f3863977e468f611ef118ebd01421289dd86ee1ae99cb068c3bce2b
COPY nginx.conf /etc/nginx/nginx.conf
COPY public/ /usr/share/nginx/html/
USER 101:101
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=4s --start-period=10s --retries=3 CMD wget -qO /dev/null http://127.0.0.1:8080/health || exit 1
CMD ["nginx", "-g", "daemon off;"]
