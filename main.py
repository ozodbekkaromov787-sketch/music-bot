import os
import json
import logging
import urllib.request
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Loglarni sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

TOKEN = os.environ.get("TOKEN", "8842256743:AAEkul6BCTC0HtrGqfZ47gRAk2JkeogEgdY")

def search_deezer_mp3(query):
    """Musiqa nomidan to'g'ridan-to'g'ri MP3 qidirish (Standart urllib orqali)"""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.deezer.com/search?q={encoded_query}&limit=1"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if data.get('data') and len(data['data']) > 0:
                track = data['data'][0]
                artist = track.get('artist', {}).get('name', '')
                title_track = track.get('title', '')
                full_title = f"{artist} - {title_track}"
                mp3_url = track.get('preview')
                return mp3_url, full_title
    except Exception as e:
        logging.error(f"Deezer qidiruv xatosi: {e}")
    return None, None

def download_via_cobalt(url, mode='video'):
    """Linklar (YouTube, Instagram, TikTok) uchun Cobalt API"""
    try:
        cobalt_url = 'https://api.cobalt.tools/api/json'
        payload = json.dumps({
            'url': url,
            'downloadMode': 'audio' if mode == 'audio' else 'auto',
            'audioFormat': 'mp3'
        }).encode('utf-8')
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }
        
        req = urllib.request.Request(cobalt_url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode())
            
            file_url = None
            if data.get('status') in ['redirect', 'stream']:
                file_url = data.get('url')
            elif data.get('status') == 'picker' and data.get('picker'):
                file_url = data['picker'][0].get('url')
                
            if file_url:
                ext = 'mp3' if mode == 'audio' else 'mp4'
                filename = f"downloads/file_{os.urandom(4).hex()}.{ext}"
                
                file_req = urllib.request.Request(file_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(file_req, timeout=60) as res, open(filename, 'wb') as f:
                    f.write(res.read())
                        
                return filename
    except Exception as e:
        logging.error(f"Cobalt yuklashda xatolik: {e}")
        
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 **Universal Musiqa va Video Bot!**\n\n"
        "1. **Qo'shiq nomini yozing** — topib MP3 shaklida yuboraman.\n"
        "2. **Instagram, TikTok, YouTube linkini yuboring** — video yoki audio yuklab beraman!",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # LINK yuborilgan bo'lsa
    if text.startswith("http://") or text.startswith("https://"):
        keyboard = [
            [
                InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"vid|{text}"),
                InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"aud|{text}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Formatni tanlang:", reply_markup=reply_markup)
        
    # MUSIQA NOMI yozilgan bo'lsa
    else:
        status_msg = await update.message.reply_text(f"🔍 '{text}' musiqasi qidirilmoqda...")
        mp3_url, title = search_deezer_mp3(text)
        
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
                    await query.message.reply_audio(audio=f, caption="🤖 @uztred1bot")
                else:
                    await query.message.reply_video(video=f, caption="🤖 @uztred1bot")
            await query.message.delete()
        except Exception as e:
            logging.error(f"Yuborishda xatolik: {e}")
            await query.edit_message_text("❌ Faylni yuborishda xatolik yuz berdi.")
            
        if os.path.exists(filepath):
            os.remove(filepath)
    else:
        await query.edit_message_text("❌ Ushbu link orqali yuklab bo'lmadi.")

if __name__ == '__main__':
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Bot muvaffaqiyatli ishga tushdi!")
    app.run_polling()
        
