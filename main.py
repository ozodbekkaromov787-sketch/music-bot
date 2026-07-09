import os
import json
import logging
import re
import urllib.request
import urllib.parse
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.environ.get("TOKEN", "8842256743:AAEkul6BCTC0HtrGqfZ47gRAk2JkeogEgdY")

web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot faol ishlamoqda!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def search_deezer_list(query):
    """Musiqalarni aniq va tezkor topish"""
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

def get_youtube_link(search_query):
    """Qo'shiq nomi orqali YouTube'dan to'g'ridan-to'g'ri birinchi linkni topish"""
    try:
        encoded_query = urllib.parse.quote(search_query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode()
            video_ids = re.findall(r"watch\?v=(\S{11})", html)
            if video_ids:
                return f"https://www.youtube.com/watch?v={video_ids[0]}"
    except Exception as e:
        logging.error(f"YouTube link olishda xato: {e}")
    return None

def download_via_cobalt(url, mode='audio'):
    """Cobalt API orqali aniq havola (URL) orqali to'liq yuklash"""
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
        with urllib.request.urlopen(req, timeout=35) as response:
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
                with urllib.request.urlopen(file_req, timeout=120) as res, open(filename, 'wb') as f:
                    f.write(res.read())
                return filename
    except Exception as e:
        logging.error(f"Cobalt yuklash xatosi: {e}")
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 **Musiqa va Video yuklovchi bot!**\n\n"
        "Qo'shiq nomini yozing yoki istalgan linkni (YouTube, TikTok, Instagram) yuboring.", 
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text.startswith("http://") or text.startswith("https://"):
        keyboard = [[InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"vid|{text}"), InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"aud|{text}")]]
        await update.message.reply_text("Formatni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        status_msg = await update.message.reply_text(f"🔍 \"{text}\" qidirilmoqda...")
        tracks = search_deezer_list(text)
        
        if tracks:
            msg_text = f"🔍 **\"{text}\"** bo'yicha topilgan musiqalar:\n\n"
            keyboard_row1, keyboard_row2 = [], []
            context.user_data['tracks'] = tracks
            
            for idx, track in enumerate(tracks, 1):
                artist = track.get('artist', {}).get('name', 'Noma\'lum')
                title = track.get('title', 'Musiqa')
                msg_text += f"**{idx}.** {artist} - {title}\n"
                
                btn = InlineKeyboardButton(str(idx), callback_data=f"dl_tr|{idx-1}")
                if idx <= 5:
                    keyboard_row1.append(btn)
                else:
                    keyboard_row2.append(btn)
            
            keyboard = [keyboard_row1]
            if keyboard_row2:
                keyboard.append(keyboard_row2)
                
            await status_msg.edit_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await status_msg.edit_text("❌ Kechirasiz, ushbu nomdagi qo'shiq topilmadi.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("dl_tr|"):
        idx = int(data.split("|")[1])
        tracks = context.user_data.get('tracks', [])
        
        if idx < len(tracks):
            track = tracks[idx]
            artist = track.get('artist', {}).get('name', 'Noma\'lum')
            title = track.get('title', 'Musiqa')
            
            msg = await query.message.reply_text(f"📥 **{artist} - {title}** (To'liq versiya) yuklanmoqda...")
            
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
            
            # 1. YouTube'dan to'liq linkini qidirib topamiz
            yt_link = get_youtube_link(f"{artist} {title} audio")
            filepath = None
            
            # 2. Agar YouTube link topilsa, Cobalt orqali yuklaymiz
            if yt_link:
                filepath = download_via_cobalt(yt_link, mode='audio')
                
            # 3. Zaxira: Agar Cobalt yuklay olmasa, Deezer preview (30s) yuklanadi
            is_preview = False
            if not filepath or not os.path.exists(filepath):
                mp3_url = track.get('preview')
                if mp3_url:
                    is_preview = True
                    filepath = f"downloads/{artist} - {title}.mp3".replace('/', '_').replace('\\', '_')
                    file_req = urllib.request.Request(mp3_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(file_req, timeout=30) as res, open(filepath, 'wb') as f:
                        f.write(res.read())
            
            if filepath and os.path.exists(filepath):
                await msg.edit_text("📤 Telegram'ga yuborilmoqda...")
                try:
                    caption_text = f"🎵 **{artist} - {title}**\n🤖 @uztred1bot"
                    if is_preview:
                        caption_text += "\n\n⚠️ *Diqqat: To'liq versiyasi topilmadi, qisqa variant yuborildi.*"
                        
                    with open(filepath, 'rb') as audio_file:
                        await query.message.reply_audio(
                            audio=audio_file, 
                            title=title, 
                            performer=artist, 
                            caption=caption_text, 
                            parse_mode="Markdown"
                        )
                    await msg.delete()
                except Exception as e:
                    logging.error(f"Yuborishda xato: {e}")
                    await msg.edit_text("❌ Audioni yuborishda xatolik yuz berdi.")
                if os.path.exists(filepath):
                    os.remove(filepath)
            else:
                await msg.edit_text("❌ Musiqani yuklab bo'lmadi.")
                
    elif data.startswith("vid|") or data.startswith("aud|"):
        mode_key, url = data.split("|", 1)
        mode = 'audio' if mode_key == 'aud' else 'video'
        await query.edit_message_text("📥 Havola yuklanmoqda...")
        
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
                logging.error(f"Link yuborishda xato: {e}")
                await query.edit_message_text("❌ Faylni yuborishda xatolik.")
            if os.path.exists(filepath):
                os.remove(filepath)
        else:
            await query.edit_message_text("❌ Link orqali yuklab bo'lmadi.")

if __name__ == '__main__':
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    Thread(target=run_flask).start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Bot muvaffaqiyatli ishga tushdi!")
    app.run_polling()
        
