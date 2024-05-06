import telebot
import os
from dotenv import load_dotenv
from telebot import types
import threading
import help_methods
import callbacks


class EchoBot:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv('BOT_TOKEN')
        self.bot = telebot.TeleBot(self.token)

        self.people_who_pressed_start = {}
        self.people_who_pressed_end = []
        self.game_is_start = False
        self.timer_active = False
        self.game_is_end = False
        self.current_user = None
        self.current_user_index = 0
        self.people_names = []
        self.factions_index = 0
        self.factions_tuple = [('Кристалград', 'kristal_f', 'kristal.jpg'), ('Андерфолл', 'underfall_f', 'libit.jpg'),
               ('Республика Победы', 'victory_f', 'victory_republic.jpg'), ('Королевская Гавань', 'harbor_f', 'havan.jpg'),
               ('Вольные народы', 'other_f', 'other_f.jpg')]
        self.is_identical_factions = False
        self.people_who_pressed_setting_button = []
        self.to_enable = 0
        self.to_disable = 0
        self.is_first_card = True
        self.card = None

        self.register_handlers()

    def register_handlers(self):

        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.start_game(message)

        @self.bot.message_handler(commands=['end'], func=lambda message: message.from_user.id in self.people_who_pressed_start and self.game_is_start)
        def end(message):
            self.end_game(message.chat.id)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            if call.data == 'start':
                callbacks.callback_start(self, call)
            elif call.data == 'end':
                callbacks.callback_end(self, call)
                return
            elif call.data == 'next':
                callbacks.callback_next_faction(self, call.message.chat.id, call.message.message_id, call.from_user.id)
            elif call.data.endswith('_f'):
                callbacks.callback_f(self, call.message.chat.id, call.message.message_id, call.from_user.id)
            elif call.data in ('i_factions_enable', 'i_factions_disable'):
                callbacks.callback_setting(self, call, call.message.chat.id, call.from_user.id)
            elif call.data == 'more_info':
                callbacks.callback_more_info(self, call.message.chat.id, call.message.message_id, call.from_user.id)
            elif call.data == 'back_to_factions':
                self.factions_index -= 1
                callbacks.callback_next_faction(self, call.message.chat.id, call.message.message_id, call.from_user.id)
            elif call.data == 'deal_card':
                callbacks.callback_deal_card(self, call.message.chat.id, call.from_user.id, call.message.message_id)
                print(self.card)
            elif call.data in ('event_choice1', 'event_choice2'):
                callbacks.callback_event_choices(self, call.message.chat.id, call.from_user.id, call.message.message_id)

    def next_menu_page(self, chat_id, message_id):
        self.bot.delete_message(chat_id, message_id)
        self.bot.send_message(chat_id, 'Игра начинается')

        self.current_user = help_methods.return_current_user_id(self)
        self.people_names = help_methods.name_people_who_passed_start(self, chat_id)
        self.current_user_index = 0
        self.game_is_start = True

        self.start_faction_selection(chat_id)

    def start_game(self, message):
        """
        В этом методе - логика для старта игры
        Старт вызывается /start
        """
        if self.game_is_start or self.timer_active:
            self.bot.send_message(message.chat.id, 'Игра уже запущена')
            return

        if not self.timer_active and not self.game_is_start:
            self.game_is_end = False
            self.people_who_pressed_start = {}
            text_with_button = ('Приветствую, северянин!\n'
                                'Нажми кнопку для начала партии!')

            help_methods.create_button_with_text(self, message.chat.id, 'start', text_with_button, 'start')
        else:
            self.bot.send_message(message.chat.id, 'Игра уже запущена')

    def end_game(self, chat_id):
        """
        В этом методе логика для того чтобы закоончить игру
        Метод будет вызываться через /end
        """
        text_with_button = 'Вы действительно хотите закончить игру?'
        help_methods.create_button_with_text(self, chat_id, 'да', text_with_button, 'end')

    def handle_timer(self, chat_id):
        if len(self.people_who_pressed_start) > 1:
            self.start_game_settings(chat_id)
        else:
            self.bot.send_message(chat_id, 'Не хватает игроков')
        self.timer_active = False

    def start_faction_selection(self, chat_id):
        """
        Метод для запуска выбора фракции для нового пользователя
        """
        if None in self.people_who_pressed_start.values():
            self.factions_index = 0
            self.bot.send_message(chat_id, f'{self.people_names[self.current_user_index]}, выбирай свою фракцию')

            #задаём первую карточку
            help_methods.create_buttons_with_image_for_factions(self, chat_id, 'Кристалград', 'kristal_f', 'kristal.jpg')
        else:
            self.bot.send_message(chat_id, 'Следующий этап игры')
            self.game_loop(chat_id)

    def start_game_settings(self, chat_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        keyboard = types.InlineKeyboardButton('Разрешить выбор одинаковых фракций', callback_data='i_factions_enable')
        keyboard2 = types.InlineKeyboardButton('Запретить выбор одинаковых фракций', callback_data='i_factions_disable')
        markup.add(keyboard, keyboard2)
        self.bot.send_message(chat_id, 'Настройки игры:', reply_markup=markup)

    def game_loop(self, chat_id):
        self.give_cards(chat_id)

    def give_cards(self, chat_id):
        self.bot.send_message(chat_id, f'{self.people_names[self.current_user_index]} вытягивай карту!')
        markup = types.InlineKeyboardMarkup()
        keyboard = types.InlineKeyboardButton('Тянуть!', callback_data='deal_card')
        markup.add(keyboard)
        photo = open(f'images/cards.jpg', 'rb')
        self.bot.send_photo(chat_id, photo, reply_markup=markup)

    def start_bot(self):
        self.bot.polling()

echo_bot = EchoBot()
echo_bot.start_bot()
