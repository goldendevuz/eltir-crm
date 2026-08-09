from decimal import Decimal
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.data import texts
from bot.keyboards.inline.callback_datas import gen_buy_callback, liked_product, navigate_callback, gen_edit_callback, \
    gen_pag_edit_call, gen_pagination_callback, browse_callback, liked_browse_callback, \
    search_browse_callback
from bot.utils.db_api import quick_commands

#  =================Cart Edit KB ===================
cart_edit_kb = InlineKeyboardMarkup(row_width=2, inline_keyboard=[
    [
        InlineKeyboardButton(text="✏ Tahrirlash", callback_data="edit_cart"),
        InlineKeyboardButton(text="❌ Tozalash", callback_data="wipe_cart")
    ],
    [
        InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="order")
    ]
])


#  ==================================================


class CartKeyboardGen:
    def __init__(self, data: dict, page: int = 1):
        self.keyboard = InlineKeyboardMarkup(row_width=3)
        self.data = data
        # =============Paging on card edit====================#
        self.page = page
        self.max_page = len(data['products'].keys())
        self.idx_product_ids = dict(enumerate(data['products'].keys(), start=1))
        # ====================================================#
        self.product_id = self.idx_product_ids[page]
        self.product = data["products"][self.product_id]
        self.quantity = self.product['quantity']

    def produce_edit_button(self):
        text = (f"✏ {self.quantity} dona | "
                f"{texts.money(self.product['price'])} {self.product['title']}")
        self.keyboard.add(InlineKeyboardButton(text=text, callback_data=gen_pagination_callback(page=self.page,
                                                                                                edit=True)))

    def produce_edit_quantity(self):
        text = "✏ " + str(self.quantity) + " dona"
        self.keyboard.add((InlineKeyboardButton(text="-1", callback_data=gen_pag_edit_call(product_id=self.product_id,
                                                                                           edit=True, reduce=True,
                                                                                           page=self.page))))

        self.keyboard.insert(InlineKeyboardButton(text=text, callback_data=gen_pag_edit_call(product_id=self.product_id,
                                                                                             edit=True,
                                                                                             page=self.page)))

        self.keyboard.insert(InlineKeyboardButton(text="+1", callback_data=gen_pag_edit_call(product_id=self.product_id,
                                                                                             edit=True, add=True,
                                                                                             page=self.page)))

    def produce_back_button(self):
        back_page = self.page - 1
        if back_page <= 0:
            button = InlineKeyboardButton(text='◀', callback_data=gen_pagination_callback(page=self.max_page))
            self.keyboard.add(button)
            return
        button = InlineKeyboardButton(text='◀', callback_data=gen_pagination_callback(page=back_page))
        self.keyboard.add(button)

    def produce_current_page(self):
        button_text = str(self.page) + "/" + str(self.max_page)
        button = InlineKeyboardButton(text=button_text, callback_data="test")
        self.keyboard.insert(button)

    def produce_next_button(self):
        next_page = self.page + 1
        if next_page > self.max_page:
            button = InlineKeyboardButton(text='➡', callback_data=gen_pagination_callback(page=1))
            self.keyboard.insert(button)
            return
        button = InlineKeyboardButton(text='➡', callback_data=gen_pagination_callback(page=next_page))
        self.keyboard.insert(button)

    def produce_end_editing(self):
        self.keyboard.add(InlineKeyboardButton(text="✅ Tahrirlashni yakunlash", callback_data="end_edit"))

    def build_pagination_keyboard(self) -> InlineKeyboardMarkup:
        self.produce_edit_button()
        self.produce_back_button()
        self.produce_current_page()
        self.produce_next_button()
        self.produce_end_editing()
        return self.keyboard

    def build_edit_keyboard(self) -> InlineKeyboardMarkup:
        self.produce_edit_quantity()
        self.produce_back_button()
        self.produce_current_page()
        self.produce_next_button()
        self.produce_end_editing()
        return self.keyboard


class KeyboardGen:
    def __init__(self, product, data: dict, index: int = 0, total: int = 1,
                 mode: str = "catalog"):
        self.keyboard = InlineKeyboardMarkup(row_width=3)
        self.product = product
        self.data = data
        self.is_liked = self.data["product_info"]["is_liked"]
        # Varaqlash uchun: mahsulot ro'yxatdagi o'rni va umumiy soni.
        self.index = index
        self.total = total
        # "catalog" | "liked" | "search" — varaqlash qaysi ro'yxat bo'ylab
        # borishini belgilaydi.
        self.mode = mode

    @classmethod
    async def from_product_id(cls, product_id: int, data: dict, index: int = 0,
                              total: int = 1, mode: str = "catalog"):
        product = await quick_commands.get_product(product_id)
        return cls(product=product, data=data, index=index, total=total,
                   mode=mode)

    @staticmethod
    def cart_total_price(product_list: dict):
        """Savat jami summasi. Faqat haqiqiy qatorlar hisobga olinadi."""
        return sum((Decimal(str(item["price"])) * int(item["quantity"])
                    for item in product_list.values()
                    if int(item.get("quantity", 0)) > 0), Decimal("0"))

    def produce_buy_button(self) -> None:
        callback_data = gen_buy_callback(product_id=self.product.id, product_price=str(self.product.price),
                                         category_id=self.product.subcategory.category_id)
        price = texts.money(self.product.price)
        item = self.data.get("products", {}).get(str(self.product.id))
        if not item or int(item.get("quantity", 0)) <= 0:
            product_name = f'Sotib olish "{self.product.title}" · {price}'
        else:
            quantity = item["quantity"]
            product_name = (f"{quantity} dona | Sotib olish "
                            f'"{self.product.title}" · {price}')
        self.keyboard.insert(InlineKeyboardButton(text=product_name, callback_data=callback_data))

    def produce_edit_button(self) -> None:
        quantity = self.data["products"][str(self.product.id)]["quantity"]
        self.keyboard.add(InlineKeyboardButton(text="-1", callback_data=gen_edit_callback(product_id=self.product.id,
                                                                                          reduce=True, edit=True)))
        self.keyboard.insert(InlineKeyboardButton(text="✏" + str(quantity) + " dona",
                                                  callback_data=gen_edit_callback(product_id=self.product.id,
                                                                                  edit=True)))
        self.keyboard.insert(
            InlineKeyboardButton(text="+1", callback_data=gen_edit_callback(product_id=self.product.id,
                                                                            add=True, edit=True)))

    def produce_like_button(self) -> None:
        if self.product.id not in self.data['liked_products']:
            text = "❤"
            liked_callback = liked_product.new(add=True, delete=False, product_id=self.product.id)
        else:
            text = "💘"
            liked_callback = liked_product.new(add=False, delete=True, product_id=self.product.id)
        self.keyboard.add(InlineKeyboardButton(text=text, callback_data=liked_callback))

    def produce_cart_button(self) -> None:
        total = self.cart_total_price(self.data.get("products", {}))
        self.keyboard.insert(
            InlineKeyboardButton(text="🛒 " + texts.amount(total),
                                 callback_data="show_cart"))

    def produce_back_button(self) -> None:
        self.keyboard.add(InlineKeyboardButton(text="◀ Orqaga",
                                               callback_data=navigate_callback(level=1,
                                                                               category_id=self.product.subcategory.category_id)))

    def produce_pagination(self, index: int, total: int) -> None:
        """◀ 3/18 ▶ qatori. Ro'yxat halqa bo'lib aylanadi."""
        if total <= 1:
            return
        prev_index = (index - 1) % total
        next_index = (index + 1) % total
        if self.mode == "liked":
            back = liked_browse_callback.new(index=prev_index)
            forward = liked_browse_callback.new(index=next_index)
        elif self.mode == "search":
            back = search_browse_callback.new(index=prev_index)
            forward = search_browse_callback.new(index=next_index)
        else:
            sub_id = self.product.subcategory_id
            back = browse_callback.new(subcategory_id=sub_id, index=prev_index)
            forward = browse_callback.new(subcategory_id=sub_id, index=next_index)
        self.keyboard.add(InlineKeyboardButton(text="◀", callback_data=back))
        self.keyboard.insert(InlineKeyboardButton(text=f"{index + 1}/{total}",
                                                  callback_data="noop"))
        self.keyboard.insert(InlineKeyboardButton(text="▶", callback_data=forward))

    def build_product_kb(self) -> InlineKeyboardMarkup:
        self.produce_buy_button()
        self.produce_like_button()
        self.produce_cart_button()
        self.produce_pagination(self.index, self.total)
        self.produce_back_button()
        return self.keyboard

    def build_edit_kb(self) -> InlineKeyboardMarkup:
        self.produce_edit_button()
        self.produce_like_button()
        self.produce_cart_button()
        self.produce_pagination(self.index, self.total)
        self.produce_back_button()
        return self.keyboard

    def build_auto_kb(self) -> InlineKeyboardMarkup:
        """Savatdagi holatga qarab mos klaviaturani tanlaydi.

        Ilgari ba'zi handlerlar doim build_product_kb() chaqirardi va
        savatdagi mahsulotning -1/+1 tugmalari "Sotib olish"ga almashib
        ketardi.
        """
        item = self.data.get("products", {}).get(str(self.product.id))
        if item and int(item.get("quantity", 0)) > 0:
            return self.build_edit_kb()
        return self.build_product_kb()
