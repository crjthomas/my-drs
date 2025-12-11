"""
Ball Tracking Module with Kalman Filter
"""

import numpy as np
from typing import List, Optional, Tuple
from collections import deque
from loguru import logger
import cv2


class KalmanFilter:
    """Kalman filter for ball tracking"""
    
    def __init__(self, process_noise: float = 0.01, measurement_noise: float = 0.1):
        """
        Initialize Kalman filter
        
        Args:
            process_noise: Process noise covariance
            measurement_noise: Measurement noise covariance
        """
        # State: [x, y, vx, vy]
        self.kf = cv2.KalmanFilter(4, 2)
        
        # Transition matrix (constant velocity model)
        self.kf.transitionMatrix = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        # Measurement matrix
        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=np.float32)
        
        # Process noise covariance
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * process_noise
        
        # Measurement noise covariance
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * measurement_noise
        
        # Error covariance
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)
    
    def predict(self) -> Tuple[float, float]:
        """
        Predict next state
        
        Returns:
            Predicted (x, y) position
        """
        prediction = self.kf.predict()
        return float(prediction[0]), float(prediction[1])
    
    def update(self, measurement: Tuple[float, float]) -> Tuple[float, float]:
        """
        Update filter with measurement
        
        Args:
            measurement: Measured (x, y) position
            
        Returns:
            Corrected (x, y) position
        """
        measurement_array = np.array([[measurement[0]], [measurement[1]]], dtype=np.float32)
        corrected = self.kf.correct(measurement_array)
        return float(corrected[0]), float(corrected[1])
    
    def get_velocity(self) -> Tuple[float, float]:
        """
        Get current velocity estimate
        
        Returns:
            Velocity (vx, vy)
        """
        state = self.kf.statePost
        return float(state[2]), float(state[3])


class BallTrack:
    """Represents a ball track"""
    
    def __init__(self, track_id: int, initial_position: Tuple[float, float], max_history: int = 100):
        """
        Initialize ball track
        
        Args:
            track_id: Unique track ID
            initial_position: Initial (x, y) position
            max_history: Maximum history length
        """
        self.track_id = track_id
        self.positions = deque(maxlen=max_history)
        self.velocities = deque(maxlen=max_history)
        self.timestamps = deque(maxlen=max_history)
        
        self.kalman = KalmanFilter()
        self.kalman.kf.statePost = np.array([
            [initial_position[0]],
            [initial_position[1]],
            [0],
            [0]
        ], dtype=np.float32)
        
        self.positions.append(initial_position)
        self.last_seen = 0
        self.is_active = True
        
        self.predicted_position: Optional[Tuple[float, float]] = None
    
    def update(self, position: Tuple[float, float], timestamp: int) -> None:
        """
        Update track with new detection
        
        Args:
            position: Detected (x, y) position
            timestamp: Frame timestamp
        """
        # Predict
        self.predicted_position = self.kalman.predict()
        
        # Update
        corrected_position = self.kalman.update(position)
        
        # Store
        self.positions.append(corrected_position)
        self.timestamps.append(timestamp)
        
        # Calculate velocity
        velocity = self.kalman.get_velocity()
        self.velocities.append(velocity)
        
        self.last_seen = timestamp
    
    def predict_next(self) -> Tuple[float, float]:
        """
        Predict next position
        
        Returns:
            Predicted (x, y) position
        """
        return self.kalman.predict()
    
    def get_trajectory(self) -> List[Tuple[float, float]]:
        """
        Get full trajectory
        
        Returns:
            List of positions
        """
        return list(self.positions)
    
    def get_velocity_vector(self) -> Optional[Tuple[float, float]]:
        """
        Get current velocity vector
        
        Returns:
            Velocity (vx, vy) or None
        """
        if len(self.velocities) > 0:
            return self.velocities[-1]
        return None
    
    def get_speed(self) -> float:
        """
        Get current speed magnitude
        
        Returns:
            Speed in pixels per frame
        """
        velocity = self.get_velocity_vector()
        if velocity:
            return np.sqrt(velocity[0]**2 + velocity[1]**2)
        return 0.0
    
    def get_length(self) -> int:
        """Get track length"""
        return len(self.positions)
    
    def is_valid(self, min_length: int = 5) -> bool:
        """
        Check if track is valid
        
        Args:
            min_length: Minimum track length
            
        Returns:
            True if valid
        """
        return len(self.positions) >= min_length


class BallTracker:
    """Tracks cricket ball across frames"""
    
    def __init__(
        self,
        max_frames_to_skip: int = 10,
        min_track_length: int = 5,
        distance_threshold: float = 50.0
    ):
        """
        Initialize ball tracker
        
        Args:
            max_frames_to_skip: Maximum frames to keep track without detection
            min_track_length: Minimum track length to consider valid
            distance_threshold: Maximum distance for track association
        """
        self.max_frames_to_skip = max_frames_to_skip
        self.min_track_length = min_track_length
        self.distance_threshold = distance_threshold
        
        self.tracks: List[BallTrack] = []
        self.next_track_id = 0
        self.current_frame = 0
    
    def update(self, detections: List[Tuple[float, float]]) -> List[BallTrack]:
        """
        Update tracker with new detections
        
        Args:
            detections: List of detected ball positions
            
        Returns:
            List of active tracks
        """
        self.current_frame += 1
        
        # If no active tracks and we have detections, create new tracks
        if len(self.tracks) == 0 and len(detections) > 0:
            for detection in detections:
                self._create_track(detection)
        
        # Match detections to existing tracks
        elif len(detections) > 0:
            self._associate_detections(detections)
        
        # Remove old tracks
        self._cleanup_tracks()
        
        return self.get_active_tracks()
    
    def _create_track(self, position: Tuple[float, float]) -> BallTrack:
        """
        Create new track
        
        Args:
            position: Initial position
            
        Returns:
            Created track
        """
        track = BallTrack(self.next_track_id, position)
        track.last_seen = self.current_frame
        self.tracks.append(track)
        self.next_track_id += 1
        
        logger.debug(f"Created track {track.track_id}")
        return track
    
    def _associate_detections(self, detections: List[Tuple[float, float]]) -> None:
        """
        Associate detections with existing tracks
        
        Args:
            detections: List of detected positions
        """
        # Predict positions for all tracks
        for track in self.tracks:
            if track.is_active:
                track.predict_next()
        
        # Calculate cost matrix (distances)
        cost_matrix = np.zeros((len(self.tracks), len(detections)))
        
        for i, track in enumerate(self.tracks):
            if not track.is_active:
                cost_matrix[i, :] = np.inf
                continue
            
            predicted = track.predicted_position
            if predicted is None:
                predicted = track.positions[-1]
            
            for j, detection in enumerate(detections):
                distance = np.sqrt(
                    (predicted[0] - detection[0])**2 +
                    (predicted[1] - detection[1])**2
                )
                cost_matrix[i, j] = distance
        
        # Hungarian algorithm for assignment (simplified greedy approach)
        assigned_tracks = set()
        assigned_detections = set()
        
        # Sort by distance and assign
        flat_indices = np.argsort(cost_matrix.ravel())
        
        for flat_idx in flat_indices:
            track_idx = flat_idx // len(detections)
            det_idx = flat_idx % len(detections)
            
            if track_idx in assigned_tracks or det_idx in assigned_detections:
                continue
            
            distance = cost_matrix[track_idx, det_idx]
            
            if distance < self.distance_threshold:
                # Assign detection to track
                self.tracks[track_idx].update(detections[det_idx], self.current_frame)
                assigned_tracks.add(track_idx)
                assigned_detections.add(det_idx)
        
        # Create new tracks for unassigned detections
        for det_idx, detection in enumerate(detections):
            if det_idx not in assigned_detections:
                self._create_track(detection)
        
        # Mark unassigned tracks as inactive if too old
        for track_idx, track in enumerate(self.tracks):
            if track_idx not in assigned_tracks:
                frames_since_seen = self.current_frame - track.last_seen
                if frames_since_seen > self.max_frames_to_skip:
                    track.is_active = False
    
    def _cleanup_tracks(self) -> None:
        """Remove inactive and invalid tracks"""
        self.tracks = [
            track for track in self.tracks
            if track.is_active or
            (self.current_frame - track.last_seen <= self.max_frames_to_skip * 2)
        ]
    
    def get_active_tracks(self) -> List[BallTrack]:
        """
        Get all active tracks
        
        Returns:
            List of active tracks
        """
        return [track for track in self.tracks if track.is_active]
    
    def get_valid_tracks(self) -> List[BallTrack]:
        """
        Get valid tracks (meeting minimum length requirement)
        
        Returns:
            List of valid tracks
        """
        return [
            track for track in self.tracks
            if track.is_valid(self.min_track_length)
        ]
    
    def get_best_track(self) -> Optional[BallTrack]:
        """
        Get best track (longest and most recent)
        
        Returns:
            Best track or None
        """
        valid_tracks = self.get_valid_tracks()
        
        if not valid_tracks:
            return None
        
        # Sort by length and recency
        valid_tracks.sort(
            key=lambda t: (t.get_length(), t.last_seen),
            reverse=True
        )
        
        return valid_tracks[0]
    
    def reset(self) -> None:
        """Reset tracker"""
        self.tracks = []
        self.current_frame = 0
        logger.info("Tracker reset")
