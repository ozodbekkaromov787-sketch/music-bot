import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

# Log sozlamalari
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Tokeni
TOKEN = os.getenv("BOT_TOKEN", "8842256743:AAEkul6BCTC0HtrGqfZ47gRAk2JkeogEgdY")

# Render serverini uxlab qolmasligi uchun Flask
app = Flask('')

@app.route('/')
def home():
    return "Bot faol holatda!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# /start buyrug'i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Salom! Qo'shiq nomi yoki ijrochini yozing, men sizga to'liq musiqani topib beraman.")

# Qidiruv funksiyasi
async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text("🔍 Qidirilmoqda, biroz kuting...")
    
    # Jamendo va Deezer ochiq bazalaridan qidirish
    url = f"https://api.deezer.com/search?q={query}&limit=5"
    try:
        res = requests.get(url, timeout=10).json()
        tracks = res.get('data', [])
        
        if not tracks:
            await status_msg.edit_text("❌ Afsuski, hech qanday musiqa topilmadi.")
            return

        keyboard = []
        text = "🎵 **Topilgan musiqalar:**\n\n"
        
        for idx, track in enumerate(tracks, 1):
            title = track.get('title')
            artist = track.get('artist', {}).get('name')
            track_id = track.get('id')
            
            text += f"{idx}. {artist} - {title}\n"
            keyboard.append([InlineKeyboardButton(f"📥 {idx}-musiqani yuklash", callback_data=f"tr_{track_id}")])
            
        await status_msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        await status_msg.edit_text("❌ Qidiruvda xatolik yuz berdi.")

# Yuklab berish funksiyasi
async def download_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    track_id = query.data.split('_')[1]
    msg = await query.message.reply_text("📥 Musiqa serverdan yuklanmoqda...")
    
    try:
        track_info = requests.get(f"https://api.deezer.com/track/{track_id}", timeout=10).json()
        preview_url = track_info.get('preview')
        title = track_info.get('title')
        artist = track_info.get('artist', {}).get('name')
        
        if preview_url:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=preview_url,
                title=title,
                performer=artist
            )
            await msg.delete()
        else:
            await msg.edit_text("❌ Ushbu faylni yuklab bo'lmadi.")
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        await msg.edit_text("❌ Yuborishda xatolik yuz berdi.")

def main():
    Thread(target=run_flask).start()
    
    app_bot = Application.builder().token(TOKEN).build()
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))
    app_bot.add_handler(CallbackQueryHandler(download_music, pattern="^tr_"))
    
    app_bot.run_polling()

if __name__ == '__main__':
    main()
    
