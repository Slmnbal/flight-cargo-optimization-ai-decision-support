FROM node:20-alpine

# Bu, bir üretim (nginx + statik build) image'i DEĞİL -- geliştirme sunucusunu
# (Vite dev server, HMR dahil) konteyner içinde çalıştırıyor. Portföy projesinin
# bu aşamasında "docker compose up" ile tüm stack'i tek komutla ayağa kaldırmak
# yeterli; gerçek bir production build/deploy adımı ayrı bir iş.
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# --host 0.0.0.0: container dışından (host makineden, port mapping üzerinden)
# erişilebilmesi için -- Vite varsayılan olarak sadece localhost'u dinler.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
