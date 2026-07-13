import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

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
                "query": f"{artist} - {title}"
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
        
    msg = await query.message.reply_text(f"📥 **{track_info['query']}**\nTo'liq MP3 tayyorlanmoqda...")
    
    # Hech qanday yt-dlp'siz to'g'ridan-to'g'ri yuqori sifatli MP3 havola yaratuvchi ochiq API
    music_url = f"https://music-api-download.vercel.app/download?query={requests.utils.quote(track_info['query'])}"
    
    try:
        # Telegramga tayyor audio havolasini yuboramiz (Serverga og'irlik tushmaydi)
        await context.bot.send_audio(
            chat_id=query.message.chat_id,
            audio=music_url,
            title=track_info['title'],
            performer=track_info['artist'],
            timeout=60
        )
        await msg.delete()
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        # Muqobil 2-chi zaxira API server
        try:
            backup_url = f"https://yt-download-api.vercel.app/api/search?q={requests.utils.quote(track_info['query'])}"
            res = requests.get(backup_url, timeout=10).json()
            if isinstance(res, list) and len(res) > 0:
                audio_link = res[0].get('url') or res[0].get('download_url')
                if audio_link:
                    await context.bot.send_audio(
                        chat_id=query.message.chat_id,
                        audio=audio_link,
                        title=track_info['title'],
                        performer=track_info['artist']
                    )
                    await msg.delete()
                    return
            await msg.edit_text("❌ Yuklash serverida xatolik. Birozdan so'ng urining.")
        except:
            await msg.edit_text("❌ Musiqani yuklab bo'lmadi.")

def main():
    Thread(target=run_flask).start()
    
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))
    app_bot.add_handler(CallbackQueryHandler(download_music, pattern="^dl_"))
    
    app_bot.run_polling()

if __name__ == '__main__':
    main()
    
