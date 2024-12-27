import requests
from API_KEY import API_KEY
from datetime import datetime

def get_weather_data(latitude, longitude):
    try:
        # Получение locationKey по координатам
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

        # Извлечение данных
        dates = []
        temperatures = []
        humidities = []
        wind_speeds = []
        precip_probs = []

        for day in forecast_data["DailyForecasts"]:
            dates.append(datetime.fromtimestamp(day["EpochDate"]).strftime('%Y-%m-%d'))
            temperatures.append(round((day["Temperature"]["Minimum"]["Value"] + day["Temperature"]["Maximum"]["Value"]) / 2, 1))
            wind_speeds.append(day["Day"]["Wind"]["Speed"]["Value"])
            precip_probs.append(day["Day"]["PrecipitationProbability"])
            humidities.append(round((day["Day"]["RelativeHumidity"]["Minimum"] + day["Day"]["RelativeHumidity"]["Maximum"]) / 2))

        return {
            "Dates": dates,
            "Temperatures": temperatures,
            "Humidities": humidities,
            "Wind_speeds": wind_speeds,
            "Precip_probs": precip_probs
        }
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
        return None
    except KeyError as e:
        print(f"Ошибка обработки данных JSON: {e}")
        return None

def check_bad_weather(temperature, wind_speed, precipitation_probability):
    str_to_return = "Good"
    if temperature < 0 or temperature > 35 or wind_speed > 50 or precipitation_probability > 70:
        str_to_return = "Bad"
        if temperature < 0:
            str_to_return += ", слишком холодно"
        if temperature > 35:
            str_to_return += ", слишком жарко"
        if wind_speed > 50:
            str_to_return += ", слишком сильный ветер"
        if precipitation_probability > 70:
            str_to_return += ", слишком высокая вероятность осадков"
    return str_to_return