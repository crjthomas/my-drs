"""
Ball Trajectory Prediction Module
"""

import numpy as np
from typing import List, Tuple, Optional
from scipy.optimize import curve_fit
from loguru import logger


class TrajectoryPredictor:
    """Predicts ball trajectory using physics-based models"""
    
    def __init__(
        self,
        gravity: float = 9.81,
        air_resistance: float = 0.47,
        ball_mass: float = 0.16,
        ball_radius: float = 0.036,
        pixel_to_meter: float = 0.01
    ):
        """
        Initialize trajectory predictor
        
        Args:
            gravity: Gravitational acceleration (m/s^2)
            air_resistance: Drag coefficient
            ball_mass: Ball mass (kg)
            ball_radius: Ball radius (meters)
            pixel_to_meter: Pixel to meter conversion ratio
        """
        self.gravity = gravity
        self.air_resistance = air_resistance
        self.ball_mass = ball_mass
        self.ball_radius = ball_radius
        self.pixel_to_meter = pixel_to_meter
        
        # Air density (kg/m^3) at sea level
        self.air_density = 1.225
        
        # Calculate drag coefficient constant
        self.drag_constant = (
            0.5 * self.air_density * self.air_resistance *
            np.pi * self.ball_radius**2 / self.ball_mass
        )
    
    def predict_trajectory(
        self,
        positions: List[Tuple[float, float]],
        timestamps: Optional[List[int]] = None,
        num_points: int = 30
    ) -> List[Tuple[float, float]]:
        """
        Predict future trajectory
        
        Args:
            positions: List of (x, y) positions
            timestamps: List of frame timestamps
            num_points: Number of points to predict
            
        Returns:
            List of predicted (x, y) positions
        """
        if len(positions) < 3:
            logger.warning("Insufficient points for trajectory prediction")
            return []
        
        # Convert to numpy arrays
        positions_array = np.array(positions)
        x_positions = positions_array[:, 0]
        y_positions = positions_array[:, 1]
        
        # Use timestamps or create uniform spacing
        if timestamps is None:
            t = np.arange(len(positions))
        else:
            t = np.array(timestamps)
        
        try:
            # Fit polynomial to trajectory
            x_poly = self._fit_polynomial(t, x_positions, degree=2)
            y_poly = self._fit_polynomial(t, y_positions, degree=2)
            
            # Predict future points
            future_t = np.linspace(t[-1], t[-1] + num_points, num_points)
            predicted_x = np.polyval(x_poly, future_t)
            predicted_y = np.polyval(y_poly, future_t)
            
            # Combine predictions
            predicted_positions = list(zip(predicted_x, predicted_y))
            
            return predicted_positions
        
        except Exception as e:
            logger.error(f"Error predicting trajectory: {e}")
            return []
    
    def predict_with_physics(
        self,
        positions: List[Tuple[float, float]],
        fps: float = 60.0,
        num_points: int = 30
    ) -> List[Tuple[float, float]]:
        """
        Predict trajectory using physics-based model with air resistance
        
        Args:
            positions: List of (x, y) positions in pixels
            fps: Frames per second
            num_points: Number of points to predict
            
        Returns:
            List of predicted (x, y) positions
        """
        if len(positions) < 3:
            return []
        
        try:
            # Estimate initial velocity
            dt = 1.0 / fps
            
            # Use recent positions to estimate velocity
            recent_positions = positions[-5:] if len(positions) >= 5 else positions
            
            # Calculate average velocity
            vx = (recent_positions[-1][0] - recent_positions[0][0]) / (len(recent_positions) * dt)
            vy = (recent_positions[-1][1] - recent_positions[0][1]) / (len(recent_positions) * dt)
            
            # Convert to meters
            x0 = recent_positions[-1][0] * self.pixel_to_meter
            y0 = recent_positions[-1][1] * self.pixel_to_meter
            vx = vx * self.pixel_to_meter
            vy = vy * self.pixel_to_meter
            
            # Simulate trajectory with physics
            predicted = []
            x, y = x0, y0
            
            for _ in range(num_points):
                # Calculate drag force
                v = np.sqrt(vx**2 + vy**2)
                
                if v > 0:
                    drag_x = -self.drag_constant * v * vx
                    drag_y = -self.drag_constant * v * vy
                else:
                    drag_x = drag_y = 0
                
                # Update velocities
                vx += drag_x * dt
                vy += (drag_y - self.gravity) * dt
                
                # Update positions
                x += vx * dt
                y += vy * dt
                
                # Convert back to pixels
                predicted.append((x / self.pixel_to_meter, y / self.pixel_to_meter))
            
            return predicted
        
        except Exception as e:
            logger.error(f"Error in physics-based prediction: {e}")
            return []
    
    def _fit_polynomial(self, x: np.ndarray, y: np.ndarray, degree: int = 2) -> np.ndarray:
        """
        Fit polynomial to data
        
        Args:
            x: X coordinates
            y: Y coordinates
            degree: Polynomial degree
            
        Returns:
            Polynomial coefficients
        """
        return np.polyfit(x, y, degree)
    
    def estimate_landing_point(
        self,
        positions: List[Tuple[float, float]],
        ground_y: float
    ) -> Optional[Tuple[float, float]]:
        """
        Estimate where ball will land on ground
        
        Args:
            positions: List of (x, y) positions
            ground_y: Y coordinate of ground
            
        Returns:
            Estimated landing point (x, y) or None
        """
        if len(positions) < 3:
            return None
        
        try:
            # Predict trajectory
            predicted = self.predict_trajectory(positions, num_points=50)
            
            if not predicted:
                return None
            
            # Find first point below ground level
            for i, (x, y) in enumerate(predicted):
                if y >= ground_y:
                    if i > 0:
                        # Interpolate between previous and current point
                        x1, y1 = predicted[i-1]
                        x2, y2 = x, y
                        
                        # Linear interpolation
                        t = (ground_y - y1) / (y2 - y1) if y2 != y1 else 0
                        landing_x = x1 + t * (x2 - x1)
                        
                        return (landing_x, ground_y)
                    else:
                        return (x, ground_y)
            
            # If no intersection found, extrapolate
            if len(predicted) >= 2:
                x1, y1 = predicted[-2]
                x2, y2 = predicted[-1]
                
                if y2 != y1:
                    t = (ground_y - y1) / (y2 - y1)
                    landing_x = x1 + t * (x2 - x1)
                    return (landing_x, ground_y)
            
            return None
        
        except Exception as e:
            logger.error(f"Error estimating landing point: {e}")
            return None
    
    def calculate_pitch_point(
        self,
        positions: List[Tuple[float, float]],
        ground_y: float
    ) -> Optional[Tuple[float, float]]:
        """
        Calculate where ball pitched (first bounce)
        
        Args:
            positions: List of (x, y) positions
            ground_y: Y coordinate of ground
            
        Returns:
            Pitch point (x, y) or None
        """
        # Find first position at or below ground level
        for i, (x, y) in enumerate(positions):
            if y >= ground_y:
                return (x, ground_y)
        
        # If not found, estimate
        return self.estimate_landing_point(positions, ground_y)
    
    def estimate_impact_point_on_line(
        self,
        trajectory: List[Tuple[float, float]],
        line_x: float
    ) -> Optional[Tuple[float, float]]:
        """
        Estimate where trajectory crosses a vertical line (e.g., stumps)
        
        Args:
            trajectory: Predicted trajectory points
            line_x: X coordinate of vertical line
            
        Returns:
            Impact point (x, y) or None
        """
        if not trajectory or len(trajectory) < 2:
            return None
        
        # Find crossing point
        for i in range(len(trajectory) - 1):
            x1, y1 = trajectory[i]
            x2, y2 = trajectory[i + 1]
            
            # Check if line crosses between these two points
            if (x1 <= line_x <= x2) or (x2 <= line_x <= x1):
                # Linear interpolation
                if x2 != x1:
                    t = (line_x - x1) / (x2 - x1)
                    y = y1 + t * (y2 - y1)
                    return (line_x, y)
        
        return None
    
    def calculate_trajectory_metrics(
        self,
        positions: List[Tuple[float, float]]
    ) -> dict:
        """
        Calculate various trajectory metrics
        
        Args:
            positions: List of (x, y) positions
            
        Returns:
            Dictionary of metrics
        """
        if len(positions) < 2:
            return {}
        
        positions_array = np.array(positions)
        
        # Calculate distances
        distances = np.sqrt(np.sum(np.diff(positions_array, axis=0)**2, axis=1))
        total_distance = np.sum(distances)
        
        # Calculate direction
        start = positions_array[0]
        end = positions_array[-1]
        direction = np.arctan2(end[1] - start[1], end[0] - start[0])
        
        # Calculate curvature (rate of direction change)
        if len(positions) >= 3:
            angles = []
            for i in range(len(positions) - 2):
                v1 = positions_array[i+1] - positions_array[i]
                v2 = positions_array[i+2] - positions_array[i+1]
                
                angle = np.arctan2(v2[1], v2[0]) - np.arctan2(v1[1], v1[0])
                angles.append(angle)
            
            avg_curvature = np.mean(np.abs(angles)) if angles else 0
        else:
            avg_curvature = 0
        
        return {
            'total_distance': total_distance,
            'direction_angle': np.degrees(direction),
            'average_curvature': avg_curvature,
            'num_points': len(positions),
            'start_point': tuple(start),
            'end_point': tuple(end)
        }
