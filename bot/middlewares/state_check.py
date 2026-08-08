from aiogram import Dispatcher
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineQuery



class CheckState(BaseMiddleware):
    async def check_state_data(self, user_id, chat_id):
        dp = Dispatcher.get_current()
        async with dp.current_state(chat=chat_id, user=user_id).proxy() as state_data:
            if not state_data.get("liked_products"):
                state_data["liked_products"] = []
            if not state_data.get("products"):
                state_data["products"] = {}
            if not state_data.get("product_info"):
                state_data["product_info"] = {}
        return

    async def on_pre_process_message(self, msg: Message, data: dict):
        """
        On pre_process check user state_data if it's have a keys ['liked_products', 'product_info']
        :param msg:
        :param data:
        :return:
        """
        user_id, chat_id = msg.from_user.id, msg.chat.id
        await self.check_state_data(user_id, chat_id)

    async def on_pre_process_callback_query(self, query: CallbackQuery, data: dict):
        callback_data = dict(query)
        user_id = query.from_user.id
        chat_id = callback_data["chat"]["id"] if callback_data.get("chat") else callback_data['from']['id']
        await self.check_state_data(user_id, chat_id)

    async def on_pre_process_inline_query(self, query: InlineQuery, data: dict):
        """
        Inline queries have no `chat`, so the FSM state is keyed by user_id for both
        chat and user (same as aiogram's own storage lookup for inline updates).
        Katalog endi oddiy xabarlar orqali ko'rsatiladi, lekin foydalanuvchi
        botni qo'lda @nom bilan chaqirsa ham holat tayyor bo'lishi kerak.
        """
        user_id = query.from_user.id
        await self.check_state_data(user_id, user_id)
