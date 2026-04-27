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
