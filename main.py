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

        self.people_who_pressed_start = []
        self.people_who_pressed_end = []
        self.game_is_start = False
        self.timer_active = False
        self.game_is_end = False

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
            self.people_who_pressed_start = []
            text_with_button = ('Приветствую, северянин!\n'
                                'Нажми кнопку для начала партии!')

            self.create_button(message, 'start', text_with_button, 'start')
        else:
            self.bot.send_message(message.chat.id, 'Игра уже запущена')

    def end_game(self, message):
        """
        В этом методе логика для того чтобы закоончить игру
        Метод будет вызываться через /end
        """
        text_with_button = 'Вы действительно хотите закончить игру?'
        self.create_button(message, 'да', text_with_button, 'end')

    def create_button(self, message, text_in_the_button, text_with_button, callback_name):
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

        lst = self.people_who_pressed_start
        user_id = call.from_user.id

        if user_id not in self.people_who_pressed_start:
            lst.append(user_id)
        else:
            self.bot.send_message(call.message.chat.id, 'Вы уже в очереди')
            return

        if not self.timer_active:
            self.timer_active = True
            self.bot.send_message(call.message.chat.id, 'Игра начнётся через 15 секунд,\n'
                                                        'если хотя-бы 2 человека примут игру')
            threading.Timer(15, self.handle_timer, args=[call.message.chat.id]).start()

        self.bot.send_message(call.message.chat.id, f'{len(lst)} в очереди')

    def handle_timer(self, chat_id):
        if len(self.people_who_pressed_start) > 1:
            self.bot.send_message(chat_id, 'Игра начинается')
            self.game_is_start = True
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


echo_bot = EchoBot()
echo_bot.start_bot()
