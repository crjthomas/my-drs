#!/usr/bin/env python3
"""
Camera Calibration Script for LBW Decision System
"""

import cv2
import numpy as np
import yaml
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_manager import ConfigManager
from src.video_capture import VideoCapture


class CameraCalibrator:
    """Handles camera calibration for the LBW system"""
    
    def __init__(self, config_path='config/config.yaml'):
        self.config = ConfigManager(config_path)
        self.calibration_data = {
            'camera_matrix': None,
            'distortion_coefficients': None,
            'perspective_matrix': None,
            'reference_points': {
                'world': [],
                'image': []
            },
            'pixel_to_meter': None,
            'calibration_date': None,
            'calibration_location': None,
            'camera_model': None,
            'notes': ''
        }
        
        self.reference_points = []
        self.current_frame = None
    
    def run_interactive_calibration(self):
        """Run interactive calibration"""
        print("=" * 70)
        print("LBW DECISION SYSTEM - CAMERA CALIBRATION")
        print("=" * 70)
        print()
        print("This calibration will help the system understand:")
        print("  - Camera distortion")
        print("  - Perspective transformation")
        print("  - Real-world measurements")
        print()
        print("Instructions:")
        print("1. Position camera at umpire's view")
        print("2. Ensure entire pitch and stumps are visible")
        print("3. Click on reference points when prompted")
        print("4. Enter real-world measurements")
        print()
        input("Press Enter to start calibration...")
        print()
        
        # Start video capture
        video_config = self.config.config['video']
        capture = VideoCapture(
            source=video_config['source'],
            width=video_config['width'],
            height=video_config['height'],
            fps=video_config['fps']
        )
        
        if not capture.start():
            print("Error: Failed to start video capture")
            return False
        
        print("Capturing calibration frame...")
        print("Press 's' to capture, 'q' to quit")
        
        # Capture frame for calibration
        calibration_frame = None
        while True:
            ret, frame, _ = capture.read()
            if not ret:
                continue
            
            cv2.imshow('Calibration - Press S to capture', frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('s'):
                calibration_frame = frame.copy()
                break
            elif key == ord('q'):
                capture.stop()
                cv2.destroyAllWindows()
                return False
        
        capture.stop()
        
        if calibration_frame is None:
            print("Error: No frame captured")
            return False
        
        print("Frame captured!")
        print()
        
        # Get reference points
        self.current_frame = calibration_frame
        self._get_reference_points()
        
        # Calculate calibration parameters
        self._calculate_calibration()
        
        # Save calibration
        self._save_calibration()
        
        cv2.destroyAllWindows()
        
        print()
        print("=" * 70)
        print("Calibration completed successfully!")
        print("Calibration saved to: config/camera_calibration.yaml")
        print("=" * 70)
        
        return True
    
    def _get_reference_points(self):
        """Get reference points from user"""
        print("Click on the following points in order:")
        print("  1. Umpire position (bottom center)")
        print("  2. Far stumps (center)")
        print("  3. Far stumps right edge")
        print("  4. Near stumps right edge")
        print()
        print("Press 'r' to reset points, 'c' to continue when done")
        
        self.reference_points = []
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                self.reference_points.append((x, y))
                print(f"Point {len(self.reference_points)}: ({x}, {y})")
                
                # Draw point
                cv2.circle(self.current_frame, (x, y), 5, (0, 255, 0), -1)
                cv2.putText(
                    self.current_frame,
                    str(len(self.reference_points)),
                    (x + 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )
                cv2.imshow('Calibration - Click reference points', self.current_frame)
        
        cv2.namedWindow('Calibration - Click reference points')
        cv2.setMouseCallback('Calibration - Click reference points', mouse_callback)
        cv2.imshow('Calibration - Click reference points', self.current_frame)
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('r'):
                # Reset
                self.reference_points = []
                self.current_frame = self.current_frame.copy()
                cv2.imshow('Calibration - Click reference points', self.current_frame)
                print("Points reset")
            elif key == ord('c') and len(self.reference_points) >= 4:
                break
        
        # Store image reference points
        self.calibration_data['reference_points']['image'] = self.reference_points[:4]
        
        # Get real-world measurements
        print()
        print("Enter real-world measurements:")
        
        pitch_length = float(input("Pitch length (meters) [default 20.12]: ") or "20.12")
        stump_width = float(input("Stump width (meters) [default 0.23]: ") or "0.23")
        
        # Define world coordinates (assuming flat ground, z=0)
        self.calibration_data['reference_points']['world'] = [
            [0, 0, 0],  # Umpire position
            [pitch_length, 0, 0],  # Far stumps center
            [pitch_length, stump_width, 0],  # Far stumps right
            [0, stump_width, 0]  # Near stumps right
        ]
    
    def _calculate_calibration(self):
        """Calculate calibration parameters"""
        print()
        print("Calculating calibration parameters...")
        
        # Calculate pixel to meter ratio
        # Use distance between reference points
        img_points = np.array(self.calibration_data['reference_points']['image'])
        world_points = np.array(self.calibration_data['reference_points']['world'])
        
        # Calculate distance in pixels
        pixel_dist = np.linalg.norm(img_points[1] - img_points[0])
        
        # Calculate distance in meters
        meter_dist = np.linalg.norm(world_points[1] - world_points[0])
        
        # Calculate ratio
        self.calibration_data['pixel_to_meter'] = meter_dist / pixel_dist
        
        print(f"Pixel to meter ratio: {self.calibration_data['pixel_to_meter']:.6f}")
        
        # Calculate perspective transformation matrix
        src_points = img_points.astype(np.float32)
        dst_points = world_points[:, :2].astype(np.float32) * 100  # Scale for better numerical stability
        
        if len(src_points) >= 4:
            matrix = cv2.getPerspectiveTransform(src_points[:4], dst_points[:4])
            self.calibration_data['perspective_matrix'] = matrix.tolist()
        
        # Add metadata
        from datetime import datetime
        self.calibration_data['calibration_date'] = datetime.now().isoformat()
        self.calibration_data['calibration_location'] = input("\nCalibration location (optional): ") or "Unknown"
        self.calibration_data['camera_model'] = input("Camera model (optional): ") or "Unknown"
        self.calibration_data['notes'] = input("Notes (optional): ") or ""
    
    def _save_calibration(self):
        """Save calibration data"""
        output_path = Path('config/camera_calibration.yaml')
        
        with open(output_path, 'w') as f:
            yaml.dump(self.calibration_data, f, default_flow_style=False)
        
        # Update main config with pixel_to_meter ratio
        self.config.set('calibration.pixel_to_meter_ratio', self.calibration_data['pixel_to_meter'])
        self.config.save_config()
        
        print(f"Calibration saved to {output_path}")


def main():
    """Main entry point"""
    calibrator = CameraCalibrator()
    
    try:
        calibrator.run_interactive_calibration()
    except KeyboardInterrupt:
        print("\nCalibration interrupted by user")
    except Exception as e:
        print(f"\nError during calibration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
