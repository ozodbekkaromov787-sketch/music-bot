import os
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = os.environ.get("TOKEN")

async def start(update, context):
    await update.message.reply_text('Bot ishlamoqda!')

if __name__ == '__main__':
    # drop_pending_updates=True eski so'rovlarni o'chirib tashlaydi
    app = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Bot ishga tushdi...")
    # drop_pending_updates=True bu yerda juda muhim
    app.run_polling(drop_pending_updates=True)
    
        
    
    
    
  
