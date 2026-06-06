import asyncio
import os
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# =========================
# 🔑 TOKEN
# =========================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================
# 🗄 SQLite база
# =========================
conn = sqlite3.connect("countdowns.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS countdowns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    date TEXT
)
""")

conn.commit()

# =========================
# 📌 Клавиатура
# =========================
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Создать отсчёт")],
        [KeyboardButton(text="📋 Мои отсчёты")],
    ],
    resize_keyboard=True
)

# =========================
# 💾 БД функции
# =========================
def add_countdown(user_id: int, title: str, date: str):
    cursor.execute(
        "INSERT INTO countdowns (user_id, title, date) VALUES (?, ?, ?)",
        (user_id, title, date)
    )
    conn.commit()


def get_countdowns(user_id: int):
    cursor.execute(
        "SELECT title, date FROM countdowns WHERE user_id = ?",
        (user_id,)
    )
    return cursor.fetchall()

# =========================
# 🚀 START
# =========================
@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer(
        "Привет! Я бот-отсчёт ⏳\nВыбери действие:",
        reply_markup=menu
    )

# =========================
# 📅 КНОПКА СОЗДАНИЯ
# =========================
@dp.message(F.text == "📅 Создать отсчёт")
async def create_countdown(message: Message):
    await message.answer(
        "Напиши в формате:\n\nНазвание ГГГГ-ММ-ДД\n\nПример:\nПолёт 2026-08-15"
    )

# =========================
# 📋 МОИ ОТСЧЁТЫ (ФИКС)
# =========================
@dp.message(F.text == "📋 Мои отсчёты")
async def my_countdowns(message: Message):
    data = get_countdowns(message.from_user.id)

    if not data:
        await message.answer("Пока тут пусто 😄")
        return

    text = "📋 Твои отсчёты:\n\n"
    for title, date in data:
        text += f"📌 {title} — {date}\n"

    await message.answer(text)

# =========================
# 💬 ВВОД ОТСЧЁТА (ИСПРАВЛЕННЫЙ)
# =========================
@dp.message(F.text)
async def handle_input(message: Message):

    # ❌ игнорируем кнопки и команды
    if message.text.startswith("/"):
        return

    if message.text in ["📋 Мои отсчёты", "📅 Создать отсчёт"]:
        return

    # ✅ сохраняем формат: "Название 2026-08-15"
    if " " in message.text:
        try:
            title, date = message.text.rsplit(" ", 1)

            add_countdown(message.from_user.id, title, date)

            await message.answer(
                f"✅ Отсчёт сохранён!\n\n📌 {title}\n📅 {date}"
            )
        except:
            await message.answer(
                "❌ Ошибка формата.\nПример:\nПолёт 2026-08-15"
            )

# =========================
# ▶️ RUN
# =========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
