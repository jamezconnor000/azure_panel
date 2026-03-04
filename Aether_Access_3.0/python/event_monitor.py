#!/usr/bin/env python3
"""Event monitoring utility"""
import time
from hal_interface import HAL

def main():
    hal = HAL()
    hal.connect('localhost', 5000)
    hal.subscribe_to_events(max_batch=50)
    
    print('Monitoring events... (Ctrl+C to exit)')
    try:
        while True:
            events = hal.get_events()
            for event in events:
                print(f'Event: {event}')
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nExiting...')
    finally:
        hal.disconnect()

if __name__ == '__main__':
    main()
