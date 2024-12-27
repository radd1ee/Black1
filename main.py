from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ErrorEvent
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
import requests
import logging
import asyncio
from datetime import datetime
from API import API_TOKEN
from API_KEY import API_KEY

logging.basicConfig(level=logging.INFO)

API_TOKEN = API_TOKEN
HELP_COMMAND = """
Список доступных команд:
/start - начать сессию с ботом
/help - получить помощь
/weather - используется для прогноза погоды
"""

button_about = KeyboardButton(text="О боте")
button_help = KeyboardButton(text="/help")
button_weather = KeyboardButton(text="/weather")
reply_keyboard = ReplyKeyboardMarkup(keyboard=[[button_about], [button_help], [button_weather]], resize_keyboard=True)

button_day1 = InlineKeyboardButton(text="1 день", callback_data="1")
button_day2 = InlineKeyboardButton(text="2 дня", callback_data="2")
button_day3 = InlineKeyboardButton(text="3 дня", callback_data="3")
button_day4 = InlineKeyboardButton(text="4 дня", callback_data="4")
button_day5 = InlineKeyboardButton(text="5 дней", callback_data="5")
inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_day1], [button_day2], [button_day3], [button_day4], [button_day5]])

button_done = KeyboardButton(text="Получить прогноз")
reply_keyboard_done = ReplyKeyboardMarkup(keyboard=[[button_done]], resize_keyboard=True)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher()

router = Router()

dp.include_router(router)

class UserInfo(StatesGroup):
    waiting_for_latitude = State()
    waiting_for_longitude = State()
    waiting_for_days = State()

user_data = {}

@dp.message(F.text == '/start')
async def start_command(message: types.Message):
    await message.answer("Добро пожаловать в бота для прогноза погоды!", reply_markup=reply_keyboard)
    await message.delete()

@dp.message(F.text == '/help')
async def help_command(message: types.Message):
    await message.answer(HELP_COMMAND)
    await message.delete()

@dp.message(F.text == 'О боте')
async def about_command(message: types.Message):
    await message.answer("Это бот написанный студентом Центрального университета, который может отправлять запросы погоды")
    await message.delete()

@dp.message(F.text == '/weather')
async def weather_command(message: types.Message, state: FSMContext):
    await message.answer("Введите широту:")
    await message.delete()
    await state.set_state(UserInfo.waiting_for_latitude)

@dp.message(F.text == 'Получить прогноз')
async def done_command(message: types.Message):
    try:
        data = user_data[message.from_user.id]
        latitude = data["latitude"]
        longitude = data["longitude"]
        location_url = "http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
        location_params = {
            "apikey": API_KEY,
            "q": f"{latitude},{longitude}",
            "language": "ru-ru"
        }
        response = requests.get(location_url, params=location_params)
        response.raise_for_status()
        location_data = response.json()
        location_key = location_data["Key"]

        # Получение прогноза на 5 дней
        forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/5day/{location_key}"
        forecast_params = {
            "apikey": API_KEY,
            "language": "ru-ru",
            "details": True,
            "metric": True
        }
        response = requests.get(forecast_url, params=forecast_params)
        response.raise_for_status()
        forecast_data = response.json()

        dates = []
        temperatures = []
        humidities = []
        wind_speeds = []
        precip_probs = []

        for day in forecast_data["DailyForecasts"]:
            dates.append(datetime.fromtimestamp(day["EpochDate"]).strftime('%Y-%m-%d'))
            temperatures.append(
                round((day["Temperature"]["Minimum"]["Value"] + day["Temperature"]["Maximum"]["Value"]) / 2, 1))
            wind_speeds.append(day["Day"]["Wind"]["Speed"]["Value"])
            precip_probs.append(day["Day"]["PrecipitationProbability"])
            humidities.append(
                round((day["Day"]["RelativeHumidity"]["Minimum"] + day["Day"]["RelativeHumidity"]["Maximum"]) / 2))

        info = {
            "Даты": dates,
            "Температуры": temperatures,
            "Влажность": humidities,
            "Скорость ветра": wind_speeds,
        }
        formatted_message = "Прогноз погоды:\n"
        for key, value in info.items():
            formatted_message += f"{key} - {value[:days]}\n"
        try:
            await message.reply(formatted_message)
            logging.info("List sent to user.")
        except Exception as e:
            logging.error(f"Error sending list message: {e}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при запросе к API: {e}")
    except KeyError as e:
        logging.error(f"Ошибка обработки данных JSON: {e}")

@dp.message(UserInfo.waiting_for_latitude)
async def process_first_city(message: types.Message, state: FSMContext):
    latitude = message.text
    await state.update_data(latitude=latitude)
    await message.reply("Теперь долготу:")
    await state.set_state(UserInfo.waiting_for_longitude)

@dp.message(UserInfo.waiting_for_longitude)
async def process_second_city(message: types.Message, state: FSMContext):
    longitude = message.text
    data = await state.get_data()
    latitude = data.get('latitude')
    user_id = message.from_user.id
    user_data[user_id] = {"latitude": latitude, "longitude": longitude}
    await message.answer(f"Отлично! Широта {latitude}, Долгота: {longitude}", reply_markup=inline_keyboard)
    await state.set_state(UserInfo.waiting_for_days)

@dp.callback_query(UserInfo.waiting_for_days)
async def process_days(callback: types.CallbackQuery, state: FSMContext):
    global days
    days = int(callback.data)
    await callback.message.answer(f"Количество дней: {days}", reply_markup=reply_keyboard_done)
    await callback.answer()

@dp.errors()
async def handle_error(event: ErrorEvent):
    logging.error(f'Произошла ошибка: {event.exception}')
    if event.update.message:
        await event.update.message.answer('Извините, произошла ошибка.')

if __name__ == '__main__':
    try:
        asyncio.run(dp.start_polling(bot))
    except Exception as e:
        logging.error(f'Ошибка при запуске бота: {e}')