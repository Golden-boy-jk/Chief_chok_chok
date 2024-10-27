# bot_main.py
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage  # Импортируем MemoryStorage
from token_data import BOT_TOKEN
from recipes_handler import register_handlers

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())  # Используем MemoryStorage для FSM

# Регистрация обработчиков из файла recipes_handler.py
register_handlers(dp)

# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Привет! Я бот, который поможет вам найти рецепты. Используйте команду /category_search_random <число рецептов> для поиска рецептов по категории."
    )

# Запуск бота в режиме polling
if __name__ == '__main__':
    dp.run_polling(bot)
