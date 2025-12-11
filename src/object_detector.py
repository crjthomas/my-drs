"""
Object Detection Module using YOLOv8
"""

import cv2
import numpy as np
import torch
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from loguru import logger


class Detection:
    """Represents a detected object"""
    
    def __init__(
        self,
        bbox: Tuple[int, int, int, int],
        confidence: float,
        class_id: int,
        class_name: str
    ):
        """
        Initialize detection
        
        Args:
            bbox: Bounding box as (x1, y1, x2, y2)
            confidence: Detection confidence
            class_id: Class ID
            class_name: Class name
        """
        self.bbox = bbox
        self.confidence = confidence
        self.class_id = class_id
        self.class_name = class_name
        
        # Calculate center and dimensions
        self.center = (
            (bbox[0] + bbox[2]) // 2,
            (bbox[1] + bbox[3]) // 2
        )
        self.width = bbox[2] - bbox[0]
        self.height = bbox[3] - bbox[1]
        self.area = self.width * self.height
    
    def get_center(self) -> Tuple[int, int]:
        """Get center point of detection"""
        return self.center
    
    def get_bbox(self) -> Tuple[int, int, int, int]:
        """Get bounding box"""
        return self.bbox
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'bbox': self.bbox,
            'center': self.center,
            'confidence': self.confidence,
            'class_id': self.class_id,
            'class_name': self.class_name,
            'width': self.width,
            'height': self.height,
            'area': self.area
        }


class ObjectDetector:
    """Object detector using YOLOv8 or custom models"""
    
    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.5,
        nms_threshold: float = 0.4,
        device: str = 'cuda',
        classes: Optional[Dict[str, int]] = None
    ):
        """
        Initialize object detector
        
        Args:
            model_path: Path to model weights
            confidence_threshold: Minimum confidence for detections
            nms_threshold: Non-maximum suppression threshold
            device: Device to run on ('cuda' or 'cpu')
            classes: Dictionary mapping class names to IDs
        """
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.device = device
        self.classes = classes or {
            'ball': 0,
            'batsman': 1,
            'stumps': 2,
            'pads': 3,
            'bat': 4
        }
        
        self.model = None
        self.class_names = {v: k for k, v in self.classes.items()}
        
        # Load model
        self._load_model()
    
    def _load_model(self) -> None:
        """Load detection model"""
        try:
            # Check if model file exists
            if not self.model_path.exists():
                logger.warning(f"Model file not found: {self.model_path}")
                logger.info("Using fallback detection method")
                self.model = None
                return
            
            # Try to load YOLOv8 model
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(self.model_path))
                
                # Set device
                if self.device == 'cuda' and torch.cuda.is_available():
                    self.model.to('cuda')
                    logger.info("Model loaded on CUDA")
                else:
                    self.model.to('cpu')
                    logger.info("Model loaded on CPU")
                
                logger.info(f"YOLOv8 model loaded from {self.model_path}")
            
            except ImportError:
                logger.warning("ultralytics not available, using fallback detection")
                self.model = None
        
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            logger.info("Using fallback detection method")
            self.model = None
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect objects in frame
        
        Args:
            frame: Input frame
            
        Returns:
            List of detections
        """
        if self.model is not None:
            return self._detect_with_model(frame)
        else:
            return self._detect_fallback(frame)
    
    def _detect_with_model(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect using trained model
        
        Args:
            frame: Input frame
            
        Returns:
            List of detections
        """
        try:
            # Run inference
            results = self.model(frame, conf=self.confidence_threshold, iou=self.nms_threshold, verbose=False)
            
            detections = []
            
            # Process results
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    
                    # Get class name
                    class_name = self.class_names.get(class_id, f"class_{class_id}")
                    
                    # Create detection
                    detection = Detection(
                        bbox=(x1, y1, x2, y2),
                        confidence=confidence,
                        class_id=class_id,
                        class_name=class_name
                    )
                    
                    detections.append(detection)
            
            return detections
        
        except Exception as e:
            logger.error(f"Error in model detection: {e}")
            return []
    
    def _detect_fallback(self, frame: np.ndarray) -> List[Detection]:
        """
        Fallback detection using classical computer vision
        This is a simplified approach for testing without a trained model
        
        Args:
            frame: Input frame
            
        Returns:
            List of detections
        """
        detections = []
        
        # Detect ball using color and shape
        ball_detections = self._detect_ball_fallback(frame)
        detections.extend(ball_detections)
        
        # Detect stumps using edge detection
        stump_detections = self._detect_stumps_fallback(frame)
        detections.extend(stump_detections)
        
        return detections
    
    def _detect_ball_fallback(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect cricket ball using color and circular shape
        
        Args:
            frame: Input frame
            
        Returns:
            List of ball detections
        """
        detections = []
        
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define red color range (cricket ball is typically red or white)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        # Create mask
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        # Morphological operations
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find circles using Hough transform
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9, 9), 2)
        
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=50,
            param2=30,
            minRadius=5,
            maxRadius=30
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            
            for circle in circles[0, :]:
                x, y, r = circle
                
                # Create detection
                detection = Detection(
                    bbox=(x - r, y - r, x + r, y + r),
                    confidence=0.7,
                    class_id=self.classes['ball'],
                    class_name='ball'
                )
                
                detections.append(detection)
        
        return detections
    
    def _detect_stumps_fallback(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect stumps using edge detection and vertical line detection
        
        Args:
            frame: Input frame
            
        Returns:
            List of stump detections
        """
        detections = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=100,
            minLineLength=50,
            maxLineGap=10
        )
        
        if lines is not None:
            # Filter for vertical lines (stumps are vertical)
            vertical_lines = []
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Calculate angle
                angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                
                # Check if line is vertical (angle close to 90 degrees)
                if 80 <= angle <= 100:
                    vertical_lines.append((x1, y1, x2, y2))
            
            # Group nearby vertical lines as stumps
            if len(vertical_lines) >= 3:
                # Use the first 3 vertical lines as stumps
                x_coords = [line[0] for line in vertical_lines[:3]]
                y_coords = [min(line[1], line[3]) for line in vertical_lines[:3]]
                
                x_min = min(x_coords) - 20
                y_min = min(y_coords) - 20
                x_max = max(x_coords) + 20
                y_max = max([max(line[1], line[3]) for line in vertical_lines[:3]]) + 20
                
                detection = Detection(
                    bbox=(x_min, y_min, x_max, y_max),
                    confidence=0.6,
                    class_id=self.classes['stumps'],
                    class_name='stumps'
                )
                
                detections.append(detection)
        
        return detections
    
    def get_detections_by_class(self, detections: List[Detection], class_name: str) -> List[Detection]:
        """
        Filter detections by class name
        
        Args:
            detections: List of all detections
            class_name: Class name to filter
            
        Returns:
            Filtered detections
        """
        return [d for d in detections if d.class_name == class_name]
    
    def draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """
        Draw detections on frame
        
        Args:
            frame: Input frame
            detections: List of detections
            
        Returns:
            Frame with drawn detections
        """
        output = frame.copy()
        
        # Define colors for each class
        colors = {
            'ball': (0, 0, 255),      # Red
            'batsman': (0, 255, 0),   # Green
            'stumps': (255, 0, 0),    # Blue
            'pads': (255, 255, 0),    # Cyan
            'bat': (255, 0, 255)      # Magenta
        }
        
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            color = colors.get(detection.class_name, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{detection.class_name}: {detection.confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            
            cv2.rectangle(
                output,
                (x1, y1 - label_size[1] - 5),
                (x1 + label_size[0], y1),
                color,
                -1
            )
            
            cv2.putText(
                output,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
            
            # Draw center point
            cv2.circle(output, detection.center, 5, color, -1)
        
        return output
