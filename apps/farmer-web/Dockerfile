# Build context = repository root (pnpm workspace):
#   docker build -f apps/farmer-web/Dockerfile -t agri-ai-network-farmer-web .
# NEXT_PUBLIC_* values are inlined at build time from apps/farmer-web/.env.production, which
# infrastructure/cloud-run/deploy.sh generates (gitignored) just before the build.
FROM node:22-slim AS build
ENV PNPM_HOME=/pnpm PATH=/pnpm:$PATH NEXT_TELEMETRY_DISABLED=1
RUN corepack enable
WORKDIR /repo
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/farmer-web/package.json apps/farmer-web/
RUN pnpm install --frozen-lockfile --filter farmer-web
COPY apps/farmer-web apps/farmer-web
RUN pnpm --filter farmer-web build

FROM node:22-slim
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=8080 HOSTNAME=0.0.0.0
WORKDIR /app
COPY --from=build --chown=node:node /repo/apps/farmer-web/.next/standalone ./
COPY --from=build --chown=node:node /repo/apps/farmer-web/.next/static ./apps/farmer-web/.next/static
COPY --from=build --chown=node:node /repo/apps/farmer-web/public ./apps/farmer-web/public
USER node
EXPOSE 8080
CMD ["node", "apps/farmer-web/server.js"]
