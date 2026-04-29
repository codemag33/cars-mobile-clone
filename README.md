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

Первый лист, опционально с заголовком в первой строке. Колонки:

| # | Поле | Пример |
|---|---|---|
| A | brand | BMW |
| B | model | X5 |
| C | price | 5600000 |
| D | year | 2020 |
| E | mileage | 45000 |
| F | fuel | Дизель |
| G | transmission | АКПП |
| H | vin | WBAFE41070LN12345 |
| I | location (опц.) | Москва |

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

## Быстрый старт (Docker)

```bash
echo "BOT_TOKEN=123456:ABC..." > .env
docker compose up --build
```

- API: <http://localhost:8000>
- Frontend: <http://localhost:8080>

Запуск через Docker
1. Установите Docker (если ещё нет)
Windows/Mac: Docker Desktop → https://www.docker.com/products/docker-desktop/
Linux (Ubuntu/Debian):

curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# перезайдите, чтобы применилось
Проверка: docker --version && docker compose version
2. Клонируйте репо и настройте токен

git clone https://github.com/codemag33/cars-mobile-clone.git
cd cars-mobile-clone
Создайте .env файл в корне репо с токеном вашего Telegram-бота (возьмите у @BotFather → /newbot):


cat > .env <<EOF
BOT_TOKEN=123456789:AAA-ваш-токен-от-BotFather
ALLOWED_USER_IDS=
EOF
Если хотите ограничить кто может грузить Excel — в ALLOWED_USER_IDS через запятую ваши Telegram user_id (узнать можно через @userinfobot). Пустое = любой пользователь.

3. Запустите одной командой

docker compose up --build



Поднимутся три контейнера:

api (FastAPI) → http://localhost:8000 (docs: http://localhost:8000/docs)
bot (aiogram, подключится к Telegram и начнёт слушать)
frontend (Vue + nginx) → http://localhost:8080




4. Как пользоваться
Откройте http://localhost:8080 в браузере — увидите пустой каталог.
В Telegram найдите вашего бота по имени (которое дали у BotFather) → /start.
Отправьте боту .xlsx файл с колонками: brand, model, price, year, mileage, fuel, transmission, vin, location.
Бот ответит «Создано N / дубликатов M», обновите страницу фронта — объявления появятся.





5. Остановка / очистка

docker compose down          # остановить

docker compose down -v       # остановить + удалить БД SQLite

docker compose logs -f bot   # посмотреть логи конкретного сервиса

docker compose up -d --build # запустить в фоне

Возможные проблемы
Порт 8080 или 8000 занят → поправьте в docker-compose.yml ("8888:80" вместо "8080:80").
Бот не отвечает → docker compose logs bot; чаще всего неверный BOT_TOKEN.
CORS ошибки на фронте → в production frontend проксирует /api/ на backend через nginx, всё должно работать из коробки. Если запускаете фронт на другом порту — проверьте frontend/nginx.conf.
