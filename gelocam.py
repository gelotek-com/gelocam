from threading import Thread
import telebot
from flask import Flask, jsonify, request
import cv2
import os
import time

app = Flask(__name__)

current_command = "null"

TOKEN = ''
PERSONAL_CHAT_ID = 

bot = telebot.TeleBot(TOKEN)

# Files for saving images
SAVE_FOLDER = './photos'
os.makedirs(SAVE_FOLDER, exist_ok=True)

# counter for received photos
photo_counter = 0
photos_number = 20



        #HTTP SERVER 

@app.route('/upload', methods=['POST'])
def upload_photo():
    global photo_counter

    photo_data = request.data
    if not photo_data:
        return jsonify({"error": "No photo data"}), 400

    # Save photo
    filename = os.path.join(SAVE_FOLDER, f'photo_{photo_counter}.jpg')
    with open(filename, 'wb') as f:
        f.write(photo_data)

    print(f"Picture {photo_counter + 1} saved: {filename}")
    photo_counter += 1

    # separate the thread to avoid problems
    if photo_counter >= photos_number:
        Thread(target=handle_video_creation).start()
        photo_counter = 0  # reset for next videos

    return jsonify({"status": "photo received", "count": photo_counter})


def handle_video_creation():
    time.sleep(0.5)  # Waiting for all photos
    create_video()

    video_path = os.path.join(SAVE_FOLDER, 'video_esp.mp4')
    try:
        with open(video_path, "rb") as video:
            bot.send_video(PERSONAL_CHAT_ID, video, caption="Here's your video")
            print("Video sent successfully.")
    except FileNotFoundError:
        print("Video file not found. Something went wrong.")


def create_video():
    images = []
    for i in range(photos_number):
        path_img = os.path.join(SAVE_FOLDER, f'photo_{i}.jpg')
        img = cv2.imread(path_img)
        if img is None:
            print(f"Error loading {path_img}")
            return
        images.append(img)

    #  video dimension = pic dimension
    height, width, layers = images[0].shape
    video_path = os.path.join(SAVE_FOLDER, 'video_esp.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(video_path, fourcc, 4, (width, height))  # 3 fps

    for img in images:
        video.write(img)

    video.release()
    print(f"Video created: {video_path}")








@app.route('/command', methods=['GET'])
#with this method, the ESP as a client knows when to record
def command():
    global current_command
    cmd = current_command
    current_command = "null"
    return jsonify({"command": cmd})





        #TELEGRAM UI

@bot.message_handler(commands=['video'])
def handle_foto(message):
    if message.chat.id != PERSONAL_CHAT_ID:
        bot.reply_to(message, "Unauthorized.")
        return

    global current_command
    current_command = "take_video"
    bot.send_message(message.chat.id, "Video request sent to ESP32.")

@bot.message_handler(commands=['help'])
def help_message(message):
    if message.chat.id != PERSONAL_CHAT_ID:
        bot.reply_to(message, "Unauthorized.")
        return

    bot.send_message(message.chat.id, "/video - Receive a 5-second video from the ESP32.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.chat.id != PERSONAL_CHAT_ID:
        return
    
    #bot.reply_to(message, "/help to see all available commands")
    bot.send_message(message.chat.id, "/help to see all available commands")

def run_bot():
    print("Telegram Bot started...")
    bot.polling()



        #MAIN

if __name__ == '__main__':
    # Starting telegram bot polling with a different thread
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Starting Flask server on main thread 
    print("Flask server started...")
    app.run(host='0.0.0.0', port=5000)
