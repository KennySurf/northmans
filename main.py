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

        self.register_handlers()

    def register_handlers(self):

        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.start_game(message)

        @self.bot.message_handler(commands=['end'], func=lambda message: message.from_user.id in self.people_who_pressed_start and self.game_is_start)
        def end(message):
            self.end_game(message)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            if call.data == 'start':
                self.callback_start(call)
            elif call.data == 'end':
                self.callback_end(call)
                return

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

            self.create_button_with_text(message, 'start', text_with_button, 'start')
        else:
            self.bot.send_message(message.chat.id, 'Игра уже запущена')

    def end_game(self, message):
        """
        В этом методе логика для того чтобы закоончить игру
        Метод будет вызываться через /end
        """
        text_with_button = 'Вы действительно хотите закончить игру?'
        self.create_button_with_text(message, 'да', text_with_button, 'end')

    def create_button_with_text(self, message, text_in_the_button, text_with_button, callback_name):
        keyboard = types.InlineKeyboardMarkup()
        callback_button = types.InlineKeyboardButton(text=text_in_the_button, callback_data=callback_name)
        keyboard.add(callback_button)
        self.bot.send_message(message.chat.id, text_with_button, reply_markup=keyboard)

    def callback_start(self, call):
        """
        Этот метод для обработки кнопки start
        """
        if self.game_is_start or self.game_is_end:
            self.bot.send_message(call.message.chat.id, 'Эта кнопка больше недоступна\nИспользуй /start или /end')
            return

        people_dict = self.people_who_pressed_start
        user_id = call.from_user.id

        if user_id not in self.people_who_pressed_start:
            people_dict.update({user_id: None})
        else:
            self.bot.send_message(call.message.chat.id, 'Вы уже в очереди')
            return

        if not self.timer_active:
            self.timer_active = True
            self.bot.send_message(call.message.chat.id, 'Игра начнётся через 15 секунд,\n'
                                                        'если хотя-бы 2 человека примут игру')
            threading.Timer(15, self.handle_timer, args=[call.message.chat.id]).start()

        self.bot.send_message(call.message.chat.id, f'{len(people_dict)} в очереди')

    def handle_timer(self, chat_id):
        if len(self.people_who_pressed_start) > 1:
            self.bot.send_message(chat_id, 'Игра начинается')

            self.current_user = list(self.people_who_pressed_start.keys())[0]
            self.people_names = self.name_people_who_passed_start(chat_id)
            self.current_user_index = 0
            self.game_is_start = True

            self.faction_selection(chat_id)
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

    def start_bot(self):
        self.bot.polling()

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

    def faction_selection(self, chat_id):
        self.bot.send_message(chat_id, f'{self.people_names[self.current_user_index]}, выбирай свою фракцию')
        self.send_available_factions(chat_id)
        self.index_increase()

    def index_increase(self):
        if self.current_user_index + 1 < len(self.people_who_pressed_start):
            self.current_user_index += 1
        else:
            self.current_user_index = 0

    def send_available_factions(self, chat_id):
        self.create_button_with_image(chat_id, 'Кристалград', 'kristal', 'kristal.jpg')
        self.create_button_with_image(chat_id, 'Андерфолл', 'underfall', 'libit.jpg')
        self.create_button_with_image(chat_id, 'Королевская Гавань', 'harbor', 'havan.jpg')

    def create_button_with_image(self, chat_id, text_in_keyboard: str, callback_name: str, photo_with_ex: str):
        markup = types.InlineKeyboardMarkup()
        keyboard = types.InlineKeyboardButton(text_in_keyboard, callback_data=callback_name)
        markup.add(keyboard)
        photo = open(f'images/{photo_with_ex}', 'rb')
        self.bot.send_photo(chat_id, photo, reply_markup=markup)

echo_bot = EchoBot()
echo_bot.start_bot()
