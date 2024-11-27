# handlers.py

from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from typing import Optional, Dict, Any
from keyboards import get_commands_keyboard 

import asyncpg
from weather import get_weather
import logging
import re

logger = logging.getLogger(__name__)

router = Router()

# CallbackData для команды /help
class HelpCallback(CallbackData, prefix='help'):
    command_name: str

# CallbackData для выбора города
class CityCallback(CallbackData, prefix='city'):
    city_name: str

# Определение состояний FSM для редактирования
class EditNotificationStates(StatesGroup):
    waiting_for_new_data = State()


def parse_time_and_city(input_str: str) -> Optional[Dict[str, Any]]:
    pattern = r'^(\d{2}):(\d{2}),\s*(.+)$'
    match = re.match(pattern, input_str)
    if match:
        hours, minutes, city = match.groups()
        hours = int(hours)
        minutes = int(minutes)
        if 0 <= hours < 24 and 0 <= minutes < 60 and city.strip():
            from datetime import time
            return {'time': time(hour=hours, minute=minutes), 'city': city.strip()}
    return None


# Обработчик команды /start
@router.message(CommandStart())
async def send_welcome(message: Message):
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer(
        "Привет! Я бот, который может отправлять прогноз погоды.\n"
        "Используй /set для настройки времени отправки уведомлений о погоде,\n"
        "либо просто отправь название города для получения прогноза.",
        reply_markup=get_commands_keyboard()
    )

# Обработчик команды /help с инлайн-кнопками
@router.message(Command(commands=['help']))
async def send_help(message: Message):
    logger.info(f"Получена команда /help от пользователя {message.from_user.id}")
    
    # Создаём инлайн-клавиатуру с кнопками для каждой команды
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="/start", callback_data=HelpCallback(command_name="start").pack())],
        [InlineKeyboardButton(text="/help", callback_data=HelpCallback(command_name="help").pack())],
        [InlineKeyboardButton(text="/set", callback_data=HelpCallback(command_name="set").pack())],
        [InlineKeyboardButton(text="/forecast", callback_data=HelpCallback(command_name="forecast").pack())],
        [InlineKeyboardButton(text="/edit", callback_data=HelpCallback(command_name="edit").pack())],
        [InlineKeyboardButton(text="/clear", callback_data=HelpCallback(command_name="clear").pack())],
        [InlineKeyboardButton(text="/list", callback_data=HelpCallback(command_name="list").pack())],
        [InlineKeyboardButton(text="/delete", callback_data=HelpCallback(command_name="delete").pack())],
    ])
    
    await message.answer("Выберите команду для получения информации:", reply_markup=keyboard)

# Обработчик нажатий на кнопки помощи
@router.callback_query(HelpCallback.filter())
async def help_command_selected(callback_query: CallbackQuery, callback_data: HelpCallback, db: asyncpg.pool.Pool):
    command = callback_data.command_name

    help_texts = {
        "start": (
            "/start - Начать работу с ботом.\n"
            "Используйте эту команду для инициализации взаимодействия с ботом."
        ),
        "help": (
            "/help - Получить справку.\n"
            "Отображает список доступных команд и их описание."
        ),
        "set": (
            "/set - Установить время отправки уведомлений о погоде.\n"
            "Формат ввода: `/set HH:MM, Название города` (например, `/set 09:30, Москва`)."
        ),
        "forecast": (
            "/forecast - Получить прогноз погоды.\n"
            "Выберите город из списка или отправьте название города для получения прогноза."
        ),
        "edit": (
            "/edit - Изменить время или город для уведомлений о погоде.\n"
            "Используйте команду `/edit` и следуйте инструкциям."
        ),
        "clear": (
            "/clear - Очистить все настройки уведомлений о погоде.\n"
            "После выполнения этой команды вы больше не будете получать уведомления о погоде."
        ),
        "list": (
            "/list - Просмотреть все ваши уведомления о погоде."
        ),
        "delete": (
            "/delete - Удалить конкретное уведомление о погоде.\n"
            "Используйте команду `/delete` и следуйте инструкциям."
        )
    }

    help_text = help_texts.get(command, "Неизвестная команда.")

    await callback_query.message.answer(help_text)
    await callback_query.answer()

# Обработчик команды /set с аргументами
@router.message(Command(commands=['set']))
async def set_notification_time_and_city(message: Message, db: asyncpg.pool.Pool):
    logger.info(f"Получена команда /set от пользователя {message.from_user.id}: {message.text}")
    user_input = message.text[4:].strip()  # Извлекаем текст после "/set"

    if not user_input:
        await message.answer(
            "Пожалуйста, используйте команду в формате: `/set HH:MM, Название города` (например, `/set 09:30, Москва`).",
            parse_mode="Markdown"
        )
        return

    parsed = parse_time_and_city(user_input)
    if parsed:
        user_id = message.from_user.id
        notification_time = parsed['time']
        city = parsed['city']
        logger.info(f"Добавление нового уведомления для пользователя {user_id}: город {city}, время {notification_time}")

        await db.execute('''
            INSERT INTO users (user_id, city, notification_time)
            VALUES ($1, $2, $3)
        ''', user_id, city, notification_time)

        await message.answer(
            f"Новое уведомление добавлено: прогноз погоды для города {city} каждый день в {notification_time.strftime('%H:%M')} по московскому времени."
        )
    else:
        await message.answer(
            "Некорректный формат. Пожалуйста, используйте команду в формате: `/set HH:MM, Название города` (например, `/set 09:30, Москва`).",
            parse_mode="Markdown"
        )
        logger.warning(f"Пользователь {message.from_user.id} отправил некорректные данные: {message.text}")

# Обработчик команды /edit
@router.message(Command(commands=['edit']))
async def initiate_edit_notification(message: Message, db: asyncpg.pool.Pool, state: FSMContext):
    user_id = message.from_user.id
    logger.info(f"Получена команда /edit от пользователя {user_id}")

    # Получаем все уведомления пользователя
    rows = await db.fetch('''
        SELECT id, city, notification_time FROM users
        WHERE user_id = $1
        ORDER BY notification_time
    ''', user_id)

    if not rows:
        await message.answer("У вас нет установленных уведомлений. Используйте команду `/set` для их создания.", parse_mode="Markdown")
        return

    # Создаём инлайн-клавиатуру с уведомлениями для выбора
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"ID {row['id']}: {row['notification_time'].strftime('%H:%M')} - {row['city']}",
                              callback_data=f"edit_{row['id']}")] for row in rows
    ])

    await message.answer("Выберите уведомление для редактирования:", reply_markup=keyboard)

# Обработчик выбора уведомления для редактирования
@router.callback_query(lambda c: c.data and c.data.startswith('edit_'))
async def edit_selected_notification(callback_query: CallbackQuery, db: asyncpg.pool.Pool, state: FSMContext):
    user_id = callback_query.from_user.id
    notification_id = int(callback_query.data.split('_')[1])

    logger.info(f"Пользователь {user_id} выбрал уведомление с ID {notification_id} для редактирования")

    # Проверяем, что уведомление принадлежит пользователю
    exists = await db.fetchval('''
        SELECT EXISTS(SELECT 1 FROM users WHERE id = $1 AND user_id = $2)
    ''', notification_id, user_id)

    if not exists:
        await callback_query.message.answer("Уведомление не найдено или не принадлежит вам.")
        await callback_query.answer()
        return

    await callback_query.message.answer(
        "Отправьте новое время и город в формате: `HH:MM, Название города` (например, `10:00, Санкт-Петербург`).",
        parse_mode="Markdown"
    )

    # Устанавливаем состояние и сохраняем ID уведомления
    await state.set_state(EditNotificationStates.waiting_for_new_data)
    await state.update_data(notification_id=notification_id)

    await callback_query.answer()

# Обработка нового ввода для редактирования
@router.message(EditNotificationStates.waiting_for_new_data)
async def process_new_edit_data(message: Message, db: asyncpg.pool.Pool, state: FSMContext):
    user_input = message.text.strip()

    parsed = parse_time_and_city(user_input)
    if parsed:
        data = await state.get_data()
        notification_id = data.get('notification_id')
        if not notification_id:
            await message.answer("Произошла ошибка. Попробуйте снова.")
            await state.clear()
            return

        new_time = parsed['time']
        new_city = parsed['city']

        logger.info(f"Обновление уведомления ID {notification_id} для пользователя {message.from_user.id}: город {new_city}, время {new_time}")

        await db.execute('''
            UPDATE users
            SET city = $1, notification_time = $2
            WHERE id = $3
        ''', new_city, new_time, notification_id)

        await message.answer(
            f"Уведомление обновлено: прогноз погоды для города {new_city} каждый день в {new_time.strftime('%H:%M')} по московскому времени."
        )
        await state.clear()
    else:
        await message.answer(
            "Некорректный формат. Пожалуйста, используйте формат: `HH:MM, Название города` (например, `10:00, Санкт-Петербург`).",
            parse_mode="Markdown"
        )
        logger.warning(f"Пользователь {message.from_user.id} отправил некорректные данные при редактировании: {message.text}")

# Обработчик команды /clear
@router.message(Command(commands=['clear']))
async def clear_notification_settings(message: Message, db: asyncpg.pool.Pool):
    user_id = message.from_user.id
    logger.info(f"Получена команда /clear от пользователя {user_id}")

    # Проверяем, существует ли запись для пользователя
    exists = await db.fetchval('SELECT EXISTS(SELECT 1 FROM users WHERE user_id = $1)', user_id)
    if exists:
        await db.execute('DELETE FROM users WHERE user_id = $1', user_id)
        await message.answer("Ваши настройки уведомлений о погоде были успешно удалены. Вы больше не будете получать прогнозы.")
        logger.info(f"Настройки пользователя {user_id} были удалены.")
    else:
        await message.answer("У вас нет установленных уведомлений о погоде.")
        logger.info(f"Пользователь {user_id} попытался очистить несуществующие настройки.")

# Обработчик команды /list
@router.message(Command(commands=['list']))
async def list_notifications(message: Message, db: asyncpg.pool.Pool):
    user_id = message.from_user.id
    logger.info(f"Получена команда /list от пользователя {user_id}")

    # Получаем все уведомления пользователя
    rows = await db.fetch('''
        SELECT id, city, notification_time FROM users
        WHERE user_id = $1
        ORDER BY notification_time
    ''', user_id)

    if not rows:
        await message.answer("У вас нет установленных уведомлений. Используйте команду `/set` для их создания.", parse_mode="Markdown")
        return

    # Форматируем список уведомлений
    notifications = []
    for row in rows:
        notifications.append(f"**ID {row['id']}**: {row['notification_time'].strftime('%H:%M')} - {row['city']}")

    notifications_text = "\n".join(notifications)

    await message.answer(
        f"Ваши текущие уведомления о погоде:\n{notifications_text}",
        parse_mode="Markdown"
    )

# Обработчик команды /delete
@router.message(Command(commands=['delete']))
async def initiate_delete_notification(message: Message, db: asyncpg.pool.Pool):
    user_id = message.from_user.id
    logger.info(f"Получена команда /delete от пользователя {user_id}")

    # Получаем все уведомления пользователя
    rows = await db.fetch('''
        SELECT id, city, notification_time FROM users
        WHERE user_id = $1
        ORDER BY notification_time
    ''', user_id)

    if not rows:
        await message.answer("У вас нет установленных уведомлений для удаления.")
        return

    # Создаём инлайн-клавиатуру с уведомлениями для выбора
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"ID {row['id']}: {row['notification_time'].strftime('%H:%M')} - {row['city']}",
                              callback_data=f"delete_{row['id']}")] for row in rows
    ])

    await message.answer("Выберите уведомление для удаления:", reply_markup=keyboard)

# Обработчик выбора уведомления для удаления
@router.callback_query(lambda c: c.data and c.data.startswith('delete_'))
async def delete_selected_notification(callback_query: CallbackQuery, db: asyncpg.pool.Pool):
    user_id = callback_query.from_user.id
    notification_id = int(callback_query.data.split('_')[1])

    logger.info(f"Пользователь {user_id} выбрал уведомление с ID {notification_id} для удаления")

    # Проверяем, что уведомление принадлежит пользователю
    exists = await db.fetchval('''
        SELECT EXISTS(SELECT 1 FROM users WHERE id = $1 AND user_id = $2)
    ''', notification_id, user_id)

    if not exists:
        await callback_query.message.answer("Уведомление не найдено или не принадлежит вам.")
        await callback_query.answer()
        return

    # Удаляем уведомление
    await db.execute('''
        DELETE FROM users WHERE id = $1
    ''', notification_id)

    await callback_query.message.answer(f"Уведомление ID {notification_id} было успешно удалено.")
    logger.info(f"Уведомление ID {notification_id} пользователя {user_id} было удалено.")

    await callback_query.answer()

# Обработчик команды /forecast
@router.message(Command(commands=['forecast']))
async def forecast_command(message: Message, db: asyncpg.pool.Pool):
    user_id = message.from_user.id

    # Получаем наиболее часто используемые города пользователя
    rows = await db.fetch('''
        SELECT city FROM user_cities
        WHERE user_id = $1
        ORDER BY frequency DESC
        LIMIT 5
    ''', user_id)

    if rows:
        cities = [row['city'] for row in rows]
    else:
        cities = ['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань']

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=city, callback_data=CityCallback(city_name=city).pack())] for city in cities
    ])
    keyboard.add(InlineKeyboardButton(text="Другой город", switch_inline_query_current_chat=""))

    await message.answer("Выберите город из списка или отправьте название города:", reply_markup=keyboard)

# Обработчик выбора города
@router.callback_query(CityCallback.filter())
async def city_selected(callback_query: CallbackQuery, callback_data: CityCallback, db: asyncpg.pool.Pool):
    city_name = callback_data.city_name
    user_id = callback_query.from_user.id

    logger.info(f"Пользователь {user_id} выбрал город {city_name}")

    # Обновляем или добавляем частоту использования города для пользователя
    await db.execute('''
        INSERT INTO user_cities (user_id, city, frequency)
        VALUES ($1, $2, 1)
        ON CONFLICT (user_id, city) DO UPDATE
        SET frequency = user_cities.frequency + 1
    ''', user_id, city_name)

    # Получаем прогноз погоды на ближайшие 24 часа
    weather_data = await get_weather(city_name, hours=24)
    if weather_data:
        forecast_message = f"Прогноз погоды для {city_name} на ближайшие 24 часа:\n"
        forecasts = weather_data.get('list', [])[:8]  # 8 прогнозов (3 часа)

        for forecast in forecasts:
            dt_txt = forecast['dt_txt']
            temp = forecast['main']['temp']
            description = forecast['weather'][0]['description']
            forecast_message += f"{dt_txt}: {temp}°C, {description}\n"

        await callback_query.message.answer(forecast_message)
    else:
        await callback_query.message.answer("Не удалось получить данные о погоде.")
        logger.warning(f"Не удалось получить данные о погоде для города: {city_name}")

    await callback_query.answer()

# Обработчик сообщений без команд
@router.message(lambda message: message.text and not message.text.startswith('/'))
async def send_forecast_on_city_name(message: Message, db: asyncpg.pool.Pool):
    city_name = message.text.strip()
    user_id = message.from_user.id

    logger.info(f"Получено сообщение с названием города от пользователя {user_id}: {city_name}")

    if not city_name:
        await message.answer("Пожалуйста, отправьте корректное название города.")
        logger.warning(f"Пользователь {user_id} отправил пустое название города.")
        return

    weather_data = await get_weather(city_name, hours=24)
    if weather_data:
        forecast_message = f"Прогноз погоды для {city_name} на ближайшие 24 часа:\n"
        forecasts = weather_data.get('list', [])[:8]  # 8 прогнозов (3 часа)

        for forecast in forecasts:
            dt_txt = forecast['dt_txt']
            temp = forecast['main']['temp']
            description = forecast['weather'][0]['description']
            forecast_message += f"{dt_txt}: {temp}°C, {description}\n"

        await message.answer(forecast_message)
    else:
        await message.answer("Не удалось получить данные о погоде.")
        logger.warning(f"Не удалось получить данные о погоде для города: {city_name}")
