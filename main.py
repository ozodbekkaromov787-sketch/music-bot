 aniqroq ko'rish uchun
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.environ.get("TOKEN")

async def start(update, context):
    await update.message.reply_text('Bot ishga tushdi! Musiqa nomini yozing.')

async def echo(update, context):
    # Hozircha shunchaki yozgan narsangizni qaytaradi
    await update.message.reply_text(f"Siz yozdingiz: {update.message.text}")

if __name__ == '__main__':
    if not TOKEN:
        print("TOKEN topilmadi!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        print("Bot ishga tushdi!")
        app.run_polling()

