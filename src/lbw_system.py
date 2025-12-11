"""
Main LBW Decision System
Integrates all components for real-time LBW decision making
"""

import cv2
import time
import numpy as np
from pathlib import Path
from typing import Optional, List
from loguru import logger

from src.config_manager import ConfigManager
from src.logger_setup import setup_logger, log_decision
from src.video_capture import VideoCapture, FramePreprocessor
from src.object_detector import ObjectDetector, Detection
from src.ball_tracker import BallTracker, BallTrack
from src.trajectory_predictor import TrajectoryPredictor
from src.lbw_decision import LBWDecisionEngine, LBWDecisionData, Decision
from src.visualizer import Visualizer
from src.performance_monitor import PerformanceMonitor


class LBWDecisionSystem:
    """Main LBW Decision System"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize LBW Decision System
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = ConfigManager(config_path)
        
        # Setup logging
        setup_logger(
            log_path=self.config.get('output.log_path'),
            log_level=self.config.get('output.log_level', 'INFO')
        )
        
        logger.info("Initializing LBW Decision System")
        
        # Initialize components
        self._init_components()
        
        # State
        self.running = False
        self.paused = False
        self.last_decision: Optional[LBWDecisionData] = None
        
        logger.info("LBW Decision System initialized successfully")
    
    def _init_components(self) -> None:
        """Initialize all system components"""
        
        # Video capture
        video_config = self.config.config['video']
        self.video_capture = VideoCapture(
            source=video_config['source'],
            width=video_config['width'],
            height=video_config['height'],
            fps=video_config['fps'],
            buffer_size=video_config['buffer_size']
        )
        
        # Frame preprocessor
        self.preprocessor = FramePreprocessor()
        
        # Object detector
        detection_config = self.config.config['detection']
        self.detector = ObjectDetector(
            model_path=detection_config['model_path'],
            confidence_threshold=detection_config['confidence_threshold'],
            nms_threshold=detection_config['nms_threshold'],
            device=detection_config['device'],
            classes=detection_config['classes']
        )
        
        # Ball tracker
        tracking_config = self.config.config['tracking']
        self.tracker = BallTracker(
            max_frames_to_skip=tracking_config['max_frames_to_skip'],
            min_track_length=tracking_config['min_track_length'],
            distance_threshold=tracking_config['distance_threshold']
        )
        
        # Trajectory predictor
        trajectory_config = self.config.config['trajectory']
        calibration_config = self.config.config['calibration']
        self.trajectory_predictor = TrajectoryPredictor(
            gravity=trajectory_config['gravity'],
            air_resistance=trajectory_config['air_resistance'],
            ball_mass=trajectory_config['ball_mass'],
            ball_radius=trajectory_config['ball_radius'],
            pixel_to_meter=calibration_config['pixel_to_meter_ratio']
        )
        
        # LBW decision engine
        lbw_config = self.config.config['lbw']
        self.decision_engine = LBWDecisionEngine(
            pitch_length=lbw_config['pitch_length'],
            stump_height=lbw_config['stump_height'],
            stump_width=lbw_config['stump_width'],
            impact_threshold=lbw_config['impact_threshold'],
            line_threshold=lbw_config['line_threshold'],
            pitching_threshold=lbw_config['pitching_threshold'],
            wicket_margin=lbw_config['wicket_margin'],
            umpires_call_impact=lbw_config['umpires_call']['impact'],
            umpires_call_wicket=lbw_config['umpires_call']['wicket'],
            umpires_call_pitching=lbw_config['umpires_call']['pitching'],
            min_confidence=lbw_config['min_confidence'],
            pixel_to_meter=calibration_config['pixel_to_meter_ratio']
        )
        
        # Visualizer
        viz_config = self.config.config['output']['visualization']
        self.visualizer = Visualizer(
            show_detections=viz_config['show_detections'],
            show_trajectory=viz_config['show_trajectory'],
            show_decision=viz_config['show_decision'],
            overlay_transparency=viz_config['overlay_transparency']
        )
        
        # Performance monitor
        monitoring_config = self.config.config['monitoring']
        self.performance_monitor = PerformanceMonitor()
        if monitoring_config['enabled']:
            self.performance_monitor.start_monitoring()
        
        # Video writer (if saving)
        self.video_writer: Optional[cv2.VideoWriter] = None
        if self.config.get('output.save_video'):
            self._init_video_writer()
    
    def _init_video_writer(self) -> None:
        """Initialize video writer for saving output"""
        output_path = Path(self.config.get('output.output_path'))
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = output_path / f"lbw_output_{timestamp}.mp4"
        
        # Get video properties
        width = self.config.get('video.width')
        height = self.config.get('video.height')
        fps = self.config.get('video.fps')
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            str(output_file),
            fourcc,
            fps,
            (width, height)
        )
        
        logger.info(f"Video writer initialized: {output_file}")
    
    def start(self) -> None:
        """Start the LBW decision system"""
        logger.info("Starting LBW Decision System")
        
        # Start video capture
        if not self.video_capture.start():
            logger.error("Failed to start video capture")
            return
        
        self.running = True
        
        # Main processing loop
        try:
            self._processing_loop()
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Error in processing loop: {e}", exc_info=True)
        finally:
            self.stop()
    
    def _processing_loop(self) -> None:
        """Main processing loop"""
        logger.info("Entering main processing loop")
        
        prev_frame = None
        frame_count = 0
        
        while self.running:
            loop_start = time.time()
            
            # Read frame
            ret, frame, frame_number = self.video_capture.read()
            
            if not ret or frame is None:
                logger.warning("Failed to read frame")
                time.sleep(0.01)
                continue
            
            frame_count += 1
            self.performance_monitor.record_frame()
            
            # Check if we should process this frame
            process_every_n = self.config.get('processing.process_every_n_frames', 1)
            if frame_count % process_every_n != 0:
                continue
            
            # Process frame
            processed_frame, detections, tracks = self._process_frame(frame, prev_frame)
            
            # Make LBW decision if we have a valid track
            decision_data = None
            if tracks:
                best_track = self.tracker.get_best_track()
                if best_track and best_track.get_length() >= 10:
                    decision_data = self._make_lbw_decision(best_track, detections)
                    if decision_data:
                        self.last_decision = decision_data
                        self.performance_monitor.record_decision()
            
            # Visualize
            if self.config.get('output.display'):
                viz_frame = self.visualizer.draw_frame(
                    processed_frame,
                    detections=detections,
                    tracks=tracks,
                    decision_data=decision_data or self.last_decision,
                    fps=self.performance_monitor.get_fps(),
                    frame_number=frame_number
                )
                
                # Display
                cv2.imshow('LBW Decision System', viz_frame)
                
                # Save if enabled
                if self.video_writer:
                    self.video_writer.write(viz_frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logger.info("Quit requested")
                break
            elif key == ord('p'):
                self.paused = not self.paused
                logger.info(f"Paused: {self.paused}")
            elif key == ord('r'):
                self.tracker.reset()
                self.last_decision = None
                logger.info("Tracker reset")
            elif key == ord('s'):
                # Save screenshot
                self._save_screenshot(viz_frame)
            
            # Wait if paused
            while self.paused and self.running:
                key = cv2.waitKey(100) & 0xFF
                if key == ord('p'):
                    self.paused = False
                elif key == ord('q'):
                    self.running = False
                    break
            
            # Record processing time
            processing_time = time.time() - loop_start
            self.performance_monitor.record_processing_time(processing_time)
            
            prev_frame = frame
        
        logger.info("Exited processing loop")
    
    def _process_frame(
        self,
        frame: np.ndarray,
        prev_frame: Optional[np.ndarray]
    ) -> tuple:
        """
        Process a single frame
        
        Args:
            frame: Current frame
            prev_frame: Previous frame
            
        Returns:
            Tuple of (processed_frame, detections, tracks)
        """
        processed_frame = frame.copy()
        
        # Detect objects
        detection_start = time.time()
        detections = self.detector.detect(frame)
        detection_time = time.time() - detection_start
        self.performance_monitor.record_detection_time(detection_time)
        self.performance_monitor.record_detection(len(detections))
        
        # Extract ball detections
        ball_detections = self.detector.get_detections_by_class(detections, 'ball')
        ball_positions = [det.get_center() for det in ball_detections]
        
        # Update stumps position if detected
        stumps_detections = self.detector.get_detections_by_class(detections, 'stumps')
        if stumps_detections:
            stumps_center = stumps_detections[0].get_center()
            self.decision_engine.set_stumps_position(stumps_center)
            
            # Estimate ground level from stumps
            stumps_bbox = stumps_detections[0].get_bbox()
            ground_y = stumps_bbox[3]  # Bottom of stumps
            self.decision_engine.set_ground_level(ground_y)
        
        # Track ball
        tracking_start = time.time()
        tracks = self.tracker.update(ball_positions)
        tracking_time = time.time() - tracking_start
        self.performance_monitor.record_tracking_time(tracking_time)
        
        return processed_frame, detections, tracks
    
    def _make_lbw_decision(
        self,
        track: BallTrack,
        detections: List[Detection]
    ) -> Optional[LBWDecisionData]:
        """
        Make LBW decision based on ball track
        
        Args:
            track: Ball track
            detections: Current detections
            
        Returns:
            LBW decision data or None
        """
        # Get ball trajectory
        trajectory = track.get_trajectory()
        
        if len(trajectory) < 10:
            return None
        
        # Predict trajectory
        predicted_trajectory = self.trajectory_predictor.predict_trajectory(
            trajectory,
            num_points=30
        )
        
        # Find impact point (check if ball hit pads)
        pad_detections = self.detector.get_detections_by_class(detections, 'pads')
        impact_point = None
        
        if pad_detections:
            # Use pad position as impact point
            impact_point = pad_detections[0].get_center()
        else:
            # Check if trajectory suggests impact
            # (This is simplified - in real system would use more sophisticated detection)
            if len(trajectory) >= 2:
                # Check if ball direction changed significantly (potential impact)
                recent_velocity = track.get_velocity_vector()
                if recent_velocity:
                    speed = track.get_speed()
                    # If speed dropped significantly, might be impact
                    if speed < 5:  # Threshold
                        impact_point = trajectory[-1]
        
        # Make decision
        decision_data = self.decision_engine.make_decision(
            ball_trajectory=trajectory,
            predicted_trajectory=predicted_trajectory,
            impact_point=impact_point
        )
        
        # Log decision
        if self.config.get('output.log_decisions'):
            log_decision(decision_data.to_dict())
        
        return decision_data
    
    def _save_screenshot(self, frame: np.ndarray) -> None:
        """Save screenshot of current frame"""
        output_path = Path(self.config.get('output.output_path'))
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = output_path / f"screenshot_{timestamp}.png"
        
        cv2.imwrite(str(filename), frame)
        logger.info(f"Screenshot saved: {filename}")
    
    def stop(self) -> None:
        """Stop the LBW decision system"""
        logger.info("Stopping LBW Decision System")
        
        self.running = False
        
        # Stop video capture
        self.video_capture.stop()
        
        # Stop performance monitoring
        self.performance_monitor.stop_monitoring()
        
        # Print statistics
        self.performance_monitor.print_statistics()
        
        # Release video writer
        if self.video_writer:
            self.video_writer.release()
        
        # Close windows
        cv2.destroyAllWindows()
        
        logger.info("LBW Decision System stopped")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
