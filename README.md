# LBW Decision System

**Real-time Cricket LBW Decision Making using Computer Vision**

A personal-use computer vision system that processes video from an umpire's perspective to make Leg Before Wicket (LBW) decisions during local cricket matches with friends.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/opencv-4.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

---

## 🎯 Overview

This system uses computer vision and machine learning to analyze cricket match footage in real-time and assist with LBW decisions. It detects the ball, tracks its trajectory, predicts where it would have gone, and applies LBW rules to make a decision.

**Perfect for:** Local cricket matches, friendly games, practice sessions, and backyard cricket with friends!

### Key Features

- ✅ **Real-time video processing** at 60 FPS
- ✅ **Object detection** (ball, batsman, stumps, pads, bat)
- ✅ **Ball tracking** with Kalman filtering
- ✅ **Trajectory prediction** using physics-based models
- ✅ **LBW decision logic** following cricket rules
- ✅ **Visual overlay** with trajectory and decision display
- ✅ **Performance monitoring** with FPS and latency tracking
- ✅ **Flexible deployment** (local, Docker, or cloud)

---

## 🏗️ Architecture

The system consists of several integrated components:

```
┌─────────────────┐
│  Video Capture  │ ← Camera/Video File
└────────┬────────┘
         ↓
┌─────────────────┐
│  Preprocessing  │ ← Noise reduction, enhancement
└────────┬────────┘
         ↓
┌─────────────────┐
│ Object Detection│ ← YOLOv8 or fallback CV
└────────┬────────┘
         ↓
┌─────────────────┐
│  Ball Tracking  │ ← Kalman filter
└────────┬────────┘
         ↓
┌─────────────────┐
│   Trajectory    │ ← Physics-based prediction
│   Prediction    │
└────────┬────────┘
         ↓
┌─────────────────┐
│  LBW Decision   │ ← Rule engine
│     Engine      │
└────────┬────────┘
         ↓
┌─────────────────┐
│  Visualization  │ → Display/Output
└─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Webcam or video file
- (Optional) NVIDIA GPU for faster processing

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd workspace
```

2. **Run setup script:**
```bash
./scripts/setup.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Create necessary directories
- Set up configuration files

3. **Activate virtual environment:**
```bash
source venv/bin/activate
```

4. **Run system test:**
```bash
python scripts/test_system.py
```

### Calibration (Important!)

Before first use, calibrate the camera from the umpire's position:

```bash
python scripts/calibrate.py
```

Follow the on-screen instructions to:
1. Position camera at umpire's view
2. Click reference points (stumps, pitch boundaries)
3. Enter real-world measurements

### Running the System

**With webcam:**
```bash
python main.py
```

**With video file:**
```bash
python main.py --video /path/to/cricket_match.mp4
```

**With custom configuration:**
```bash
python main.py --config my_config.yaml
```

### Keyboard Controls

- **`q`** - Quit application
- **`p`** - Pause/Resume processing
- **`r`** - Reset tracker (use between deliveries)
- **`s`** - Save screenshot

---

## 📋 Core Technologies

### Computer Vision (OpenCV)

The system uses OpenCV for:
- **Video capture** and frame extraction
- **Image preprocessing** (denoising, enhancement, color correction)
- **Object detection** fallback using classical CV techniques
- **Feature extraction** and tracking
- **Visualization** and overlay rendering

### Machine Learning

#### Object Detection: YOLOv8
- Detects ball, batsman, stumps, pads, and bat
- Real-time inference at 60+ FPS
- Falls back to classical CV if model not available

#### Ball Tracking: Kalman Filter
- Predicts ball position in next frame
- Handles occlusion and missed detections
- Maintains multiple track hypotheses

#### Trajectory Prediction
- **Polynomial fitting** for simple trajectories
- **Physics-based model** with gravity and air resistance
- **Extrapolation** to predict stump impact point

### LBW Decision Logic

Implements official cricket LBW rules:

1. ✅ **Pitching:** Did ball pitch outside leg? (NOT OUT)
2. ✅ **Impact:** Was impact in line with stumps?
3. ✅ **Hitting:** Would ball have hit stumps?
4. ✅ **Umpire's Call:** Marginal decisions flagged

---

## 🎥 Field Deployment Guide

### Camera Setup (Critical!)

**For best results:**

1. **Position:** Mount camera at umpire's end, slightly elevated (5-6 feet high)
2. **Angle:** Straight down the pitch toward stumps
3. **Frame:** Ensure both sets of stumps are visible
4. **Stability:** Use tripod or stable mount (no hand-held!)
5. **Lighting:** Ensure good lighting, avoid backlight

### Pre-Match Checklist

- [ ] Camera positioned at umpire's view
- [ ] Both stumps clearly visible in frame
- [ ] Camera stable (tripod recommended)
- [ ] Calibration completed
- [ ] System tested with practice deliveries
- [ ] Laptop/device fully charged
- [ ] Backup power source available

### During Match

1. **Start system** before first delivery
2. **Press `r`** between deliveries to reset tracker
3. **Press `s`** to save interesting decisions for review
4. **Monitor FPS** - should stay above 30 FPS

### Troubleshooting in the Field

**Ball not detected?**
- Check lighting conditions
- Adjust confidence threshold in config
- Use red ball for better contrast

**Stuttering/Low FPS?**
- Reduce video resolution
- Increase `process_every_n_frames`
- Close other applications

**Inaccurate decisions?**
- Re-run calibration
- Check camera hasn't moved
- Ensure stumps are visible

---

## ⚠️ Limitations (Single-Angle System)

### Known Limitations

#### 1. **Occlusion Issues**
- **Problem:** Batsman's body can block ball view
- **Mitigation:** Position camera slightly to side if possible
- **Impact:** May miss some detections during impact

#### 2. **2D vs 3D Trajectory**
- **Problem:** Single camera sees 2D projection only
- **Mitigation:** Physics-based 3D reconstruction from 2D
- **Impact:** Less accurate than professional systems

#### 3. **In-Line Detection**
- **Problem:** Hard to judge "in-line" from single angle
- **Mitigation:** Conservative thresholds, use Umpire's Call
- **Impact:** Some marginal decisions may be incorrect

#### 4. **Lighting Conditions**
- **Problem:** Shadows, direct sunlight affect detection
- **Mitigation:** Adaptive preprocessing, CLAHE enhancement
- **Impact:** May struggle in poor lighting

#### 5. **Ball Color Confusion**
- **Problem:** Red ball on red/brown pitch difficult to track
- **Mitigation:** HSV color filtering, shape detection
- **Impact:** Better with white ball or contrast backgrounds

#### 6. **No Height Information**
- **Problem:** Difficult to judge ball height accurately
- **Mitigation:** Use stump height as reference
- **Impact:** Height-based decisions less reliable

### Comparison to Professional Systems

| Feature | This System | Professional (Hawk-Eye) |
|---------|-------------|-------------------------|
| Cameras | 1 angle | 6+ angles |
| 3D Accuracy | Estimated | Precise (mm level) |
| Ball Tracking | 2D + estimation | Full 3D tracking |
| Cost | Free / Low | $50,000+ |
| Setup Time | 5 minutes | Hours |
| Use Case | Friendly matches | Professional cricket |

### Best Use Cases

✅ **Good for:**
- Friendly matches with clear LBW situations
- Practice and training feedback
- Learning LBW rules
- Fun with friends!

❌ **Not suitable for:**
- Professional/competitive matches
- Situations requiring mm-accuracy
- Poor lighting conditions
- High-stakes decisions

---

## 🔧 Configuration

### Main Configuration File

`config/config.yaml` contains all system settings:

```yaml
video:
  source: 0              # Webcam index or video path
  width: 1920
  height: 1080
  fps: 60

detection:
  confidence_threshold: 0.5
  device: cuda           # cuda or cpu

tracking:
  max_frames_to_skip: 10
  min_track_length: 5

lbw:
  impact_threshold: 0.05
  line_threshold: 0.1
```

### Environment Variables

Create `.env` file (from `.env.example`):

```bash
VIDEO_SOURCE=0
USE_GPU=true
DEVICE=cuda
SAVE_VIDEO=false
LOG_LEVEL=INFO
```

---

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker-compose build

# Run system
./scripts/docker_deploy.sh

# View logs
docker-compose logs -f

# Stop system
docker-compose down
```

### GPU Support (NVIDIA)

Uncomment GPU settings in `docker-compose.yml`:

```yaml
runtime: nvidia
environment:
  - NVIDIA_VISIBLE_DEVICES=all
```

---

## 📊 Performance

### Expected Performance

**On Modern Laptop (CPU):**
- FPS: 20-30
- Latency: 50-100ms
- CPU Usage: 60-80%

**On GPU (NVIDIA GTX 1060+):**
- FPS: 50-60
- Latency: 20-30ms
- GPU Usage: 40-60%

### Optimization Tips

1. **Reduce resolution:** Lower video resolution for faster processing
2. **Skip frames:** Process every 2nd or 3rd frame
3. **Use GPU:** Enable CUDA if NVIDIA GPU available
4. **Close apps:** Free up system resources
5. **Reduce ROI:** Limit detection region

---

## 📁 Project Structure

```
workspace/
├── src/                      # Source code
│   ├── config_manager.py     # Configuration management
│   ├── video_capture.py      # Video input and preprocessing
│   ├── object_detector.py    # Object detection (YOLOv8)
│   ├── ball_tracker.py       # Ball tracking (Kalman)
│   ├── trajectory_predictor.py # Trajectory prediction
│   ├── lbw_decision.py       # LBW decision engine
│   ├── visualizer.py         # Visualization
│   ├── performance_monitor.py # Performance tracking
│   └── lbw_system.py         # Main system integration
├── config/                   # Configuration files
├── scripts/                  # Utility scripts
│   ├── setup.sh             # Setup script
│   ├── calibrate.py         # Calibration tool
│   ├── test_system.py       # System tests
│   └── docker_deploy.sh     # Docker deployment
├── models/                   # ML models (user-provided)
├── logs/                     # Log files
├── output/                   # Output videos/screenshots
├── main.py                   # Main entry point
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
└── docker-compose.yml       # Docker Compose configuration
```

---

## 🎓 Development Steps Overview

### 1. Video Input and Preprocessing
- Captures video frames from camera/file
- Applies denoising and enhancement
- Handles frame buffering for smooth processing

### 2. Object Detection and Tracking
- Detects ball, batsman, stumps using YOLOv8
- Falls back to classical CV if model unavailable
- Tracks objects across frames

### 3. Ball Tracking
- Uses Kalman filter for smooth tracking
- Handles occlusion and missed detections
- Maintains trajectory history

### 4. Trajectory Prediction
- Fits polynomial to ball path
- Applies physics (gravity, air resistance)
- Predicts impact point on stumps

### 5. LBW Decision Logic
- Checks pitching position
- Validates impact zone
- Predicts stump impact
- Applies cricket rules

### 6. Visualization
- Overlays detections and trajectory
- Displays decision with confidence
- Shows performance metrics

---

## 🧪 Testing

### Run All Tests

```bash
python scripts/test_system.py
```

### Manual Testing

Test individual components:

```python
# Test detector
from src.object_detector import ObjectDetector
detector = ObjectDetector('models/cricket_detector.pt')

# Test tracker
from src.ball_tracker import BallTracker
tracker = BallTracker()

# Test decision engine
from src.lbw_decision import LBWDecisionEngine
engine = LBWDecisionEngine()
```

---

## 🤝 Contributing

This is a personal project, but suggestions are welcome!

### Ideas for Improvement

- [ ] Multi-camera support for 3D tracking
- [ ] Mobile app for field deployment
- [ ] Machine learning for better trajectory prediction
- [ ] Historical decision database
- [ ] Slow-motion replay feature
- [ ] Voice announcement of decisions

---

## 📝 License

This project is open source and available for personal use.

---

## 🙏 Acknowledgments

- OpenCV community for computer vision tools
- Ultralytics for YOLOv8 implementation
- Cricket community for LBW rules and guidance

---

## 📞 Support

For issues or questions:
1. Check documentation in `docs/` folder
2. Review configuration in `config/config.yaml`
3. Run system tests: `python scripts/test_system.py`

---

## 🎮 Quick Reference

### Common Commands

```bash
# Setup
./scripts/setup.sh

# Calibrate
python scripts/calibrate.py

# Test
python scripts/test_system.py

# Run with webcam
python main.py

# Run with video
python main.py --video match.mp4

# Run headless (no display)
python main.py --no-display --save-video
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit |
| `p` | Pause/Resume |
| `r` | Reset tracker |
| `s` | Screenshot |

---

**Enjoy your cricket matches with friends! 🏏**

*Remember: This is a fun personal project. Always defer to the umpire's decision in the spirit of the game!*
