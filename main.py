import os
from telegram.ext import ApplicationBuilder, CommandHandler

# Tokenni Render muhitidan (Environment Variables) oladi
TOKEN = os.environ.get("TOKEN")

async def start(update, context):
    await update.message.reply_text('Salom! Bot ishlamoqda!')

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
    
  
