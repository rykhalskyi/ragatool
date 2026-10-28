# Stage 1: Build Angular
FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build -- --configuration production

# Stage 2: Nginx
FROM nginx:alpine

# Deploy-time configuration. API_URL is what the browser calls; the default is
# same-origin /api, which this nginx proxies to BACKEND_URL. No rebuild needed
# to move the app to another host.
ENV API_URL=/api
ENV BACKEND_URL=http://backend:8000

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.d/40-write-runtime-config.sh /docker-entrypoint.d/40-write-runtime-config.sh
RUN chmod +x /docker-entrypoint.d/40-write-runtime-config.sh

# copy all build output automatically
COPY --from=builder /app/dist/ragatouille/browser /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
