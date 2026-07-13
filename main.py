import os
import logging
import requests
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

# Loglarni sozlash
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Sizning tokeningiz joylandi:
TOKEN = os.getenv("BOT_TOKEN", "8842256743:AAEkul6BCTC0HtrGqfZ47gRAk2JkeogEgdY")

app = Flask('')

@app.route('/')
def home():
    return "Bot muvaffaqiyatli ishlamoqda!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Salom! Qo'shiq nomini yozing, men sizga TO'LIQ MP3 faylini topib beraman.")

async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text("🔍 Musiqa qidirilmoqda...")
    
    # Deezer orqali aniq nom va ijrochilarni topamiz
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
            
            text += f"{idx}. **{artist}** - {title}\n"
            keyboard.append([InlineKeyboardButton(f"📥 {idx}-musiqani yuklash", callback_data=f"dl_{idx}")])
            
            context.user_data[f"tr_{idx}"] = {
                "title": title,
                "artist": artist,
                "query": f"{artist} {title}"
            }
            
        await status_msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        await status_msg.edit_text("❌ Qidiruvda xatolik yuz berdi.")

async def download_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    idx = query.data.split('_')[1]
    track_info = context.user_data.get(f"tr_{idx}")
    
    if not track_info:
        await query.message.reply_text("❌ Qaytadan qidirib ko'ring.")
        return
        
    msg = await query.message.reply_text(f"📥 **{track_info['artist']} - {track_info['title']}**\nTo'liq MP3 yuklanmoqda...")
    
    search_q = track_info['query']
    filename = f"song_{query.from_user.id}.mp3"
    
    # SoundCloud orqali yuklash (3-5 daqiqalik to'liq MP3)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filename,
        'quiet': True,
        'default_search': 'scsearch1:',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_q])
            
        if os.path.exists(filename):
            with open(filename, 'rb') as audio_file:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=audio_file,
                    title=track_info['title'],
                    performer=track_info['artist']
                )
            os.remove(filename)
            await msg.delete()
        else:
            await msg.edit_text("❌ Faylni saqlashda xatolik bo'ldi.")
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        await msg.edit_text("❌ Yuklashda xatolik yuz berdi. Qaytadan urinib ko'ring.")

def main():
    Thread(target=run_flask).start()
    
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))
    app_bot.add_handler(CallbackQueryHandler(download_music, pattern="^dl_"))
    
    app_bot.run_polling()

if __name__ == '__main__':
    main()
        
