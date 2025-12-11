# Field Deployment Guide

**Quick Reference for Using LBW System at Local Cricket Matches**

---

## Pre-Match Setup (30 minutes)

### 1. Equipment Checklist

**Required:**
- [ ] Laptop with system installed
- [ ] Webcam or camera with USB connection
- [ ] Tripod or stable mounting solution
- [ ] Power bank or extension cord
- [ ] Sunshade for laptop screen (if outdoors)

**Optional:**
- [ ] Portable monitor for better viewing
- [ ] Wireless keyboard/mouse for remote control
- [ ] Backup camera
- [ ] Mobile hotspot (if uploading decisions)

### 2. System Check (15 minutes)

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Run system test
python scripts/test_system.py

# 3. Check camera
python main.py --video 0

# Press 'q' to quit after confirming video works
```

**If any tests fail:**
- Check camera connection
- Verify Python environment
- Review error logs in `logs/`

### 3. Camera Positioning (10 minutes)

**Optimal Setup:**

```
                    BATSMAN
                       |
                       |
    ←------------------┼------------------→
    OFF SIDE           |           LEG SIDE
                       |
                   [STUMPS]
                       |
                       |
                    ───▼───
                   │CAMERA│  ← 5-6 feet high
                   └──────┘
                       |
                    UMPIRE
```

**Positioning Guidelines:**

1. **Height:** 5-6 feet (1.5-2 meters) above ground
   - Too low: Can't see over batsman
   - Too high: Loses depth perception

2. **Distance:** At umpire's normal position (behind stumps)
   - Not too close (wide angle distortion)
   - Not too far (ball too small)

3. **Angle:** Straight down the pitch
   - Both sets of stumps should be visible
   - Minimal side angle

4. **Stability:** Secure mount
   - Use tripod with weight
   - Avoid areas with foot traffic
   - Shield from wind if outdoors

### 4. Calibration (5 minutes)

**Run calibration script:**

```bash
python scripts/calibrate.py
```

**Calibration Steps:**

1. **Capture Frame**
   - Press 's' when pitch is empty
   - Ensure both stumps visible

2. **Mark Reference Points**
   - Click: Bottom of near stumps (umpire end)
   - Click: Center of far stumps
   - Click: Right edge of far stumps
   - Click: Right edge of near stumps
   - Press 'c' when done

3. **Enter Measurements**
   - Pitch length: Usually 20.12m (22 yards)
   - Stump width: Usually 0.23m (9 inches)
   - Location: "Local Ground Name"
   - Notes: Date, weather conditions

4. **Verify Calibration**
   - System will show overlay
   - Check if measurements look correct
   - Re-calibrate if needed

---

## During Match

### Starting the System

```bash
# Start system with your configuration
python main.py

# With video file (for testing first)
python main.py --video test_match.mp4

# Save output for later review
python main.py --save-video
```

**You should see:**
- Live video feed
- Green FPS counter (should be 20+)
- Detection boxes when objects appear
- LBW decision panel (right side)

### Operating Guidelines

#### Between Deliveries

**Press `r` to reset tracker**
- Do this before each delivery
- Clears old ball trajectory
- Prevents confusion with previous ball

#### During Delivery

**Do NOT touch anything**
- Let system track automatically
- Watch for ball detection (red box)
- Observe trajectory line (yellow)

#### After Potential LBW

**Check decision panel:**
- **OUT** (red) - Ball would have hit stumps
- **NOT OUT** (green) - Doesn't meet LBW criteria
- **UMPIRE'S CALL** (orange) - Marginal decision

**Press `s` to save screenshot** if you want to review later

#### Managing Performance

**If FPS drops below 20:**
1. Press `p` to pause
2. Close other applications
3. Reduce video quality in config
4. Press `p` to resume

### Dealing with Issues

#### Ball Not Detected

**Immediate fixes:**
1. Check lighting - add portable lights if needed
2. Clean camera lens
3. Ensure ball contrasts with pitch

**Config adjustments:**
```yaml
detection:
  confidence_threshold: 0.3  # Lower = more detections
```

#### False Detections

**If system detects wrong objects:**
1. Press `r` to reset
2. Wait for clear delivery
3. Adjust confidence threshold up

#### Occlusion Issues

**If batsman blocks view:**
- Note: This is a known limitation
- Decision may be "INSUFFICIENT DATA"
- Use umpire's judgment

#### System Crashed

```bash
# Quick restart
python main.py

# If persists, check logs
tail -f logs/lbw_system_*.log
```

---

## Post-Match

### Reviewing Decisions

**Saved screenshots in:** `output/`

**View decision log:**
```bash
cat logs/decisions_*.log
```

**Analysis:**
- Count OUT vs NOT OUT decisions
- Review confidence scores
- Check any controversial decisions

### Performance Report

```bash
# System will print on exit:
# - Total frames processed
# - Average FPS
# - Decisions made
# - CPU/Memory usage
```

### Backup Data

```bash
# Copy important files
cp -r output/ backup_$(date +%Y%m%d)/
cp logs/decisions_*.log backup_$(date +%Y%m%d)/
```

---

## Tips for Best Results

### 🌞 Lighting

**Best:**
- Overcast day (even lighting)
- Indoor with good lights
- Early morning/late afternoon

**Avoid:**
- Direct harsh sunlight
- Strong shadows across pitch
- Backlighting (sun behind stumps)

### 🏏 Ball Selection

**Best:**
- Red ball (traditional)
- White ball on green grass
- New or semi-new ball

**Challenges:**
- Old dark ball on dark pitch
- Pink ball (sometimes)
- Wet ball

### 📹 Camera Settings

**If your camera allows:**
- Shutter speed: 1/500s or faster (reduce motion blur)
- ISO: Auto (or 200-400 in good light)
- White balance: Daylight
- Focus: Manual (lock on stumps)

### 🎯 Usage Strategy

**For friendly matches:**
1. Use for "close" LBW appeals only
2. Don't interrupt game flow
3. Show replay to players after
4. Remember: It's for fun!

**For practice:**
1. Test all LBWs for learning
2. Compare with umpire's decision
3. Discuss marginal calls
4. Build understanding of LBW rules

---

## Common Scenarios

### Scenario 1: Clear LBW

**Ball pitched in line, hit pad in front of stumps**

Expected result:
- ✅ Clear trajectory tracking
- ✅ Impact detected
- ✅ Decision: OUT (high confidence 85%+)

### Scenario 2: Pitched Outside Leg

**Ball clearly pitched outside leg stump**

Expected result:
- ✅ Pitching point detected
- ✅ Decision: NOT OUT immediately
- ✅ Reason: "Pitched outside leg"

### Scenario 3: Impact Outside Off

**Ball hit pad outside off stump line**

Expected result:
- ✅ Impact zone: OUTSIDE OFF
- ✅ Decision: NOT OUT
- ✅ Reason: "Impact outside off stump"

### Scenario 4: Going Over

**Ball hit pad low but bouncing trajectory**

Expected result:
- ⚠️ May show hitting stumps (system limitation)
- ⚠️ Height judgment less reliable
- 💡 Use umpire judgment for final decision

### Scenario 5: Batsman Blocks View

**Body obscures ball during impact**

Expected result:
- ❌ Ball tracking lost
- ❌ Decision: INSUFFICIENT DATA
- 💡 Can't make decision - need clear view

---

## Keyboard Quick Reference

| Key | Action | When to Use |
|-----|--------|-------------|
| `q` | Quit system | End of match |
| `p` | Pause/Resume | Take break, adjust camera |
| `r` | Reset tracker | **Before each delivery** |
| `s` | Screenshot | Save interesting decision |

---

## Emergency Procedures

### System Frozen

1. Press `Ctrl+C` to force quit
2. Restart: `python main.py`
3. If still frozen, reboot laptop

### Camera Disconnected

1. System will show error
2. Reconnect camera USB
3. Restart system

### Battery Low

1. Press `q` to quit properly
2. Connect to power
3. Restart when charged

### Rain/Weather

1. Save current session: Press `q`
2. Protect equipment
3. Can resume with same calibration if camera position unchanged

---

## Quick Start Checklist

**5 Minutes Before First Ball:**

1. [ ] System running (`python main.py`)
2. [ ] Camera view clear - both stumps visible
3. [ ] FPS > 20 (check top-left corner)
4. [ ] Press `r` (tracker reset)
5. [ ] Tell players system is ready
6. [ ] Position yourself to see both screen and field

**Remember:** You're the backup umpire. Your decision matters most in a friendly game! The system is a helpful tool, not the final authority.

---

## Support & Troubleshooting

**For technical issues:**
1. Check `logs/lbw_system_*.log`
2. Run `python scripts/test_system.py`
3. Review `docs/TECHNICAL_GUIDE.md`

**For cricket rules:**
- Review LBW laws: https://www.lords.org/mcc/the-laws-of-cricket
- Consult experienced umpires

---

## Making It Fun!

**Ideas for friendly matches:**
1. **"Hawkeye Challenge"** - Players can review decisions after innings
2. **"Umpire vs System"** - Compare umpire's call with system
3. **"Learning Mode"** - Discuss each LBW to understand rules better
4. **"Replay Reel"** - Save all LBWs for post-match entertainment

Remember: Cricket is about sportsmanship and fun. Use this system to enhance the experience, not replace the spirit of the game!

---

**Good luck and enjoy your match! 🏏**
