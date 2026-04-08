/*
 * ESP32-CAM Camera Web Server
 * 
 * Hardware: ESP32 + OV2640 Camera Module
 * 
 * Connections:
 *   - GND -> GND
 *   - 3.3V -> 3.3V
 *   - U0TXD -> GPIO 1 (optional, for serial debug)
 *   - U0RXD -> GPIO 3 (optional)
 *   - GPIO 0 -> CAM_CLK
 *   - GPIO 2 -> CAM_D0
 *   - GPIO 4 -> CAM_D1
 *   - GPIO 5 -> CAM_D2
 *   - GPIO 18 -> CAM_D3
 *   - GPIO 19 -> CAM_D4
 *   - GPIO 21 -> CAM_D5
 *   - GPIO 22 -> CAM_D6
 *   - GPIO 23 -> CAM_D7
 *   - GPIO 25 -> CAM_PCLK
 *   - GPIO 26 -> CAM_HREF
 *   - GPIO 27 -> CAM_VSYNC
 *   - GPIO 32 -> CAM_SDA (SCCB)
 *   - GPIO 33 -> CAM_SCL (SCCB)
 * 
 * Upload instructions:
 *   1. Select "AI Thinker ESP32-CAM" in Tools > Board
 *   2. Set Partition Scheme: "Huge APP (3MB)"
 *   3. Hold GPIO 0 (flash button) + press EN to enter boot mode
 *   4. Upload sketch
 *   5. Reset after upload completes
 * 
 * Access: http://<IPAddress>/stream
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <esp_http_server.h>
#include <esp_timer.h>

// ============================================
// WiFi Configuration - UPDATE THESE
// ============================================
const char* ssid = "motorola";
const char* password = "edge50pro";

// ============================================
// Camera Pin Configuration
// ============================================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ============================================
// Stream HTML Page
// ============================================
const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <title>ESP32-CAM Stream</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { margin: 0; padding: 0; background: #000; }
    img { width: 100%; max-width: 640px; display: block; margin: 0 auto; }
    .container { padding: 10px; text-align: center; color: #fff; font-family: sans-serif; }
  </style>
</head>
<body>
  <div class="container">
    <h2>ESP32-CAM Video Stream</h2>
    <img id="stream" src="/stream" />
  </div>
</body>
</html>
)rawliteral";

// ============================================
// HTTP Handlers
// ============================================
static esp_err_t index_handler(httpd_req_t *req) {
  httpd_resp_send(req, INDEX_HTML, strlen(INDEX_HTML));
  return ESP_OK;
}

typedef struct {
  httpd_handle_t stream_httpd;
  size_t         jpg_buf_len;
  uint8_t       *jpg_buf;
  camera_fb_t    *fb;
} streaming_state_t;

static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    httpd_resp_send_500(req);
    return ESP_FAIL;
  }

  httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=frame");
  httpd_resp_set_hdr(req, "X-Framerate", "15");

  while (true) {
    if (fb->format != PIXFORMAT_JPEG) {
      continue;
    }

    httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
    
    fb = esp_camera_fb_get();
    if (!fb) break;
  }

  return ESP_FAIL;
}

// ============================================
// Server Configuration
// ============================================
httpd_uri_t index_uri = {
  .uri       = "/",
  .method    = HTTP_GET,
  .handler   = index_handler,
  .user_ctx  = NULL
};

httpd_uri_t stream_uri = {
  .uri       = "/stream",
  .method    = HTTP_GET,
  .handler   = stream_handler,
  .user_ctx  = NULL
};

// ============================================
// Camera Configuration
// ============================================
void startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;
  config.ctrl_port = 32768;

  httpd_handle_t server = NULL;
  if (httpd_start(&server, &config) == ESP_OK) {
    httpd_register_uri_handler(server, &index_uri);
    httpd_register_uri_handler(server, &stream_uri);
  }
}

camera_config_t getCameraConfig() {
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
  config.pin_pclk    = PCLK_GPIO_NUM;
  config.pin_vsync   = VSYNC_GPIO_NUM;
  config.pin_href    = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn    = PWDN_GPIO_NUM;
  config.pin_reset   = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size   = FRAMESIZE_VGA;  // 640x480 - good for detection
  config.jpeg_quality = 12;              // Lower = better quality
  config.fb_count     = 2;
  return config;
}

// ============================================
// Setup & Loop
// ============================================
void setup() {
  Serial.begin(115200);
  Serial.println();

  // Initialize camera
  camera_config_t config = getCameraConfig();
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  // Configure camera sensor
  sensor_t *s = esp_camera_sensor_get();
  if (s != NULL) {
    s->set_brightness(s, 1);
    s->set_contrast(s, 1);
    s->set_saturation(s, 0);
    s->set_whitebal(s, 1);
    s->set_awb_gain(s, 1);
    s->set_wb_mode(s, 0);
    s->set_exposure_ctrl(s, 1);
    s->set_aec2(s, 0);
    s->set_ae_level(s, 0);
    s->set_aec_value(s, 300);
    s->set_gain_ctrl(s, 1);
    s->set_agc_gain(s, 0);
    s->set_bpc(s, 0);
    s->set_wpc(s, 0);
  }

  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("Camera Stream Ready! Go to: http://");
  Serial.println(WiFi.localIP());

  startCameraServer();
}

void loop() {
  delay(1000);
}
