import os
import asyncio
from flask import Flask
from threading import Thread
from telegram.ext import ApplicationBuilder, CommandHandler

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot ishlamoqda!"

def run_web():
    app_web.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

TOKEN = os.environ.get("TOKEN")

async def start(update, context):
    await update.message.reply_text('Salom! Bot ishlamoqda!')

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    # Veb-serverni alohida thread'da ishga tushirish
    Thread(target=run_web).start()
    
    print("Bot ishga tushdi...")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
    
    
    
    
  
