import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

# BOT SOZLAMALARI (Sizning shaxsiy ma'lumotlaringiz o'rnatildi 🚀)
BOT_TOKEN = "8572560610:AAEBjz6nR6-eVHimmB7QgZjLX9DkXdW0tBA"
MAIN_CHANNEL_ID = -1003394493877                      # Sizning asosiy kanalingiz ID-si
SECRET_CHANNEL_LINK = "https://t.me/+yUONzDEUCag3ZWJi"  # Sizning maxfiy kanalingiz ssilkasi

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# MA'LUMOTLAR BAZASI
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referrer_id INTEGER,
            referral_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# Foydalanuvchini bazaga qo'shish va taklif qilganga xabar yuborish
async def get_or_create_user(user_id, referrer_id=None):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT referrer_id, referral_count FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        if referrer_id and referrer_id != user_id:
            # Yangi odamni bazaga qo'shish
            cursor.execute("INSERT INTO users (user_id, referrer_id) VALUES (?, ?)", (user_id, referrer_id))
            # Taklif qilgan odamning ballini oshirish
            cursor.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?", (referrer_id,))
            conn.commit()
            
            # Yangi ballni tekshirish va taklif qilganga XABAR YUBORISH
            cursor.execute("SELECT referral_count FROM users WHERE user_id = ?", (referrer_id,))
            new_count = cursor.fetchone()[0]
            
            await send_referral_notification(referrer_id, new_count)
        else:
            cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            conn.commit()
    conn.close()

def get_referral_count(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT referral_count FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

# ODAM QO'SHILGANDA DO'STIGA BORADIGAN QUYUNChLI XABAR
async def send_referral_notification(referrer_id: int, current_count: int):
    needed = 5 - current_count
    try:
        if current_count < 5:
            text = (
                f"🥳 **Opa-aka! Ssilkangiz bilan bitta jonli odam kirdi!**\n\n"
                f"📊 Hozirgi hisob: **{current_count}/5**\n"
                f"🏃‍♂️ Maxfiy linkka yetishga yana **{needed} ta** odam qoldi. "
                f"Ssilkani guruhlarga qisir qilib tashlang, daryo bo'lib oqib kelsin! 🚀"
            )
        else:
            text = (
                f"⚡️ **Opa-aka, e'lon! Marra zabt etildi!** 🎉\n\n"
                f"Siz jami **{current_count} ta** odam to'pladingiz (Sizga haykal qo'ysak arziydi 🗿).\n"
                f"Botga kirib **'Tekshirish va Ssilkani olish 🔑'** tugmasini bosing va mukofotni qo'lga kiriting!"
            )
        await bot.send_message(chat_id=referrer_id, text=text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Xabar yuborishda xatolik: {e}")

# KANALGA QO'SHILGANINI TEKSHIRISH
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=MAIN_CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'creator', 'administrator']:
            return True
        return False
    except Exception as e:
        logging.error(f"Tekshirish xatosi: {e}")
        return False

# /start KOMANDASI
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        
    await get_or_create_user(user_id, referrer_id)
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Tekshirish va Ssilkani olish 🔑", callback_data="check_sub"))
    kb.row(InlineKeyboardButton(text="Mening shaxsiy ssilkam 🔗", callback_data="my_ref"))
    
    await message.answer(
        f"Xush kelibsiz, {message.from_user.first_name}!  👋✨\n\n"
        f"🤖 **Bu shunchaki bot emas, bu — Maxfiy Kanal eshigi!**\n\n"
        f"U ichkaridagi daxshat narsalarni ko'rish uchun ikkita arzimagan shart bor:\n"
        f"1️⃣ Bizning asosiy kanalga shartta a'zo bo'lasiz (u yersiz hayot qiziqmas 🪐).\n"
        f"2️⃣ O'zingizning maxsus ssilkangiz orqali **5 ta tirik odam** taklif qilasiz.\n\n"
        f"⚠️ *Eslatma: 'Uydirma' (bot-akkauntlar) qo'shsangiz botimiz xafa bo'ladi va sizni o'tkazmaydi!* 😎\n\n"
        f"Qani, pastdagi tugmalarni bosib harakatni boshlang:",
        reply_markup=kb.as_markup()
    )

# TUGMALAR ISHLASHI
@dp.callback_query(F.data == "check_sub")
async def process_check_sub(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        await callback.answer("Hali asosiy kanalga a'zo bo'lmabsiz-ku, usta!  ❌ Avval a'zo bo'ling!", show_alert=True)
        return
        
    ref_count = get_referral_count(user_id)
    if ref_count < 5:
        needed = 5 - ref_count
        await callback.answer(
            f"Shoshilmang-da endi! 🛑\n\n"
            f"Hozircha {ref_count} ta odamingiz bor. Yana {needed} ta odam yetishmayapti.\n"
            f"Do'stlar degan kunda asqatadi, ssilkani tarqating! ⚡️", 
            show_alert=True
        )
        return
        
    await callback.message.answer(
        f"Uuuu, daxshat! Gap bo'lishi mumkin emas! 🏁🎉\n\n"
        f"Siz haqiqiy professonalsiz. Hamma shartlar "
        f"bajarildi! Mana sizga o'sha dunyo izlagan maxfiy havola:\n\n"
        f"👉 {SECRET_CHANNEL_LINK} 👈\n\n"
        f"Kirib mazza qiling! 😉"
    )
    await callback.answer()

@dp.callback_query(F.data == "my_ref")
async def process_my_ref(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    ref_count = get_referral_count(user_id)
    
    await callback.message.answer(
        f"💎 **Sizning oltinga teng shaxsiy havolangiz:**\n`{ref_link}`\n\n"
        f"📊 Progress: **{ref_count}/5** (Xudo xohlasa oz qoldi! 📉)\n\n"
        f"☝️ **Nima qilish kerak?** Usbu ssilkani nusxalab olib, guruhlarga, do'stlaringizga tashlang. "
        f"Ular kirib bitta start bossa — sizga bitta odam qo'shiladi. Qani ketdik! 🫵🔥",
        parse_mode="Markdown"
    )
    await callback.answer()

async def main():
    init_db()
    print("Kayfiyatni ko'taruvchi bot muvaffaqiyatli ishga tushdi...🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())