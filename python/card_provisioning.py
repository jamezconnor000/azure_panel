#!/usr/bin/env python3
"""Card provisioning utility"""
import argparse
from hal_interface import HAL

def main():
    parser = argparse.ArgumentParser(description='HAL Card Provisioning')
    parser.add_argument('--add-card', type=int, help='Add card ID')
    parser.add_argument('--facility', type=int, default=100, help='Facility code')
    parser.add_argument('--number', type=int, help='Card number')
    parser.add_argument('--delete', type=int, help='Delete card ID')
    
    args = parser.parse_args()
    
    hal = HAL()
    hal.connect('localhost', 5000)
    
    if args.add_card:
        card = {
            'card_id': args.add_card,
            'facility_code': args.facility,
            'card_number': args.number or args.add_card,
        }
        if hal.add_card(card):
            print(f'✓ Card {args.add_card} added')
    
    hal.disconnect()

if __name__ == '__main__':
    main()
