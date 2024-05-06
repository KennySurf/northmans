from random import choice
from telebot import types


def event(self, chat_id):
    events_dict = {'Событие': ('шанс 1', 'шанс 2', 'шанс 3'),
                   'Шмотка': ('мотка 1', 'шмотка 2', 'шмотка 3'),
                   'Испытание': ('испытание 1', 'испытание 2', 'испытание 3')}

    markup = types.InlineKeyboardMarkup()

    keyboard = types.InlineKeyboardButton('Выбор 1', callback_data='event_choice1')
    keyboard2 = types.InlineKeyboardButton('Выбор 2', callback_data='event_choice2')

    markup.add(keyboard, keyboard2)
    self.bot.send_message(chat_id, f'{self.people_names[self.current_user_index]}, тебе выпало {choice(events_dict[self.card])}', reply_markup=markup)

