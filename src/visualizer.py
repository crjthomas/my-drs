"""
Visualization Module for LBW Decision System
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from src.object_detector import Detection
from src.ball_tracker import BallTrack
from src.lbw_decision import LBWDecisionData, Decision


class Visualizer:
    """Handles visualization of detections, trajectories, and decisions"""
    
    def __init__(
        self,
        show_detections: bool = True,
        show_trajectory: bool = True,
        show_decision: bool = True,
        overlay_transparency: float = 0.3
    ):
        """
        Initialize visualizer
        
        Args:
            show_detections: Show object detections
            show_trajectory: Show ball trajectory
            show_decision: Show LBW decision
            overlay_transparency: Transparency for overlays
        """
        self.show_detections = show_detections
        self.show_trajectory = show_trajectory
        self.show_decision = show_decision
        self.overlay_transparency = overlay_transparency
        
        # Colors (BGR format)
        self.colors = {
            'ball': (0, 0, 255),      # Red
            'batsman': (0, 255, 0),   # Green
            'stumps': (255, 0, 0),    # Blue
            'pads': (255, 255, 0),    # Cyan
            'bat': (255, 0, 255),     # Magenta
            'trajectory': (0, 255, 255),  # Yellow
            'predicted': (255, 128, 0),   # Orange
            'out': (0, 0, 255),       # Red
            'not_out': (0, 255, 0),   # Green
            'umpires_call': (0, 165, 255),  # Orange
            'pitch_mark': (255, 255, 255),  # White
            'impact_mark': (255, 0, 255)    # Magenta
        }
    
    def draw_frame(
        self,
        frame: np.ndarray,
        detections: Optional[List[Detection]] = None,
        tracks: Optional[List[BallTrack]] = None,
        decision_data: Optional[LBWDecisionData] = None,
        fps: Optional[float] = None,
        frame_number: Optional[int] = None
    ) -> np.ndarray:
        """
        Draw all visualizations on frame
        
        Args:
            frame: Input frame
            detections: Object detections
            tracks: Ball tracks
            decision_data: LBW decision data
            fps: Current FPS
            frame_number: Frame number
            
        Returns:
            Visualized frame
        """
        output = frame.copy()
        
        # Draw detections
        if self.show_detections and detections:
            output = self.draw_detections(output, detections)
        
        # Draw trajectories
        if self.show_trajectory and tracks:
            output = self.draw_trajectories(output, tracks)
        
        # Draw decision overlay
        if self.show_decision and decision_data:
            output = self.draw_decision_overlay(output, decision_data)
        
        # Draw info panel
        output = self.draw_info_panel(output, fps, frame_number)
        
        return output
    
    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Detection]
    ) -> np.ndarray:
        """
        Draw object detections
        
        Args:
            frame: Input frame
            detections: List of detections
            
        Returns:
            Frame with detections drawn
        """
        output = frame.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            color = self.colors.get(detection.class_name, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{detection.class_name}: {detection.confidence:.2f}"
            label_size, baseline = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                2
            )
            
            # Draw label background
            cv2.rectangle(
                output,
                (x1, y1 - label_size[1] - baseline - 5),
                (x1 + label_size[0], y1),
                color,
                -1
            )
            
            # Draw label text
            cv2.putText(
                output,
                label,
                (x1, y1 - baseline - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
            
            # Draw center point
            cv2.circle(output, detection.center, 5, color, -1)
        
        return output
    
    def draw_trajectories(
        self,
        frame: np.ndarray,
        tracks: List[BallTrack]
    ) -> np.ndarray:
        """
        Draw ball trajectories
        
        Args:
            frame: Input frame
            tracks: List of ball tracks
            
        Returns:
            Frame with trajectories drawn
        """
        output = frame.copy()
        
        for track in tracks:
            trajectory = track.get_trajectory()
            
            if len(trajectory) < 2:
                continue
            
            # Draw trajectory line
            points = np.array(trajectory, dtype=np.int32)
            
            # Draw with gradient (older points lighter)
            for i in range(len(points) - 1):
                alpha = (i + 1) / len(points)  # 0 to 1
                thickness = int(2 + alpha * 3)
                
                pt1 = tuple(points[i])
                pt2 = tuple(points[i + 1])
                
                cv2.line(output, pt1, pt2, self.colors['trajectory'], thickness)
            
            # Draw current position (larger)
            if len(points) > 0:
                current_pos = tuple(points[-1])
                cv2.circle(output, current_pos, 8, self.colors['ball'], -1)
                cv2.circle(output, current_pos, 10, self.colors['trajectory'], 2)
            
            # Draw velocity vector
            velocity = track.get_velocity_vector()
            if velocity and len(points) > 0:
                current_pos = points[-1]
                end_pos = (
                    int(current_pos[0] + velocity[0] * 5),
                    int(current_pos[1] + velocity[1] * 5)
                )
                cv2.arrowedLine(
                    output,
                    tuple(current_pos),
                    end_pos,
                    self.colors['trajectory'],
                    2,
                    tipLength=0.3
                )
        
        return output
    
    def draw_predicted_trajectory(
        self,
        frame: np.ndarray,
        trajectory: List[Tuple[float, float]]
    ) -> np.ndarray:
        """
        Draw predicted trajectory
        
        Args:
            frame: Input frame
            trajectory: Predicted trajectory points
            
        Returns:
            Frame with predicted trajectory
        """
        output = frame.copy()
        
        if len(trajectory) < 2:
            return output
        
        # Draw dashed line for prediction
        points = np.array(trajectory, dtype=np.int32)
        
        for i in range(len(points) - 1):
            if i % 2 == 0:  # Dashed effect
                pt1 = tuple(points[i])
                pt2 = tuple(points[i + 1])
                cv2.line(output, pt1, pt2, self.colors['predicted'], 2)
        
        return output
    
    def draw_decision_overlay(
        self,
        frame: np.ndarray,
        decision_data: LBWDecisionData
    ) -> np.ndarray:
        """
        Draw LBW decision overlay
        
        Args:
            frame: Input frame
            decision_data: Decision data
            
        Returns:
            Frame with decision overlay
        """
        output = frame.copy()
        h, w = output.shape[:2]
        
        # Draw predicted trajectory
        if decision_data.predicted_trajectory:
            output = self.draw_predicted_trajectory(
                output,
                decision_data.predicted_trajectory
            )
        
        # Draw pitching point
        if decision_data.pitching_point:
            pt = tuple(map(int, decision_data.pitching_point))
            cv2.circle(output, pt, 10, self.colors['pitch_mark'], 2)
            cv2.circle(output, pt, 15, self.colors['pitch_mark'], 1)
            cv2.putText(
                output,
                "PITCH",
                (pt[0] - 30, pt[1] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                self.colors['pitch_mark'],
                2
            )
        
        # Draw impact point
        if decision_data.impact_point:
            pt = tuple(map(int, decision_data.impact_point))
            cv2.circle(output, pt, 10, self.colors['impact_mark'], 2)
            cv2.circle(output, pt, 15, self.colors['impact_mark'], 1)
            cv2.putText(
                output,
                "IMPACT",
                (pt[0] - 35, pt[1] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                self.colors['impact_mark'],
                2
            )
        
        # Draw decision panel
        output = self.draw_decision_panel(output, decision_data)
        
        return output
    
    def draw_decision_panel(
        self,
        frame: np.ndarray,
        decision_data: LBWDecisionData
    ) -> np.ndarray:
        """
        Draw decision information panel
        
        Args:
            frame: Input frame
            decision_data: Decision data
            
        Returns:
            Frame with decision panel
        """
        output = frame.copy()
        h, w = output.shape[:2]
        
        # Panel dimensions
        panel_width = 400
        panel_height = 300
        panel_x = w - panel_width - 20
        panel_y = 20
        
        # Create semi-transparent overlay
        overlay = output.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay, self.overlay_transparency, output, 1 - self.overlay_transparency, 0, output)
        
        # Draw panel border
        cv2.rectangle(
            output,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (255, 255, 255),
            2
        )
        
        # Draw decision
        decision_color = {
            Decision.OUT: self.colors['out'],
            Decision.NOT_OUT: self.colors['not_out'],
            Decision.UMPIRES_CALL: self.colors['umpires_call'],
            Decision.INSUFFICIENT_DATA: (128, 128, 128)
        }.get(decision_data.decision, (255, 255, 255))
        
        # Decision text
        cv2.putText(
            output,
            "LBW DECISION",
            (panel_x + 20, panel_y + 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        
        cv2.putText(
            output,
            decision_data.decision.value,
            (panel_x + 20, panel_y + 75),
            cv2.FONT_HERSHEY_BOLD,
            1.2,
            decision_color,
            3
        )
        
        # Confidence
        confidence_text = f"Confidence: {decision_data.confidence:.1%}"
        cv2.putText(
            output,
            confidence_text,
            (panel_x + 20, panel_y + 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )
        
        # Decision details
        y_offset = 145
        line_height = 25
        
        details = [
            f"Pitching: {decision_data.pitching_zone.value}",
            f"Impact: {decision_data.impact_zone.value}",
            f"Hitting: {'YES' if decision_data.hits_stumps else 'NO'}",
            "",
            f"Impact in line: {'YES' if decision_data.impact_in_line else 'NO'}",
            f"Pitched outside leg: {'YES' if decision_data.pitched_outside_leg else 'NO'}"
        ]
        
        for detail in details:
            cv2.putText(
                output,
                detail,
                (panel_x + 20, panel_y + y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (200, 200, 200),
                1
            )
            y_offset += line_height
        
        return output
    
    def draw_info_panel(
        self,
        frame: np.ndarray,
        fps: Optional[float] = None,
        frame_number: Optional[int] = None
    ) -> np.ndarray:
        """
        Draw information panel with FPS and frame number
        
        Args:
            frame: Input frame
            fps: Current FPS
            frame_number: Frame number
            
        Returns:
            Frame with info panel
        """
        output = frame.copy()
        
        info_text = []
        
        if fps is not None:
            info_text.append(f"FPS: {fps:.1f}")
        
        if frame_number is not None:
            info_text.append(f"Frame: {frame_number}")
        
        if not info_text:
            return output
        
        # Draw info in top-left corner
        y_offset = 30
        for text in info_text:
            cv2.putText(
                output,
                text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            y_offset += 30
        
        return output
    
    def create_split_view(
        self,
        original: np.ndarray,
        processed: np.ndarray
    ) -> np.ndarray:
        """
        Create side-by-side comparison view
        
        Args:
            original: Original frame
            processed: Processed frame with visualizations
            
        Returns:
            Combined frame
        """
        # Resize if needed
        h1, w1 = original.shape[:2]
        h2, w2 = processed.shape[:2]
        
        if h1 != h2 or w1 != w2:
            processed = cv2.resize(processed, (w1, h1))
        
        # Concatenate horizontally
        combined = np.hstack([original, processed])
        
        # Add labels
        cv2.putText(
            combined,
            "ORIGINAL",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2
        )
        
        cv2.putText(
            combined,
            "PROCESSED",
            (w1 + 20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2
        )
        
        return combined
