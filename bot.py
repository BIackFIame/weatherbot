# bot.py

import asyncio
import logging
import sys
import logging.handlers  # Для RotatingFileHandler
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiolimiter import AsyncLimiter
from datetime import datetime
import pytz

from config import settings
from database import Database
from middlewares import DatabaseMiddleware, RateLimitMiddleware
from handlers import router
from weather import get_weather

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s:%(name)s:%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.handlers.RotatingFileHandler('bot.log', maxBytes=1_000_000, backupCount=5)  # Исправлено здесь
    ]
)

logger = logging.getLogger(__name__)

# Часовой пояс Москвы
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

async def send_weather_update(db_pool, bot: Bot):
    try:
        now = datetime.now(MOSCOW_TZ).time().replace(second=0, microsecond=0)
        logger.info(f"Выполнение запланированной задачи на время: {now.strftime('%H:%M')}")

        async with db_pool.acquire() as conn:
            rows = await conn.fetch('SELECT user_id, city FROM users WHERE notification_time = $1', now)
            logger.info(f"Найдено {len(rows)} пользователей для уведомления.")

            for row in rows:
                user_id = row['user_id']
                city = row['city']
                logger.info(f"Отправка прогноза погоды пользователю {user_id} для города {city}.")
                weather_data = await get_weather(city, hours=24)
                if weather_data:
                    forecast_message = f"Прогноз погоды для {city} на ближайшие 24 часа:\n"
                    forecasts = weather_data.get('list', [])[:8]  # 8 прогнозов (3 часа)

                    for forecast in forecasts:
                        dt_txt = forecast['dt_txt']
                        temp = forecast['main']['temp']
                        description = forecast['weather'][0]['description']
                        forecast_message += f"{dt_txt}: {temp}°C, {description}\n"

                    await bot.send_message(user_id, forecast_message)
                    logger.info(f"Отправлен прогноз погоды пользователю {user_id}")
                else:
                    await bot.send_message(user_id, "Не удалось получить данные о погоде.")
                    logger.warning(f"Не удалось получить данные о погоде для города: {city}")
    except Exception as e:
        logger.error(f"Ошибка при выполнении запланированной задачи: {e}")

async def main():
    # Инициализация базы данных
    db = Database()
    await db.connect()

    # Инициализация бота
    bot = Bot(token=settings.TELEGRAM_TOKEN, parse_mode='HTML')
    dp = Dispatcher()

    # Настройка middleware
    limiter = AsyncLimiter(5, 60)  # 5 запросов в минуту на пользователя
    db_middleware = DatabaseMiddleware(db)
    rate_limit_middleware = RateLimitMiddleware(limiter)
    dp.message.middleware(db_middleware)
    dp.callback_query.middleware(db_middleware)
    dp.message.middleware(rate_limit_middleware)
    dp.callback_query.middleware(rate_limit_middleware)

    # Регистрируем роутеры
    dp.include_router(router)

    # Настройка планировщика
    scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)
    scheduler.add_job(send_weather_update, 'cron', minute='*', args=[db.pool, bot])
    scheduler.start()
    logger.info("Планировщик задач запущен.")

    try:
        logger.info("Запуск бота")
        await dp.start_polling(bot)
    finally:
        await bot.close()
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
