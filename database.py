# database.py

import asyncpg
import logging
from config import settings

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool: asyncpg.pool.Pool = None

    async def connect(self):
        logger.info(f"Подключение к базе данных по адресу: {settings.DATABASE_URL}")
        self.pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
        logger.info("Пул соединений с базой данных создан.")
        await self.create_tables()

    async def create_tables(self):
        async with self.pool.acquire() as conn:
            # Создание таблицы users с новым столбцом id
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    city TEXT NOT NULL,
                    notification_time TIME NOT NULL
                );
            ''')

            # Создание таблицы user_cities
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_cities (
                    user_id BIGINT,
                    city TEXT,
                    frequency INT DEFAULT 1,
                    PRIMARY KEY (user_id, city)
                );
            ''')

            # Обновление таблицы users: добавление столбца id, если он не существует
            await conn.execute('''
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS id SERIAL;
            ''')

            # Удаление существующего первичного ключа на user_id, если он существует
            await conn.execute('''
                ALTER TABLE users 
                DROP CONSTRAINT IF EXISTS users_pkey;
            ''')

            # Установка нового первичного ключа на id
            await conn.execute('''
                ALTER TABLE users 
                ADD PRIMARY KEY (id);
            ''')

            logger.info("Таблицы базы данных созданы или уже существуют и обновлены.")

    async def close(self):
        await self.pool.close()
        logger.info("Пул соединений с базой данных закрыт.")
