
import os
import re
import json
import tempfile
import threading
from flask import Flask, request
import telebot
import yt_dlp

TOKEN = os.environ["BOT_TOKEN"]
PUBLIC_URL = os.environ["PUBLIC_URL"].rstrip("/")
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

MAX_SIZE = 45 * 1024 * 1024

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
    bot.reply_to(
        message,
        "📥 Welcome to YESITH SOCIAL MEDIA DOWNLOADER!\n\n"
        "Send a public video link from:\n"
        "TikTok, Instagram, Facebook, YouTube or X.\n\n"
        "Only download videos you are authorized to save."
    )


@bot.message_handler(func=lambda m: bool(m.text))
def download_video(message):
    match = re.search(r'https?://[^\s]+', message.text)

    if not match:
        bot.reply_to(message, "❌ Please send a video link.")
        return

    url = match.group(0).rstrip(".,!?)")
    platform = detect_platform(url)

    if not platform:
        bot.reply_to(message, "❌ Unsupported platform.")
        return

    status = bot.reply_to(
        message,
        f"✅ {platform} link detected!\n⏳ Processing..."
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
                "socket_timeout": 30
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            if not os.path.isfile(filename):
                raise Exception("Video file not found")

            if os.path.getsize(filename) > MAX_SIZE:
                raise Exception("Video is too large")

            with open(filename, "rb") as video:
                bot.send_video(
                    message.chat.id,
                    video,
                    caption="✅ YESITH SOCIAL MEDIA DOWNLOADER"
                )

        bot.delete_message(
            message.chat.id,
            status.message_id
        )

    except Exception:
        bot.edit_message_text(
            "❌ Download failed.\n\n"
            "Video may be private, restricted, "
            "unsupported or too large.",
            message.chat.id,
            status.message_id
        )


@app.route("/", methods=["GET"])
def home():
    return "YESITH SOCIAL MEDIA DOWNLOADER is running!"


@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    if request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    ) != WEBHOOK_SECRET:
        return "Unauthorized", 401

    data = request.get_json(silent=True)

    if data:
        update = telebot.types.Update.de_json(
            json.dumps(data)
        )

        threading.Thread(
            target=bot.process_new_updates,
            args=([update],),
            daemon=True
        ).start()

    return "OK", 200


def setup_webhook():
    bot.set_webhook(
        url=PUBLIC_URL + "/telegram",
        secret_token=WEBHOOK_SECRET
    )


setup_webhook()

print("YESITH SOCIAL MEDIA DOWNLOADER is running!")
