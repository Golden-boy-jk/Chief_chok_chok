import aiohttp
import asyncio
from aiogram import Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from googletrans import Translator
from random import choices
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

translator = Translator()


# Конечный автомат для поиска рецептов
class RecipeStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_recipes = State()


# Команда для поиска случайных рецептов по категории
async def category_search_random(message: types.Message, state: FSMContext):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("Пожалуйста, укажите число после команды /category_search_random.")
        return

    num_recipes = int(args[1])
    await state.update_data(num_recipes=num_recipes)

    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.themealdb.com/api/json/v1/1/list.php?c=list") as resp:
            data = await resp.json()
            categories = [item['strCategory'] for item in data['meals']]

            # Создаем клавиатуру сразу с кнопками
            markup = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=category)] for category in categories],
                resize_keyboard=True
            )

    await message.answer("Выберите категорию рецептов:", reply_markup=markup)
    await state.set_state(RecipeStates.waiting_for_category)


# Обработчик выбора категории
async def category_selected(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    num_recipes = user_data.get("num_recipes")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?c={message.text}") as resp:
            data = await resp.json()
            meals = choices(data['meals'], k=num_recipes)
            meal_ids = [meal['idMeal'] for meal in meals]
            meal_names = [translator.translate(meal['strMeal'], dest='ru').text for meal in meals]

            await state.update_data(meal_ids=meal_ids)

            recipes_message = "\n".join(meal_names)
            await message.answer(
                f"Рецепты:\n{recipes_message}\n\nНажмите 'Получить рецепты', чтобы увидеть полный список.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="Получить рецепты")]],
                    resize_keyboard=True
                ))

    await state.set_state(RecipeStates.waiting_for_recipes)


# Обработчик, выводящий список рецептов
async def display_recipes(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    meal_ids = user_data.get("meal_ids")

    async with aiohttp.ClientSession() as session:
        tasks = [session.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}") for meal_id in meal_ids]
        responses = await asyncio.gather(*tasks)

        for resp in responses:
            data = await resp.json()
            meal = data['meals'][0]

            recipe_text = translator.translate(meal['strInstructions'], dest='ru').text
            ingredients = [f"{meal[f'strIngredient{i}']} - {meal[f'strMeasure{i}']}" for i in range(1, 21) if
                           meal[f'strIngredient{i}']]

            ingredients_text = translator.translate(", ".join(ingredients), dest='ru').text
            await message.answer(f"{meal['strMeal']}\n\nРецепт:\n{recipe_text}\n\nИнгредиенты:\n{ingredients_text}")

    await state.clear()


# Регистрация всех обработчиков
def register_handlers(dp: Dispatcher):
    dp.message.register(category_search_random, Command("category_search_random"))
    dp.message.register(category_selected, RecipeStates.waiting_for_category)
    dp.message.register(display_recipes, RecipeStates.waiting_for_recipes)
