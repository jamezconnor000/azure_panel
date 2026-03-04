"""Utility functions"""

def format_timestamp(ts):
    from datetime import datetime
    return datetime.fromtimestamp(ts).isoformat()

def deny_reason_str(reason):
    reasons = {
        0: 'Card Not Found',
        1: 'No Permission',
        2: 'Time Restriction',
        3: 'Card Blocked',
    }
    return reasons.get(reason, 'Unknown')
