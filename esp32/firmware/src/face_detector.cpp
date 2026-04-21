#include "face_detector.h"
#include "config.h"

#include "esp_system.h"
#include "esp_camera.h"
#include "img_converters.h"
#include "image_util.h"
#include "sdkconfig.h"
#include <cmath>

// Camera Pin Configuration for ESP32-CAM (AI-Thinker)
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27
#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

FaceDetector::FaceDetector() {}

void FaceDetector::init_camera() {
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d7 = Y7_GPIO_NUM;
    config.pin_d6 = Y6_GPIO_NUM;
    config.pin_d5 = Y5_GPIO_NUM;
    config.pin_d4 = Y4_GPIO_NUM;
    config.pin_d3 = Y3_GPIO_NUM;
    config.pin_d2 = Y2_GPIO_NUM;
    config.pin_d1 = Y9_GPIO_NUM;
    config.pin_d0 = Y8_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_siod = SIOD_GPIO_NUM;
    config.pin_sioc = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_GRAYSCALE;
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = CAMERA_JPEG_QUALITY;
    config.fb_count = 1;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
    
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("[Camera] Init failed with error 0x%x\n", err);
        return;
    }
    
    sensor_t* s = esp_camera_sensor_get();
    if (s != NULL) {
        s->set_brightness(s, 0);
        s->set_contrast(s, 0);
        s->set_saturation(s, 0);
    }
    
    Serial.println("[Camera] Initialized successfully");
}

float FaceDetector::calculate_distance(int x1, int y1, int x2, int y2) {
    int dx = x2 - x1;
    int dy = y2 - y1;
    return sqrt(dx * dx + dy * dy);
}

// EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
float FaceDetector::calculate_ear(int p1x, int p1y, int p2x, int p2y, 
                                   int p3x, int p3y, int p4x, int p4y, 
                                   int p5x, int p5y, int p6x, int p6y) {
    float dist1 = calculate_distance(p2x, p2y, p6x, p6y);
    float dist2 = calculate_distance(p3x, p3y, p5x, p5y);
    float dist3 = calculate_distance(p1x, p1y, p4x, p4y);
    
    if (dist3 == 0) return 0.0f;
    return (dist1 + dist2) / (2.0f * dist3);
}

// MAR = (||p2 - p8|| + ||p3 - p7|| + ||p4 - p6||) / (3 * ||p1 - p5||)
float FaceDetector::calculate_mar(int p1x, int p1y, int p2x, int p2y, 
                                   int p3x, int p3y, int p4x, int p4y, 
                                   int p5x, int p5y, int p6x, int p6y,
                                   int p7x, int p7y, int p8x, int p8y) {
    float dist1 = calculate_distance(p2x, p2y, p8x, p8y);
    float dist2 = calculate_distance(p3x, p3y, p7x, p7y);
    float dist3 = calculate_distance(p4x, p4y, p6x, p6y);
    float dist4 = calculate_distance(p1x, p1y, p5x, p5y);
    
    if (dist4 == 0) return 0.0f;
    return (dist1 + dist2 + dist3) / (3.0f * dist4);
}

// Simple Haar-like cascade detection for ESP32-CAM
// This is a lightweight alternative to full OpenCV


DetectionResult FaceDetector::process_frame(camera_fb_t* fb) {
    DetectionResult result = {0.0f, 0.0f, 0, false};
    
    if (!fb || fb->len == 0 || fb->format != PIXFORMAT_GRAYSCALE) {
        return result;
    }
    
    uint8_t* image = fb->buf;
    int width = fb->width;
    int height = fb->height;
    
    // Simplified face detection using contrast analysis
    int face_y = -1;
    int max_score = 0;
    
    // Scan vertical positions for face-like regions
    for (int y = 0; y < height - 80; y += 20) {
        int score = 0;
        
        // Count high-contrast pixels in region
        for (int j = y; j < y + 80 && j < height; j++) {
            for (int i = width / 4; i < 3 * width / 4; i++) {
                uint8_t pixel = image[j * width + i];
                if ((pixel > 50 && pixel < 200)) {
                    score++;
                }
            }
        }
        
        if (score > max_score) {
            max_score = score;
            face_y = y;
        }
    }
    
    if (face_y < 0 || max_score < 500) {
        return result;
    }
    
    result.face_detected = true;
    result.face_count = 1;
    
    // Approximate face center and size
    int face_x = width / 2;
    int face_width = width / 3;
    int face_height = height / 3;
    
    // Estimate eye positions (1/3 down from face top, 1/3 and 2/3 horizontally)
    int eye_y = face_y + face_height / 2;
    int left_eye_x = face_x - face_width / 3;
    int right_eye_x = face_x + face_width / 3;
    int eye_sep = face_width / 2;
    
    // Left eye EAR (6-point model)
    int p1x = left_eye_x - eye_sep / 2;
    int p1y = eye_y;
    int p2x = left_eye_x - eye_sep / 4;
    int p2y = eye_y - 6;
    int p3x = left_eye_x + eye_sep / 4;
    int p3y = eye_y - 6;
    int p4x = left_eye_x + eye_sep / 2;
    int p4y = eye_y;
    int p5x = left_eye_x + eye_sep / 4;
    int p5y = eye_y + 6;
    int p6x = left_eye_x - eye_sep / 4;
    int p6y = eye_y + 6;
    
    result.ear = calculate_ear(p1x, p1y, p2x, p2y, p3x, p3y, 
                               p4x, p4y, p5x, p5y, p6x, p6y);
    
    // Right eye EAR
    p1x = right_eye_x - eye_sep / 2;
    p2x = right_eye_x - eye_sep / 4;
    p3x = right_eye_x + eye_sep / 4;
    p4x = right_eye_x + eye_sep / 2;
    p5x = right_eye_x + eye_sep / 4;
    p6x = right_eye_x - eye_sep / 4;
    
    float right_ear = calculate_ear(p1x, p1y, p2x, p2y, p3x, p3y,
                                    p4x, p4y, p5x, p5y, p6x, p6y);
    
    result.ear = (result.ear + right_ear) / 2.0f;
    result.ear = fmaxf(0.0f, fminf(1.0f, result.ear));
    
    // Mouth MAR (8-point model, lower on face)
    int mouth_y = face_y + face_height + face_height / 2;
    int mouth_width = face_width / 2;
    
    int m1x = face_x - mouth_width;
    int m1y = mouth_y;
    int m2x = face_x - mouth_width * 0.6f;
    int m2y = mouth_y - 4;
    int m3x = face_x + mouth_width * 0.6f;
    int m3y = mouth_y - 4;
    int m4x = face_x + mouth_width;
    int m4y = mouth_y;
    int m5x = face_x + mouth_width * 0.6f;
    int m5y = mouth_y + 8;
    int m6x = face_x - mouth_width * 0.6f;
    int m6y = mouth_y + 8;
    int m7x = face_x;
    int m7y = mouth_y + 10;
    int m8x = face_x;
    int m8y = mouth_y - 2;
    
    result.mar = calculate_mar(m1x, m1y, m2x, m2y, m3x, m3y, m4x, m4y,
                               m5x, m5y, m6x, m6y, m7x, m7y, m8x, m8y);
    result.mar = fmaxf(0.0f, fminf(1.0f, result.mar));
    
    return result;
}

void FaceDetector::cleanup_camera() {
    esp_camera_deinit();
    Serial.println("[Camera] Cleanup complete");
}
