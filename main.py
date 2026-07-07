logging
from telegram.ext import ApplicationBuilder, MessageHandler, filters
import yt_dlp

logging.basicConfig(level=logging.INFO)

def search_yt(query):
    ydl_opts = {'format': 'bestaudio', 'default_search': 'ytsearch1', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            video = info['entries'][0]
            return video['webpage_url'], video['title']
        except:
            return None, None

async def find_song(update, context):
    query = update.message.text
    await update.message.reply_text("🔍 Qidirilmoqda...")
    url, title = search_yt(query)
    if url:
        await update.message.reply_text(f"✅ Topildi: {title}\n🔗 {url}")
    else:
        await update.message.reply_text("❌ Uzr, topilmadi.")

if __name__ == '__main__':
    token = os.environ.get("TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), find_song))
    app.run_polling()
    


