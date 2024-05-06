from random import shuffle

cards = []


def create_cards():
    global cards

    cards = ['Событие', 'Шмотка', 'Испытание'] * 10
    shuffle(cards)


def deal():
    global cards

    if len(cards):
        return cards.pop(0)
    return None
