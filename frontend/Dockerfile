FROM node:20-alpine

WORKDIR /app
COPY package.json ./
RUN npm install

COPY . .

# Next.js resolves async rewrites() during `next build` and bakes the
# destination URL into the build manifest. The runtime env var is too late.
# Set it here so the build produces the correct internal proxy URL.
ARG INTERNAL_API_URL=http://api:8000
ENV INTERNAL_API_URL=${INTERNAL_API_URL}

RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
