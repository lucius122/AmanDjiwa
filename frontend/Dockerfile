# Frontend AmanDjiwa: build Vite statis, lalu disajikan Caddy (sekaligus reverse proxy /api → backend).
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# API dipanggil di origin yang sama (/api -> backend lewat Caddy), jadi tanpa CORS.
ENV VITE_API_URL=/api
RUN npm run check:tokens && npm run build

FROM caddy:2-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv
