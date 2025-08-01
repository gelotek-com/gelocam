from threading import Thread
import telebot
from flask import Flask, jsonify, request
import cv2
import os
import time
import numpy as np

app = Flask(__name__)

current_command = "null"

TOKEN = ''
PERSONAL_CHAT_ID = 

bot = telebot.TeleBot(TOKEN)

# Files for saving images
SAVE_FOLDER = './photos'
CHECK_FOLDER = './photos_check'
os.makedirs(SAVE_FOLDER, exist_ok=True)

# counter for received photos
photo_counter = 0
photos_number = 20

# check function
first_photo_path = os.path.join('photos_check', 'first.jpg')
second_photo_path = os.path.join('photos_check', 'second.jpg')


# HTTP SERVER

def check_photos():
    screen_gray = cv2.imread(first_photo_path, 0)
    template = cv2.imread(second_photo_path, 0)
    # matching between the two photos
    res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.9
    loc = np.where(res >= threshold)

    if len(loc[0]) > 0:
        print("No worries, the images are similar.")
        return False
    else:
        print("Warning, the images are different.")
        return True 

@app.route('/check', methods=['POST'])
def check_photo():
    global current_command

    photo_data = request.data
    if not photo_data:
        return jsonify({"error": "No photo data"}), 400

    # Save photo
    filename = os.path.join(CHECK_FOLDER, f'first.jpg')
    with open(filename, 'wb') as f:
        f.write(photo_data)

    print(f"Picture saved: {filename}")
    
    if os.path.exists(second_photo_path) and os.path.exists(first_photo_path):
        if check_photos():
            print("Now creating the video...")
            bot.send_message(PERSONAL_CHAT_ID, "Check this out")
            with open(first_photo_path, "rb") as f:
                bot.send_photo(PERSONAL_CHAT_ID, f)

            os.remove(second_photo_path)
            os.remove(first_photo_path)

            if current_command == "null": 
                return jsonify({"status": "photo received", "action": "video", "mode": "null"})

            return jsonify({"status": "photo received", "action": "video", "mode": "sensor"})
        else:
            print("Now replacing the second photo with the first one.")
            os.replace(first_photo_path, second_photo_path)

            if current_command == "null": 
                return jsonify({"status": "photo received", "action": "null", "mode": "null"})

            return jsonify({"status": "photo received", "action": "null", "mode": "sensor"})
    else:
        print("Check not possible, only one photo available.")
        os.replace(first_photo_path, second_photo_path)

        if current_command == "null": 
            return jsonify({"status": "photo received", "action": "null", "mode": "null"})

        return jsonify({"status": "photo received", "action": "null", "mode": "sensor"})


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

    return "OK", 200


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

    # video dimension = picture dimension
    height, width, layers = images[0].shape
    video_path = os.path.join(SAVE_FOLDER, 'video_esp.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(video_path, fourcc, 4, (width, height))  # 4 fps

    for img in images:
        video.write(img)

    video.release()
    print(f"Video created: {video_path}")


@app.route('/command', methods=['GET'])
# ESP (as client) uses this method to know when to record
def command():
    global current_command
    cmd = current_command
    
    if current_command != "motion_sensor":
        current_command = "null"

    return jsonify({"command": cmd})


# TELEGRAM UI

@bot.message_handler(commands=['video'])
def handle_photo(message):
    if message.chat.id != PERSONAL_CHAT_ID:
        bot.reply_to(message, "Unauthorized.")
        return

    global current_command
    current_command = "take_video"
    bot.send_message(message.chat.id, "Video request sent to ESP32.")

@bot.message_handler(commands=['motion_sensor'])
def motion_sensor(message):
    if message.chat.id != PERSONAL_CHAT_ID:
        bot.reply_to(message, "Unauthorized.")
        return

    global current_command
    current_command = "motion_sensor"
    bot.send_message(message.chat.id, "motion_sensor mode is on")
    bot.send_message(message.chat.id, "/end_motion_sensor to end the mode")

@bot.message_handler(commands=['end_motion_sensor'])
def end_motion_sensor(message):
    if message.chat.id != PERSONAL_CHAT_ID:
        bot.reply_to(message, "Unauthorized.")
        return

    global current_command
    current_command = "null"

    time.sleep(1)
    if os.path.exists(second_photo_path):
        os.remove(second_photo_path)
        
    bot.send_message(message.chat.id, "motion_sensor mode disabled")

@bot.message_handler(commands=['status'])
def status(message):
    if message.chat.id != PERSONAL_CHAT_ID:
        bot.reply_to(message, "Unauthorized.")
        return

    global current_command
    bot.send_message(message.chat.id, f"Active mode: {current_command}")

@bot.message_handler(commands=['help'])
def help_message(message):
    if message.chat.id != PERSONAL_CHAT_ID:
        bot.reply_to(message, "Unauthorized.")
        return

    bot.send_message(message.chat.id, "/video - Receive a 5-second video from the ESP32.\n/motion_sensor - ESP32 will detect motion.\n/end_motion_sensor - End motion_sensor mode.\n/status - Check which mode is active.\n/help - List all available commands.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.chat.id != PERSONAL_CHAT_ID:
        return

    bot.send_message(message.chat.id, "/help to see all available commands")

def run_bot():
    print("Telegram Bot started...")
    bot.polling()


# MAIN

if __name__ == '__main__':
    # Start telegram bot polling in a separate thread
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Start Flask server on main thread
    print("Flask server started...")
    app.run(host='0.0.0.0', port=5000)
