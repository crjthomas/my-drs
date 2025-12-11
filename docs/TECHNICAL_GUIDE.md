# Technical Guide - LBW Decision System

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Core Algorithms](#core-algorithms)
3. [Object Detection](#object-detection)
4. [Ball Tracking](#ball-tracking)
5. [Trajectory Prediction](#trajectory-prediction)
6. [LBW Decision Logic](#lbw-decision-logic)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting](#troubleshooting)

---

## System Architecture

### Component Overview

The system follows a modular pipeline architecture:

```
Video Input → Preprocessing → Detection → Tracking → Prediction → Decision → Output
```

### Threading Model

- **Main Thread:** User interface and control flow
- **Capture Thread:** Video frame acquisition (non-blocking)
- **Processing Thread:** Frame processing pipeline
- **Monitor Thread:** Performance monitoring

### Data Flow

```python
# Frame acquisition
frame = video_capture.read()

# Object detection
detections = detector.detect(frame)

# Ball tracking
ball_positions = [d.center for d in detections if d.class_name == 'ball']
tracks = tracker.update(ball_positions)

# Trajectory prediction
trajectory = tracks[0].get_trajectory()
predicted = predictor.predict_trajectory(trajectory)

# LBW decision
decision = engine.make_decision(trajectory, predicted, impact_point)

# Visualization
output = visualizer.draw_frame(frame, detections, tracks, decision)
```

---

## Core Algorithms

### 1. Object Detection

#### YOLOv8 (Primary Method)

**When available:** Uses trained YOLOv8 model for object detection

**Advantages:**
- Fast inference (50-60 FPS on GPU)
- Accurate multi-object detection
- Handles occlusion well

**Classes detected:**
- Ball (class 0)
- Batsman (class 1)
- Stumps (class 2)
- Pads (class 3)
- Bat (class 4)

**Configuration:**
```yaml
detection:
  model_path: "models/cricket_detector.pt"
  confidence_threshold: 0.5
  nms_threshold: 0.4
  device: "cuda"
```

#### Classical CV (Fallback Method)

**Ball Detection:**
```python
# Color-based detection (red ball)
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
lower_red = np.array([0, 100, 100])
upper_red = np.array([10, 255, 255])
mask = cv2.inRange(hsv, lower_red, upper_red)

# Circular shape detection
circles = cv2.HoughCircles(
    gray, cv2.HOUGH_GRADIENT,
    dp=1, minDist=50,
    param1=50, param2=30,
    minRadius=5, maxRadius=30
)
```

**Stumps Detection:**
```python
# Edge detection for vertical lines
edges = cv2.Canny(gray, 50, 150)
lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100)

# Filter for vertical lines (80-100 degrees)
vertical_lines = [l for l in lines if 80 <= angle(l) <= 100]
```

---

### 2. Ball Tracking

#### Kalman Filter Implementation

**State Vector:** `[x, y, vx, vy]`
- Position: (x, y)
- Velocity: (vx, vy)

**Transition Model (Constant Velocity):**
```
x_new = x + vx * dt
y_new = y + vy * dt
vx_new = vx
vy_new = vy
```

**Prediction Step:**
```python
def predict(self):
    # Predict next state
    self.state = self.F @ self.state
    self.covariance = self.F @ self.covariance @ self.F.T + self.Q
    return self.state[:2]  # Return position
```

**Update Step:**
```python
def update(self, measurement):
    # Kalman gain
    K = self.covariance @ self.H.T @ inv(self.H @ self.covariance @ self.H.T + self.R)
    
    # Update state
    self.state = self.state + K @ (measurement - self.H @ self.state)
    
    # Update covariance
    self.covariance = (I - K @ self.H) @ self.covariance
```

#### Track Management

**Association:** Hungarian algorithm for detection-to-track matching

```python
# Cost matrix: Euclidean distance
cost_matrix[i, j] = distance(track[i].predicted_pos, detection[j].pos)

# Assign detections to tracks
assignments = hungarian_algorithm(cost_matrix)
```

**Track States:**
- **Active:** Recently updated with detection
- **Lost:** No detection for N frames
- **Terminated:** Lost for too long

**Configuration:**
```yaml
tracking:
  max_frames_to_skip: 10    # Keep track for 10 frames without detection
  min_track_length: 5       # Need 5 points for valid track
  distance_threshold: 50    # Maximum distance for association (pixels)
```

---

### 3. Trajectory Prediction

#### Method 1: Polynomial Fitting

**For simple trajectories:**

```python
# Fit 2nd order polynomial
x_poly = np.polyfit(t, x_positions, deg=2)
y_poly = np.polyfit(t, y_positions, deg=2)

# Predict future points
future_t = np.arange(t_last, t_last + num_points)
predicted_x = np.polyval(x_poly, future_t)
predicted_y = np.polyval(y_poly, future_t)
```

**Advantages:**
- Fast computation
- Works well for parabolic paths

**Limitations:**
- Doesn't account for physics
- Poor for complex trajectories

#### Method 2: Physics-Based Model

**Equations of motion with air resistance:**

```python
# Forces
F_gravity = m * g
F_drag = -0.5 * rho * Cd * A * v^2

# Acceleration
ax = F_drag_x / m
ay = (F_drag_y - F_gravity) / m

# Update velocity
vx += ax * dt
vy += ay * dt

# Update position
x += vx * dt
y += vy * dt
```

**Parameters:**
```yaml
trajectory:
  gravity: 9.81              # m/s^2
  air_resistance: 0.47       # Drag coefficient
  ball_mass: 0.16           # kg
  ball_radius: 0.036        # meters
```

**Advantages:**
- More realistic trajectory
- Better for longer predictions

**Limitations:**
- Requires accurate initial velocity
- Sensitive to parameters

#### Landing Point Estimation

```python
def estimate_landing_point(trajectory, ground_y):
    for i in range(len(trajectory) - 1):
        x1, y1 = trajectory[i]
        x2, y2 = trajectory[i+1]
        
        if y1 <= ground_y <= y2:
            # Linear interpolation
            t = (ground_y - y1) / (y2 - y1)
            landing_x = x1 + t * (x2 - x1)
            return (landing_x, ground_y)
```

---

### 4. LBW Decision Logic

#### Cricket LBW Rules Implementation

**Rule 1: Pitching**
```python
def check_pitching(pitching_point, stumps_x):
    # If pitched outside leg stump → NOT OUT
    if pitching_point.x < stumps_x - stump_width/2 - threshold:
        return "OUTSIDE_LEG", Decision.NOT_OUT
    
    # If pitched in line → Continue checking
    return "IN_LINE", None
```

**Rule 2: Impact**
```python
def check_impact(impact_point, stumps_x):
    # Impact must be in line with stumps
    distance = abs(impact_point.x - stumps_x)
    
    if distance <= stump_width/2 + line_threshold:
        return "IN_LINE", True
    
    # If impact outside off and not offering shot → NOT OUT
    if impact_point.x > stumps_x + stump_width/2 + line_threshold:
        return "OUTSIDE_OFF", Decision.NOT_OUT
    
    return "OUTSIDE", Decision.NOT_OUT
```

**Rule 3: Hitting Wickets**
```python
def check_hitting_wickets(predicted_trajectory, stumps_pos):
    # Find closest point to stumps
    for point in predicted_trajectory:
        # Check horizontal distance
        x_dist = abs(point.x - stumps_pos.x)
        
        # Check vertical height
        y_height = abs(point.y - ground_y)
        
        # Check if within stump dimensions
        if x_dist <= stump_width/2 and y_height <= stump_height:
            return True, y_height
    
    return False, None
```

**Umpire's Call Logic**
```python
def determine_decision(pitching, impact, hitting):
    # Clear decisions
    if not pitching_inline or not impact_inline or not hitting_wickets:
        return Decision.NOT_OUT, confidence
    
    # Check margins for Umpire's Call
    if impact_distance > line_threshold and impact_distance <= umpires_call_margin:
        return Decision.UMPIRES_CALL, confidence
    
    if wicket_distance > wicket_threshold and wicket_distance <= umpires_call_margin:
        return Decision.UMPIRES_CALL, confidence
    
    # Clear OUT
    return Decision.OUT, confidence
```

#### Decision Confidence

Confidence score based on:
1. **Track quality:** Longer tracks = higher confidence
2. **Detection confidence:** Higher detection scores = higher confidence
3. **Trajectory fit:** Better polynomial fit = higher confidence
4. **Occlusion:** Less occlusion = higher confidence

```python
confidence = (
    track_quality * 0.3 +
    detection_confidence * 0.3 +
    trajectory_fit * 0.2 +
    occlusion_score * 0.2
)
```

---

## Performance Optimization

### 1. Frame Processing Pipeline

**Optimize video capture:**
```python
# Use threaded capture
video_capture = VideoCapture(source, buffer_size=30)
video_capture.start()  # Runs in separate thread
```

**Skip frames if needed:**
```yaml
processing:
  process_every_n_frames: 1  # Process every frame
  # Set to 2 or 3 for better performance
```

### 2. Detection Optimization

**Region of Interest (ROI):**
```yaml
detection:
  roi:
    enabled: true
    x_min: 0.1  # Only process center 80% of frame
    x_max: 0.9
```

**Batch processing:**
```python
# Process multiple frames in batch (GPU)
detections = detector.detect_batch([frame1, frame2, frame3])
```

### 3. Memory Management

**Limit history:**
```python
# Limit trajectory history
track.positions = deque(maxlen=100)  # Keep last 100 points
```

**Clear old tracks:**
```python
# Remove tracks older than threshold
tracks = [t for t in tracks if current_time - t.last_seen < max_age]
```

### 4. GPU Utilization

**CUDA optimization:**
```python
# Enable CUDA for detection
detector.model.to('cuda')

# Enable CUDA for image processing
import cupy as cp
img_gpu = cp.asarray(img)
```

---

## Troubleshooting

### Issue: Low FPS

**Diagnosis:**
```bash
# Check CPU/GPU usage
python scripts/test_system.py
```

**Solutions:**
1. Reduce video resolution
2. Increase `process_every_n_frames`
3. Enable GPU if available
4. Reduce detection confidence threshold
5. Disable video saving

### Issue: Ball Not Detected

**Diagnosis:**
- Check ball visibility in frame
- Review detection confidence scores
- Test with static ball image

**Solutions:**
1. Adjust color ranges for ball detection
2. Lower confidence threshold
3. Improve lighting conditions
4. Use contrasting ball color

### Issue: Inaccurate Trajectory

**Diagnosis:**
- Check track length (need 10+ points)
- Review Kalman filter parameters
- Verify calibration

**Solutions:**
1. Increase `min_track_length`
2. Adjust Kalman filter noise parameters
3. Re-run calibration
4. Use physics-based prediction

### Issue: Wrong LBW Decisions

**Diagnosis:**
- Review decision log
- Check stump detection
- Verify ground level calibration

**Solutions:**
1. Re-calibrate camera
2. Adjust decision thresholds
3. Verify stump position detection
4. Check trajectory prediction accuracy

---

## Advanced Topics

### Custom Model Training

To train your own YOLOv8 model:

```bash
# Collect cricket images
# Annotate with labelImg or Roboflow
# Train YOLOv8
from ultralytics import YOLO

model = YOLO('yolov8n.pt')
model.train(data='cricket.yaml', epochs=100)
```

### Multi-Camera Setup

For future 3D tracking:

```python
# Calibrate multiple cameras
calibrations = [calibrate_camera(i) for i in range(num_cameras)]

# Triangulate 3D position
position_3d = triangulate(detections_cam1, detections_cam2, calibrations)
```

### Machine Learning Trajectory

Train LSTM for better prediction:

```python
# Prepare trajectory sequences
X = [trajectory[:10] for trajectory in trajectories]
y = [trajectory[10:] for trajectory in trajectories]

# Train LSTM
model = LSTM(input_dim=2, hidden_dim=64, output_dim=2)
model.fit(X, y)
```

---

## Performance Benchmarks

### Hardware Requirements

**Minimum:**
- CPU: Intel i5 or equivalent
- RAM: 4 GB
- Camera: 720p @ 30 FPS

**Recommended:**
- CPU: Intel i7 or equivalent
- RAM: 8 GB
- GPU: NVIDIA GTX 1060 or better
- Camera: 1080p @ 60 FPS

### Expected Performance

| Configuration | FPS | Latency | CPU | GPU |
|--------------|-----|---------|-----|-----|
| Minimal (720p, CPU) | 15-20 | 100ms | 80% | - |
| Standard (1080p, CPU) | 20-30 | 50ms | 90% | - |
| Performance (1080p, GPU) | 50-60 | 20ms | 30% | 60% |

---

## References

- OpenCV Documentation: https://docs.opencv.org/
- YOLOv8: https://github.com/ultralytics/ultralytics
- Cricket LBW Laws: https://www.lords.org/mcc/the-laws-of-cricket
- Kalman Filtering: https://www.kalmanfilter.net/

---

*For more information, see main README.md and other documentation in docs/ folder.*
