# Weather Notification Bot

**Weather Notification Bot** is a Telegram bot that sends daily weather forecasts to users at specified times for their chosen cities. Stay updated effortlessly with personalized weather alerts.

## Features

- **Set Multiple Notifications:** Schedule weather updates for different cities and times.
- **Manage Notifications:** Add, list, edit, and delete your weather alerts.
- **User-Friendly Interface:** Interactive keyboard for easy command selection.
- **Automated Updates:** Sends forecasts automatically using APScheduler.

## Installation

### Prerequisites

- **Python 3.9+**
- **PostgreSQL**
- **Docker (Optional for containerized setup)**

### Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/weather-notification-bot.git
   cd weather-notification-bot
   ```

2. **Configure Environment Variables**

   Create a `.env` file in the root directory:

   ```env
   BOT_TOKEN=your_telegram_bot_token
   DATABASE_URL=postgresql://user:password@localhost:5432/weather_bot_db
   TIMEZONE=Europe/Moscow
   ```

3. **Set Up the Database**

   ```bash
   psql -U postgres
   ```

   In the PostgreSQL prompt:

   ```sql
   CREATE DATABASE weather_bot_db;
   CREATE USER user WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE weather_bot_db TO user;
   \q
   ```

4. **Install Dependencies**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Run the Bot**

   ```bash
   python bot.py
   ```

   *Alternatively, using Docker:*

   ```bash
   docker-compose up -d
   ```

## Usage

### Available Commands

- `/start` : Start the bot and view the command menu.
- `/set` : Set a new weather notification (`/set HH:MM, City`).
- `/list` : List all your current notifications.
- `/edit` : Edit an existing notification.
- `/delete` : Delete a specific notification.
- `/clear` : Remove all your weather notifications.

**Example:**

1. **Set a Notification**

   ```
   /set 09:30, Москва
   ```

   *Bot Response:*

   ```
   Новое уведомление добавлено: прогноз погоды для города Москва каждый день в 09:30 по московскому времени.
   ```

2. **List Notifications**

   ```
   /list
   ```

   *Bot Response:*

   ```
   Ваши текущие уведомления о погоде:
   **ID 1**: 09:30 - Москва
   ```



## License

This project is licensed under a [Custom License](LICENSE).

© 2024 [BIackFIame]

### Contact

For any inquiries or to request permission for commercial use, please contact:

- **Email:** help.of.project.s@gmail.com
