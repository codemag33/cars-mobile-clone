"""Telegram bot: receive .xlsx, parse first sheet, push cars to API."""

from __future__ import annotations

import asyncio
import logging
import os

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Document, Message

from parser import parse_excel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ALLOWED_USER_IDS = {
    int(uid) for uid in os.getenv("ALLOWED_USER_IDS", "").split(",") if uid.strip().isdigit()
}

dp = Dispatcher()


def _format_api_error(resp: "httpx.Response", payload: list[dict]) -> str:
    """Turn a FastAPI validation error into something humans can read."""
    try:
        body = resp.json()
    except ValueError:
        return resp.text[:500] or "пустой ответ"

    detail = body.get("detail") if isinstance(body, dict) else body
    if not isinstance(detail, list):
        return str(detail)[:500]

    lines: list[str] = []
    for err in detail[:10]:
        loc = err.get("loc", [])
        row_idx = loc[1] if len(loc) > 1 and isinstance(loc[1], int) else None
        field = ".".join(str(p) for p in loc[2:]) or "<root>"
        msg = err.get("msg", "invalid")
        bad_value = ""
        if row_idx is not None and row_idx < len(payload):
            bad_value = f" (получили: {payload[row_idx].get(field)!r})"
        row_label = f"строка {row_idx + 1}" if row_idx is not None else "payload"
        lines.append(f"{row_label} · {field}: {msg}{bad_value}")
    if len(detail) > 10:
        lines.append(f"...и ещё {len(detail) - 10} ошибок")
    return "\n".join(lines)


@dp.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(
        "Привет! Пришлите мне `.xlsx` файл с продажами авто — "
        "я распарсю первый лист и опубликую объявления на сайте.\n\n"
        "Ожидаемые колонки: brand, model, price, year, mileage, fuel, "
        "transmission, vin, location.",
        parse_mode="Markdown",
    )


@dp.message(F.document)
async def on_document(message: Message, bot: Bot) -> None:
    if ALLOWED_USER_IDS and (message.from_user is None or message.from_user.id not in ALLOWED_USER_IDS):
        await message.answer("⛔ У вас нет прав загружать файлы.")
        return

    document: Document = message.document  # type: ignore[assignment]
    if not document.file_name or not document.file_name.lower().endswith(".xlsx"):
        await message.answer("Пришлите файл с расширением .xlsx")
        return

    status_msg = await message.answer("⏳ Скачиваю и парсю файл...")

    file = await bot.get_file(document.file_id)
    if file.file_path is None:
        await status_msg.edit_text("Не удалось получить путь к файлу.")
        return
    buf = await bot.download_file(file.file_path)
    if buf is None:
        await status_msg.edit_text("Не удалось скачать файл.")
        return

    data = buf.read()
    parsed = parse_excel(data)

    if not parsed.cars:
        err_text = "\n".join(parsed.errors[:10]) or "пустой файл"
        await status_msg.edit_text(f"❌ Не нашёл валидных строк.\n\n{err_text}")
        return

    payload = [car.to_payload() for car in parsed.cars]

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/api/cars/bulk", json=payload)
        except httpx.HTTPError as exc:
            logger.exception("API call failed")
            await status_msg.edit_text(f"❌ Ошибка обращения к API: {exc}")
            return

    if resp.status_code >= 400:
        detail = _format_api_error(resp, payload)
        logger.error("API %s: %s", resp.status_code, resp.text)
        await status_msg.edit_text(
            f"❌ API вернул {resp.status_code}.\n\n{detail}"[:4000]
        )
        return

    body = resp.json()
    summary_lines = [
        f"✅ Готово!",
        f"Создано: {body.get('created', 0)}",
        f"Дубликатов пропущено: {body.get('skipped_duplicates', 0)}",
    ]
    if parsed.errors:
        summary_lines.append(f"Невалидных строк в файле: {len(parsed.errors)}")
    if body.get("invalid"):
        summary_lines.append(f"Отклонено API: {body['invalid']}")
    await status_msg.edit_text("\n".join(summary_lines))


async def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN env var is required")
    bot = Bot(token=BOT_TOKEN)
    logger.info("Bot starting, API at %s", API_BASE_URL)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
