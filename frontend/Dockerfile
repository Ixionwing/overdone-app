# syntax=docker/dockerfile:1

FROM node:22.19.0-bookworm-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22.19.0-bookworm-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ARG API_URL=http://api:8000
ENV API_URL=${API_URL}
RUN npm run build

FROM node:22.19.0-bookworm-slim AS runtime
WORKDIR /app
RUN groupadd --gid 1000 nodejs \
    && useradd --uid 1000 --gid nodejs --create-home nextjs
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
