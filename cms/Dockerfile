FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# NOTE: 5180 is the deliberately non-default port for the CMS (usual Vite default is 5173)
EXPOSE 5180

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
