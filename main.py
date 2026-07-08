os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Loglarni sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Bot tokenini shu yerga yozasiz
TOKEN = os.environ.get("TOKEN", "8842256743:AAEkul6BCTC0HtrGqfZ47gRAk2JkeogEgdY")

# YouTube'dan qidirish funksiyasi
def search_yt(query):
    ydl_opts = {
        'format': 'bestaudio',
        'default_search': 'ytsearch',
        'quiet': True,
        'nocheckcertificate': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info and len(info['entries']) > 0:
                video = info['entries'][0]
                return video['webpage_url'], video['title']
            return None, None
        except Exception as e:
            logging.error(f"YouTube izlashda xatolik: {e}")
            return None, None

# /start buyrug'i kelganda
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Musiqa botiga xush kelibsiz! Musiqa nomini yoki ijrochini yuboring.")

# Musiqa nomini qidirish
async def find_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_message = await update.message.reply_text(f"🔍 '{query}' qidirilmoqda...")
    
    url, title = search_yt(query)
    
    if url:
        await status_message.edit_text(f"✅ Topildi:\n\n🎵 *{title}*\n🔗 {url}", parse_mode="Markdown")
    else:
        await status_message.edit_text("❌ Hech narsa topilmadi yoki qidiruvda xatolik yuz berdi. Boshqa nom kiritib ko'ring.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), find_song))

    print("Bot muvaffaqiyatli ishga tushdi!")
    app.run_polling()

