from dateutil.parser import parse
from dotenv import load_dotenv
from datetime import date
import requests
import os

load_dotenv()
# Trello API credentials
TRELLO_API_KEY = os.getenv('TRELLO_API_KEY')
TRELLO_TOKEN = os.getenv('TRELLO_TOKEN')
TRELLO_BOARD_ID = os.getenv('TRELLO_BOARD_ID')  # ie: https://trello.com/b/<board_id>/
TRELLO_QUERY = { 'key': TRELLO_API_KEY, 'token': TRELLO_TOKEN }

# LIFX API credentials
LIFX_API_KEY = os.getenv('LIFX_API_KEY')
LIFX_SELECTOR = os.getenv('LIFX_SELECTOR')  # eg: group:office4


def get_trello_list_id() -> str:
    """Fetches and returns (str) first list id from Trello board."""
    url = f'https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/lists'
    res = requests.get(url, params=TRELLO_QUERY).json()

    return res[0]['id'] # return first list id


def list_trello_card_ids(list_id: str) -> list:
    """
    Fetches the IDs of cards in a Trello list that are past due or due today.
        `list_id` (str): Trello list id.
    Returns list of card ids that are past due or due today.
    """
    url = f'https://api.trello.com/1/lists/{list_id}/cards'
    cards = requests.get(url, params=TRELLO_QUERY).json()

    ids = []
    for card in cards:
        if not card['dueComplete'] and parse(card['due']).date() <= date.today(): 
            print(f"[{card['name']}] card is incomplete!")
            ids.append(card['id'])

    return ids


def check_trello_card(card_id: str) -> bool:
    """
    Checks if all checklist items of Trello card are complete.
        `card_id` (str): Trello card id.
    Returns (bool) True if all items are complete, False otherwise.
    """
    url = f'https://api.trello.com/1/cards/{card_id}/checklists'
    checklists = requests.get(url, params=TRELLO_QUERY).json()

    # return False if any checklist item is incomplete
    return all(
        item['state'] == 'complete'
        for checklist in checklists
        for item in checklist['checkItems']
    )


def check_all_trello_cards() -> bool:
    """Checks if all cards in the first Trello list have completed checklists.

    Returns (bool) True if all checklists are complete, False if any are incomplete.
    """
    list_id = get_trello_list_id()
    cards = list_trello_card_ids(list_id)

    return all(check_trello_card(card) for card in cards)


def flash_lifx_lights(selector: str, from_color: str = 'white', color: str = '#4952ac', period: float = 0.7, cycles: int = 7) -> int:
    """
    Flashes LIFX lights based on the following parameters:
        `selector` (str): [LIFX identifier](https://api.developer.lifx.com/reference/selectors) for specific light(s). 
        `from_color` (str): Initial color of the light, defaults to 'white'.
        `color` (str): Color to flash to, defaults to '#4952ac' (purple).
        `period` (float): Duration of one flash cycle in seconds, defaults to 0.7.
        `cycles` (int): Number of times effect repeats, defaults to 7.
    Returns (int) LIFX API request status code.
    """
    url = f'https://api.lifx.com/v1/lights/{selector}/effects/breathe'
    headers = { 'Authorization': f'Bearer {LIFX_API_KEY}' }
    data = {
        'from_color': from_color,
        'color': color,
        'period': period,
        'cycles': cycles,
    }

    res = requests.post(url, data=data, headers=headers)
    return res.status_code


def main():
    try:
        if not check_all_trello_cards():
            print('🚨 Checklists are incomplete!')
            return flash_lifx_lights(LIFX_SELECTOR)
        return print('🚀 All checklists completed!')
    except Exception as e:
        print(f'Error: {e}')


if __name__ == '__main__':
    main()
