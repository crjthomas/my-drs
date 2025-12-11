"""
Video Capture and Preprocessing Module
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from queue import Queue, Full
from threading import Thread, Event
from loguru import logger


class VideoCapture:
    """Handles video capture and preprocessing"""
    
    def __init__(
        self,
        source: int | str = 0,
        width: int = 1920,
        height: int = 1080,
        fps: int = 60,
        buffer_size: int = 30
    ):
        """
        Initialize video capture
        
        Args:
            source: Video source (camera index or file path)
            width: Frame width
            height: Frame height
            fps: Target frames per second
            buffer_size: Size of frame buffer
        """
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps
        self.buffer_size = buffer_size
        
        self.capture: Optional[cv2.VideoCapture] = None
        self.frame_queue = Queue(maxsize=buffer_size)
        self.stop_event = Event()
        self.capture_thread: Optional[Thread] = None
        
        self.frame_count = 0
        self.dropped_frames = 0
        
    def start(self) -> bool:
        """
        Start video capture
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Open video source
            self.capture = cv2.VideoCapture(self.source)
            
            if not self.capture.isOpened():
                logger.error(f"Failed to open video source: {self.source}")
                return False
            
            # Set video properties
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Get actual properties
            actual_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.capture.get(cv2.CAP_PROP_FPS))
            
            logger.info(f"Video capture started: {actual_width}x{actual_height} @ {actual_fps} FPS")
            
            # Start capture thread
            self.stop_event.clear()
            self.capture_thread = Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            return True
        
        except Exception as e:
            logger.error(f"Error starting video capture: {e}")
            return False
    
    def _capture_loop(self) -> None:
        """Internal capture loop running in separate thread"""
        while not self.stop_event.is_set():
            try:
                ret, frame = self.capture.read()
                
                if not ret:
                    logger.warning("Failed to read frame")
                    continue
                
                self.frame_count += 1
                
                # Try to add frame to queue
                try:
                    self.frame_queue.put((self.frame_count, frame), timeout=0.01)
                except Full:
                    # Queue is full, drop frame
                    self.dropped_frames += 1
                    if self.dropped_frames % 100 == 0:
                        logger.warning(f"Dropped {self.dropped_frames} frames")
            
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                break
    
    def read(self) -> Tuple[bool, Optional[np.ndarray], int]:
        """
        Read frame from buffer
        
        Returns:
            Tuple of (success, frame, frame_number)
        """
        try:
            if self.frame_queue.empty():
                return False, None, 0
            
            frame_number, frame = self.frame_queue.get(timeout=0.1)
            return True, frame, frame_number
        
        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return False, None, 0
    
    def stop(self) -> None:
        """Stop video capture"""
        logger.info("Stopping video capture")
        
        # Signal stop
        self.stop_event.set()
        
        # Wait for thread to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        
        # Release capture
        if self.capture:
            self.capture.release()
        
        # Clear queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except:
                break
        
        logger.info(f"Video capture stopped. Processed {self.frame_count} frames, dropped {self.dropped_frames}")
    
    def is_running(self) -> bool:
        """Check if capture is running"""
        return self.capture is not None and self.capture.isOpened() and not self.stop_event.is_set()
    
    def get_fps(self) -> float:
        """Get actual capture FPS"""
        if self.capture:
            return self.capture.get(cv2.CAP_PROP_FPS)
        return 0.0
    
    def get_resolution(self) -> Tuple[int, int]:
        """Get actual frame resolution"""
        if self.capture:
            width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return width, height
        return 0, 0
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


class FramePreprocessor:
    """Handles frame preprocessing and enhancement"""
    
    @staticmethod
    def denoise(frame: np.ndarray) -> np.ndarray:
        """
        Remove noise from frame
        
        Args:
            frame: Input frame
            
        Returns:
            Denoised frame
        """
        return cv2.fastNlMeansDenoisingColored(frame, None, 10, 10, 7, 21)
    
    @staticmethod
    def enhance_contrast(frame: np.ndarray) -> np.ndarray:
        """
        Enhance frame contrast
        
        Args:
            frame: Input frame
            
        Returns:
            Enhanced frame
        """
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    @staticmethod
    def apply_roi(frame: np.ndarray, roi: Tuple[float, float, float, float]) -> np.ndarray:
        """
        Apply region of interest mask
        
        Args:
            frame: Input frame
            roi: ROI as (x_min, y_min, x_max, y_max) in relative coordinates
            
        Returns:
            Masked frame
        """
        h, w = frame.shape[:2]
        x_min = int(roi[0] * w)
        y_min = int(roi[1] * h)
        x_max = int(roi[2] * w)
        y_max = int(roi[3] * h)
        
        mask = np.zeros((h, w), dtype=np.uint8)
        mask[y_min:y_max, x_min:x_max] = 255
        
        return cv2.bitwise_and(frame, frame, mask=mask)
    
    @staticmethod
    def stabilize(frame: np.ndarray, prev_frame: Optional[np.ndarray]) -> np.ndarray:
        """
        Stabilize frame using previous frame
        
        Args:
            frame: Current frame
            prev_frame: Previous frame
            
        Returns:
            Stabilized frame
        """
        if prev_frame is None:
            return frame
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect features
        orb = cv2.ORB_create()
        kp1, des1 = orb.detectAndCompute(gray1, None)
        kp2, des2 = orb.detectAndCompute(gray2, None)
        
        if des1 is None or des2 is None:
            return frame
        
        # Match features
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        
        if len(matches) < 10:
            return frame
        
        # Extract matched points
        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        
        # Find transformation
        matrix, _ = cv2.estimateAffinePartial2D(dst_pts, src_pts)
        
        if matrix is None:
            return frame
        
        # Apply transformation
        h, w = frame.shape[:2]
        stabilized = cv2.warpAffine(frame, matrix, (w, h))
        
        return stabilized
