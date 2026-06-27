# Multi-stage: builda o frontend React e serve com nginx

# Stage 1: Build do frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Copia package.json e instala deps
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Copia código e builda
COPY frontend/ ./
RUN npm run build

# Stage 2: Nginx com estáticos + proxy
FROM nginx:alpine

# Remove config default
RUN rm /etc/nginx/conf.d/default.conf

# Copia config customizada
COPY infra/nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Copia build do frontend
COPY --from=builder /app/dist /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

EXPOSE 80
