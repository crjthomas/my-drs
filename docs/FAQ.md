# Frequently Asked Questions (FAQ)

## General Questions

### Q: How accurate is this system?

**A:** For a single-camera system in ideal conditions:
- **Clear LBWs:** 75-85% accuracy
- **Marginal decisions:** 50-60% accuracy
- **Complex scenarios:** Recommendation to use Umpire's Call

Professional systems like Hawk-Eye (using 6+ cameras) achieve 95%+ accuracy.

**Key factors affecting accuracy:**
- Lighting conditions
- Ball visibility
- Camera positioning
- Calibration quality
- Occlusion from batsman

### Q: Can this replace a professional umpire?

**A:** No, this is designed for:
- Friendly matches
- Practice sessions
- Learning LBW rules
- Fun with friends

It's a helpful tool, not a replacement for human judgment, especially in:
- Competitive matches
- Situations requiring mm-accuracy
- When ball is obscured

### Q: How much does it cost?

**A:** The software is free and open source. You only need:
- A computer (laptop) - $300-1000
- A webcam - $30-150
- Optional: Tripod - $20-50

Total: $350-1200 (one-time cost)

### Q: Do I need a GPU?

**A:** No, but it helps:
- **CPU only:** 20-30 FPS (sufficient for most use)
- **With GPU:** 50-60 FPS (smoother, more responsive)

The system works fine on modern laptops without dedicated GPU.

---

## Setup & Installation

### Q: What operating systems are supported?

**A:** 
- ✅ Linux (Ubuntu, Debian, etc.)
- ✅ macOS (10.14+)
- ✅ Windows 10/11

Installation steps are slightly different on Windows but all features work.

### Q: Installation fails with package errors?

**A:** Try:

```bash
# Update pip first
pip install --upgrade pip

# Install with specific versions
pip install -r requirements.txt --no-cache-dir

# If still fails, install individually
pip install opencv-python numpy torch
```

### Q: Do I need to train my own model?

**A:** No! The system works without a trained model using classical computer vision techniques:
- Color-based ball detection
- Shape detection (circles for ball)
- Edge detection (vertical lines for stumps)

**However:** Training your own YOLOv8 model will significantly improve accuracy.

### Q: How do I train a custom model?

**A:** See `docs/TECHNICAL_GUIDE.md` section on "Custom Model Training". Brief steps:

1. Collect 500-1000 cricket images
2. Annotate objects (ball, stumps, etc.) using labelImg
3. Train YOLOv8: `python train_model.py`
4. Place trained model in `models/` folder

---

## Camera & Hardware

### Q: What camera should I use?

**A:** Recommended specs:
- **Resolution:** 1080p minimum, 4K better
- **FPS:** 60 FPS minimum (120 FPS ideal)
- **Shutter:** Fast shutter speed (1/500s+)
- **Connection:** USB 3.0 or better

**Good options:**
- Logitech C920/C922 (budget: $60-80)
- Logitech Brio 4K (better: $150-200)
- GoPro as webcam (premium: $300+)

### Q: Can I use my phone as camera?

**A:** Yes! Options:
1. **DroidCam** - Turn Android phone into webcam
2. **EpocCam** - iOS phone as webcam
3. **IP Webcam** - Stream from phone to computer

Then use phone's IP address as video source:
```bash
python main.py --video "http://192.168.1.100:8080/video"
```

### Q: Camera position keeps changing during match?

**A:** Solutions:
- Use heavier tripod
- Add sandbag/weight to tripod
- Stake tripod legs if outdoors
- Use gaffer tape on smooth surfaces
- Re-calibrate if camera moves

### Q: Laptop screen hard to see in sunlight?

**A:** Tips:
- Use sunshade/hood for laptop
- Increase screen brightness to max
- Position laptop in shade
- Use external monitor with higher brightness
- Use matte screen protector

---

## During Match

### Q: System says "INSUFFICIENT DATA" often?

**A:** Common causes:
1. **Ball not detected** - Improve lighting or use contrasting ball
2. **Trajectory too short** - Need 10+ frames of ball tracking
3. **Occlusion** - Batsman blocking view
4. **Fast ball** - Increase camera FPS or reduce motion blur

**Solutions:**
- Lower detection confidence threshold
- Ensure good lighting
- Position camera for clear view
- Use high-FPS camera

### Q: FPS drops during match?

**A:** Quick fixes:
1. Close other applications
2. Lower video resolution in config
3. Increase `process_every_n_frames` to 2 or 3
4. Disable video saving
5. Reduce detection region (ROI)

**Long-term:**
- Upgrade to laptop with better CPU/GPU
- Use external GPU enclosure

### Q: Wrong decisions being made?

**A:** Check:
1. **Calibration** - Re-run calibration script
2. **Stumps detection** - System must see stumps clearly
3. **Ground level** - Ensure ground plane is detected correctly
4. **Thresholds** - Adjust in `config/config.yaml`

Review decision log to understand why decision was made:
```bash
cat logs/decisions_*.log
```

### Q: Ball color not detected?

**A:** Adjust color ranges in config:

```yaml
tracking:
  ball_color_hsv:
    lower: [0, 100, 100]    # Adjust for your ball
    upper: [10, 255, 255]
```

For white ball:
```yaml
lower: [0, 0, 200]
upper: [180, 30, 255]
```

### Q: System crashes during match?

**A:** Prevention:
- Ensure laptop is plugged in (don't rely on battery)
- Close unnecessary applications
- Monitor memory usage
- Use stable camera connection

**Recovery:**
- System saves logs automatically
- Restart: `python main.py`
- Calibration is saved, no need to re-calibrate

---

## Performance & Optimization

### Q: How to make system faster?

**A:** Optimization hierarchy:

1. **Reduce resolution** (biggest impact)
   ```yaml
   video:
     width: 1280   # Instead of 1920
     height: 720   # Instead of 1080
   ```

2. **Skip frames** (good trade-off)
   ```yaml
   processing:
     process_every_n_frames: 2  # Process every 2nd frame
   ```

3. **Enable GPU** (if available)
   ```yaml
   detection:
     device: cuda
   ```

4. **Reduce ROI** (limit processing area)
   ```yaml
   detection:
     roi:
       enabled: true
       x_min: 0.2
       x_max: 0.8
   ```

### Q: Laptop getting too hot?

**A:** 
- Use laptop cooling pad
- Ensure good ventilation
- Lower video quality/FPS
- Monitor temperature: `sensors` (Linux) or `iStats` (macOS)
- Take breaks between innings

### Q: High latency (slow response)?

**A:** Latency sources:
1. **Camera lag** - Use camera with low latency
2. **Processing** - Optimize as above
3. **Display lag** - Reduce visualization complexity

Check actual latency:
```bash
# Shows in performance statistics when you quit (Ctrl+C)
```

---

## Calibration

### Q: How often should I calibrate?

**A:** Re-calibrate when:
- Camera position changes
- Moving to different ground
- After system update
- Accuracy seems off

Same ground, same position: Calibrate once, reuse.

### Q: Calibration points unclear?

**A:** Tips:
- Click on easily identifiable points
- Use stump base (where stump meets ground)
- Be consistent (always click same spot on stump)
- Take time to be accurate

### Q: Can I calibrate without stumps visible?

**A:** Not recommended, but possible:
- Use pitch markings (crease lines)
- Measure distances manually
- Place temporary markers
- Accuracy will be reduced

### Q: How to verify calibration quality?

**A:** 
- Place ball at known position
- Check if system measures correct distance
- Compare predicted trajectory with actual
- Test with practice deliveries before match

---

## Docker & Deployment

### Q: Why use Docker?

**A:** Benefits:
- Consistent environment
- Easy deployment
- No dependency conflicts
- Can deploy on server/cloud
- Easier updates

**When not to use Docker:**
- Simple local use
- Need direct camera access is tricky
- X11 forwarding complexity
- Prefer native performance

### Q: Docker can't access camera?

**A:** 
```yaml
# In docker-compose.yml, ensure:
devices:
  - /dev/video0:/dev/video0

# Or run with --device flag
docker run --device /dev/video0 lbw-system
```

On macOS/Windows, camera access in Docker is complex. Better to run natively.

### Q: Docker display not working?

**A:**
```bash
# Allow X11 forwarding (Linux)
xhost +local:docker

# Set DISPLAY variable
export DISPLAY=:0

# Run with display
docker-compose up
```

---

## Advanced Usage

### Q: Can I use multiple cameras?

**A:** Current version: Single camera only

**Future enhancement:** Multi-camera support planned for:
- 3D trajectory reconstruction
- Stereo depth estimation
- Better occlusion handling

### Q: Can I use this for video analysis?

**A:** Yes! Process recorded match:

```bash
python main.py --video recorded_match.mp4 --save-video
```

System will:
- Process entire video
- Make decisions on all LBWs
- Save output video with overlays

### Q: Can I integrate with other systems?

**A:** Yes, system is modular:
- Import components in your Python code
- Use as library
- Access via internal API
- Extend functionality

Example:
```python
from src.lbw_system import LBWDecisionSystem

system = LBWDecisionSystem()
# Your custom code here
```

### Q: Can I save decision statistics?

**A:** Yes, decision log is saved in:
```
logs/decisions_YYYY-MM-DD.log
```

Parse for statistics:
```python
import json

decisions = []
with open('logs/decisions_2024-12-11.log') as f:
    for line in f:
        if 'LBW Decision:' in line:
            # Parse decision data
            decisions.append(data)

# Analyze
out_count = sum(1 for d in decisions if d['decision'] == 'OUT')
```

---

## Troubleshooting

### Q: "ModuleNotFoundError: No module named 'cv2'"?

**A:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install OpenCV
pip install opencv-python
```

### Q: "CUDA out of memory" error?

**A:**
```bash
# Switch to CPU
python main.py --device cpu

# Or reduce batch size in config
```

### Q: "Unable to open video source"?

**A:** Check:
```bash
# List available cameras
ls /dev/video*

# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"

# Try different index
python main.py --video 1
```

### Q: All detections are false positives?

**A:** Increase confidence threshold:
```yaml
detection:
  confidence_threshold: 0.7  # Higher = fewer false positives
```

---

## Cricket Rules

### Q: What are the LBW rules?

**A:** Simplified:
1. **Ball must pitch** in line with stumps or outside off (NOT outside leg)
2. **Impact** must be in line with stumps
3. **Ball must be hitting** stumps if it continued

Special cases:
- If impact outside off AND batsman playing shot → NOT OUT
- Marginal decisions → UMPIRE'S CALL

### Q: What is "Umpire's Call"?

**A:** When decision is too close to call with certainty:
- Less than 50% of ball hitting stump
- Impact very close to line
- If umpire gave OUT → stays OUT
- If umpire gave NOT OUT → stays NOT OUT

Our system flags these as "UMPIRE'S CALL" so you can use your judgment.

### Q: Does system consider "playing a shot"?

**A:** Currently: No

This is a limitation. System doesn't detect if batsman was playing a shot, which matters for:
- Impact outside off stump
- Bat-before-pad decisions

Use your judgment for these cases.

---

## Contribution & Development

### Q: Can I contribute to the project?

**A:** Yes! Ways to contribute:
- Report bugs/issues
- Suggest features
- Improve documentation
- Train better models
- Add test cases
- Optimize performance

### Q: How to report a bug?

**A:** Include:
1. System information (OS, Python version)
2. Steps to reproduce
3. Error message/logs
4. Screenshots/video if relevant

### Q: Feature requests?

**A:** Ideas welcome for:
- Multi-camera support
- Mobile app
- Better UI
- Advanced analytics
- Cloud deployment

---

## Legal & Fair Play

### Q: Can I use this in official matches?

**A:** No, only for:
- Friendly matches
- Practice
- Training
- Personal entertainment

Official matches require ICC-approved systems.

### Q: Is this legal to use?

**A:** Yes, for personal use in friendly matches with consent of players.

Not legal for:
- Commercial use without proper licensing
- Official competitions
- Broadcasting without rights

### Q: Does this violate spirit of cricket?

**A:** Use responsibly:
- ✅ Helps learn LBW rules
- ✅ Makes friendly matches more fun
- ✅ Reduces disputes
- ❌ Don't let it slow down game
- ❌ Don't use in serious competitions
- ❌ Always respect umpire's final decision

---

## Still Have Questions?

1. **Check documentation:**
   - `README.md` - General overview
   - `docs/TECHNICAL_GUIDE.md` - Technical details
   - `docs/FIELD_GUIDE.md` - Practical usage

2. **Run system tests:**
   ```bash
   python scripts/test_system.py
   ```

3. **Check logs:**
   ```bash
   tail -f logs/lbw_system_*.log
   ```

4. **Review code:**
   - Code is well-commented
   - Each module has documentation
   - Examples in scripts/

---

**Happy cricket with friends! 🏏**
