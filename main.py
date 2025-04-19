from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
import os

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
user_links = {}

def get_format_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Видео", callback_data='video'),
            InlineKeyboardButton("Аудио", callback_data='audio')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def download_from_youtube(url, media_type):
    filename = 'output.mp4' if media_type == 'video' else 'output.mp3'
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if media_type == 'video' else 'bestaudio',
        'outtmpl': filename,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if media_type == 'audio' else [],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return filename

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if 'youtube.com' in url or 'youtu.be' in url:
        user_id = update.message.from_user.id
        user_links[user_id] = url
        await update.message.reply_text("Что скачать?", reply_markup=get_format_keyboard())
    else:
        await update.message.reply_text("Отправь ссылку на YouTube.")

async def handle_format_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    media_type = query.data
    url = user_links.get(user_id)

    if not url:
        await query.edit_message_text("Сначала отправь ссылку на видео.")
        return

    await query.edit_message_text(f"Скачиваю {media_type}...")

    try:
        file_path = download_from_youtube(url, media_type)
        if media_type == 'video':
            await context.bot.send_video(chat_id=user_id, video=open(file_path, 'rb'))
        else:
            await context.bot.send_audio(chat_id=user_id, audio=open(file_path, 'rb'))
        os.remove(file_path)
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"Ошибка: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_format_choice))
    app.run_polling()
