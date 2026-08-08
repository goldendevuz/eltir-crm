"""Xabarni tahrirlash uchun yagona yordamchi.

Katalog inline rejimda qurilgan paytda barcha tahrirlar
`edit_message_reply_markup(inline_message_id=...)` orqali qilingan edi.
Endi mahsulotlar chatga oddiy xabar sifatida yuboriladi va u yerda
inline_message_id `None` bo'ladi — o'sha chaqiruvlar xato beradi. Bu modul
ikkala holatni ham to'g'ri manzillaydi, shuning uchun handlerlar qayerdan
kelganini bilishi shart emas.
"""
from aiogram.utils.exceptions import MessageNotModified

from bot.loader import bot


def _target(call):
    """(inline_message_id, chat_id, message_id) uchligini qaytaradi.

    `call` CallbackQuery ham, holatda saqlangan dict ham bo'lishi mumkin —
    cart.py savat tahririda dict ko'rinishida saqlaydi.
    """
    if isinstance(call, dict):
        inline_id = call.get("inline_message_id")
        message = call.get("message") or {}
        chat = message.get("chat") or {}
        return inline_id, chat.get("id"), message.get("message_id")
    inline_id = call.inline_message_id
    message = call.message
    if message is None:
        return inline_id, None, None
    return inline_id, message.chat.id, message.message_id


async def edit_markup(call, markup):
    inline_id, chat_id, message_id = _target(call)
    try:
        if inline_id:
            await bot.edit_message_reply_markup(inline_message_id=inline_id,
                                                reply_markup=markup)
        else:
            await bot.edit_message_reply_markup(chat_id=chat_id,
                                                message_id=message_id,
                                                reply_markup=markup)
    except MessageNotModified:
        # Bir xil klaviatura qayta yuborilsa Telegram xato beradi; bu
        # foydalanuvchi uchun muammo emas.
        pass


async def edit_text(call, text, markup=None):
    inline_id, chat_id, message_id = _target(call)
    try:
        if inline_id:
            await bot.edit_message_text(text=text, inline_message_id=inline_id,
                                        reply_markup=markup)
        else:
            await bot.edit_message_text(text=text, chat_id=chat_id,
                                        message_id=message_id,
                                        reply_markup=markup)
    except MessageNotModified:
        pass
