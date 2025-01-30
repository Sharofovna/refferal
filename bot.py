import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import asyncio

API_TOKEN = '7693456729:AAEmU0Vkrp54S51oNptDVMngVimq8MeYbU4'  # O'zingizning bot tokeningizni kiriting
CHANNEL_USERNAME = '@fakt7_24'  # Kanal username
ADMIN_ID = 123456789  # Admin Telegram ID

# Logger sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher obyektlarini yaratish
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Foydalanuvchi ma'lumotlarini kuzatish uchun dictionary
user_data = {}
referrals = {}  # Taklif qilgan foydalanuvchilar ro'yxati


# Tugmalarni yaratish
def create_channel_check_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton(text="Obuna bo'ldim", callback_data="subscription_done")]
    ])
    return keyboard


def create_phone_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def create_user_reply_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Natijalarim")],
            [KeyboardButton(text="Reyting")],
            [KeyboardButton(text="Do'stlarni taklif qilish")],
            [KeyboardButton(text="Qoidalar")]
        ],
        resize_keyboard=True
    )
    return keyboard


@dp.message(Command('start'))
async def start_command(message: types.Message):
    # Referral ID ni olish
    referrer_id = message.text.split('=')[-1]
    referrer_id = int(referrer_id) if referrer_id.isdigit() else None

    logging.info(f"Start komanda ishladi. Foydalanuvchi ID: {message.from_user.id}, Referrer ID: {referrer_id}")

    if message.from_user.id == ADMIN_ID:
        await message.answer("Assalomu alaykum, admin! Bu bot bir kanalda ishlash uchun sozlangan.")
    else:
        # Referral link orqali kelganlarni yangilash
        if referrer_id and referrer_id != message.from_user.id:
            if referrer_id not in referrals:
                referrals[referrer_id] = []  # Taklif qiluvchi ro'yxatini yaratish
            if message.from_user.id not in referrals[referrer_id]:
                referrals[referrer_id].append(message.from_user.id)  # Foydalanuvchini ro'yxatga qo'shish

        keyboard = create_channel_check_keyboard()
        await message.answer("Iltimos, kanalga a'zo bo'ling va 'Obuna bo'ldim' tugmasini bosing.",
                             reply_markup=keyboard)


@dp.callback_query(lambda call: call.data == "subscription_done")
async def subscription_done(call: CallbackQuery):
    chat_member = await bot.get_chat_member(CHANNEL_USERNAME, call.from_user.id)

    if chat_member.status in ['member', 'administrator', 'creator']:
        user_data[call.from_user.id] = {}
        referrals.setdefault(call.from_user.id, [])  # Foydalanuvchi uchun bo'sh ro'yxat yaratiladi

        await call.message.answer("Kanalga a'zo bo'lganingiz uchun rahmat! Iltimos, ismingizni yozib yuboring.")
    else:
        await call.message.answer(
            "Kechirasiz, siz kanalga a'zo bo'lmagan ekansiz. Iltimos, avval kanalga a'zo bo'ling.")
    await call.answer()


@dp.message(lambda message: message.from_user.id in user_data and 'name' not in user_data[message.from_user.id])
async def ask_phone(message: types.Message):
    user_data[message.from_user.id]['name'] = message.text
    await message.answer("Ismingiz qabul qilindi! Endi telefon raqamingizni yuboring.",
                         reply_markup=create_phone_keyboard())


@dp.message(lambda message: message.contact and message.from_user.id in user_data)
async def provide_referral_link(message: types.Message):
    user_data[message.from_user.id]['phone'] = message.contact.phone_number
    bot_info = await bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"

    # Foydalanuvchining o'z ro'yxatiga ham qo'shish
    referrals.setdefault(message.from_user.id, [])

    # Taklif qilgan foydalanuvchi ro'yxatiga yangi foydalanuvchini qo'shish
    if message.from_user.id in referrals:
        for ref_id in referrals:
            if message.from_user.id != ref_id:
                if message.from_user.id not in referrals[ref_id]:
                    referrals[ref_id].append(message.from_user.id)

    await message.answer(f"Raqamingiz qabul qilindi! Sizning referal linkingiz: {referral_link}",
                         reply_markup=create_user_reply_keyboard())


@dp.message(lambda message: message.text == "Natijalarim" and message.from_user.id in referrals)
async def show_user_results(message: types.Message):
    user_referrals = len(referrals.get(message.from_user.id, []))
    await message.answer(f"Siz {user_referrals} ta odamni taklif qilgansiz.")


@dp.message(lambda message: message.text == "Reyting")
async def show_ranking(message: types.Message):
    ranking = sorted(referrals.items(), key=lambda x: len(x[1]), reverse=True)
    ranking_message = "Reyting:\n\n"
    for rank, (user_id, ref_list) in enumerate(ranking, start=1):
        user_name = (await bot.get_chat(user_id)).first_name
        ranking_message += f"{rank}. {user_name} - {len(ref_list)} ta odam taklif qilgan.\n"

    await message.answer(ranking_message)


@dp.message(lambda message: message.text == "Do'stlarni taklif qilish")
async def invite_friends(message: types.Message):
    bot_info = await bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    await message.answer(f"Do'stlaringizni taklif qilish uchun havola: {referral_link}")


@dp.message(lambda message: message.text == "Qoidalar")
async def show_rules(message: types.Message):
    rules = """
    1. Kanalga a'zo bo'lish.
    2. Telefon raqamingizni yuboring.
    3. Har bir taklif uchun referal havola olish imkoniyati.
    4. Qoidalarni buzgan foydalanuvchilar bloklanadi.
    """
    await message.answer(rules)


async def main():
    dp.message.register(start_command, Command('start'))
    dp.callback_query.register(subscription_done, lambda call: call.data == "subscription_done")

    def check_user(message):
        return message.from_user.id in user_data and 'name' not in user_data[message.from_user.id]

    dp.message.register(ask_phone, check_user)

    dp.message.register(provide_referral_link, lambda message: message.contact and message.from_user.id in user_data)
    dp.message.register(show_user_results, lambda message: message.text == "Natijalarim")
    dp.message.register(show_ranking, lambda message: message.text == "Reyting")
    dp.message.register(invite_friends, lambda message: message.text == "Do'stlarni taklif qilish")
    dp.message.register(show_rules, lambda message: message.text == "Qoidalar")

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
