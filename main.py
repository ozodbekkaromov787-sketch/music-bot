import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Token muhit o'zgaruvchisidan olinadi (yoki qo'shtirnoq ichiga o'zingiznikini qo'ying)
TOKEN = os.environ.get("TOKEN", "8842256743:AAEkul6BCTC0HtrGqfZ47gRAk2JkeogEgdY")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Musiqa botiga xush kelibsiz! Musiqa nomini yuboring.")

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text(f"Qidirilmoqda: {user_text}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    # Xabar va buyruqlarni ro'yxatdan o'tkazish
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))

    print("Bot muvaffaqiyatli ishga tushdi!")
    app.run_polling()
  
