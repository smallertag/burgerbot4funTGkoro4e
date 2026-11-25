
import asyncio
import logging
import random
import json
import sqlite3
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command

# ==========================================
# НАСТРОЙКИ
# ==========================================

TOKEN = "9140669630:AAG-dzTr5-VntMwj-1mqoI1YZoT7aehzhdc"

bot = Bot(token=TOKEN)
dp = Dispatcher()

MOSCOW_TZ = timezone(timedelta(hours=3))


# ==========================================
# 1. БУРГЕРЫ
# ==========================================

BURGER_IMAGES = [
    "https://ibb.co/5WhynKDd",
    "https://ibb.co/prf8pnJn",
    "https://ibb.co/ZzPwX1Z8"
]


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я готов присылать бургеры и Соню. Просто напиши мне!\n\n"
        "🃏 Новые команды:\n"
        "/roll — выбить карточку\n"
        "/cards — посмотреть альбом\n"
        "/inventory — посмотреть коллекцию\n"
        "/countdown — обратный отсчёт\n"
        "/weather — погода"
    )


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


# ==========================================
# 2. СОНЯ
# ==========================================

@dp.message(F.text.lower().regexp(r"(соня|соне|соню|сонечка)"))
async def send_sonya(message: types.Message):
    sonya_direct_link = "https://i.ibb.co/ccb0JXwq/photo.jpg"

    try:
        await message.answer_photo(
            photo=sonya_direct_link,
            caption="соня"
        )
    except Exception as e:
        await message.answer(
            "Не удалось загрузить фото Сони по ссылке. Проверь её актуальность!"
        )
        logging.error(f"Sonya error: {e}")


# ==========================================
# 3. ОТВЕТ НА ОПРЕДЕЛЁННЫЕ СЛОВА
# ==========================================

@dp.message(F.text.regexp(r"(?i)(?<!\w)(пидор|пидар|питар)(?!\w)"))
async def answer_insult(message: types.Message):
    await message.answer("нет ты")


# ==========================================
# 4. ОБРАТНЫЙ ОТСЧЁТ
# ==========================================

def get_next_date(month, day, now):
    target = now.replace(
        month=month,
        day=day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    if target <= now:
        target = target.replace(year=target.year + 1)

    return target


def format_countdown(target, now):
    difference = target - now
    total_seconds = int(difference.total_seconds())

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    return f"📅 {days} дн. {hours} ч. {minutes} мин."


def create_countdown():
    now = datetime.now(MOSCOW_TZ)

    events = [
        ("☀️ 1 июня", 6, 1),
        ("🎄 Новый год", 1, 1),
        ("🎒 1 сентября", 9, 1)
    ]

    result = "⏳ ОБРАТНЫЙ ОТСЧЁТ\n"
    result += "━━━━━━━━━━━━━━\n\n"

    for name, month, day in events:
        target = get_next_date(month, day, now)
        result += f"{name}\n"
        result += f"Осталось: {format_countdown(target, now)}\n\n"

    result += "━━━━━━━━━━━━━━\n"
    result += "🕒 Время московское"

    return result


@dp.message(Command("countdown"))
async def cmd_countdown(message: types.Message):
    await message.answer(create_countdown())


@dp.message(F.text.lower().contains("сколько осталось"))
async def countdown_text(message: types.Message):
    await message.answer(create_countdown())


# ==========================================
# 5. ПОГОДА
# ==========================================

WEATHER_CITIES = {
    "питер": {
        "name": "Санкт-Петербург",
        "latitude": 59.9343,
        "longitude": 30.3351
    },
    "спб": {
        "name": "Санкт-Петербург",
        "latitude": 59.9343,
        "longitude": 30.3351
    },
    "санкт-петербург": {
        "name": "Санкт-Петербург",
        "latitude": 59.9343,
        "longitude": 30.3351
    },
    "сестрорецк": {
        "name": "Сестрорецк",
        "latitude": 60.0980,
        "longitude": 29.9630
    },
    "кронштадт": {
        "name": "Кронштадт",
        "latitude": 59.9970,
        "longitude": 29.7660
    }
}


def get_weather_description(code):
    descriptions = {
        0: "Ясно ☀️",
        1: "Преимущественно ясно 🌤",
        2: "Переменная облачность ⛅",
        3: "Пасмурно ☁️",
        45: "Туман 🌫",
        48: "Изморозь 🌫",
        51: "Лёгкая морось 🌧",
        53: "Морось 🌧",
        55: "Сильная морось 🌧",
        61: "Небольшой дождь 🌧",
        63: "Дождь 🌧",
        65: "Сильный дождь 🌧",
        71: "Небольшой снег ❄️",
        73: "Снег ❄️",
        75: "Сильный снегопад 🌨",
        80: "Ливень 🌧",
        81: "Сильный ливень 🌧",
        82: "Очень сильный ливень ⛈",
        95: "Гроза ⛈",
        96: "Гроза с градом ⛈",
        99: "Сильная гроза ⛈"
    }

    return descriptions.get(code, "Неизвестная погода 🌡")


def fetch_weather(latitude, longitude):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
        "daily": "sunrise,sunset,temperature_2m_max,temperature_2m_min",
        "timezone": "Europe/Moscow",
        "forecast_days": 1
    }

    url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urllib.parse.urlencode(params)
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "TelegramWeatherBot"}
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


async def send_weather_for_city(message, city_key):
    city = WEATHER_CITIES[city_key]

    try:
        data = await asyncio.to_thread(
            fetch_weather,
            city["latitude"],
            city["longitude"]
        )

        current = data["current"]
        daily = data["daily"]

        temperature = current["temperature_2m"]
        feels_like = current["apparent_temperature"]
        wind = current["wind_speed_10m"]
        precipitation = current["precipitation"]
        code = current["weather_code"]

        description = get_weather_description(code)

        sunrise = daily["sunrise"][0].split("T")[1]
        sunset = daily["sunset"][0].split("T")[1]

        temp_max = daily["temperature_2m_max"][0]
        temp_min = daily["temperature_2m_min"][0]

        weather_message = (
            f"📍 {city['name']}\n"
            f"━━━━━━━━━━━━━━\n"
            f"{description}\n\n"
            f"🌡 Температура: {temperature}°C\n"
            f"🤔 Ощущается как: {feels_like}°C\n"
            f"📈 Максимум: {temp_max}°C\n"
            f"📉 Минимум: {temp_min}°C\n"
            f"💨 Ветер: {wind} км/ч\n"
            f"🌧 Осадки: {precipitation} мм\n\n"
            f"🌅 Восход солнца: {sunrise}\n"
            f"🌇 Закат солнца: {sunset}\n"
            f"━━━━━━━━━━━━━━\n"
            f"🕒 Время московское"
        )

        await message.answer(weather_message)

    except Exception as e:
        logging.error(f"Weather error: {e}")
        await message.answer(
            f"Не удалось получить погоду для {city['name']} 😢"
        )


@dp.message(Command("weather"))
async def cmd_weather(message: types.Message):
    text = message.text.lower()

    city_key = None

    for key in WEATHER_CITIES:
        if key in text:
            city_key = key
            break

    if city_key:
        await send_weather_for_city(message, city_key)
    else:
        await message.answer(
            "🌤 Выбирай город:\n\n"
            "/weather питер\n"
            "/weather сестрорецк\n"
            "/weather кронштадт\n\n"
            "Или просто /weather для прогноза во всех трёх городах."
        )

        for key in ["питер", "сестрорецк", "кронштадт"]:
            await send_weather_for_city(message, key)


@dp.message(F.text.lower().contains("погода"))
async def weather_text(message: types.Message):
    text = message.text.lower()

    city_key = None

    for key in WEATHER_CITIES:
        if key in text:
            city_key = key
            break

    if city_key:
        await send_weather_for_city(message, city_key)
    else:
        for key in ["питер", "сестрорецк", "кронштадт"]:
            await send_weather_for_city(message, key)


# ==========================================
# 6. КОЛЛЕКЦИОННЫЕ КАРТОЧКИ
# ==========================================

DB_NAME = "cards.db"
CARD_COOLDOWN = 12 * 60 * 60

CARDS = [
    {
        "id": "burger_1",
        "name": "Классический бургер",
        "rarity": "Обычная",
        "emoji": "🍔",
        "weight": 50,
        # КАРТИНКА 1
        "image": "https://ibb.co/S4hvP26j"
    },
    {
        "id": "burger_2",
        "name": "Чикен-бургер",
        "rarity": "Необычная",
        "emoji": "🍗",
        "weight": 25,
        # КАРТИНКА 2
        "image": "https://ibb.co/1GXzxPVd"
    },
    {
        "id": "burger_3",
        "name": "Двойной бургер",
        "rarity": "Редкая",
        "emoji": "🍔",
        "weight": 15,
        # КАРТИНКА 3
        "image": "https://ibb.co/CpJ84CCY"
    },
    {
        "id": "burger_4",
        "name": "Золотой бургер",
        "rarity": "Эпическая",
        "emoji": "✨",
        "weight": 7,
        # КАРТИНКА 4
        "image": "https://ibb.co/4ZsMzZ39"
    },
    {
        "id": "burger_5",
        "name": "Мистический бургер",
        "rarity": "Легендарная",
        "emoji": "🔥",
        "weight": 2,
        # КАРТИНКА 5
        "image": "https://ibb.co/HLLMs8bq"
    },
    {
        "id": "sonya",
        "name": "Соня",
        "rarity": "СЕКРЕТНАЯ",
        "emoji": "👑",
        "weight": 1,
        # КАРТИНКА СОНИ
        "image": "https://i.ibb.co/ccb0JXwq/photo.jpg"
    }
]


# ==========================================
# БАЗА ДАННЫХ КАРТОЧЕК
# ==========================================

def init_cards_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_cards (
                user_id INTEGER,
                card_id TEXT,
                amount INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, card_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS card_cooldowns (
                user_id INTEGER PRIMARY KEY,
                last_roll INTEGER
            )
        """)


def get_card_count(user_id, card_id):
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT amount FROM user_cards WHERE user_id = ? AND card_id = ?",
            (user_id, card_id)
        ).fetchone()

        return row[0] if row else 0


def add_card(user_id, card_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO user_cards (user_id, card_id, amount)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, card_id)
            DO UPDATE SET amount = amount + 1
        """, (user_id, card_id))


def get_inventory(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        rows = conn.execute(
            "SELECT card_id, amount FROM user_cards WHERE user_id = ?",
            (user_id,)
        ).fetchall()

        return dict(rows)


def get_last_roll(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT last_roll FROM card_cooldowns WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        return row[0] if row else 0


def set_last_roll(user_id, timestamp):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO card_cooldowns (user_id, last_roll)
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET last_roll = excluded.last_roll
        """, (user_id, timestamp))


# ==========================================
# ВЫБИВАНИЕ КАРТОЧКИ
# ==========================================

def get_random_card():
    return random.choices(
        CARDS,
        weights=[card["weight"] for card in CARDS],
        k=1
    )[0]


@dp.message(Command("roll"))
async def cmd_roll(message: types.Message):
    user_id = message.from_user.id
    now = int(datetime.now(timezone.utc).timestamp())

    last_roll = get_last_roll(user_id)
    remaining = CARD_COOLDOWN - (now - last_roll)

    if remaining > 0:
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60

        await message.answer(
            "⏳ Ты уже выбивал карточку!\n\n"
            f"Следующая попытка через: {hours} ч. {minutes} мин."
        )
        return

    card = get_random_card()
    previous_amount = get_card_count(user_id, card["id"])
    duplicate = previous_amount > 0

    add_card(user_id, card["id"])
    set_last_roll(user_id, now)

    if duplicate:
        result_text = "🔁 ПОВТОРКА! Такая карточка уже есть в твоей коллекции."
    else:
        result_text = "✨ НОВАЯ КАРТОЧКА! Поздравляем!"

    caption = (
        f"{card['emoji']} ТЕБЕ ВЫПАЛА КАРТОЧКА!\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"📌 Название: {card['name']}\n"
        f"💎 Редкость: {card['rarity']}\n\n"
        f"{result_text}\n"
        f"📦 Теперь у тебя таких: {previous_amount + 1}\n"
        f"━━━━━━━━━━━━━━\n"
        f"⏳ Следующая попытка через 12 часов"
    )

    image = card["image"]

    if image.startswith(("https://", "http://")) and "ВСТАВЬ_" not in image:
        try:
            await message.answer_photo(
                photo=image,
                caption=caption
            )
        except Exception as e:
            logging.error(f"Card image error: {e}")
            await message.answer(caption)
    else:
        await message.answer(caption)


# ==========================================
# ИНВЕНТАРЬ
# ==========================================

@dp.message(Command("inventory"))
async def cmd_inventory(message: types.Message):
    user_id = message.from_user.id
    inventory = get_inventory(user_id)

    if not inventory:
        await message.answer(
            "📦 Твоя коллекция пока пуста!\n\n"
            "Используй /roll, чтобы выбить первую карточку."
        )
        return

    result = "📦 ТВОЯ КОЛЛЕКЦИЯ\n"
    result += "━━━━━━━━━━━━━━\n\n"

    for card in CARDS:
        amount = inventory.get(card["id"], 0)

        if amount > 0:
            result += (
                f"{card['emoji']} {card['name']}\n"
                f"💎 {card['rarity']}\n"
                f"📦 Количество: {amount}\n\n"
            )

    result += "━━━━━━━━━━━━━━"
    await message.answer(result)


# ==========================================
# АЛЬБОМ КАРТОЧЕК
# ==========================================

@dp.message(Command("cards"))
async def cmd_cards(message: types.Message):
    user_id = message.from_user.id
    inventory = get_inventory(user_id)

    result = "🃏 КОЛЛЕКЦИОННЫЙ АЛЬБОМ\n"
    result += "━━━━━━━━━━━━━━\n\n"

    collected = 0

    for card in CARDS:
        amount = inventory.get(card["id"], 0)

        if amount > 0:
            collected += 1
            status = f"✅ Получена ({amount} шт.)"
        else:
            status = "🔒 Не получена"

        result += (
            f"{card['emoji']} {card['name']}\n"
            f"💎 {card['rarity']}\n"
            f"{status}\n\n"
        )

    result += (
        "━━━━━━━━━━━━━━\n"
        f"📊 Собрано: {collected}/{len(CARDS)} карточек\n"
        "🎲 Команда выбивания: /roll"
    )

    await message.answer(result)


# ==========================================
# 7. ЗАПУСК БОТА
# ==========================================

async def main():
    logging.basicConfig(level=logging.INFO)

    init_cards_db()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
