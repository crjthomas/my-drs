#!/usr/bin/env python3
"""
LBW Decision System - Main Entry Point
Real-time cricket LBW decision making using computer vision
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.lbw_system import LBWDecisionSystem
from loguru import logger


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='LBW Decision System - Real-time cricket umpiring assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration
  python main.py
  
  # Run with custom config file
  python main.py --config my_config.yaml
  
  # Run with specific video source
  python main.py --video /path/to/video.mp4
  
  # Run with webcam (device 1)
  python main.py --video 1
  
  # Run without display (headless mode)
  python main.py --no-display
  
Keyboard Controls:
  q - Quit application
  p - Pause/Resume processing
  r - Reset tracker
  s - Save screenshot
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    
    parser.add_argument(
        '--video',
        type=str,
        help='Video source (camera index or file path). Overrides config.'
    )
    
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Run without display (headless mode)'
    )
    
    parser.add_argument(
        '--save-video',
        action='store_true',
        help='Save output video'
    )
    
    parser.add_argument(
        '--device',
        type=str,
        choices=['cuda', 'cpu'],
        help='Processing device (cuda or cpu). Overrides config.'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    # Parse arguments
    args = parse_arguments()
    
    # Print banner
    print("=" * 70)
    print("LBW DECISION SYSTEM")
    print("Real-time Cricket Umpiring Assistant")
    print("=" * 70)
    print()
    
    try:
        # Initialize system
        logger.info("Initializing LBW Decision System...")
        system = LBWDecisionSystem(config_path=args.config)
        
        # Apply command line overrides
        if args.video:
            # Try to convert to int (camera index)
            try:
                video_source = int(args.video)
            except ValueError:
                video_source = args.video
            
            system.config.set('video.source', video_source)
            logger.info(f"Video source set to: {video_source}")
        
        if args.no_display:
            system.config.set('output.display', False)
            logger.info("Display disabled (headless mode)")
        
        if args.save_video:
            system.config.set('output.save_video', True)
            logger.info("Video saving enabled")
        
        if args.device:
            system.config.set('detection.device', args.device)
            logger.info(f"Device set to: {args.device}")
        
        if args.log_level:
            system.config.set('output.log_level', args.log_level)
        
        # Start system
        logger.info("Starting system...")
        print()
        print("System running. Press 'q' to quit, 'p' to pause, 'r' to reset, 's' for screenshot")
        print()
        
        with system:
            system.start()
        
        print()
        print("=" * 70)
        print("System stopped successfully")
        print("=" * 70)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\nInterrupted by user")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nError: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
