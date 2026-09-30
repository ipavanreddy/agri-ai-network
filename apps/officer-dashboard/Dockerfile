# Build context = repository root (pnpm workspace):
#   docker build -f apps/officer-dashboard/Dockerfile -t agri-ai-network-officer-dashboard .
# NEXT_PUBLIC_* values are inlined at build time from apps/officer-dashboard/.env.production, which
# infrastructure/cloud-run/deploy.sh generates (gitignored) just before the build.
FROM node:22-slim AS build
ENV PNPM_HOME=/pnpm PATH=/pnpm:$PATH NEXT_TELEMETRY_DISABLED=1
RUN corepack enable
WORKDIR /repo
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/officer-dashboard/package.json apps/officer-dashboard/
RUN pnpm install --frozen-lockfile --filter officer-dashboard
COPY apps/officer-dashboard apps/officer-dashboard
RUN pnpm --filter officer-dashboard build

FROM node:22-slim
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=8080 HOSTNAME=0.0.0.0
WORKDIR /app
COPY --from=build --chown=node:node /repo/apps/officer-dashboard/.next/standalone ./
COPY --from=build --chown=node:node /repo/apps/officer-dashboard/.next/static ./apps/officer-dashboard/.next/static
COPY --from=build --chown=node:node /repo/apps/officer-dashboard/public ./apps/officer-dashboard/public
USER node
EXPOSE 8080
CMD ["node", "apps/officer-dashboard/server.js"]
