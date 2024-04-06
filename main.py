import telebot
import os
from dotenv import load_dotenv
from telebot import types
import threading


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
                self.callback_start(call)
            elif call.data == 'end':
                self.callback_end(call)
                return
            elif call.data == 'next':
                self.callback_next_faction(call.message.chat.id, call.message.message_id, call.from_user.id)
            elif call.data.endswith('_f'):
                self.callback_f(call.message.chat.id, call.message.message_id, call.from_user.id)
            elif call.data in ('i_factions_enable', 'i_factions_disable'):
                self.callback_setting(call, call.message.chat.id, call.from_user.id)
            elif call.data == 'more_info':
                self.callback_more_info(call.message.chat.id, call.message.message_id, call.from_user.id)
            elif call.data == 'back_to_factions':
                self.factions_index -= 1
                self.callback_next_faction(call.message.chat.id, call.message.message_id, call.from_user.id)

    def callback_more_info(self, chat_id, message_id, user_id):
        if user_id != self.return_current_user_id():
            return

        self.bot.delete_message(chat_id, message_id)

        text1 = 'kristal'
        text2 = 'underfall'
        text3 = 'victory'
        text4 = 'havan'
        text5 = 'other'

        texts = [text1, text2, text3, text4, text5]
        self.create_button_with_text(chat_id, 'Назад', texts[self.factions_index], 'back_to_factions')

    def next_menu_page(self, chat_id, message_id):
        self.bot.delete_message(chat_id, message_id)
        self.bot.send_message(chat_id, 'Игра начинается')

        self.current_user = self.return_current_user_id()
        self.people_names = self.name_people_who_passed_start(chat_id)
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

            self.create_button_with_text(message.chat.id, 'start', text_with_button, 'start')
        else:
            self.bot.send_message(message.chat.id, 'Игра уже запущена')

    def end_game(self, chat_id):
        """
        В этом методе логика для того чтобы закоончить игру
        Метод будет вызываться через /end
        """
        text_with_button = 'Вы действительно хотите закончить игру?'
        self.create_button_with_text(chat_id, 'да', text_with_button, 'end')

    def create_button_with_text(self, chat_id, text_in_the_button, text_with_button, callback_name):
        keyboard = types.InlineKeyboardMarkup()
        callback_button = types.InlineKeyboardButton(text=text_in_the_button, callback_data=callback_name)
        keyboard.add(callback_button)
        self.bot.send_message(chat_id, text_with_button, reply_markup=keyboard)

    def callback_start(self, call):
        """
        Этот метод для обработки кнопки start
        """
        if self.game_is_start or self.game_is_end:
            self.bot.send_message(call.message.chat.id, 'Эта кнопка больше недоступна\nИспользуй /start или /end')
            return

        user_id = call.from_user.id

        if user_id not in self.people_who_pressed_start:
            self.people_who_pressed_start.update({user_id: None})
        else:
            self.bot.send_message(call.message.chat.id, 'Вы уже в очереди')
            return

        if not self.timer_active:
            self.timer_active = True
            self.bot.send_message(call.message.chat.id, 'Игра начнётся через 15 секунд,\n'
                                                        'если хотя-бы 2 человека примут игру')
            threading.Timer(15, self.handle_timer, args=[call.message.chat.id]).start()

        self.bot.send_message(call.message.chat.id, f'{len(self.people_who_pressed_start)} в очереди')

    def handle_timer(self, chat_id):
        if len(self.people_who_pressed_start) > 1:
            self.start_game_settings(chat_id)
        else:
            self.bot.send_message(chat_id, 'Не хватает игроков')
        self.timer_active = False

    def callback_end(self, call):
        """
        Этот метод для обработки кнопки end
        """

        user_id = call.from_user.id
        if not self.game_is_start or user_id not in self.people_who_pressed_start:
            self.bot.send_message(call.message.chat.id, 'Эта кнопка уже недоступна')
            return

        lst = self.people_who_pressed_end

        if user_id not in lst:
            lst.append(user_id)

            how_more_people_need = len(self.people_who_pressed_start) - len(lst) - 1
            if_append_txt = (f'Для выхода требуется ещё {how_more_people_need}')

            if not how_more_people_need:
                self.bot.send_message(call.message.chat.id, 'Игра окончена!')
                self.game_is_start = False
                self.game_is_end = True
                self.people_who_pressed_end = []
                return

            self.bot.send_message(call.message.chat.id, if_append_txt)
        else:
            self.bot.send_message(call.message.chat.id, 'Вы уже голосовали')

    def callback_next_faction(self, chat_id, message_id, user_id):
        if user_id != self.return_current_user_id():
            return

        self.bot.delete_message(chat_id, message_id)
        self.factions_index += 1
        self.factions_index %= 5

        self.create_buttons_with_image_for_factions(chat_id, self.factions_tuple[self.factions_index][0], self.factions_tuple[self.factions_index][1], self.factions_tuple[self.factions_index][2])

    def callback_f(self, chat_id, message_id, user_id):
        if user_id != self.return_current_user_id():
            return

        if not self.is_identical_factions:
            if self.factions_tuple[self.factions_index][0] in self.people_who_pressed_start.values():
                self.bot.send_message(chat_id, 'Эта фракция уже занята другим игроком')
                return

        self.bot.delete_message(chat_id, message_id)
        self.people_who_pressed_start[self.return_current_user_id()] = self.factions_tuple[self.factions_index][0]
        self.index_increase()
        print(self.people_who_pressed_start)
        self.start_faction_selection(chat_id)

    def name_people_who_passed_start(self, chat_id):
        """
        Этот метод активируется только когда запускается игра и возвращает имена всех участников
        :return: лист имён всех, кто нажал на кнопку start
        """
        names = []
        for user_id in tuple(self.people_who_pressed_start.keys()):
            user_info = self.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            name = user_info.user.first_name
            names.append(name)
        return names

    def start_faction_selection(self, chat_id):
        """
        Метод для запуска выбора фракции для нового пользователя
        """
        if None in self.people_who_pressed_start.values():
            self.factions_index = 0
            self.bot.send_message(chat_id, f'{self.people_names[self.current_user_index]}, выбирай свою фракцию')

            #задаём первую карточку
            self.create_buttons_with_image_for_factions(chat_id, 'Кристалград', 'kristal_f', 'kristal.jpg')
        else:
            self.bot.send_message(chat_id, 'Следующий этап игры')

    def index_increase(self):
        if self.current_user_index + 1 < len(self.people_who_pressed_start):
            self.current_user_index += 1
        else:
            self.current_user_index = 0

    def return_current_user_id(self):
        return list(self.people_who_pressed_start.keys())[self.current_user_index]

    def create_buttons_with_image_for_factions(self, chat_id, text_in_keyboard: str, callback_name: str, photo_with_ex: str):
        markup = types.InlineKeyboardMarkup(row_width=1)
        keyboard1 = types.InlineKeyboardButton(text_in_keyboard, callback_data=callback_name)
        keyboard2 = types.InlineKeyboardButton('Подробнее', callback_data='more_info')
        keyboard3 = types.InlineKeyboardButton('Далее', callback_data='next')
        markup.add(keyboard1, keyboard2, keyboard3)
        photo = open(f'images/{photo_with_ex}', 'rb')
        self.bot.send_photo(chat_id, photo, reply_markup=markup)

    def start_game_settings(self, chat_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        keyboard = types.InlineKeyboardButton('Разрешить выбор одинаковых фракций', callback_data='i_factions_enable')
        keyboard2 = types.InlineKeyboardButton('Запретить выбор одинаковых фракций', callback_data='i_factions_disable')
        markup.add(keyboard, keyboard2)
        self.bot.send_message(chat_id, 'Настройки игры:', reply_markup=markup)

    def callback_setting(self, call, chat_id, user_id):
        if user_id not in self.people_who_pressed_start.keys():
            return

        if user_id in self.people_who_pressed_setting_button:
            self.bot.send_message(chat_id, 'Вы уже голосовали за эту настройку')
            return

        self.people_who_pressed_setting_button.append(user_id)
        votes_left = len(self.people_who_pressed_start) - len(self.people_who_pressed_setting_button) - 1

        if call.data == "i_factions_enable":
            self.to_enable += 1
        else:
            self.to_disable += 1

        if votes_left:
            self.bot.send_message(chat_id, f'Голосов осталось: {votes_left}')
        else:
            if self.to_disable == self.to_enable:
                self.bot.send_message(chat_id, 'Голоса равны, последний голос определил настройки')
                self.is_identical_factions = True if call.data == "i_factions_enable" else False
            else:
                self.is_identical_factions = True if self.to_enable > self.to_disable else False

            self.to_disable = 0
            self.to_enable = 0
            self.people_who_pressed_setting_button = []
            self.next_menu_page(chat_id, call.message.message_id)

    def start_bot(self):
        self.bot.polling()


echo_bot = EchoBot()
echo_bot.start_bot()
