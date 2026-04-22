"""
UBNAD - Windows Edition
Main event orchestration and analysis loop
Enhanced with advanced suspicion scoring, reasoning, and alerts
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
from core.suspicion_engine import calculate_suspicion, determine_risk_level
from core.alert_manager import generate_alert
from database.activity_store import init_db, insert_event
from config import should_alert, is_trusted_process, is_safe_port

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
total_events_processed = 0
total_alerts_generated = 0

def signal_handler(signum, frame):
    """Handle graceful shutdown on Ctrl+C."""
    global running
    logger.info("Shutdown signal received, stopping...")
    logger.info(f"Total events processed: {total_events_processed}")
    logger.info(f"Total alerts generated: {total_alerts_generated}")
    running = False
    
    if collector:
        collector.stop()
    
    sys.exit(0)

def process_event(event):
    """Process a single network event through comprehensive analysis pipeline."""
    global total_events_processed, total_alerts_generated
    
    try:
        total_events_processed += 1
        
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
        
        # Traffic estimate (placeholder for now)
        traffic = 500
        
        # Update behavior baseline
        update_profile(process_name, traffic, intent)
        baseline = get_baseline(process_name)
        
        # Convert timestamp string to float for suspicion calculation
        try:
            from datetime import datetime
            ts_float = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timestamp()
        except:
            ts_float = time.time()
        
        # Calculate comprehensive suspicion score (0-100 scale)
        score, reasons = calculate_suspicion(
            process_name, 
            traffic, 
            intent, 
            baseline,
            dest_ip=dest_ip,
            dest_port=dest_port,
            timestamp=ts_float
        )
        
        # Determine risk level using enhanced scoring
        risk_level = determine_risk_level(score)
        
        # Determine severity for display
        if score >= 76:
            severity = "CRITICAL"
        elif score >= 51:
            severity = "HIGH"
        elif score >= 26:
            severity = "MEDIUM"
        else:
            severity = "SAFE"
        
        # Generate alert if needed
        should_generate_alert, alert_msg, alert_severity = generate_alert(
            process_name,
            dest_ip,
            dest_port,
            score,
            idle,
            reasons,
            intent
        )
        
        if should_generate_alert:
            logger.warning(f"🚨 ALERT: {alert_msg}")
            total_alerts_generated += 1
        
        # Create event dictionary for database - BACKWARD COMPATIBLE
        db_event = {
            "timestamp": timestamp_str,
            "pid": pid,
            "process_name": process_name,
            "dest_ip": dest_ip,
            "dest_port": dest_port,
            "intent_score": intent,
            "suspicion_score": score,
            "risk_level": risk_level,
            "severity": severity,
            "reasons": reasons,
            "protocol": "TCP"
        }
        
        # Store to database
        insert_event(db_event)
        
        # Log summary for high-risk events
        if score > 50:
            logger.info(f"⚠️  {risk_level}: {process_name} ({pid}) -> {dest_ip}:{dest_port} (Score: {score:.1f})")
            if reasons:
                logger.info(f"   Reasons: {', '.join(reasons)}")
        
    except Exception as e:
        logger.error(f"Error processing event: {e}", exc_info=True)

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
