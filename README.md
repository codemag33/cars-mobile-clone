# cars-mobile-clone

Telegram-бот → FastAPI → Vue 3. Принимает Excel с продажами авто, парсит первый
лист, сохраняет в SQLite и публикует объявления на сайте в стиле mobile.de.

## Архитектура

```
Telegram user → aiogram bot → POST /api/cars → FastAPI → SQLite
                                                          ↓
                                          Vue 3 SPA ← GET /api/cars
```

## Структура

- `api/` — FastAPI backend (SQLModel + SQLite, дедуп по VIN).
- `bot/` — Telegram-бот на aiogram, парсит первый лист `.xlsx` через openpyxl.
- `frontend/` — Vue 3 + Vite SPA по шаблону mobile.de с фильтрами.
- `docker-compose.yml` — поднимает api + bot + frontend (через nginx) одной командой.

## Формат Excel

Парсер ищет в первых 10 строках листа строку-заголовок и сопоставляет колонки
по названию (русские и английские алиасы). Лишние колонки игнорируются,
порядок не важен.

**Обязательные колонки:** `Марка` / `Brand`, `Модель` / `Model`, `VIN`,
`Год выпуска` / `Year`, `Пробег` / `Mileage`, `Цена продажи` / `Price`.

**Опциональные:** `Топливо` / `Fuel`, `Коробка` / `Transmission`,
`Месторасположение` / `Location`.

Числа можно с единицами измерения — `"1 500 000 руб."`, `"2020 г."`,
`"150 000 км."` парсер чистит.

Дубликаты по `vin` пропускаются.

## Быстрый старт (без Docker)

### Backend

```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API доступно на <http://localhost:8000>, документация на <http://localhost:8000/docs>.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Сайт на <http://localhost:5173>.

### Telegram bot

```bash
cd bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export BOT_TOKEN=123456:ABC...   # токен от @BotFather
export API_BASE_URL=http://localhost:8000
python main.py
```

Отправьте боту `.xlsx` файл — он распарсит первый лист и зальёт авто в API.

## Быстрый старт (Docker, локально)

```bash
echo "BOT_TOKEN=123456:ABC..." > .env
docker compose up --build
```

- API: <http://localhost:8000>
- Frontend: <http://localhost:8080>

## Деплой на VPS с HTTPS

Используется отдельный overlay `docker-compose.prod.yml` с Caddy в качестве
reverse-proxy — он автоматически получает и продлевает TLS-сертификат от
Let's Encrypt.

Перед запуском:

1. Купите домен и направьте A-запись на IP вашего VPS.
2. Откройте порты 80 и 443 (`ufw allow 80,443/tcp`).
3. Установите Docker (`curl -fsSL https://get.docker.com | sudo sh`).

```bash
git clone https://github.com/codemag33/cars-mobile-clone.git
cd cars-mobile-clone

cat > .env <<EOF
BOT_TOKEN=123456:ABC...
ALLOWED_USER_IDS=
DOMAIN=cars.example.com
EOF

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Через 30-60 секунд сайт будет доступен по `https://cars.example.com`,
API — по `https://cars.example.com/api/cars`. Логи: `docker compose logs -f caddy`.

Обновление:

```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
