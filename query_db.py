#!/usr/bin/env python3
"""Query database for recent events."""

from database.activity_store import fetch_recent_events

events = fetch_recent_events(15)
print(f"\n{'='*80}")
print(f"Total events in database: {len(events)}")
print(f"{'='*80}\n")

if events:
    for event in events:
        print(f"{event['timestamp']} | {event['process_name']:20} | {event['dest_ip']}:{event['dest_port']}")
else:
    print("No events found in database")

print(f"\n{'='*80}")
