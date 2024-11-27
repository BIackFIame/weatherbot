from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_commands_keyboard() -> ReplyKeyboardMarkup:
    """
    Создаёт клавиатуру с командами для бота.
    """
    keyboard = [
        [
            KeyboardButton(text="/start"),
            KeyboardButton(text="/set")
        ],
        [
            KeyboardButton(text="/list"),
            KeyboardButton(text="/edit")
        ],
        [
            KeyboardButton(text="/delete"),
            KeyboardButton(text="/clear")
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )
