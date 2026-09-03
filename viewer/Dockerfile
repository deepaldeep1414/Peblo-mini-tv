FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# NOTE: 5190 is the deliberately non-default port for the Viewer (usual Vite default is 5173)
EXPOSE 5190

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
