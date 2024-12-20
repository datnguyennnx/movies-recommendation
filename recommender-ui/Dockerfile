# Use the official Bun image
FROM oven/bun:1 as base
WORKDIR /app

# Install dependencies
FROM base AS install
COPY package.json bun.lockb ./
RUN bun install --frozen-lockfile

# Build the application
FROM base AS build
COPY --from=install /app/node_modules ./node_modules
COPY . .
RUN bun run build

# Production image
FROM base AS release
COPY .env.local .env.local 
COPY --from=install /app/node_modules ./node_modules
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY --from=build /app/package.json .
COPY --from=build /app/next.config.mjs .

# Run the app
USER bun
EXPOSE 3000
CMD ["bun", "run", "start"]