"""
LBW Decision Logic Module
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from enum import Enum
from loguru import logger
from dataclasses import dataclass


class Decision(Enum):
    """LBW Decision outcomes"""
    OUT = "OUT"
    NOT_OUT = "NOT OUT"
    UMPIRES_CALL = "UMPIRE'S CALL"
    INSUFFICIENT_DATA = "INSUFFICIENT DATA"


class ImpactZone(Enum):
    """Impact zone classification"""
    IN_LINE = "IN LINE"
    OUTSIDE_OFF = "OUTSIDE OFF"
    OUTSIDE_LEG = "OUTSIDE LEG"
    NO_IMPACT = "NO IMPACT"


class PitchingZone(Enum):
    """Pitching zone classification"""
    IN_LINE = "IN LINE"
    OUTSIDE_OFF = "OUTSIDE OFF"
    OUTSIDE_LEG = "OUTSIDE LEG"
    NO_PITCH = "NO PITCH"


@dataclass
class LBWDecisionData:
    """Data structure for LBW decision"""
    decision: Decision
    confidence: float
    
    # Impact details
    impact_zone: ImpactZone
    impact_point: Optional[Tuple[float, float]]
    impact_distance_from_stumps: float
    
    # Pitching details
    pitching_zone: PitchingZone
    pitching_point: Optional[Tuple[float, float]]
    pitching_distance_from_stumps: float
    
    # Trajectory details
    hits_stumps: bool
    stumps_impact_height: Optional[float]
    stumps_impact_distance: float
    
    # Additional info
    ball_trajectory: List[Tuple[float, float]]
    predicted_trajectory: List[Tuple[float, float]]
    
    # Rule checks
    pitched_outside_leg: bool
    impact_in_line: bool
    hitting_wickets: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'decision': self.decision.value,
            'confidence': self.confidence,
            'impact_zone': self.impact_zone.value,
            'impact_point': self.impact_point,
            'pitching_zone': self.pitching_zone.value,
            'pitching_point': self.pitching_point,
            'hits_stumps': self.hits_stumps,
            'stumps_impact_height': self.stumps_impact_height,
            'pitched_outside_leg': self.pitched_outside_leg,
            'impact_in_line': self.impact_in_line,
            'hitting_wickets': self.hitting_wickets
        }


class LBWDecisionEngine:
    """Engine for making LBW decisions"""
    
    def __init__(
        self,
        pitch_length: float = 20.12,
        stump_height: float = 0.71,
        stump_width: float = 0.23,
        impact_threshold: float = 0.05,
        line_threshold: float = 0.1,
        pitching_threshold: float = 0.05,
        wicket_margin: float = 0.02,
        umpires_call_impact: float = 0.15,
        umpires_call_wicket: float = 0.15,
        umpires_call_pitching: float = 0.10,
        min_confidence: float = 0.7,
        pixel_to_meter: float = 0.01
    ):
        """
        Initialize LBW decision engine
        
        Args:
            pitch_length: Length of cricket pitch (meters)
            stump_height: Height of stumps (meters)
            stump_width: Width of stumps (meters)
            impact_threshold: Threshold for impact detection (meters)
            line_threshold: Threshold for in-line detection (meters)
            pitching_threshold: Threshold for pitching detection (meters)
            wicket_margin: Margin for hitting wickets (meters)
            umpires_call_impact: Umpire's call margin for impact (meters)
            umpires_call_wicket: Umpire's call margin for wicket (meters)
            umpires_call_pitching: Umpire's call margin for pitching (meters)
            min_confidence: Minimum confidence for decision
            pixel_to_meter: Pixel to meter conversion ratio
        """
        self.pitch_length = pitch_length
        self.stump_height = stump_height
        self.stump_width = stump_width
        self.impact_threshold = impact_threshold
        self.line_threshold = line_threshold
        self.pitching_threshold = pitching_threshold
        self.wicket_margin = wicket_margin
        self.umpires_call_impact = umpires_call_impact
        self.umpires_call_wicket = umpires_call_wicket
        self.umpires_call_pitching = umpires_call_pitching
        self.min_confidence = min_confidence
        self.pixel_to_meter = pixel_to_meter
        
        # Reference points (to be calibrated)
        self.stumps_position: Optional[Tuple[float, float]] = None
        self.stumps_x: Optional[float] = None
        self.ground_y: Optional[float] = None
    
    def set_stumps_position(self, position: Tuple[float, float]) -> None:
        """
        Set stumps position from detection
        
        Args:
            position: (x, y) position of stumps center
        """
        self.stumps_position = position
        self.stumps_x = position[0]
        logger.info(f"Stumps position set to {position}")
    
    def set_ground_level(self, y: float) -> None:
        """
        Set ground level Y coordinate
        
        Args:
            y: Y coordinate of ground
        """
        self.ground_y = y
        logger.info(f"Ground level set to {y}")
    
    def make_decision(
        self,
        ball_trajectory: List[Tuple[float, float]],
        predicted_trajectory: List[Tuple[float, float]],
        impact_point: Optional[Tuple[float, float]],
        pad_position: Optional[Tuple[float, float]] = None
    ) -> LBWDecisionData:
        """
        Make LBW decision based on ball trajectory and impact
        
        Args:
            ball_trajectory: Observed ball trajectory
            predicted_trajectory: Predicted trajectory to stumps
            impact_point: Point where ball hit pad
            pad_position: Position of pad
            
        Returns:
            LBW decision data
        """
        if not self._is_calibrated():
            logger.warning("System not calibrated, decision may be inaccurate")
        
        # Initialize decision data
        decision_data = LBWDecisionData(
            decision=Decision.INSUFFICIENT_DATA,
            confidence=0.0,
            impact_zone=ImpactZone.NO_IMPACT,
            impact_point=impact_point,
            impact_distance_from_stumps=0.0,
            pitching_zone=PitchingZone.NO_PITCH,
            pitching_point=None,
            pitching_distance_from_stumps=0.0,
            hits_stumps=False,
            stumps_impact_height=None,
            stumps_impact_distance=0.0,
            ball_trajectory=ball_trajectory,
            predicted_trajectory=predicted_trajectory,
            pitched_outside_leg=False,
            impact_in_line=False,
            hitting_wickets=False
        )
        
        # Check minimum requirements
        if len(ball_trajectory) < 5:
            logger.warning("Insufficient trajectory data for decision")
            return decision_data
        
        # Analyze pitching point
        pitching_point = self._find_pitching_point(ball_trajectory)
        pitching_zone = self._classify_pitching_zone(pitching_point)
        decision_data.pitching_point = pitching_point
        decision_data.pitching_zone = pitching_zone
        
        if pitching_point and self.stumps_position:
            decision_data.pitching_distance_from_stumps = self._calculate_distance(
                pitching_point, self.stumps_position
            )
        
        # Check if pitched outside leg - immediate NOT OUT
        if pitching_zone == PitchingZone.OUTSIDE_LEG:
            decision_data.pitched_outside_leg = True
            decision_data.decision = Decision.NOT_OUT
            decision_data.confidence = 0.95
            logger.info("Decision: NOT OUT - Pitched outside leg stump")
            return decision_data
        
        # Analyze impact point
        if impact_point:
            impact_zone = self._classify_impact_zone(impact_point)
            decision_data.impact_zone = impact_zone
            
            if self.stumps_position:
                decision_data.impact_distance_from_stumps = self._calculate_distance(
                    impact_point, self.stumps_position
                )
            
            # Check if impact is in line
            decision_data.impact_in_line = self._is_in_line(
                impact_point,
                self.line_threshold
            )
        else:
            # No impact detected
            decision_data.decision = Decision.NOT_OUT
            decision_data.confidence = 0.9
            logger.info("Decision: NOT OUT - No impact detected")
            return decision_data
        
        # Check if ball would hit stumps
        stumps_impact = self._check_stumps_impact(predicted_trajectory)
        decision_data.hits_stumps = stumps_impact['hits']
        decision_data.stumps_impact_height = stumps_impact.get('height')
        decision_data.stumps_impact_distance = stumps_impact.get('distance', 0)
        decision_data.hitting_wickets = stumps_impact['hits']
        
        # Make final decision based on LBW rules
        decision_data.decision, decision_data.confidence = self._apply_lbw_rules(
            decision_data
        )
        
        logger.info(f"Decision: {decision_data.decision.value} (confidence: {decision_data.confidence:.2f})")
        
        return decision_data
    
    def _is_calibrated(self) -> bool:
        """Check if system is calibrated"""
        return self.stumps_position is not None and self.ground_y is not None
    
    def _find_pitching_point(
        self,
        trajectory: List[Tuple[float, float]]
    ) -> Optional[Tuple[float, float]]:
        """
        Find where ball pitched (bounced)
        
        Args:
            trajectory: Ball trajectory
            
        Returns:
            Pitching point or None
        """
        if not trajectory or self.ground_y is None:
            return None
        
        # Find first point at or below ground level
        for i, (x, y) in enumerate(trajectory):
            if y >= self.ground_y - 10:  # Small tolerance
                return (x, self.ground_y)
        
        return None
    
    def _classify_pitching_zone(self, point: Optional[Tuple[float, float]]) -> PitchingZone:
        """
        Classify where ball pitched
        
        Args:
            point: Pitching point
            
        Returns:
            Pitching zone
        """
        if point is None or self.stumps_x is None:
            return PitchingZone.NO_PITCH
        
        x_diff = point[0] - self.stumps_x
        x_diff_meters = abs(x_diff) * self.pixel_to_meter
        
        stump_half_width = self.stump_width / 2
        
        # Outside leg (left side if stumps on right)
        if x_diff < -stump_half_width - self.line_threshold:
            return PitchingZone.OUTSIDE_LEG
        
        # Outside off (right side if stumps on right)
        elif x_diff > stump_half_width + self.line_threshold:
            return PitchingZone.OUTSIDE_OFF
        
        # In line
        else:
            return PitchingZone.IN_LINE
    
    def _classify_impact_zone(self, point: Tuple[float, float]) -> ImpactZone:
        """
        Classify where ball impacted
        
        Args:
            point: Impact point
            
        Returns:
            Impact zone
        """
        if self.stumps_x is None:
            return ImpactZone.NO_IMPACT
        
        x_diff = point[0] - self.stumps_x
        x_diff_meters = abs(x_diff) * self.pixel_to_meter
        
        stump_half_width = self.stump_width / 2
        
        # Outside leg
        if x_diff < -stump_half_width - self.line_threshold:
            return ImpactZone.OUTSIDE_LEG
        
        # Outside off
        elif x_diff > stump_half_width + self.line_threshold:
            return ImpactZone.OUTSIDE_OFF
        
        # In line
        else:
            return ImpactZone.IN_LINE
    
    def _is_in_line(self, point: Tuple[float, float], threshold: float) -> bool:
        """
        Check if point is in line with stumps
        
        Args:
            point: Point to check
            threshold: Threshold in meters
            
        Returns:
            True if in line
        """
        if self.stumps_x is None:
            return False
        
        x_diff_meters = abs(point[0] - self.stumps_x) * self.pixel_to_meter
        return x_diff_meters <= threshold + self.stump_width / 2
    
    def _check_stumps_impact(
        self,
        trajectory: List[Tuple[float, float]]
    ) -> Dict:
        """
        Check if trajectory would hit stumps
        
        Args:
            trajectory: Predicted trajectory
            
        Returns:
            Dictionary with impact information
        """
        result = {
            'hits': False,
            'height': None,
            'distance': float('inf')
        }
        
        if not trajectory or self.stumps_x is None or self.ground_y is None:
            return result
        
        # Find closest approach to stumps
        min_distance = float('inf')
        closest_point = None
        
        for point in trajectory:
            x, y = point
            
            # Check if point is at stumps X coordinate
            x_dist = abs(x - self.stumps_x)
            
            if x_dist < min_distance:
                min_distance = x_dist
                closest_point = point
        
        if closest_point is None:
            return result
        
        x, y = closest_point
        x_dist_meters = abs(x - self.stumps_x) * self.pixel_to_meter
        
        # Check if within stump width
        if x_dist_meters <= self.stump_width / 2 + self.wicket_margin:
            # Check height
            height_from_ground = abs(y - self.ground_y) * self.pixel_to_meter
            
            # Check if height is within stumps
            if height_from_ground <= self.stump_height + self.wicket_margin:
                result['hits'] = True
                result['height'] = height_from_ground
                result['distance'] = x_dist_meters
        
        return result
    
    def _calculate_distance(
        self,
        point1: Tuple[float, float],
        point2: Tuple[float, float]
    ) -> float:
        """
        Calculate Euclidean distance between two points
        
        Args:
            point1: First point
            point2: Second point
            
        Returns:
            Distance in meters
        """
        dx = (point1[0] - point2[0]) * self.pixel_to_meter
        dy = (point1[1] - point2[1]) * self.pixel_to_meter
        return np.sqrt(dx**2 + dy**2)
    
    def _apply_lbw_rules(self, data: LBWDecisionData) -> Tuple[Decision, float]:
        """
        Apply LBW rules to make final decision
        
        Args:
            data: Decision data
            
        Returns:
            Tuple of (Decision, confidence)
        """
        # Rule 1: Pitched outside leg - NOT OUT (already checked)
        if data.pitched_outside_leg:
            return Decision.NOT_OUT, 0.95
        
        # Rule 2: Impact outside off stump and not playing shot - NOT OUT (simplified)
        # In real system, would need to detect if batsman is playing shot
        if data.impact_zone == ImpactZone.OUTSIDE_OFF:
            return Decision.NOT_OUT, 0.85
        
        # Rule 3: Impact not in line - NOT OUT
        if not data.impact_in_line:
            return Decision.NOT_OUT, 0.90
        
        # Rule 4: Not hitting stumps - NOT OUT
        if not data.hitting_wickets:
            return Decision.NOT_OUT, 0.85
        
        # If all conditions satisfied, check for umpire's call
        impact_distance = data.impact_distance_from_stumps
        stumps_distance = data.stumps_impact_distance
        
        # Check umpire's call margins
        umpires_call_factors = []
        
        # Impact margin
        if impact_distance > self.line_threshold:
            if impact_distance <= self.umpires_call_impact:
                umpires_call_factors.append('impact')
        
        # Wicket hitting margin
        if stumps_distance > self.wicket_margin:
            if stumps_distance <= self.umpires_call_wicket:
                umpires_call_factors.append('wicket')
        
        # If in umpire's call zone
        if umpires_call_factors:
            return Decision.UMPIRES_CALL, 0.75
        
        # Clear OUT
        return Decision.OUT, 0.90
