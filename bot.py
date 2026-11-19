
import os
import re
import tempfile
import telebot
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing!")

bot = telebot.TeleBot(TOKEN)

MAX_SIZE = 49 * 1024 * 1024

PLATFORMS = {
    "tiktok.com": "TikTok",
    "instagram.com": "Instagram",
    "facebook.com": "Facebook",
    "fb.watch": "Facebook",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "x.com": "X",
    "twitter.com": "X"
}


def detect_platform(url):
    for domain, name in PLATFORMS.items():
        if domain in url.lower():
            return name
    return None


@bot.message_handler(commands=["start"])
def start(message):
    name = message.from_user.first_name or "there"

    bot.reply_to(
        message,
        f"📥 Welcome to YESITH SOCIAL MEDIA DOWNLOADER!\n\n"
        f"Hello {name}! 👋\n\n"
        f"Supported platforms:\n"
        f"• TikTok\n• Instagram\n• Facebook\n"
        f"• YouTube\n• X (Twitter)\n\n"
        f"Send a public video link to get started!"
    )


@bot.message_handler(func=lambda m: bool(m.text))
def download_video(message):
    url_match = re.search(
        r'https?://[^\s]+',
        message.text
    )

    if not url_match:
        bot.reply_to(message, "❌ Please send a valid video link.")
        return

    url = url_match.group(0).rstrip(".,!?)")
    platform = detect_platform(url)

    if not platform:
        bot.reply_to(message, "❌ Unsupported platform.")
        return

    status = bot.reply_to(
        message,
        f"✅ {platform} link detected!\n\n"
        "⏳ Processing video..."
    )

    try:
        with tempfile.TemporaryDirectory() as folder:

            options = {
                "format": "best[ext=mp4]/best",
                "outtmpl": os.path.join(folder, "video.%(ext)s"),
                "noplaylist": True,
                "max_filesize": MAX_SIZE,
                "quiet": True,
                "no_warnings": True,
                "socket_timeout": 30,
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            if not os.path.isfile(filename):
                raise Exception("Video file not found.")

            if os.path.getsize(filename) > MAX_SIZE:
                raise Exception("Video is too large for Telegram.")

            with open(filename, "rb") as video:
                bot.send_video(
                    message.chat.id,
                    video,
                    caption="✅ Downloaded by YESITH SOCIAL MEDIA DOWNLOADER"
                )

        bot.delete_message(
            message.chat.id,
            status.message_id
        )

    except Exception as error:
        bot.edit_message_text(
            "❌ Download failed.\n\n"
            "This video may be private, restricted, "
            "unsupported or too large.\n\n"
            "Please try another publicly accessible "
            "video that you are authorized to download.",
            message.chat.id,
            status.message_id
        )


print("YESITH SOCIAL MEDIA DOWNLOADER is running!")

bot.infinity_polling(
    skip_pending=True,
    timeout=30,
    long_polling_timeout=30
)
