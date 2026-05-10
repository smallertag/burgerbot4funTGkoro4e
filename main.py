import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command

# Вставь сюда свой токен
TOKEN = "8498773512:AAFc2uI2kTyVBQGiFSCz11vdTOb5iutAiGk"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Список ПРЯМЫХ ссылок на картинки бургеров
# (Важно: ссылка должна вести на файл изображения, а не на страницу рецепта)
BURGER_IMAGES = [
    "https://ibb.co/5WhynKDd",
    "https://ibb.co/prf8pnJn",
    "https://ibb.co/ZzPwX1Z8"
]

# 1. Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я готов присылать бургеры и Соню. Просто напиши мне!")

# 2. Обработка слова "бургер"
@dp.message(F.text.lower().contains("бургер"))
async def send_burger(message: types.Message):
    random_burger = random.choice(BURGER_IMAGES)
    try:
        await message.answer_photo(
            photo=random_burger,
            caption="бургер🍔"
        )
    except Exception as e:
        await message.answer("Ошибка при загрузке бургера :(")
        logging.error(f"Burger error: {e}")

# 3. Обработка имени "Соня" и его форм по ссылке
@dp.message(F.text.lower().regexp(r"(соня|соне|соню|сонечка)"))
async def send_sonya(message: types.Message):
    # ПРЯМАЯ ссылка на твое фото (я взял ту, что ты скидывал ранее, в виде прямого линка)
    # Если эта ссылка перестанет работать, замени её на новую прямую ссылку
    sonya_direct_link = "https://i.ibb.co/ccb0JXwq/photo.jpg" 
    
    try:
        await message.answer_photo(
            photo=sonya_direct_link, 
            caption="соня"
        )
    except Exception as e:
        await message.answer("Не удалось загрузить фото Сони по ссылке. Проверь её актуальность!")
        logging.error(f"Sonya error: {e}")

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")