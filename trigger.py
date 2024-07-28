from dotenv import load_dotenv
import requests
import datetime
import os

load_dotenv()

# Trello API credentials
TRELLO_API_KEY = os.getenv('TRELLO_API_KEY')
TRELLO_TOKEN = os.getenv('TRELLO_TOKEN')
TRELLO_BOARD_ID = os.getenv('TRELLO_BOARD_ID')  # ie: https://trello.com/b/<board_id>/

# LIFX API credentials
LIFX_API_KEY = os.getenv('LIFX_API_KEY')
LIFX_SELECTOR = os.getenv('LIFX_SELECTOR')  # eg: group:office4


def get_trello_list_id():
    url = f'https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/lists'
    query = { 'key': TRELLO_API_KEY, 'token': TRELLO_TOKEN, 'fields': ['id'] }

    res = requests.get(url, params=query).json()
    # return first list id
    return res[0]['id']


def get_trello_card_ids(list_id: str):
    url = f'https://api.trello.com/1/lists/{list_id}/cards'
    query = { 'key': TRELLO_API_KEY, 'token': TRELLO_TOKEN, 'fields': ['id'] }

    return requests.get(url, params=query).json()


def check_trello_checklist(card_id: str):
    url = f'https://api.trello.com/1/cards/{card_id}/checklists'
    query = { 'key': TRELLO_API_KEY, 'token': TRELLO_TOKEN }

    checklists = requests.get(url, params=query).json()

    # return False if any checklist item is incomplete
    return not any(
        item['state'] != 'complete'
        for checklist in checklists
        for item in checklist['checkItems']
    )

# Check all cards for completed checklists
def check_all_cards():
    list_id = get_trello_list_id()
    cards = get_trello_card_ids(list_id)

    for card in cards:
        if not check_trello_checklist(card['id']):
            return False
    return True

# Flashes LIFX lights from white -> purple
def flash_lifx_lights():
    url = f'https://api.lifx.com/v1/lights/{LIFX_SELECTOR}/effects/breathe'

    headers = { 'Authorization': f'Bearer {LIFX_API_KEY}' }

    data = {
        'from_color': 'white',
        'color': '#4952ac', # purple
        'period': 0.7,
        'cycles': 7,
    }

    res = requests.post(url, data=data, headers=headers)
    return res.status_code


def main():
    all_completed = check_all_cards()
    if not all_completed:
        print('🔔 Checklists are incomplete!')
        return flash_lifx_lights()
    return print('🚀 All checklists completed!')

    # # scheduled cron for 10:00 AM
    # now = datetime.datetime.now()
    # if now.hour == 10 and now.minute == 0:
    #     all_completed = check_all_cards()
    #     if not all_completed:
    #         return flash_lifx_lights()

if __name__ == '__main__':
    main()
