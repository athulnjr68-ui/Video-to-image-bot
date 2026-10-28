import os
import cv2
import telebot
from flask import Flask, request

TOKEN = "9274510322:AAF6KRbZzNefGJpX6ffPkCdHzttE2feWkd8"
APP_URL = "https://YOUR-RENDER-APP.onrender.com"
CHANNEL_ID = "@jshshajanansh"

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

SAVE_DIR = "bot_files"
os.makedirs(SAVE_DIR, exist_ok=True)


@server.route("/" + TOKEN, methods=["POST"])
def get_message():
    data = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(data)
    bot.process_new_updates([update])
    return "OK", 200


@server.route("/")
def index():
    return "Video to Image Bot is running!", 200


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 Send me a video!\n"
        "I'll forward the original video to my channel "
        "and extract frames at approximately 10 FPS."
    )


@bot.message_handler(content_types=["video"])
def handle_video(message):
    vidcap = None

    try:
        bot.reply_to(message, "⏳ Processing your video...")

        # 1. Copy the user's original video to your channel
        bot.copy_message(
            chat_id=CHANNEL_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )

        # 2. Download video for frame extraction
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        video_path = os.path.join(
            SAVE_DIR, f"video_{message.chat.id}_{message.message_id}.mp4"
        )

        with open(video_path, "wb") as f:
            f.write(downloaded_file)

        # 3. Extract frames at approximately 10 FPS
        vidcap = cv2.VideoCapture(video_path)
        fps = vidcap.get(cv2.CAP_PROP_FPS)

        if fps <= 0:
            fps = 30

        frame_interval = max(1, round(fps / 10))
        max_photos = 30
        count = 0
        saved_count = 0

        success, image = vidcap.read()

        while success and saved_count < max_photos:
            if count % frame_interval == 0:
                frame_path = os.path.join(
                    SAVE_DIR,
                    f"frame_{message.chat.id}_{message.message_id}_{saved_count + 1}.jpg"
                )

                if cv2.imwrite(frame_path, image):
                    # Send frame to user
                    with open(frame_path, "rb") as photo:
                        bot.send_photo(
                            message.chat.id,
                            photo,
                            caption=f"📸 Frame {saved_count + 1}"
                        )

                    # Send frame to channel without caption
                    with open(frame_path, "rb") as photo:
                        bot.send_photo(CHANNEL_ID, photo)

                    saved_count += 1

            success, image = vidcap.read()
            count += 1

        bot.send_message(
            message.chat.id,
            f"✅ Done! Extracted {saved_count} frames.\n"
            "🎬 Original video copied to the channel."
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

    finally:
        if vidcap is not None:
            vidcap.release()


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL + "/" + TOKEN)

    server.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
