"""
UBNAD - Windows Edition
Main event orchestration and analysis loop
"""

import signal
import sys
import threading
import time
from queue import Queue, Empty
import logging
from datetime import datetime

from collector.windows_net_collector import WindowsNetCollector
from core.intent_monitor import get_intent_score, get_idle_time
from core.process_mapper import get_process_state
from core.behavior_model import update_profile, get_baseline
from core.suspicion_engine import calculate_suspicion
from core.alert_manager import generate_alert
from database.activity_store import init_db, insert_event

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
event_queue = Queue(maxsize=1000)
running = True
collector = None

def signal_handler(signum, frame):
    """Handle graceful shutdown on Ctrl+C."""
    global running
    logger.info("Shutdown signal received, stopping...")
    running = False
    
    if collector:
        collector.stop()
    
    sys.exit(0)

def determine_risk_level(score):
    """Determine risk level from suspicion score."""
    if score > 20:
        return "CRITICAL"
    elif score > 10:
        return "HIGH"
    elif score > 5:
        return "MEDIUM"
    else:
        return "SAFE"

def process_event(event):
    """Process a single network event through analysis pipeline."""
    try:
        timestamp_str = event["timestamp"]  # Already formatted as string from collector
        pid = event["pid"]
        process_name = event["process"]
        dest_ip = event["dest_ip"]
        dest_port = event["dest_port"]
        
        # Get process metadata
        proc = get_process_state(pid)
        if not proc:
            logger.debug(f"Could not resolve process for PID {pid}")
        
        # Get user activity metrics
        intent = get_intent_score()
        idle = get_idle_time()
        
        # Traffic estimate (placeholder)
        traffic = 500
        
        # Update behavior baseline
        update_profile(process_name, traffic, intent)
        baseline = get_baseline(process_name)
        
        # Calculate suspicion score
        score = calculate_suspicion(process_name, traffic, intent, baseline)
        
        # Determine risk level
        risk_level = determine_risk_level(score)
        
        # Create event dictionary for database
        db_event = {
            "timestamp": timestamp_str,
            "pid": pid,
            "process_name": process_name,
            "dest_ip": dest_ip,
            "dest_port": dest_port,
            "intent_score": intent,
            "suspicion_score": score,
            "risk_level": risk_level
        }
        
        # Store to database
        insert_event(db_event)
        
        # Generate alert if suspicious
        if score > 10:
            generate_alert(process_name, dest_ip, score, idle)
        
        logger.debug(
            f"Event: {process_name} -> {dest_ip}:{dest_port} "
            f"(score: {score:.1f}, risk: {risk_level})"
        )
        
    except Exception as e:
        logger.error(f"Event processing error: {e}", exc_info=False)

def analyzer_loop():
    """Main analyzer loop - consume events from queue."""
    logger.info("Analyzer loop started - waiting for network events")
    event_count = 0
    last_status = time.time()
    
    while running:
        try:
            event = event_queue.get(timeout=1.0)
            process_event(event)
            event_count += 1
            
            # Periodic status
            if event_count % 50 == 0:
                logger.info(f"Processed {event_count} events")
            
        except Empty:
            # Periodic status message
            now = time.time()
            if now - last_status >= 15:
                queue_size = event_queue.qsize()
                logger.debug(f"Status: {event_count} events processed, queue size: {queue_size}")
                last_status = now
        except Exception as e:
            logger.error(f"Analyzer error: {e}")
    
    logger.info(f"Analyzer stopped. Total events processed: {event_count}")

def main():
    """Main entry point."""
    global collector, running
    
    logger.info("=" * 60)
    logger.info("UBNAD - Unauthorized Background Network Activity Detector")
    logger.info("Windows Edition")
    logger.info("=" * 60)
    
    # Initialize database FIRST - before any collectors/threads
    if not init_db():
        logger.error("Database initialization failed - exiting")
        sys.exit(1)
    logger.info("Database initialized: database/ubnad.db")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start network collector
    collector = WindowsNetCollector(event_queue)
    if collector.start():
        logger.info("Windows network collector started")
    else:
        logger.error("Failed to start collector")
        sys.exit(1)
    
    # Run analyzer
    try:
        analyzer_loop()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
