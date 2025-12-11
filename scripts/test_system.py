#!/usr/bin/env python3
"""
System Test Script for LBW Decision System
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np
from src.config_manager import ConfigManager
from src.object_detector import ObjectDetector
from src.ball_tracker import BallTracker
from src.trajectory_predictor import TrajectoryPredictor
from src.lbw_decision import LBWDecisionEngine


def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    try:
        config = ConfigManager()
        assert config.get('video.fps') > 0
        print("✓ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_detector():
    """Test object detector"""
    print("\nTesting object detector...")
    try:
        detector = ObjectDetector(
            model_path='models/cricket_detector.pt',
            confidence_threshold=0.5
        )
        
        # Create dummy frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detections = detector.detect(frame)
        
        print(f"✓ Detector initialized (detections: {len(detections)})")
        return True
    except Exception as e:
        print(f"✗ Detector test failed: {e}")
        return False


def test_tracker():
    """Test ball tracker"""
    print("\nTesting ball tracker...")
    try:
        tracker = BallTracker()
        
        # Simulate ball positions
        positions = [(100, 100), (105, 102), (110, 105), (115, 108)]
        tracks = tracker.update(positions)
        
        print(f"✓ Tracker initialized (tracks: {len(tracks)})")
        return True
    except Exception as e:
        print(f"✗ Tracker test failed: {e}")
        return False


def test_trajectory_predictor():
    """Test trajectory predictor"""
    print("\nTesting trajectory predictor...")
    try:
        predictor = TrajectoryPredictor()
        
        # Create sample trajectory
        positions = [(i, i*2) for i in range(10)]
        predicted = predictor.predict_trajectory(positions, num_points=5)
        
        print(f"✓ Predictor initialized (predicted points: {len(predicted)})")
        return True
    except Exception as e:
        print(f"✗ Predictor test failed: {e}")
        return False


def test_decision_engine():
    """Test LBW decision engine"""
    print("\nTesting LBW decision engine...")
    try:
        engine = LBWDecisionEngine()
        engine.set_stumps_position((320, 400))
        engine.set_ground_level(450)
        
        # Create sample trajectory
        trajectory = [(i*10, 400 - i*5) for i in range(10)]
        predicted = [(i*10, 400 - i*5) for i in range(10, 20)]
        impact = (150, 380)
        
        decision = engine.make_decision(trajectory, predicted, impact)
        
        print(f"✓ Decision engine initialized (decision: {decision.decision.value})")
        return True
    except Exception as e:
        print(f"✗ Decision engine test failed: {e}")
        return False


def test_video_capture():
    """Test video capture"""
    print("\nTesting video capture...")
    try:
        # Try to open default camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("⚠ Camera not available (this is OK if no camera connected)")
            return True
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            print(f"✓ Video capture working (frame shape: {frame.shape})")
            return True
        else:
            print("⚠ Could not read frame from camera")
            return True  # Not critical
    except Exception as e:
        print(f"⚠ Video capture test failed: {e}")
        return True  # Not critical


def test_opencv():
    """Test OpenCV functionality"""
    print("\nTesting OpenCV...")
    try:
        # Test basic operations
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        print("✓ OpenCV operations working")
        return True
    except Exception as e:
        print(f"✗ OpenCV test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("LBW DECISION SYSTEM - SYSTEM TEST")
    print("=" * 70)
    print()
    
    tests = [
        ("Configuration", test_config),
        ("OpenCV", test_opencv),
        ("Object Detector", test_detector),
        ("Ball Tracker", test_tracker),
        ("Trajectory Predictor", test_trajectory_predictor),
        ("LBW Decision Engine", test_decision_engine),
        ("Video Capture", test_video_capture)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("All tests passed! System is ready to use.")
        return 0
    else:
        print(f"Warning: {total - passed} test(s) failed.")
        print("Please fix the issues before running the system.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
