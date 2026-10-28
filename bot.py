import os
import telebot
from flask import Flask, request

TOKEN = "9274510322:AAGrIXaBoz4Gb0eGOmkPcT5COEwhh2Mekis"
APP_URL = "https://video-to-image-bot-xxxx.onrender.com"  # Ningalude Render URL iviade nalkuka
CHANNEL_ID = "@jshshajanansh"

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

@server.route('/' + TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route('/')
def index():
    return "Video Bot is running!", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hi! 👋 Send me a video, and I'll forward it to the channel!")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    try:
        bot.reply_to(message, "⚙️ Forwarding video to the channel... Please wait!")
        
        # User ayakunna video straight aayi channel-ilekk forward cheyyunnu (caption illathe)
        bot.send_video(CHANNEL_ID, message.video.file_id)
        
        bot.reply_to(message, "✅ Done! Video successfully forwarded to the channel.")
        
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL + '/' + TOKEN)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
