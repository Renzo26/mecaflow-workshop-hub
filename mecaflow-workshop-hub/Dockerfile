FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Descobre onde os assets estáticos foram gerados
RUN ls -la && (ls .output/public 2>/dev/null || ls dist 2>/dev/null || ls dist/client 2>/dev/null || true)

FROM nginx:alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copia assets estáticos — ajuste o caminho se o build gerar em outro lugar
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
