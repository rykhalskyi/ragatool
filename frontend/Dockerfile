# Stage 1: Build Angular
FROM node:20-slim AS builder

WORKDIR /app

ARG API_URL=http://backend:4301

COPY package*.json ./
RUN npm ci

COPY . .

# Replace apiUrl in environment.ts (safe version)
RUN sed -i "s|apiUrl: '.*'|apiUrl: '${API_URL}'|" \
    src/environments/environment.ts

RUN npm run build -- --configuration production

# Stage 2: Nginx
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf

# copy all build output automatically
COPY --from=builder /app/dist/ragatouille/browser /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
