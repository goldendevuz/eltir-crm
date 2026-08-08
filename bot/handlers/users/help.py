from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp

from bot.data import texts
from bot.loader import dp


@dp.message_handler(CommandHelp())
async def bot_help(message: types.Message):
    await message.answer(texts.HELP)
