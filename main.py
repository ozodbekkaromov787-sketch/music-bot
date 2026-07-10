import os
import json
import logging
import re
import urllib.request
import urllib.parse
import glob
from threading import Thread
from flask import Flask
import yt_dlp
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
    """Faqat ro'yxatni chiroyli ko'rsatish uchun Deezer qidiruvi"""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.deezer.com/search?q={encoded_query}&limit=10"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get('data', [])
    except Exception as e:
        logging.error(f"Deezer error: {e}")
    return []

def download_by_text_or_url(target, mode='audio'):
    """yt-dlp orqali linkni ham, shunchaki matnli qidiruvni ham TO'LIQ yuklash"""
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    unique_id = os.urandom(4).hex()
    
    # Agar target link bo'lmasa, uni YouTube qidiruviga aylantiramiz
    if not target.startswith("http://") and not target.startswith("https://"):
        search_target = f"ytsearch1:{target} audio"
    else:
        search_target = target

    if mode == 'audio':
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': f'downloads/media_{unique_id}.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True
        }
    else:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': f'downloads/media_{unique_id}.mp4',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_target])
            
        files = glob.glob(f"downloads/media_{unique_id}.*")
        if files:
            return files[0]
    except Exception as e:
        logging.error(f"yt-dlp yuklash xatosi: {e}")
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 **Musiqa va Video yuklovchi professional bot!**\n\n"
        "• Qo'shiq nomini yozing — TO'LIQ variantini topib beraman.\n"
        "• Har qanday linkni yuboring — audio yoki video qilib yuklab beraman.", 
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if "http://" in text or "https://" in text:
        urls = re.findall(r'https?://[^\s]+', text)
        target_url = urls[0] if urls else text
        
        keyboard = [
            [
                InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"vid|{target_url}"), 
                InlineKeyboardButton("🎵 Audio", callback_data=f"aud|{target_url}")
            ]
        ]
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
            # Agar Deezer ro'yxat topa olmasa, to'g'ridan-to'g'ri yozilgan matn bo'yicha qidirib yuklab olish tugmasi
            keyboard = [[InlineKeyboardButton("🔍 To'g'ridan-to'g'ri yuklash", callback_data=f"force_dl|{text}")]]
            await status_msg.edit_text("⚠️ Ro'yxat topilmadi. Quyidagi tugma orqali qidirib ko'ring:", reply_markup=InlineKeyboardMarkup(keyboard))

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
            
            msg = await query.message.reply_text(f"📥 **{artist} - {title}** (To'liq versiya) qidirilmoqda va yuklanmoqda...")
            
            # Endi 29 soniyalik linkni emas, to'g'ridan-to'g'ri nomi bo'yicha to'liq audioni qidiramiz
            search_query = f"{artist} {title}"
            filepath = download_by_text_or_url(search_query, mode='audio')
            
            # Agar to'liq variant o'xshamasa, oxirgi chora sifatida preview yuklaydi
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
                
    elif data.startswith("force_dl|"):
        search_query = data.split("|")[1]
        msg = await query.message.reply_text(f"📥 **{search_query}** yuklanmoqda...")
        filepath = download_by_text_or_url(search_query, mode='audio')
        
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, 'rb') as audio_file:
                    await query.message.reply_audio(audio=audio_file, caption=f"🎵 {search_query}\n🤖 @uztred1bot")
                await msg.delete()
            except Exception as e:
                await msg.edit_text("❌ Yuborishda xatolik.")
            if os.path.exists(filepath):
                os.remove(filepath)
        else:
            await msg.edit_text("❌ Topilmadi.")

    elif data.startswith("vid|") or data.startswith("aud|"):
        mode_key, url = data.split("|", 1)
        mode = 'audio' if mode_key == 'aud' else 'video'
        await query.edit_message_text("📥 Havola yuklanmoqda...")
        
        filepath = download_by_text_or_url(url, mode)
        if filepath and os.path.exists(filepath):
            await query.message.reply_text("📤 Telegram'ga yuborilmoqda...")
            try:
                with open(filepath, 'rb') as f:
                    if mode == 'audio':
                        await query.message.reply_audio(audio=f, caption="🤖 @uztred1bot")
                    else:
                        await query.message.reply_video(video=f, caption="🤖 @uztred1bot")
                await query.message.delete()
            except Exception as e:
                await query.edit_message_text("❌ Faylni yuborishda xatolik.")
            if os.path.exists(filepath):
                os.remove(filepath)
        else:
            await query.edit_message_text("❌ Afsuski, yuklab olish imkoni bo'lmadi.")

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
            
