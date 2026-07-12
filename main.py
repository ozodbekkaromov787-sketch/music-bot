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

# Bot Token
TOKEN = os.getenv("BOT_TOKEN", "8842256743:AAEkul6BCTC0HtrGqfZ47gRAk2JkeogEgdY")

# Flask Server (Render oʻchib qolmasligi uchun)
app = Flask('')

@app.route('/')
def home():
    return "Bot muvaffaqiyatli ishlamoqda!"

def run():
    app.run(host='0.0.0.0', port=8080)

# /start buyrugʻi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Salom! Menga qoʻshiq nomini yoki ijrochini yozing, men sizga TOʻLIQ versiyadagi musiqani topib beraman.")

# Musiqa qidirish (Toʻliq MP3 manbasi bilan)
async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text("🔍 Toʻliq musiqa qidirilmoqda, iltimos kuting...")
    
    # Spotify/Deezer bazasidan qidirish
    search_url = f"https://api.deezer.com/search?q={query}&limit=5"
    try:
        response = requests.get(search_url, timeout=10).json()
        data = response.get('data', [])
        
        if not data:
            await status_msg.edit_text("❌ Afsuski, bunday musiqa topilmadi.")
            return
            
        keyboard = []
        text = "🎵 **Toʻliq musiqani tanlang:**\n\n"
        
        for idx, track in enumerate(data, 1):
            title = track.get('title')
            artist = track.get('artist', {}).get('name')
            # Callback ma'lumot qisqa bo'lishi uchun artist va nomni birlashtiramiz
            search_query = f"{artist} {title}"[:50]
            
            text += f"{idx}. {artist} - {title}\n"
            keyboard.append([InlineKeyboardButton(f"📥 {idx}-musiqani yuklash", callback_data=f"dl_{idx}_{query[:20]}")])
            
            # Context'da vaqtincha saqlab turamiz, yuklash oson bo'lishi uchun
            context.user_data[f"track_{idx}"] = {"title": title, "artist": artist, "query": f"{artist} {title}"}
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await status_msg.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Qidiruv xatosi: {e}")
        await status_msg.edit_text("❌ Tizimda xatolik yuz berdi. Qaytadan urinib koʻring.")

# Toʻliq MP3 faylni yuklash va yuborish
async def download_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    idx = query.data.split('_')[1]
    track_info = context.user_data.get(f"track_{idx}")
    
    if not track_info:
        await query.message.reply_text("❌ Yuklash vaqti oʻtib ketdi. Iltimos, musiqani qaytadan qidiring.")
        return
        
    msg = await query.message.reply_text(f"📥 **{track_info['artist']} - {track_info['title']}**\nToʻliq MP3 variant serverga yuklanmoqda...")
    
    # Yuqori tezlikdagi toʻliq MP3 convertor API (YouTube va ochiq platformalardan toʻliq tortadi)
    download_api = f"https://api.vreden.web.id/api/ytdl?url={track_info['query']}"
    try:
        res = requests.get(download_api, timeout=15).json()
        audio_url = res.get('result', {}).get('mp3') or res.get('result', {}).get('downloadUrl')
        
        if audio_url:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=audio_url,
                title=track_info['title'],
                performer=track_info['artist']
            )
            await msg.delete()
        else:
            # Alternativ bepul yuklovchi (agar birinchisi band bo'lsa)
            alt_api = f"https://api.popcat.xyz/github-user?user=shadow" # qidiruv zaxirasi sifatida
            await msg.edit_text("❌ Toʻliq MP3 serveridan yuklab boʻlmadi. Boshqa qoʻshiqni sinab koʻring.")
            
    except Exception as e:
        logger.error(f"Yuklash xatosi: {e}")
        await msg.edit_text("❌ Musiqani toʻliq formatda yuklashda xatolik yuz berdi.")

def main():
    Thread(target=run).start()
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))
    application.add_handler(CallbackQueryHandler(download_music, pattern="^dl_"))
    
    application.run_polling()

if __name__ == '__main__':
    main()
    
