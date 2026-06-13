FROM node:20-alpine AS build

WORKDIR /app

COPY Frontend-MatchSummary-/package.json Frontend-MatchSummary-/package-lock.json ./
RUN npm ci

COPY Frontend-MatchSummary-/ ./

# URL relativ: request-urile trec prin nginx catre backend (fara CORS)
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

FROM nginx:1.27-alpine

COPY Frontend-MatchSummary-/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
