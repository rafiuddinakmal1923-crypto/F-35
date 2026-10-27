# Build the React app, serve it with nginx behind the proxy service.
FROM node:20-alpine AS build
WORKDIR /web
COPY package.json package-lock.json ./
# npm can crash yet exit 0 on a flaky network ("Exit handler never called"): check the install really worked.
RUN npm ci --no-audit --no-fund && test -x node_modules/.bin/vite || (echo "npm ci failed: check the network or proxy and rebuild" && exit 1)
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /web/dist /usr/share/nginx/html
