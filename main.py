
import logging
import os
from telegram.ext import ApplicationBuilder, MessageHandler, filters
import yt_dlp
logging.basicConfig(level=logging.INFO)
def search_yt(query):
ydl_opts = {'format': 'bestaudio', 'default_search': 'ytsearch', 'quiet': True}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
try:
info = ydl.extract_info(query, download=False)
video = info['entries'][0]
return video['webpage_url'], video['title']
except Exception as e:
logging.error(f"YouTube'dan izlashda xatolik: {e}")
return None, None
async def find_song(update, context):
query = update.message.text
await update.message.reply_text("Qidirilmoqda...")
url, title = search_yt(query)
if url:
await update.message.reply_text(f"Topildi: {title}\n{url}")
else:
await update.message.reply_text("Hech narsa topilmadi yoki xatolik yuz berdi.")
if name == 'main':
token = os.environ.get("TOKEN")
application = ApplicationBuilder().token(token).build()
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), find_song))
application.run_polling()
