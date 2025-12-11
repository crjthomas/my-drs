# Quick Start Guide - Get Running in 5 Minutes! 🏏

## For Your Local Cricket Match with Friends

This is a **personal use** system perfect for friendly cricket matches. Let's get you up and running quickly!

---

## ⚡ Super Quick Start (Linux/Mac)

```bash
# 1. Setup (first time only - takes 3 minutes)
./scripts/setup.sh

# 2. Activate environment
source venv/bin/activate

# 3. Test system
python scripts/test_system.py

# 4. Run with webcam
python main.py
```

That's it! 🎉

---

## 🪟 Windows Quick Start

```cmd
# 1. Create virtual environment
python -m venv venv

# 2. Activate
venv\Scripts\activate

# 3. Install
pip install -r requirements.txt

# 4. Test
python scripts/test_system.py

# 5. Run
python main.py
```

---

## 🎮 Using the System

### First Time Setup

**Before going to the cricket ground:**

1. **Test at home:**
   ```bash
   python main.py --video 0
   ```
   Make sure your webcam works!

2. **Practice with a test video** (if you have one):
   ```bash
   python main.py --video test_match.mp4
   ```

### At the Ground

**Setup (5 minutes):**

1. Position laptop at umpire's end
2. Mount camera/webcam on tripod (5-6 feet high)
3. Ensure both stumps visible in frame
4. Run calibration:
   ```bash
   python scripts/calibrate.py
   ```

**During Match:**

```bash
# Start system
python main.py

# Controls:
# - Press 'r' before each delivery (resets tracker)
# - Press 's' to save screenshot of decision
# - Press 'p' to pause if needed
# - Press 'q' to quit
```

---

## 📱 What You Need

### Minimum Hardware
- Laptop (any modern laptop from last 5 years)
- Webcam (built-in or USB, 720p minimum)
- That's it!

### Recommended Hardware
- Laptop with 8GB+ RAM
- 1080p webcam at 60 FPS (like Logitech C920)
- Tripod for camera stability
- Power bank for laptop

### Nice to Have
- External monitor (easier to see during match)
- Sunshade for laptop screen (if outdoors)
- Portable table for laptop

---

## 🎯 Understanding the Display

When running, you'll see:

```
┌─────────────────────────────────────────────────────┐
│ FPS: 45.2                                          │
│ Frame: 1234                                         │
│                                                     │
│                                                     │
│          [Video Feed with Detections]              │
│                                                     │
│          🔴 Ball (red box)                         │
│          🟦 Stumps (blue box)                      │
│          ━━━ Trajectory (yellow line)             │
│          ┈┈┈ Predicted path (orange dashed)       │
│                                                     │
│                                          ┌────────┐│
│                                          │  LBW   ││
│                                          │DECISION││
│                                          │        ││
│                                          │  OUT   ││
│                                          │        ││
│                                          │ Conf:  ││
│                                          │  85%   ││
│                                          │        ││
│                                          │Pitched:││
│                                          │IN LINE ││
│                                          │        ││
│                                          │Impact: ││
│                                          │IN LINE ││
│                                          │        ││
│                                          │Hitting:││
│                                          │  YES   ││
│                                          └────────┘│
└─────────────────────────────────────────────────────┘
```

---

## 🚨 Common Issues & Quick Fixes

### "Camera not found"
```bash
# Check available cameras
ls /dev/video*

# Try different index
python main.py --video 1
```

### "Low FPS / Stuttering"
Edit `.env`:
```bash
# Reduce resolution
VIDEO_WIDTH=1280
VIDEO_HEIGHT=720

# Or in Python:
python main.py --video 0
# Then edit config/config.yaml: process_every_n_frames: 2
```

### "Ball not detected"
- Ensure good lighting
- Use red or white ball (high contrast)
- Lower confidence threshold in `config/config.yaml`

### "Wrong decisions"
- Re-run calibration: `python scripts/calibrate.py`
- Ensure stumps clearly visible
- Check camera hasn't moved

---

## 💡 Pro Tips for Best Results

### Camera Positioning
```
    BATSMAN
       |
    [STUMPS]  ← Both stumps must be visible!
       |
    ───▼───
   │CAMERA│  ← 5-6 feet high, straight angle
   └──────┘
       |
    UMPIRE
```

### Lighting
- ✅ Best: Overcast day (even lighting)
- ✅ Good: Early morning/late afternoon
- ⚠️ Challenging: Harsh midday sun
- ❌ Avoid: Backlit (sun behind stumps)

### Ball Selection
- ✅ Best: Red ball on green pitch
- ✅ Good: White ball on green pitch
- ⚠️ OK: Pink ball
- ❌ Difficult: Old dark ball on dark pitch

### Between Deliveries
**IMPORTANT:** Press `r` to reset tracker before each delivery!
This clears the old trajectory and prevents confusion.

---

## 🎓 Learning the System

### Practice Run

Before your match, do a practice session:

1. Set up camera and laptop
2. Have someone bowl a few balls
3. Watch how system tracks and decides
4. Adjust settings if needed
5. Get comfortable with controls

### Understanding Decisions

The system shows:
- **OUT (Red):** Ball would hit stumps, meets all LBW criteria
- **NOT OUT (Green):** Doesn't meet LBW criteria (e.g., pitched outside leg)
- **UMPIRE'S CALL (Orange):** Too close to call, use your judgment
- **INSUFFICIENT DATA (Gray):** Couldn't track ball properly

### Decision Factors

System checks:
1. **Pitching:** Where did ball bounce? (Can't be outside leg)
2. **Impact:** Where did ball hit pad? (Must be in line)
3. **Hitting:** Would ball hit stumps? (Predicted trajectory)

---

## 📚 Next Steps

### Improve Accuracy

1. **Calibrate properly** - Most important!
   ```bash
   python scripts/calibrate.py
   ```

2. **Train custom model** (advanced - see docs)
   - Collect cricket images
   - Annotate objects
   - Train YOLOv8

3. **Optimize for your hardware**
   - Adjust settings in `config/config.yaml`
   - Run benchmark: `python scripts/benchmark.py`

### Learn More

- **Full Manual:** `README.md`
- **Technical Details:** `docs/TECHNICAL_GUIDE.md`
- **Field Guide:** `docs/FIELD_GUIDE.md`
- **FAQ:** `docs/FAQ.md`
- **Research Context:** `docs/RESEARCH_REFERENCES.md`

---

## 🤝 Spirit of the Game

**Remember:**
- This is for **fun and learning**
- Not a replacement for umpire's judgment
- Use in **friendly matches only**
- Always respect the umpire's final decision
- Enjoy cricket with friends! 🏏

**The system helps with:**
- Learning LBW rules
- Reducing disputes in friendly matches
- Adding technology fun to backyard cricket
- Post-match analysis and discussion

**The system doesn't:**
- Replace professional umpiring systems
- Work in all conditions perfectly
- Make final decisions (you do!)

---

## 🆘 Need Help?

1. **Check FAQ:** `docs/FAQ.md`
2. **Run tests:** `python scripts/test_system.py`
3. **Check logs:** `logs/lbw_system_*.log`
4. **Review docs:** All documentation in `docs/`

---

## 🎉 You're Ready!

Congratulations! You now have a working LBW decision system.

**To recap:**
```bash
# 1. Setup (one time)
./scripts/setup.sh
source venv/bin/activate

# 2. Calibrate (at each new location)
python scripts/calibrate.py

# 3. Run (at your match)
python main.py

# 4. Use (during match)
# Press 'r' before each delivery
# Watch decisions appear
# Have fun!
```

---

**Enjoy your cricket match! 🏏🎉**

*Questions? Check the documentation or run the test system.*

---

## 📖 Documentation Index

- `README.md` - Main documentation
- `QUICKSTART.md` - This file!
- `docs/FIELD_GUIDE.md` - Practical field usage
- `docs/TECHNICAL_GUIDE.md` - Technical deep dive
- `docs/FAQ.md` - Common questions
- `docs/RESEARCH_REFERENCES.md` - Academic context
- `CITATION.md` - How to cite this work

**Choose your path:**
- **Just want to use it?** → You're done! Run `python main.py`
- **Want to understand more?** → Read `docs/FIELD_GUIDE.md`
- **Technical person?** → Check `docs/TECHNICAL_GUIDE.md`
- **Have issues?** → See `docs/FAQ.md`
- **Research context?** → Read `docs/RESEARCH_REFERENCES.md`
