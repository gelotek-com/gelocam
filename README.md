# 📷 Gelocam

**Gelocam** is a DIY video surveillance system based on the **ESP32-S3-WROOM**, designed to receive remote video requests via **Telegram**.

---

## 🧠 How It Works

- The **ESP32-S3** acts as a **camera module** and connects via **Wi-Fi** to a **PC or Raspberry Pi**.
- The PC runs a custom **Python application** that functions as both a **Telegram bot** and a **local HTTP server**.
- When a user sends the `/video` command via Telegram:
  1. The bot sends an HTTP command to the ESP32.
  2. The ESP32 captures a series of photos and sends them to the server.
  3. The server stitches them into a video and sends it back to the user on Telegram.

---

## 🆕 Version 1.1 – Motion Detection Mode

This update introduces a new **motion detection mode** to enhance surveillance capabilities.

- Users can activate this mode via Telegram.
- The ESP32 captures a photo every **0.5 seconds**.
- Each new image is compared with the previous one by the server.
- If a **difference** is detected, the server:
  - Saves the triggering frame.
  - Automatically generates a video using the same process as `/video`.


---

## 📄 License

MIT License