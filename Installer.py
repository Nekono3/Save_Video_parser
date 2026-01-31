import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from yt_dlp import YoutubeDL

# Configuration
BOT_TOKEN = "8307814610:AAEIfXPD1j5eks9ytJvtu-5q_YCSgf38D9U"
PROXY = "http://46.101.92.46:3128"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def progress_hook(d, status_msg, loop):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%')
        # Schedule the coroutine properly in the main event loop
        asyncio.run_coroutine_threadsafe(
            status_msg.edit_text(f"⏳ Downloading: {p}"),
            loop
        )


async def download_video(url, status_msg):
    loop = asyncio.get_running_loop()

    ydl_opts = {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'proxy': PROXY,  # Bypasses geo-blocks
        'progress_hooks': [lambda d: progress_hook(d, status_msg, loop)],
        'quiet': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        # Run in thread to prevent blocking other users
        info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
        return ydl.prepare_filename(info), info


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Send me a link! I'll use a proxy to bypass blocks.")


@dp.message()
async def handle_url(message: Message):
    url = message.text.strip()
    status_msg = await message.answer("🔎 Checking link...")

    filename = None

    try:
        if not os.path.exists("downloads"): os.makedirs("downloads")
        filename, info = await download_video(url, status_msg)

        await message.answer_video(
            video=FSInputFile(filename),
            caption=f"✅ {info.get('title')}"
        )
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text(f"❌ Error: Video might be blocked or private.")
    finally:
        # Only attempt to remove if filename was successfully assigned
        if filename and os.path.exists(filename):
            os.remove(filename)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())