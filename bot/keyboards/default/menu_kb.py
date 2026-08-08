from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.data import texts

menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=texts.BTN_PRODUCTS),
            KeyboardButton(text=texts.BTN_CART),
        ],
        [
            KeyboardButton(text=texts.BTN_SEARCH),
            KeyboardButton(text=texts.BTN_MY_ORDERS),
        ],
    ],
    resize_keyboard=True,
    selective=True)


def phone_request_kb() -> ReplyKeyboardMarkup:
    """Telegram raqamni faqat tugma orqali ulasha oladi."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=texts.BTN_SEND_PHONE,
                                  request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        selective=True,
    )
