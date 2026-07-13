import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# O'zingizning yangi tokeningizni qo'ying
TOKEN = os.getenv("BOT_TOKEN", "8842256743:AAEkul6BCTC0HtrGqfZ47gRAk2JkeogEgdY")

app = Flask('')

@app.route('/')
def home():
    return "Bot ishlamoqda!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Salom! Musiqa nomini yozing, men sizga MP3 faylini topib beraman.")

async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text("🔍 Musiqa qidirilmoqda...")
    
    url = f"https://api.deezer.com/search?q={query}&limit=5"
    try:
        res = requests.get(url, timeout=10).json()
        tracks = res.get('data', [])
        
        if not tracks:
            await status_msg.edit_text("❌ Musiqa topilmadi.")
            return

        keyboard = []
        text = "🎵 **Topilgan musiqalar:**\n\n"
        
        for idx, track in enumerate(tracks, 1):
            title = track.get('title')
            artist = track.get('artist', {}).get('name')
            track_id = track.get('id')
            
            text += f"{idx}. {artist} - {title}\n"
            keyboard.append([InlineKeyboardButton(f"📥 {idx}-musiqani yuklash", callback_data=f"dl_{track_id}")])
            
        await status_msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        await status_msg.edit_text("❌ Qidiruvda xatolik yuz berdi.")

async def download_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    track_id = query.data.split('_')[1]
    msg = await query.message.reply_text("📥 Musiqa yuborilmoqda...")
    
    try:
        # Qo'shiq ma'lumotlarini olish
        res = requests.get(f"https://api.deezer.com/track/{track_id}", timeout=10).json()
        audio_url = res.get('preview')
        title = res.get('title')
        artist = res.get('artist', {}).get('name')
        
        if audio_url:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=audio_url,
                title=title,
                performer=artist
            )
            await msg.delete()
        else:
            await msg.edit_text("❌ Musiqa faylini olish imkoni bo'lmadi.")
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        await msg.edit_text("❌ Yuklashda xatolik yuz berdi.")

def main():
    Thread(target=run_flask).start()
    
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))
    app_bot.add_handler(CallbackQueryHandler(download_music, pattern="^dl_"))
    
    app_bot.run_polling()

if __name__ == '__main__':
    main()
    
