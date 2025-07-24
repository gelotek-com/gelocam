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
