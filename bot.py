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

@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer("Привет! Я бот-отсчёт ⏳")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
