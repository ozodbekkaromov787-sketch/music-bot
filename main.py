import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# Loglarni sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

TOKEN = os.environ.get("TOKEN", "8842256743:AAEkul6BCTC0HtrGqfZ47gRAk2JkeogEgdY")

def get_downloader_opts(mode, output_path):
    """Yuklash rejimi (video yoki audio) uchun sozlamalar"""
    ydl_opts = {
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        # Blokirovkadan qochish uchun universal brauzer sarlavhalari
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    }
    
    if mode == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        # Telegram 50MB gacha fayl ko'targani uchun eng yaxshi lekin siqilgan formatni oladi
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        })
        
    return ydl_opts

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌟 **Universal Yuklovchi Botga xush kelibsiz!**\n\n"
        "Menga YouTube, Instagram, TikTok yoki boshqa platformalardan video havolasini (link) yuboring. "
        "Men uni sizga video yoki MP3 formatida yuklab beraman!",
        parse_mode="Markdown"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("❌ Iltimos, faqat to‘g‘ri video havolasini (link) yuboring.")
        return

    # Tugmalarni yaratish
    keyboard = [
        [
            InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"vid|{url}"),
            InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"aud|{url}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Formatni tanlang:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("|", 1)
    mode_key = data[0]  # 'vid' yoki 'aud'
    url = data[1]
    
    mode = 'audio' if mode_key == 'aud' else 'video'
    
    await query.edit_message_text("📥 Fayl serverga yuklanmoqda, kuting...")
    
    output_dir = "downloads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    ydl_opts = get_downloader_opts(mode, output_dir)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if mode == 'audio':
                base, _ = os.path.splitext(filename)
                final_file = base + ".mp3"
            else:
                # Agar video mp4 bo'lmasa yoki format o'zgargan bo'lsa tekshiramiz
                final_file = filename if os.path.exists(filename) else None
                if not final_file:
                    base, _ = os.path.splitext(filename)
                    for ext in ['.mp4', '.mkv', '.webm']:
                        if os.path.exists(base + ext):
                            final_file = base + ext
                            break

            if final_file and os.path.exists(final_file):
                await query.edit_message_text("📤 Telegram'ga jo‘natilmoqda...")
                
                with open(final_file, 'rb') as f:
                    if mode == 'audio':
                        await query.message.reply_audio(audio=f, title=info.get('title', 'Musiqa'))
                    else:
                        await query.message.reply_video(video=f, caption=info.get('title', 'Video'))
                
                await query.message.delete()
                os.remove(final_file)
            else:
                await query.edit_message_text("❌ Fayl topilmadi yoki yuklashda xatolik yuz berdi.")
                
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await query.edit_message_text("❌ Ushbu linkni yuklab bo‘lmadi. Havola to‘g‘riligini yoki video yopiq emasligini tekshiring.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Bot muvaffaqiyatli ishga tushdi!")
    app.run_polling()
    
