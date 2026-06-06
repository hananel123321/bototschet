import asyncio
import os
import sqlite3
import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# =========================
# 🔑 TOKEN
# =========================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================
# 🗄 DATABASE
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
# 🧠 STATE
# =========================
user_state = {}
user_data = {}

# =========================
# 📌 MENU
# =========================
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Создать отсчёт")],
        [KeyboardButton(text="📋 Мои отсчёты")],
    ],
    resize_keyboard=True
)

# =========================
# 💾 DB
# =========================
def add_countdown(user_id, title, date):
    cursor.execute(
        "INSERT INTO countdowns (user_id, title, date) VALUES (?, ?, ?)",
        (user_id, title, date)
    )
    conn.commit()


def get_countdowns(user_id):
    cursor.execute(
        "SELECT id, title, date FROM countdowns WHERE user_id = ?",
        (user_id,)
    )
    return cursor.fetchall()


def delete_countdown(event_id):
    cursor.execute("DELETE FROM countdowns WHERE id = ?", (event_id,))
    conn.commit()


def update_countdown(event_id, title, date):
    cursor.execute(
        "UPDATE countdowns SET title = ?, date = ? WHERE id = ?",
        (title, date, event_id)
    )
    conn.commit()

# =========================
# ⏳ CALC
# =========================
def calc_days(date_str):
    today = datetime.datetime.now().date()
    target = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    return (target - today).days


def get_message(title, days):
    if days < 0:
        return None
    if days == 0:
        return f"⏰ Сегодня: {title}!"
    if days == 1:
        return f"⏰ Завтра: {title}"
    if days == 7:
        return f"📅 Осталась неделя до {title}"
    if days == 30:
        return f"📅 Остался месяц до {title}"
    return f"⏳ До {title} осталось {days} дней"

# =========================
# ⏰ DAILY 08:00
# =========================
async def daily_notifications():
    sent_today = False

    while True:
        now = datetime.datetime.now()

        if now.hour == 8 and not sent_today:

            today = now.date()

            cursor.execute("SELECT id, user_id, title, date FROM countdowns")
            rows = cursor.fetchall()

            for event_id, user_id, title, date_str in rows:
                try:
                    target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                    days_left = (target_date - today).days

                    text = get_message(title, days_left)

                    if text:
                        await bot.send_message(user_id, text)

                    if days_left < 0:
                        delete_countdown(event_id)

                except:
                    continue

            sent_today = True

        if now.hour != 8:
            sent_today = False

        await asyncio.sleep(30)

# =========================
# 🚀 START
# =========================
@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer("Привет! Я бот-отсчёт ⏳", reply_markup=menu)

# =========================
# 📋 LIST
# =========================
@dp.message(F.text == "📋 Мои отсчёты")
async def my_countdowns(message: Message):
    data = get_countdowns(message.from_user.id)

    if not data:
        await message.answer("Пока пусто 😄")
        return

    for event_id, title, date in data:

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="⏳", callback_data=f"time_{event_id}"),
                    InlineKeyboardButton(text="✏️", callback_data=f"edit_{event_id}"),
                    InlineKeyboardButton(text="🗑", callback_data=f"del_{event_id}")
                ]
            ]
        )

        await message.answer(f"📌 {title}\n📅 {date}", reply_markup=kb)

# =========================
# ⏳ TIME LEFT BUTTON
# =========================
@dp.callback_query(F.data.startswith("time_"))
async def time_left(callback: CallbackQuery):

    event_id = int(callback.data.split("_")[1])

    cursor.execute("SELECT title, date FROM countdowns WHERE id = ?", (event_id,))
    row = cursor.fetchone()

    if not row:
        await callback.answer("Не найдено")
        return

    title, date = row
    days = calc_days(date)

    if days < 0:
        text = f"❌ {title} уже прошло"
    elif days == 0:
        text = f"⏰ {title} сегодня!"
    elif days == 1:
        text = f"⏰ До {title} остался 1 день"
    else:
        text = f"⏳ До {title} осталось {days} дней"

    await callback.message.answer(text)
    await callback.answer()

# =========================
# 🗑 DELETE
# =========================
@dp.callback_query(F.data.startswith("del_"))
async def delete_cb(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])

    delete_countdown(event_id)

    await callback.message.edit_text("🗑 Удалено")
    await callback.answer()

# =========================
# ✏️ EDIT
# =========================
@dp.callback_query(F.data.startswith("edit_"))
async def edit_cb(callback: CallbackQuery):

    event_id = int(callback.data.split("_")[1])

    user_state[callback.from_user.id] = ("edit", event_id)

    await callback.message.answer("✏️ Введи: Название 2026-08-15")
    await callback.answer()

# =========================
# 📅 CREATE
# =========================
@dp.message(F.text == "📅 Создать отсчёт")
async def create_start(message: Message):

    user_state[message.from_user.id] = ("create_title", None)

    await message.answer("✏️ Введи название события:")

# =========================
# 💬 INPUT HANDLER
# =========================
@dp.message(F.text)
async def text_handler(message: Message):

    if message.text.startswith("/"):
        return

    user_id = message.from_user.id
    state = user_state.get(user_id)

    # ================= EDIT =================
    if state and state[0] == "edit":
        try:
            event_id = state[1]
            title, date = message.text.rsplit(" ", 1)

            update_countdown(event_id, title, date)

            user_state.pop(user_id, None)

            await message.answer("✅ Обновлено!")
        except:
            await message.answer("❌ Формат: Название 2026-08-15")

        return

    # ================= CREATE =================
    if state and state[0] == "create_title":
        user_data[user_id] = {"title": message.text}
        user_state[user_id] = ("create_date", None)

        years = [2026, 2027, 2028]

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=str(y), callback_data=f"year_{y}")]
                for y in years
            ]
        )

        await message.answer("📅 Выбери год:", reply_markup=kb)
        return

# =========================
# 📅 YEAR / MONTH / DAY
# =========================
@dp.callback_query(F.data.startswith("year_"))
async def year_cb(callback: CallbackQuery):

    user_id = callback.from_user.id
    user_data[user_id]["year"] = callback.data.split("_")[1]

    months = [f"{i:02d}" for i in range(1, 13)]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=m, callback_data=f"month_{m}")] for m in months]
    )

    await callback.message.edit_text("📆 Выбери месяц:", reply_markup=kb)
    await callback.answer()


@dp.callback_query(F.data.startswith("month_"))
async def month_cb(callback: CallbackQuery):

    user_id = callback.from_user.id
    user_data[user_id]["month"] = callback.data.split("_")[1]

    days = [f"{i:02d}" for i in range(1, 32)]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=d, callback_data=f"day_{d}")] for d in days]
    )

    await callback.message.edit_text("📆 Выбери день:", reply_markup=kb)
    await callback.answer()


@dp.callback_query(F.data.startswith("day_"))
async def day_cb(callback: CallbackQuery):

    user_id = callback.from_user.id
    day = callback.data.split("_")[1]

    data = user_data[user_id]

    date = f"{data['year']}-{data['month']}-{day}"

    add_countdown(user_id, data["title"], date)

    user_state.pop(user_id, None)
    user_data.pop(user_id, None)

    await callback.message.edit_text(
        f"✅ Сохранено!\n\n📌 {data['title']}\n📅 {date}"
    )

    await callback.answer()

# =========================
# ▶️ RUN
# =========================
async def main():
    asyncio.create_task(daily_notifications())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
