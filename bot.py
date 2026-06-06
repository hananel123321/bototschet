from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram import F
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден")

bot = Bot(token=TOKEN)
dp = Dispatcher()

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Создать отсчёт")],
        [KeyboardButton(text="📋 Мои отсчёты")],
    ],
    resize_keyboard=True
)

@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer(
        "Привет! Я бот-отсчёт ⏳\nВыбери действие:",
        reply_markup=menu
    )

@dp.message(F.text == "📅 Создать отсчёт")
async def create_countdown(message: Message):
    await message.answer("Ок 👍 напиши в формате:\n\nНазвание ГГГГ-ММ-ДД\n\nПример:\nПолёт 2026-08-15")


@dp.message(F.text == "📋 Мои отсчёты")
async def my_countdowns(message: Message):
    await message.answer("Пока тут пусто 😄\nСкоро добавим сохранение!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


