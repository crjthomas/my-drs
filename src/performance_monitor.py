"""
Performance Monitoring Module
"""

import time
import psutil
import threading
from collections import deque
from typing import Dict, Optional
from loguru import logger


class PerformanceMonitor:
    """Monitors system performance and processing metrics"""
    
    def __init__(self, history_size: int = 100):
        """
        Initialize performance monitor
        
        Args:
            history_size: Number of measurements to keep in history
        """
        self.history_size = history_size
        
        # Timing metrics
        self.frame_times = deque(maxlen=history_size)
        self.processing_times = deque(maxlen=history_size)
        self.detection_times = deque(maxlen=history_size)
        self.tracking_times = deque(maxlen=history_size)
        
        # Counter metrics
        self.frames_processed = 0
        self.frames_dropped = 0
        self.detections_made = 0
        self.decisions_made = 0
        
        # Resource metrics
        self.cpu_usage = deque(maxlen=history_size)
        self.memory_usage = deque(maxlen=history_size)
        
        # Timing
        self.start_time = time.time()
        self.last_frame_time = time.time()
        
        # Monitoring thread
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
    
    def start_monitoring(self) -> None:
        """Start resource monitoring thread"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
            self.monitor_thread.start()
            logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop resource monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("Performance monitoring stopped")
    
    def _monitor_resources(self) -> None:
        """Monitor system resources in background thread"""
        while self.monitoring:
            try:
                # Get CPU usage
                cpu = psutil.cpu_percent(interval=0.1)
                self.cpu_usage.append(cpu)
                
                # Get memory usage
                memory = psutil.virtual_memory().percent
                self.memory_usage.append(memory)
                
                time.sleep(1.0)
            
            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")
                break
    
    def record_frame(self) -> None:
        """Record frame processing start"""
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        self.frame_times.append(frame_time)
        self.last_frame_time = current_time
        self.frames_processed += 1
    
    def record_processing_time(self, duration: float) -> None:
        """Record total processing time for frame"""
        self.processing_times.append(duration)
    
    def record_detection_time(self, duration: float) -> None:
        """Record detection time"""
        self.detection_times.append(duration)
    
    def record_tracking_time(self, duration: float) -> None:
        """Record tracking time"""
        self.tracking_times.append(duration)
    
    def record_detection(self, count: int = 1) -> None:
        """Record detections made"""
        self.detections_made += count
    
    def record_decision(self) -> None:
        """Record LBW decision made"""
        self.decisions_made += 1
    
    def record_dropped_frame(self) -> None:
        """Record dropped frame"""
        self.frames_dropped += 1
    
    def get_fps(self) -> float:
        """
        Get current FPS
        
        Returns:
            Frames per second
        """
        if len(self.frame_times) < 2:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
    
    def get_average_processing_time(self) -> float:
        """
        Get average processing time
        
        Returns:
            Average processing time in seconds
        """
        if not self.processing_times:
            return 0.0
        
        return sum(self.processing_times) / len(self.processing_times)
    
    def get_average_detection_time(self) -> float:
        """Get average detection time"""
        if not self.detection_times:
            return 0.0
        return sum(self.detection_times) / len(self.detection_times)
    
    def get_average_tracking_time(self) -> float:
        """Get average tracking time"""
        if not self.tracking_times:
            return 0.0
        return sum(self.tracking_times) / len(self.tracking_times)
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        if not self.cpu_usage:
            return 0.0
        return self.cpu_usage[-1]
    
    def get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        if not self.memory_usage:
            return 0.0
        return self.memory_usage[-1]
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self.start_time
    
    def get_statistics(self) -> Dict:
        """
        Get comprehensive statistics
        
        Returns:
            Dictionary of statistics
        """
        uptime = self.get_uptime()
        
        return {
            'uptime_seconds': uptime,
            'fps': self.get_fps(),
            'frames_processed': self.frames_processed,
            'frames_dropped': self.frames_dropped,
            'drop_rate': self.frames_dropped / max(self.frames_processed, 1),
            'detections_made': self.detections_made,
            'decisions_made': self.decisions_made,
            'avg_processing_time_ms': self.get_average_processing_time() * 1000,
            'avg_detection_time_ms': self.get_average_detection_time() * 1000,
            'avg_tracking_time_ms': self.get_average_tracking_time() * 1000,
            'cpu_usage_percent': self.get_cpu_usage(),
            'memory_usage_percent': self.get_memory_usage()
        }
    
    def print_statistics(self) -> None:
        """Print statistics to console"""
        stats = self.get_statistics()
        
        logger.info("=" * 60)
        logger.info("PERFORMANCE STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Uptime: {stats['uptime_seconds']:.1f} seconds")
        logger.info(f"FPS: {stats['fps']:.1f}")
        logger.info(f"Frames Processed: {stats['frames_processed']}")
        logger.info(f"Frames Dropped: {stats['frames_dropped']} ({stats['drop_rate']:.1%})")
        logger.info(f"Detections Made: {stats['detections_made']}")
        logger.info(f"Decisions Made: {stats['decisions_made']}")
        logger.info(f"Avg Processing Time: {stats['avg_processing_time_ms']:.2f} ms")
        logger.info(f"Avg Detection Time: {stats['avg_detection_time_ms']:.2f} ms")
        logger.info(f"Avg Tracking Time: {stats['avg_tracking_time_ms']:.2f} ms")
        logger.info(f"CPU Usage: {stats['cpu_usage_percent']:.1f}%")
        logger.info(f"Memory Usage: {stats['memory_usage_percent']:.1f}%")
        logger.info("=" * 60)
    
    def reset(self) -> None:
        """Reset all metrics"""
        self.frame_times.clear()
        self.processing_times.clear()
        self.detection_times.clear()
        self.tracking_times.clear()
        
        self.frames_processed = 0
        self.frames_dropped = 0
        self.detections_made = 0
        self.decisions_made = 0
        
        self.start_time = time.time()
        self.last_frame_time = time.time()
        
        logger.info("Performance metrics reset")
