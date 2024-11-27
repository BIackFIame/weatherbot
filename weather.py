# weather.py

import aiohttp
import logging
from config import settings
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from aiocache import cached, SimpleMemoryCache

logger = logging.getLogger(__name__)

@cached(ttl=600, cache=SimpleMemoryCache)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def get_weather(city_name: str, hours: int = 24) -> Optional[dict]:
    """
    Получает прогноз погоды по названию города на заданное количество часов.
    """
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'q': city_name,
            'units': 'metric',
            'lang': 'ru',
            'appid': settings.WEATHER_API_KEY
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                return data
    except Exception as e:
        logger.error(f"Ошибка при получении прогноза погоды для города {city_name}: {e}")
        return None
