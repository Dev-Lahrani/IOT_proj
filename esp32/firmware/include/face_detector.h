#ifndef FACE_DETECTOR_H
#define FACE_DETECTOR_H

#include <Arduino.h>
#include "esp_camera.h"

typedef struct {
    float ear;  // Eye Aspect Ratio
    float mar;  // Mouth Aspect Ratio
    int face_count;
    bool face_detected;
} DetectionResult;

class FaceDetector {
public:
    FaceDetector();
    void init_camera();
    DetectionResult process_frame(camera_fb_t* fb);
    void cleanup_camera();
    
private:
    float calculate_distance(int x1, int y1, int x2, int y2);
    float calculate_ear(int p1x, int p1y, int p2x, int p2y, int p3x, int p3y, 
                       int p4x, int p4y, int p5x, int p5y, int p6x, int p6y);
    float calculate_mar(int p1x, int p1y, int p2x, int p2y, int p3x, int p3y,
                       int p4x, int p4y, int p5x, int p5y, int p6x, int p6y,
                       int p7x, int p7y, int p8x, int p8y);
};

#endif // FACE_DETECTOR_H
