import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.builtin import CommandStart

from bot.data import texts
from bot.keyboards.default.menu_kb import menu
from bot.loader import bot, dp
from bot.states.user_registration_states import RegistrationStates
from bot.utils.db_api.quick_commands import create_user

PHONE_NUMBER_PATTERN = r"[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}"


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message, state: FSMContext):
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        # /start guruhdan yoki eski xabardan kelsa o'chirib bo'lmaydi —
        # bu salomlashishga to'sqinlik qilmasligi kerak.
        pass
    await message.answer(
        texts.WELCOME.format(name=message.from_user.full_name),
        reply_markup=menu,
    )


@dp.message_handler(Command("reset_state"))
async def reset_my_state(message: types.Message, state: FSMContext):
    await state.reset_state()
    await message.answer("Holat tozalandi")


@dp.message_handler(state=RegistrationStates.REGISTER_USER)
async def register_user(message: types.Message, state: FSMContext):
    user_id = int(message.from_user.id)
    try:
        await create_user(
            user_id=user_id,
            name=message.from_user.full_name or "",
            username=message.from_user.username or "",
        )
    except Exception as err:
        logging.exception(err)
    await state.reset_state(with_data=False)
    await bot_start(message, state)
