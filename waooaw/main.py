"""
WAOOAW Agent Main Entry Point

Run agents from command line:
  python waooaw/main.py wake_up             # Single wake cycle
  python waooaw/main.py watch --interval 300 # Continuous mode
  python waooaw/main.py --dry-run wake_up   # Dry run mode
"""

import sys
import os
import logging
import argparse
import time
from pathlib import Path

# Add waooaw to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from waooaw.agents.wowvision_prime import WowVisionPrime
from waooaw.config.loader import load_config


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Configure logging"""
    # Create logs directory
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    if log_file is None:
        log_file = log_dir / "wowvision-prime.log"
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={log_level}, file={log_file}")
    
    return logger


def wake_up_agent(config: dict, dry_run: bool = False, test_file: str = None):
    """Execute single wake cycle"""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize agent
        agent = WowVisionPrime(config)
        
        # Execute wake cycle
        if dry_run:
            logger.info("🧪 DRY RUN MODE - No actual changes will be made")
        
        # Add test file to config if provided
        if test_file:
            logger.info(f"🧪 TEST MODE: Processing test file: {test_file}")
            config['test_file'] = test_file
        
        agent.wake_up()
        
        # Cleanup
        agent.shutdown()
        
        logger.info("✅ Wake cycle completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Wake cycle failed: {e}", exc_info=True)
        return 1


def watch_mode(config: dict, interval: int = 300, dry_run: bool = False):
    """Continuous watch mode - wake up at regular intervals"""
    logger = logging.getLogger(__name__)
    
    logger.info(f"👁️  Watch mode started: interval={interval}s, dry_run={dry_run}")
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            logger.info(f"🔄 Starting cycle #{cycle_count}")
            
            # Execute wake cycle
            result = wake_up_agent(config, dry_run=dry_run)
            
            if result != 0:
                logger.warning(f"Cycle #{cycle_count} failed")
            
            # Wait for next cycle
            logger.info(f"💤 Sleeping for {interval}s until next cycle...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info("⏹️  Watch mode stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Watch mode error: {e}", exc_info=True)
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="WAOOAW Agent Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s wake_up                    # Single wake cycle
  %(prog)s watch --interval 300       # Watch mode (every 5 min)
  %(prog)s --dry-run wake_up          # Dry run (no changes)
  %(prog)s --config custom.yaml wake_up  # Custom config
        """
    )
    
    parser.add_argument(
        'command',
        choices=['wake_up', 'watch'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--config',
        help='Path to config file (default: waooaw/config/agent_config.yaml)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Watch mode interval in seconds (default: 300)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - no actual changes'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--test-file',
        help='Test file path for test workflows'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(log_level=args.log_level)
    
    logger.info("="*60)
    logger.info("WAOOAW Agent System - WowVision Prime")
    logger.info("="*60)
    
    # Load config
    try:
        config = load_config(args.config)
        logger.info("✅ Configuration loaded")
        
        # Override dry_run from args
        if args.dry_run:
            config['features'] = config.get('features', {})
            config['features']['dry_run'] = True
        
    except Exception as e:
        logger.error(f"❌ Failed to load configuration: {e}")
        return 1
    
    # Execute command
    if args.command == 'wake_up':
        return wake_up_agent(config, dry_run=args.dry_run, test_file=args.test_file)
    
    elif args.command == 'watch':
        return watch_mode(config, interval=args.interval, dry_run=args.dry_run)
    
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
