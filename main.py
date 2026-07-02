import os
import logging
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiohttp import web

# =====================================================================
# 🛠️ SOZLAMALAR
# =====================================================================
BOT_TOKEN = "8572560610:AAENghU7fxHYp_Yx4iq-wZAtmM_9RkmYgU4"
MAIN_CHANNEL_ID = -1003394493877  
MAIN_CHANNEL_LINK = "https://t.me/biologiya_kimyo_yonalishi"  
SECRET_CHANNEL_LINK = "https://t.me/+yUONzDEUCag3ZWJi"  
# =====================================================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- RENDER WEB SERVER QISMI ---
async def handle(request):
    return web.Response(text="Bot is running smoothly 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Web server started on port {port}")
    # Server o'chib ketmasligi uchun cheksiz kutish rejimida ushlab turamiz
    while True:
        await asyncio.sleep(3600)

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

async def get_or_create_user(user_id, referrer_id=None):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT referrer_id, referral_count FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        if referrer_id and referrer_id != user_id:
            cursor.execute("INSERT INTO users (user_id, referrer_id) VALUES (?, ?)", (user_id, referrer_id))
            cursor.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?", (referrer_id,))
            conn.commit()
            
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

# KANALGA A'ZOLIKNI TEKSHIRISH
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
    kb.row(InlineKeyboardButton(text="1️⃣ Asosiy kanalga a'zo bo'lish 📢", url=MAIN_CHANNEL_LINK))
    kb.row(InlineKeyboardButton(text="Mening shaxsiy ssilkam 🔗", callback_data="my_ref"))
    kb.row(InlineKeyboardButton(text="Tekshirish va Ssilkani olish 🔑", callback_data="check_sub"))
    
    await message.answer(
        f"Xush kelibsiz, {message.from_user.first_name}! 👋✨\n\n"
        f"🤖 **Bu shunchaki bot emas, bu — Maxfiy Kanal eshigi!**\n\n"
        f"U ichkaridagi daxshat narsalarni ko'rish uchun ikkita arzimagan shart bor:\n"
        f"1️⃣ Pastdagi tugma orqali asosiy kanalimizga shartta a'zo bo'lasiz.\n"
        f"2️⃣ O'zingizning maxsus ssilkangizni **5 ta do'stingizga** tarqatasiz.\n\n"
        f"⚠️ *Eslatma: 'Uydirma' (bot-akkauntlar) qo'shsangiz botimiz o'tkazmaydi!* 😎\n\n"
        f"Qani, pastdagi tugmalarni tartib bilan bosib harakatni boshlang:",
        reply_markup=kb.as_markup()
    )

# TEKSHIRISH TUGMASI
@dp.callback_query(F.data == "check_sub")
async def process_check_sub(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        await callback.answer("Hali asosiy kanalga a'zo bo'lmabsiz-ku, usta! ❌ Avval a'zo bo'ling, keyin ssilka beriladi!", show_alert=True)
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

# SHAXSIY SSILKA OLISH TUGMASI
@dp.callback_query(F.data == "my_ref")
async def process_my_ref(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    is_subscribed = await check_subscription(user_id)
    if not is_subscribed:
        await callback.answer("To'xtang, usta! 🛑\n\nAvval 1-shartni bajarib, 'Asosiy kanal'ga a'zo bo'ling! Shundan keyingina sizga do'stlarni taklif qilish uchun shaxsiy ssilka beriladi! 😉", show_alert=True)
        return
        
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    ref_count = get_referral_count(user_id)
    
    await callback.message.answer(
        f"💎 **Sizning oltinga teng shaxsiy havolangiz:**\n`{ref_link}`\n\n"
        f"📊 Progress: **{ref_count}/5** (Xudo xohlasa oz qoldi! 📉)\n\n"
        f"☝️ **Nima qilish kerak?** Ushbu ssilkani nusxalab (ustiga bossangiz o'zi nusxalanadi), kamida **5 ta do'stingizga** yoki guruhlarga tashlang. "
        f"Ular kirib start bossa — sizga odam qo'shiladi! 🔥",
        parse_mode="Markdown"
    )
    await callback.answer()

async def main():
    init_db()
    logging.info("Bot va Web-server parallel ishga tushmoqda...")
    # Ikkala vazifani ham parallel va uzluksiz bajarish uchun birlashtiramiz
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
