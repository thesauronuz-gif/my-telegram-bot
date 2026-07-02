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
# 🛠️ SOZLAMALAR (SIZNING SHAXSIY MA'LUMOTLARINGIZ O'RNATILDI ⚙️)
# =====================================================================
BOT_TOKEN = "8572560610:AAENghU7fxHYp_Yx4iq-wZAtmM_9RkmYgU4"

# Siz taqdim etgan to'g'ri kanal ID raqami:
MAIN_CHANNEL_ID = -1003394493877  

# Asosiy kanal a'zolik linki:
MAIN_CHANNEL_LINK = "https://t.me/+fT9YFqfG-I00M2Ey"  

# 5 ta odam yig'gandan keyin ochiladigan maxfiy havola:
SECRET_CHANNEL_LINK = "https://t.me/+yUONzDEUCag3ZWJi"  
# =====================================================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- RENDER UCHUN SOXTA VEB-SERVER QISMI ---
async def handle(request):
    return web.Response(text="Bot is running smoothly 24/7!")

app = web.Application()
app.router.add_get('/', handle)
