import asyncio
import logging
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import FSInputFile

# Вставь сюда свой токен
TOKEN = "8498773512:AAFc2uI2kTyVBQGiFSCz11vdTOb5iutAiGk"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Список ссылок на бургеры
BURGER_IMAGES = [
    "https://kartinki.pics/uploads/posts/2021-03/1616053331_17-p-prizrachnii-burger-krasivo-19.jpg",
    "https://pikuco.ru/upload/test_stable/641/64169720b0051.webp",
    "https://i.pinimg.com/originals/74/45/8d/74458d601b3e86f8742548842142999d.jpg"
]

# 1. Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я готов присылать бургеры и Соню. Просто напиши мне!")

# 2. Обработка слова "бургер"
@dp.message(F.text.lower().contains("бургер"))
async def send_burger(message: types.Message):
    random_burger = random.choice(BURGER_IMAGES)
    await message.answer_photo(
        photo=random_burger,
        caption="Вот твой сочный бургер! 🍔"
    )

# 3. Обработка имени "Соня" и его форм
@dp.message(F.text.lower().regexp(r"(соня|соне|соню|сонечк)"))
async def send_sonya(message: types.Message):
    # Автоматическое определение пути к файлу в папке со скриптом
    current_dir = os.path.dirname(__file__)
    img_path = os.path.join(current_dir, "sonya.jpg")
    
    if os.path.exists(img_path):
        photo = FSInputFile(img_path)
        await message.answer_photo(
            photo=photo, 
            caption="Лови фото Сони! ✨"
        )
    else:
        # Если файл не найден, бот напишет, где именно он его искал
        await message.answer(f"Файл не найден. Я искал его тут:\n`{img_path}`", parse_mode="Markdown")

# 4. Эхо-ответ на все остальные сообщения
@dp.message()
async def echo_message(message: types.Message):
    # Если в сообщении нет текста (например, стикер), message.text будет None
    if message.text:
        await message.reply(f"Ты написал: {message.text}. Но я жду слово 'бургер' или 'Соня'!")

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    # Удаляем вебхуки перед запуском (полезно, если бот завис)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")