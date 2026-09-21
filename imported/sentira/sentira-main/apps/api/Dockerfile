FROM node:20-bookworm-slim AS build
WORKDIR /workspace
COPY package.json package-lock.json ./
COPY apps/api/package.json apps/api/package.json
COPY apps/web/package.json apps/web/package.json
RUN npm ci
COPY apps/api apps/api
RUN npm --workspace @sentira/api run build

FROM node:20-bookworm-slim
WORKDIR /workspace
ENV NODE_ENV=production
COPY package.json package-lock.json ./
COPY apps/api/package.json apps/api/package.json
COPY apps/web/package.json apps/web/package.json
RUN npm ci --omit=dev
COPY --from=build /workspace/apps/api/dist apps/api/dist
EXPOSE 4000
CMD ["sh", "-c", "node node_modules/typeorm/cli.js migration:run -d apps/api/dist/data-source.js && node apps/api/dist/main.js"]
