FROM node:20-bookworm-slim AS build
WORKDIR /workspace
ARG NEXT_PUBLIC_API_URL=http://api:4000/api
ARG NEXT_PUBLIC_WS_URL=http://api:4000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
COPY package.json package-lock.json ./
COPY apps/api/package.json apps/api/package.json
COPY apps/web/package.json apps/web/package.json
RUN npm ci
COPY apps/web apps/web
RUN npm --workspace @sentira/web run build

FROM node:20-bookworm-slim
WORKDIR /workspace/apps/web
ENV NODE_ENV=production PORT=3000
COPY --from=build /workspace/apps/web/package.json ./package.json
COPY --from=build /workspace/apps/web/.next ./.next
COPY --from=build /workspace/node_modules /workspace/node_modules
EXPOSE 3000
CMD ["node", "/workspace/node_modules/next/dist/bin/next", "start"]
