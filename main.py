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

def search_deezer_list(query):
    """Musiqa nomidan 10 tagacha variantlar ro'yxatini olish"""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.deezer.com/search?q={encoded_query}&limit=10"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get('data', [])
    except Exception as e:
        logging.error(f"Deezer qidiruv xatosi: {e}")
    return []

def get_deezer_track_by_id(track_id):
    """ID bo'yicha aniq bitta qo'shiq ma'lumotlarini olish"""
    try:
        url = f"https://api.deezer.com/track/{track_id}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            artist = data.get('artist', {}).get('name', 'Noma\'lum')
            title = data.get('title', 'Musiqa')
            mp3_url = data.get('preview')
            return mp3_url, artist, title
    except Exception as e:
        logging.error(f"Track ID olishda xatolik: {e}")
    return None, None, None

def download_via_cobalt(url, mode='video'):
    """YouTube, Instagram, TikTok linklari uchun Cobalt API"""
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
                filename = f"downloads/media_{os.urandom(4).hex()}.{ext}"
                
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
        "1. **Qo'shiq nomini yozing** — ro'yxatdan tanlab yuklab oling.\n"
        "2. **Instagram, TikTok, YouTube linkini yuboring** — video yoki audio qilib yuklab beraman!",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # 1. LINK YUBORILGAN BO'LSA
    if text.startswith("http://") or text.startswith("https://"):
        keyboard = [
            [
                InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"vid|{text}"),
                InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"aud|{text}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Formatni tanlang:", reply_markup=reply_markup)
        
    # 2. MUSIQA NOMI YOZILGAN BO'LSA (RO'YXAT CHIQARISH)
    else:
        status_msg = await update.message.reply_text(f"🔍 \"{text}\" qidirilmoqda...")
        tracks = search_deezer_list(text)
        
        if tracks:
            msg_text = f"🔍 **\"{text}\"** bo'yicha topilgan musiqalar:\n\n"
            keyboard_row1 = []
            keyboard_row2 = []
            
            for idx, track in enumerate(tracks, 1):
                artist = track.get('artist', {}).get('name', 'Noma\'lum')
                title = track.get('title', 'Musiqa')
                track_id = track.get('id')
                
                msg_text += f"**{idx}.** {artist} - {title}\n"
                
                # Tugmalarni 2 qatorda 5 tadan taqsimlash (1, 2, 3, 4, 5 / 6, 7, 8, 9, 10)
                btn = InlineKeyboardButton(str(idx), callback_data=f"dl_tr|{track_id}")
                if idx <= 5:
                    keyboard_row1.append(btn)
                else:
                    keyboard_row2.append(btn)
            
            keyboard = [keyboard_row1]
            if keyboard_row2:
                keyboard.append(keyboard_row2)
                
            reply_markup = InlineKeyboardMarkup(keyboard)
            await status_msg.edit_text(msg_text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await status_msg.edit_text("❌ Kechirasiz, ushbu nomdagi qo'shiq topilmadi. Qayta urinib ko'ring.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # MUSIQA TUGMASI BOSILGANDA (RO'YXATDAN)
    if data.startswith("dl_tr|"):
        track_id = data.split("|")[1]
        await query.message.reply_text("📥 Musiqa yuklanmoqda, kuting...")
        
        mp3_url, artist, title = get_deezer_track_by_id(track_id)
        if mp3_url:
            try:
                await query.message.reply_audio(
                    audio=mp3_url,
                    title=title,
                    performer=artist,
                    caption=f"🎵 **{artist} - {title}**\n🤖 @uztred1bot",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logging.error(f"Audio yuborishda xatolik: {e}")
                await query.message.reply_text("❌ Audioni yuborishda xatolik bo'ldi.")
        else:
            await query.message.reply_text("❌ Musiqani yuklab bo'lmadi.")
            
    # LINK TUGMALARI BOSILGANDA (VIDEO / AUDIO)
    elif data.startswith("vid|") or data.startswith("aud|"):
        mode_key, url = data.split("|", 1)
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
    
