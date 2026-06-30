FROM node:18-alpine

WORKDIR /workspace

COPY package*.json ./

RUN npm install --production

COPY . .

EXPOSE 8000

ENV PORT=8000
ENV NODE_ENV=production

CMD ["npm", "start"]
