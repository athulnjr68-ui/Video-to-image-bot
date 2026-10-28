import os
import cv2
import telebot
from flask import Flask, request

TOKEN = "9274510322:AAGrIXaBoz4Gb0eGOmkPcT5COEwhh2Mekis"
APP_URL = "https://video-to-image-bot-xxxx.onrender.com"  # ഇവിടെ നിങ്ങളുടെ റെണ്ടർ ലിങ്ക് നൽകുക (xxxx എന്നുള്ള ഭാഗത്ത് നിങ്ങളുടെ ആപ്പ് ലിങ്കിലെ അക്ഷരങ്ങൾ വരും)
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
    bot.reply_to(message, "Hi! 👋 Send me a video, and I'll extract frames at 10 FPS and send them to you and the channel!")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    try:
        bot.reply_to(message, "⚙️ Processing video at 10 FPS... Please wait!")
        
        # Download video
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        video_path = "temp_video.mp4"
        with open(video_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # Open video with OpenCV
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
        max_photos = 30  # Spam ഒഴിവാക്കാൻ പരമാവധി ഫ്രെയിമുകളുടെ പരിധി
        
        while success and saved_count < max_photos:
            if count % frame_interval == 0:
                frame_path = f"frame_{saved_count + 1}.jpg"
                cv2.imwrite(frame_path, image)
                
                user_name = message.from_user.first_name or "User"
                
                # Send extracted photo back to user
                with open(frame_path, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption=f"📸 Frame {saved_count + 1}")
                
                # Send extracted photo to your Channel
                with open(frame_path, 'rb') as photo_channel:
                    bot.send_photo(CHANNEL_ID, photo_channel, caption=f"📸 Frame {saved_count + 1} from user: {user_name}")
                
                os.remove(frame_path)
                saved_count += 1
                
            success, image = vidcap.read()
            count += 1
            
        vidcap.release()
        os.remove(video_path)
        
        bot.reply_to(message, f"✅ Done! Successfully extracted and broadcasted {saved_count} frames.")
        
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL + '/' + TOKEN)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
