import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler

# Loglarni yoqish (xatolarni ko'rish uchun)
logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("TOKEN")

async def start(update, context):
    await update.message.reply_text('Salom! Bot ishlamoqda!')

if __name__ == '__main__':
    if not TOKEN:
        print("Xatolik: TOKEN topilmadi!")
    else:
        # Yangi versiya uchun ApplicationBuilder
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        
        print("Bot ishga tushdi...")
        # Polling usuli bilan ishga tushirish
        app.run_polling()
        
    
    
    
  
