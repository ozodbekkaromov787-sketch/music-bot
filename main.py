import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

# Loglarni sozlash
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Tokenni yuklash
TOKEN = os.getenv("BOT_TOKEN", "8842256743:AAEkul6BCTC0HtrGqfZ47gRAk2JkeogEgdY")

# Flask server (Render oʻchib qolmasligi uchun)
app = Flask('')

@app.route('/')
def home():
    return "Bot muvaffaqiyatli ishlamoqda!"

def run():
    app.run(host='0.0.0.0', port=8080)

# /start buyrugʻi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Salom! Menga qoʻshiq nomini yoki ijrochini yozing, men sizga musiqani topib beraman.")

# Musiqa qidirish (Deezer API)
async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await update.message.reply_text("🔍 Musiqa qidirilmoqda, iltimos kuting...")
    
    url = f"https://api.deezer.com/search?q={query}&limit=5"
    try:
        response = requests.get(url).json()
        data = response.get('data', [])
        
        if not data:
            await update.message.reply_text("❌ Afsuski, bunday musiqa topilmadi.")
            return
            
        keyboard = []
        text = "🎵 Qoʻshiqni tanlang:\n\n"
        
        for idx, track in enumerate(data, 1):
            title = track.get('title')
            artist = track.get('artist', {}).get('name')
            track_id = track.get('id')
            
            text += f"{idx}. {artist} - {title}\n"
            keyboard.append([InlineKeyboardButton(f"{idx}", callback_data=f"track_{track_id}")])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Qidiruv xatosi: {e}")
        await update.message.reply_text("❌ Tizimda xatolik yuz berdi. Qaytadan urinib koʻring.")

# Musiqani yuklash va yuborish
async def download_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    track_id = query.data.split('_')[1]
    await query.message.reply_text("📥 Musiqa yuklab olinmoqda...")
    
    track_url = f"https://api.deezer.com/track/{track_id}"
    try:
        track_data = requests.get(track_url).json()
        preview_url = track_data.get('preview')
        title = track_data.get('title')
        artist = track_data.get('artist', {}).get('name')
        
        if preview_url:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=preview_url,
                title=title,
                performer=artist
            )
        else:
            await query.message.reply_text("❌ Bu musiqani yuklash imkoni boʻlmadi.")
            
    except Exception as e:
        logger.error(f"Yuklash xatosi: {e}")
        await query.message.reply_text("❌ Yuklashda xatolik yuz berdi.")

def main():
    # Flaskni fonda yuritish
    Thread(target=run).start()
    
    # Bot dasturini yuritish
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))
    application.add_handler(CallbackQueryHandler(download_music, pattern="^track_"))
    
    application.run_polling()

if __name__ == '__main__':
    main()
    
