import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Log sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

# Botingizning aniq tokeni
TOKEN = os.environ.get("TOKEN", "8842256743:AAEkul6BCTC0HtrGqfZ47gRAk2JkeogEgdY")

def search_music_deezer(query):
    """Musiqa nomidan to'g'ridan-to'g'ri MP3 va ma'lumotlarni topish (100% ishlaydi)"""
    try:
        url = f"https://api.deezer.com/search?q={query}&limit=1"
        res = requests.get(url, timeout=10).json()
        if res.get('data') and len(res['data']) > 0:
            track = res['data'][0]
            title = f"{track.get('artist', {}).get('name', '')} - {track.get('title', 'Musiqa')}"
            preview_mp3 = track.get('preview')  # MP3 fayl havolasi
            return preview_mp3, title
    except Exception as e:
        logging.error(f"Musiqa qidiruvida xatolik: {e}")
    return None, None

def download_via_cobalt(url, mode='video'):
    """Linklar (YouTube, Instagram, TikTok) uchun Cobalt API"""
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    
    payload = {
        'url': url,
        'downloadMode': 'audio' if mode == 'audio' else 'auto',
        'audioFormat': 'mp3'
    }
    
    try:
        response = requests.post('https://api.cobalt.tools/api/json', json=payload, headers=headers, timeout=20)
        data = response.json()
        
        file_url = None
        if data.get('status') in ['redirect', 'stream']:
            file_url = data.get('url')
        elif data.get('status') == 'picker' and data.get('picker'):
            file_url = data['picker'][0].get('url')
            
        if file_url:
            file_res = requests.get(file_url, stream=True, timeout=60)
            ext = 'mp3' if mode == 'audio' else 'mp4'
            filename = f"downloads/file_{os.urandom(4).hex()}.{ext}"
            
            with open(filename, 'wb') as f:
                for chunk in file_res.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            return filename
    except Exception as e:
        logging.error(f"Cobalt yuklashda xatolik: {e}")
        
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 **Universal Musiqa va Video Bot!**\n\n"
        "1. Qo'shiq nomini yozsangiz — MP3 qilib topib beraman.\n"
        "2. **Instagram, TikTok yoki YouTube** havolasini (link) yuborsangiz — video/audio yuklab beraman!",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # Agar foydalanuvchi LINK yuborgan bo'lsa
    if text.startswith("http://") or text.startswith("https://"):
        keyboard = [
            [
                InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"vid|{text}"),
                InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"aud|{text}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Formatni tanlang:", reply_markup=reply_markup)
        
    # Agar foydalanuvchi MUSIQA NOMINI yozgan bo'lsa
    else:
        status_msg = await update.message.reply_text(f"🔍 '{text}' musiqasi qidirilmoqda...")
        mp3_url, title = search_music_deezer(text)
        
        if mp3_url:
            await status_msg.edit_text("📤 Audio Telegram'ga yuborilmoqda...")
            try:
                await update.message.reply_audio(
                    audio=mp3_url, 
                    title=title, 
                    caption=f"🎵 {title}\n🤖 @uztred1bot"
                )
                await status_msg.delete()
            except Exception as e:
                logging.error(f"Audio yuborishda xatolik: {e}")
                await status_msg.edit_text("❌ Audioni yuborishda xatolik yuz berdi.")
        else:
            await status_msg.edit_text("❌ Kechirasiz, ushbu nomdagi qo'shiq topilmadi. Qayta urinib ko'ring.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("|", 1)
    mode_key = data[0]
    url = data[1]
    
    mode = 'audio' if mode_key == 'aud' else 'video'
    
    await query.edit_message_text("📥 Fayl yuklanmoqda, iltimos kuting...")
    
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    filepath = download_via_cobalt(url, mode)
    
    if filepath and os.path.exists(filepath):
        await query.edit_message_text("📤 Telegram'ga yuborilmoqda...")
        try:
            with open(filepath, 'rb') as f:
                if mode == 'audio':
                    await query.message.reply_audio(audio=f)
                else:
                    await query.message.reply_video(video=f)
            await query.message.delete()
        except Exception as e:
            logging.error(f"Yuborishda xatolik: {e}")
            await query.edit_message_text("❌ Faylni yuborishda xatolik yuz berdi.")
            
        if os.path.exists(filepath):
            os.remove(filepath)
    else:
        await query.edit_message_text("❌ Link orqali yuklab bo'lmadi. Havola to'g'riligini tekshiring.")

if __name__ == '__main__':
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Bot muvaffaqiyatli ishga tushdi!")
    app.run_polling()
    
