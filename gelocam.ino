#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "esp_camera.h"

const char* ssid = "";
const char* password = "";

// URL for HTTP communication
const char* flask_server = "http://192.168.1.x:5000";

// Number of photos per video
const int NUM_PICS = 20;

// Camera configuration
#define PWDN_GPIO_NUM    -1
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM    15
#define SIOD_GPIO_NUM    4
#define SIOC_GPIO_NUM    5

#define Y9_GPIO_NUM      16
#define Y8_GPIO_NUM      17
#define Y7_GPIO_NUM      18
#define Y6_GPIO_NUM      12
#define Y5_GPIO_NUM      10
#define Y4_GPIO_NUM      8
#define Y3_GPIO_NUM      9
#define Y2_GPIO_NUM      11

#define VSYNC_GPIO_NUM   6
#define HREF_GPIO_NUM    7
#define PCLK_GPIO_NUM    13

void send_video() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    return;
  }

  for (int i = 0; i < NUM_PICS; i++) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      return;
    }

    HTTPClient http;
    String url = String(flask_server) + "/upload";
    http.begin(url);
    http.addHeader("Content-Type", "image/jpeg");

    int httpResponseCode = http.POST(fb->buf, fb->len);
    if (httpResponseCode > 0) {
      Serial.printf("Photo %d sent. Response: %d\n", i+1, httpResponseCode);
    } else {
      Serial.printf("Error sending photo %d: %s\n", i+1, http.errorToString(httpResponseCode).c_str());
    }

    http.end();
    esp_camera_fb_return(fb);

    delay(500); // Delay between sending photos
  }
}

void photo_check() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    return;
  }

  while (1) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      return;
    }

    HTTPClient http;
    String url = String(flask_server) + "/check";
    http.begin(url);
    http.addHeader("Content-Type", "image/jpeg");

    int httpResponseCode = http.POST(fb->buf, fb->len);

    if (httpResponseCode > 0) {
      Serial.printf("Photo sent. Response: %d\n", httpResponseCode);

      String payload = http.getString();
      Serial.println("Server response: " + payload);

      // Parse JSON
      DynamicJsonDocument doc(512);
      DeserializationError error = deserializeJson(doc, payload);

      if (!error) {
        const char* action = doc["action"];
        const char* mode = doc["mode"];

        if (String(action) == "video") {
          Serial.println("ALERT received");
          esp_camera_fb_return(fb);
          delay(500);
          send_video();
        }
        if (String(mode) == "sensor") {
          Serial.println("Continuing to check...");
        }
        if (String(mode) == "null") {
          Serial.println("Stopping...");
          esp_camera_fb_return(fb);
          delay(500);
          break;
        }

      } else {
        Serial.println("JSON parsing error");
      }

    } else {
      Serial.printf("Error sending photo: %s\n", http.errorToString(httpResponseCode).c_str());
    }

    http.end();
    esp_camera_fb_return(fb);
    delay(500);
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    Serial.println("PSRAM found.");
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.grab_mode = CAMERA_GRAB_LATEST;
  } else {
    Serial.println("PSRAM NOT found.");
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
    config.fb_location = CAMERA_FB_IN_DRAM;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  }

  esp_err_t err = esp_camera_init(&config);

  if (err != ESP_OK) {
    Serial.printf("Camera init failed! Error code: 0x%x\n", err);
  } else {
    Serial.println("Camera initialized successfully.");
  }
}

void loop() {
  // The ESP checks every 10 seconds for new commands
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(flask_server) + "/command";
    http.begin(url);
    int httpCode = http.GET();

    if (httpCode > 0) {
      String payload = http.getString();
      Serial.println("Flask response: " + payload);

      StaticJsonDocument<200> doc;
      DeserializationError error = deserializeJson(doc, payload);

      if (!error) {
        const char* command = doc["command"];
        Serial.println("Command received: " + String(command));

        if (strcmp(command, "take_video") == 0) {
          Serial.println("Recording!");
          send_video();
        }

        if (strcmp(command, "motion_sensor") == 0) {
          Serial.println("ESP is watching!");
          photo_check();
        }

      } else {
        Serial.println("Error parsing JSON");
      }
    } else {
      Serial.printf("HTTP request error: \n", httpCode);
    }
    http.end();
  } else {
    Serial.println("WiFi not connected");
  }

  delay(5000); // Polling delay
}
