FROM node:22-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Vite default port
EXPOSE 3000

CMD ["npm", "run", "dev"]
