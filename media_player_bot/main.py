import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from pytgcalls.exceptions import NotInCallError

from config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING
from search_engine import download_media

# Proxy settings if needed (as seen in the original project)
proxy = {
    "scheme": "http",
    "hostname": "127.0.0.1",
    "port": 7897,
}
# os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
# os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"

if not all([API_ID, API_HASH, BOT_TOKEN, SESSION_STRING]):
    print("Error: Missing credentials in .env file. Please configure them.")
    exit(1)

# Initialize bot and assistant client
bot = Client(
    "bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user_client = Client(
    "user_session",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

call_py = PyTgCalls(user_client)

@bot.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text("سلام! من ربات پخش‌کننده مدیا هستم. \nبرای پخش یک ویدیو یا موزیک، نام یا توصیف آن را با دستور 'پخش' بفرستید.\nمثال: پخش موزیک پاپ\nبرای توقف: توقف\nبرای مکث: مکث")

@bot.on_message(filters.group & filters.text & ~filters.command(["start", "help"]))
async def handle_text_commands(client: Client, message: Message):
    text = message.text.strip()
    chat_id = message.chat.id

    # Handle "پخش" on reply
    if text == "پخش" and message.reply_to_message:
        replied = message.reply_to_message
        if replied.audio or replied.video or replied.voice or replied.document:
            m = await message.reply_text("در حال دانلود فایل از گروه...")
            file_path = await replied.download()
            if not file_path:
                await m.edit_text("خطا در دانلود فایل.")
                return

            try:
                await call_py.play(
                    message.chat.id,
                    MediaStream(
                        file_path
                    )
                )
                await m.edit_text("▶️ پخش فایل در ویس‌چت شروع شد.")
            except Exception as e:
                await m.edit_text(f"خطا در پخش: {str(e)}")
        return

    # Handle "پخش " (Play with query)
    if text.startswith("پخش "):
        query = text[4:].strip()
        if not query:
            return

        m = await message.reply_text(f"در حال جستجو و دانلود `{query}` ... لطفا صبر کنید.")
        media_info = await download_media(query)

        if not media_info or not media_info.get("file_path"):
            await m.edit_text("متاسفانه نتوانستم مدیا را پیدا یا دانلود کنم.")
            return

        try:
            await call_py.play(
                chat_id,
                MediaStream(
                    media_info["file_path"]
                )
            )
            await m.edit_text(f"▶️ پخش شروع شد:\nعنوان: {media_info['title']}")
        except Exception as e:
            await m.edit_text(f"خطا در پخش: {str(e)}\n(آیا دستیار ربات در گروه عضو است و ویس‌چت فعال است؟)")

    # Handle "مکث" (Pause)
    elif text == "مکث":
        try:
            await call_py.pause_stream(chat_id)
            await message.reply_text("⏸ پخش مکث شد.")
        except NotInCallError:
            pass
        except Exception as e:
            await message.reply_text(f"خطا: {str(e)}")

    # Handle "ادامه" (Resume)
    elif text == "ادامه":
        try:
            await call_py.resume_stream(chat_id)
            await message.reply_text("▶️ پخش ادامه یافت.")
        except NotInCallError:
            pass
        except Exception as e:
            await message.reply_text(f"خطا: {str(e)}")

    # Handle "توقف" (Stop)
    elif text == "توقف":
        try:
            await call_py.leave_call(chat_id)
            await message.reply_text("⏹ پخش متوقف شد و از ویس‌چت خارج شدم.")
        except NotInCallError:
            pass
        except Exception as e:
            await message.reply_text(f"خطا: {str(e)}")

async def main():
    await user_client.start()
    await bot.start()
    await call_py.start()
    print("Bot and PyTgCalls are running...")

    # Keep the process alive
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
