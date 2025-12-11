#!/usr/bin/env python3
"""
Benchmark and Validation Script
Compares system performance against research benchmarks
"""

import sys
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
from src.config_manager import ConfigManager
from src.object_detector import ObjectDetector
from src.ball_tracker import BallTracker
from src.trajectory_predictor import TrajectoryPredictor


class SystemBenchmark:
    """Benchmarks system against research standards"""
    
    def __init__(self):
        self.results = {}
    
    def benchmark_detection_speed(self, num_frames=100):
        """Benchmark detection speed"""
        print("Benchmarking detection speed...")
        
        detector = ObjectDetector(
            model_path='models/cricket_detector.pt',
            confidence_threshold=0.5
        )
        
        # Create test frames
        frames = [np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8) 
                  for _ in range(num_frames)]
        
        # Warm-up
        for i in range(5):
            detector.detect(frames[0])
        
        # Benchmark
        start = time.time()
        for frame in frames:
            detections = detector.detect(frame)
        end = time.time()
        
        total_time = end - start
        avg_time = total_time / num_frames
        fps = 1.0 / avg_time
        
        self.results['detection'] = {
            'total_time': total_time,
            'avg_time_ms': avg_time * 1000,
            'fps': fps
        }
        
        print(f"  Detection FPS: {fps:.1f}")
        print(f"  Avg time per frame: {avg_time*1000:.2f}ms")
        
        # Compare with research
        research_range = (20, 50)  # ms from research papers
        if research_range[0] <= avg_time*1000 <= research_range[1]:
            print(f"  ✓ Within research range {research_range}ms")
        else:
            print(f"  ⚠ Outside research range {research_range}ms")
    
    def benchmark_tracking_accuracy(self, num_tracks=50):
        """Benchmark tracking accuracy with synthetic data"""
        print("\nBenchmarking tracking accuracy...")
        
        tracker = BallTracker(
            max_frames_to_skip=10,
            min_track_length=5,
            distance_threshold=50
        )
        
        # Generate synthetic trajectory (parabolic)
        ground_truth = []
        for t in range(num_tracks):
            x = 100 + t * 10
            y = 200 + t * 5 - 0.1 * t * t  # Parabola
            ground_truth.append((x, y))
        
        # Add noise to simulate detections
        noisy_detections = []
        for x, y in ground_truth:
            noise_x = np.random.normal(0, 3)
            noise_y = np.random.normal(0, 3)
            noisy_detections.append((x + noise_x, y + noise_y))
        
        # Track
        tracked_positions = []
        for detection in noisy_detections:
            tracks = tracker.update([detection])
            if tracks:
                pos = tracks[0].positions[-1]
                tracked_positions.append(pos)
        
        # Calculate RMSE
        if len(tracked_positions) == len(ground_truth):
            errors = []
            for (xt, yt), (xg, yg) in zip(tracked_positions, ground_truth):
                error = np.sqrt((xt - xg)**2 + (yt - yg)**2)
                errors.append(error)
            
            rmse = np.sqrt(np.mean(np.array(errors)**2))
            
            self.results['tracking'] = {
                'rmse': rmse,
                'mean_error': np.mean(errors),
                'max_error': np.max(errors)
            }
            
            print(f"  RMSE: {rmse:.2f} pixels")
            print(f"  Mean error: {np.mean(errors):.2f} pixels")
            
            # Compare with research
            research_target = 15  # pixels from research
            if rmse <= research_target:
                print(f"  ✓ Better than research target ({research_target}px)")
            else:
                print(f"  ⚠ Above research target ({research_target}px)")
    
    def benchmark_trajectory_prediction(self):
        """Benchmark trajectory prediction accuracy"""
        print("\nBenchmarking trajectory prediction...")
        
        predictor = TrajectoryPredictor()
        
        # Generate ground truth trajectory
        t = np.linspace(0, 2, 50)  # 2 seconds
        x = 100 + 200 * t
        y = 300 + 100 * t - 4.905 * t**2  # Projectile motion
        
        ground_truth = list(zip(x, y))
        
        # Use first 30 points to predict next 20
        known_trajectory = ground_truth[:30]
        future_ground_truth = ground_truth[30:]
        
        # Predict
        predicted = predictor.predict_trajectory(
            known_trajectory,
            num_points=len(future_ground_truth)
        )
        
        # Calculate error
        if len(predicted) == len(future_ground_truth):
            errors = []
            for (xp, yp), (xg, yg) in zip(predicted, future_ground_truth):
                error = np.sqrt((xp - xg)**2 + (yp - yg)**2)
                errors.append(error)
            
            rmse = np.sqrt(np.mean(np.array(errors)**2))
            
            self.results['prediction'] = {
                'rmse': rmse,
                'mean_error': np.mean(errors),
                'max_error': np.max(errors)
            }
            
            print(f"  RMSE: {rmse:.2f} pixels")
            print(f"  Mean error: {np.mean(errors):.2f} pixels")
            
            # Compare with research
            research_range = (10, 20)  # pixels from research
            if rmse <= research_range[1]:
                print(f"  ✓ Within research target (≤{research_range[1]}px)")
            else:
                print(f"  ⚠ Above research target (≤{research_range[1]}px)")
    
    def benchmark_end_to_end_latency(self, num_iterations=100):
        """Benchmark end-to-end latency"""
        print("\nBenchmarking end-to-end latency...")
        
        # Setup components
        detector = ObjectDetector(
            model_path='models/cricket_detector.pt',
            confidence_threshold=0.5
        )
        tracker = BallTracker()
        predictor = TrajectoryPredictor()
        
        # Test frame
        frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        
        latencies = []
        
        for _ in range(num_iterations):
            start = time.time()
            
            # Full pipeline
            detections = detector.detect(frame)
            ball_positions = [d.get_center() for d in detections]
            tracks = tracker.update(ball_positions)
            
            if tracks and len(tracks[0].positions) >= 5:
                trajectory = tracks[0].get_trajectory()
                predicted = predictor.predict_trajectory(trajectory, num_points=10)
            
            end = time.time()
            
            latencies.append((end - start) * 1000)  # Convert to ms
        
        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        
        self.results['latency'] = {
            'avg_ms': avg_latency,
            'p95_ms': p95_latency,
            'min_ms': np.min(latencies),
            'max_ms': np.max(latencies)
        }
        
        print(f"  Average latency: {avg_latency:.2f}ms")
        print(f"  P95 latency: {p95_latency:.2f}ms")
        
        # Compare with research
        research_target = 100  # ms from research papers
        if avg_latency <= research_target:
            print(f"  ✓ Below research target ({research_target}ms)")
        else:
            print(f"  ⚠ Above research target ({research_target}ms)")
    
    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "="*70)
        print("BENCHMARK SUMMARY")
        print("="*70)
        
        if 'detection' in self.results:
            print("\nDetection:")
            print(f"  FPS: {self.results['detection']['fps']:.1f}")
            print(f"  Time per frame: {self.results['detection']['avg_time_ms']:.2f}ms")
        
        if 'tracking' in self.results:
            print("\nTracking:")
            print(f"  RMSE: {self.results['tracking']['rmse']:.2f}px")
            print(f"  Mean error: {self.results['tracking']['mean_error']:.2f}px")
        
        if 'prediction' in self.results:
            print("\nPrediction:")
            print(f"  RMSE: {self.results['prediction']['rmse']:.2f}px")
            print(f"  Mean error: {self.results['prediction']['mean_error']:.2f}px")
        
        if 'latency' in self.results:
            print("\nEnd-to-End Latency:")
            print(f"  Average: {self.results['latency']['avg_ms']:.2f}ms")
            print(f"  P95: {self.results['latency']['p95_ms']:.2f}ms")
        
        print("\n" + "="*70)
        print("Research Comparison:")
        print("  Detection: 20-50ms (research) vs {:.2f}ms (ours)".format(
            self.results.get('detection', {}).get('avg_time_ms', 0)
        ))
        print("  Tracking RMSE: ≤15px (research) vs {:.2f}px (ours)".format(
            self.results.get('tracking', {}).get('rmse', 0)
        ))
        print("  Prediction RMSE: 10-20px (research) vs {:.2f}px (ours)".format(
            self.results.get('prediction', {}).get('rmse', 0)
        ))
        print("  Latency: ≤100ms (research) vs {:.2f}ms (ours)".format(
            self.results.get('latency', {}).get('avg_ms', 0)
        ))
        print("="*70)


def main():
    """Run benchmarks"""
    print("="*70)
    print("LBW DECISION SYSTEM - RESEARCH BENCHMARK")
    print("="*70)
    print()
    print("This benchmark compares system performance against")
    print("research standards from academic papers.")
    print()
    
    benchmark = SystemBenchmark()
    
    try:
        benchmark.benchmark_detection_speed()
        benchmark.benchmark_tracking_accuracy()
        benchmark.benchmark_trajectory_prediction()
        benchmark.benchmark_end_to_end_latency()
        
        benchmark.print_summary()
        
        print("\nBenchmark completed successfully!")
        return 0
    
    except Exception as e:
        print(f"\nError during benchmark: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
