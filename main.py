import os
import logging
import requests
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Loglarni sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

TOKEN = os.environ.get("TOKEN", "8842256743:AAEkul6BCTC0HtrGqfZ47gRAk2JkeogEgdY")

def search_youtube_full(query):
    """YouTube orqali to'liq 10 ta musiqani qidirish va ma'lumotlarini olish"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extract_flat': True,
        'default_search': 'ytsearch10'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            entries = info.get('entries', [])
            results = []
            for entry in entries:
                results.append({
                    'id': entry.get('id'),
                    'title': entry.get('title', 'Musiqa'),
                    'uploader': entry.get('uploader', 'Noma\'lum'),
                    'url': f"https://www.youtube.com/watch?v={entry.get('id')}"
                })
            return results
    except Exception as e:
        logging.error(f"YouTube qidiruv xatosi: {e}")
    return []

def download_youtube_mp3(yt_url):
    """YouTube video/musikasini to'liq MP3 formatida yuklab olish"""
    out_filename = f"downloads/audio_{os.urandom(4).hex()}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"{out_filename}.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }
    
    # Agar FFmpeg o'rnatilmagan bo'lsa, to'g'ridan-to'g'ri audio oqimini olamiz
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([yt_url])
            return f"{out_filename}.mp3"
    except Exception as e:
        logging.error(f"yt-dlp yuklash xatosi: {e}")
        
    # Zaxira usul: Cobalt API orqali to'liq audio yuklash
    return download_via_cobalt(yt_url, mode='audio')

def download_via_cobalt(url, mode='video'):
    """Cobalt API yordamida yuklab olish"""
    try:
        cobalt_url = 'https://api.cobalt.tools/api/json'
        payload = {
            'url': url,
            'downloadMode': 'audio' if mode == 'audio' else 'auto',
            'audioFormat': 'mp3'
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }
        
        response = requests.post(cobalt_url, json=payload, headers=headers, timeout=25).json()
        file_url = None
        
        if response.get('status') in ['redirect', 'stream']:
            file_url = response.get('url')
        elif response.get('status') == 'picker' and response.get('picker'):
            file_url = response['picker'][0].get('url')
            
        if file_url:
            ext = 'mp3' if mode == 'audio' else 'mp4'
            filename = f"downloads/media_{os.urandom(4).hex()}.{ext}"
            
            res = requests.get(file_url, stream=True, timeout=90)
            with open(filename, 'wb') as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filename
    except Exception as e:
        logging.error(f"Cobalt xatosi: {e}")
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 **To'liq Musiqa va Video Yuklovchi Bot!**\n\n"
        "1. **Qo'shiq nomini yozing** — to'liq versiyasini topib yuboraman.\n"
        "2. **YouTube, Instagram, TikTok linkini yuboring** — MP3 yoki MP4 qilib yuklab beraman!",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # LINK YUBORILGANDA
    if text.startswith("http://") or text.startswith("https://"):
        keyboard = [
            [
                InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"vid|{text}"),
                InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"aud|{text}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Formatni tanlang:", reply_markup=reply_markup)
        
    # MUSIQA NOMI YOZILGANDA
    else:
        status_msg = await update.message.reply_text(f"🔍 \"{text}\" bo'yicha to'liq musiqalar qidirilmoqda...")
        tracks = search_youtube_full(text)
        
        if tracks:
            msg_text = f"🔍 **\"{text}\"** bo'yicha topilgan to'liq musiqalar:\n\n"
            keyboard_row1 = []
            keyboard_row2 = []
            
            # Ma'lumotlarni saqlab turamiz
            context.user_data['tracks'] = tracks
            
            for idx, track in enumerate(tracks, 1):
                title = track.get('title', 'Musiqa')
                msg_text += f"**{idx}.** {title}\n"
                
                btn = InlineKeyboardButton(str(idx), callback_data=f"dl_yt|{idx-1}")
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
            await status_msg.edit_text("❌ Kechirasiz, ushbu nomdagi qo'shiq topilmadi.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # TO'LIQ MUSIQA TUGMASI BOSILGANDA
    if data.startswith("dl_yt|"):
        idx = int(data.split("|")[1])
        tracks = context.user_data.get('tracks', [])
        
        if idx < len(tracks):
            track = tracks[idx]
            msg = await query.message.reply_text(f"📥 **{track['title']}** (To'liq versiya) yuklanmoqda...")
            
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
                
            filepath = download_youtube_mp3(track['url'])
            
            if filepath and os.path.exists(filepath):
                await msg.edit_text("📤 Telegram'ga yuborilmoqda...")
                try:
                    with open(filepath, 'rb') as audio_file:
                        await query.message.reply_audio(
                            audio=audio_file,
                            title=track['title'],
                            performer=track['uploader'],
                            caption=f"🎵 **{track['title']}**\n🤖 @uztred1bot",
                            parse_mode="Markdown"
                        )
                    await msg.delete()
                except Exception as e:
                    logging.error(f"Yuborishda xatolik: {e}")
                    await msg.edit_text("❌ Audioni yuborishda xatolik yuz berdi.")
                
                if os.path.exists(filepath):
                    os.remove(filepath)
            else:
                await msg.edit_text("❌ Musiqani yuklab bo'lmadi.")
        else:
            await query.message.reply_text("❌ Xatolik yuz berdi, qaytadan qidirib ko'ring.")
            
    # LINK TUGMALARI BOSILGANDA (VIDEO / AUDIO)
    elif data.startswith("vid|") or data.startswith("aud|"):
        mode_key, url = data.split("|", 1)
        mode = 'audio' if mode_key == 'aud' else 'video'
        
        await query.edit_message_text("📥 Fayl yuklanmoqda, kuting...")
        
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
        
