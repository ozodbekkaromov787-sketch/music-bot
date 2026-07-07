import os
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler

# Tokenni Render muhitidan oladi
TOKEN = os.environ.get("TOKEN")

async def start(update, context):
    await update.message.reply_text('Salom! Bot ishlamoqda!')

async def main():
    if not TOKEN:
        print("Xatolik: TOKEN topilmadi!")
        return
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Bot ishga tushdi...")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
    
    
    
  
