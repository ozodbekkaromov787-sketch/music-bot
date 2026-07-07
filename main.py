import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import yt_dlp

logging.basicConfig(level=logging.INFO)

async def start(update, context):
    await update.message.reply_text("Salom! Musiqa nomini yozing.")

async def echo(update, context):
    # Bu yerda qidiruv funksiyasi ishlaydi
    await update.message.reply_text("Qidirilmoqda...")

if __name__ == '__main__':
    token = os.environ.get("TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    app.run_polling()
    
