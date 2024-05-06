from telebot import types


def create_button_with_text(self, chat_id, text_in_the_button, text_with_button, callback_name):
    keyboard = types.InlineKeyboardMarkup()
    callback_button = types.InlineKeyboardButton(text=text_in_the_button, callback_data=callback_name)
    keyboard.add(callback_button)
    self.bot.send_message(chat_id, text_with_button, reply_markup=keyboard)


def create_buttons_with_image_for_factions(self, chat_id, text_in_keyboard: str, callback_name: str, photo_with_ex: str):
    markup = types.InlineKeyboardMarkup(row_width=1)
    keyboard1 = types.InlineKeyboardButton(text_in_keyboard, callback_data=callback_name)
    keyboard2 = types.InlineKeyboardButton('Подробнее', callback_data='more_info')
    keyboard3 = types.InlineKeyboardButton('Далее', callback_data='next')
    markup.add(keyboard1, keyboard2, keyboard3)
    photo = open(f'images/{photo_with_ex}', 'rb')
    self.bot.send_photo(chat_id, photo, reply_markup=markup)


def index_increase(self):
    if self.current_user_index + 1 < len(self.people_who_pressed_start):
        self.current_user_index += 1
    else:
        self.current_user_index = 0


def return_current_user_id(self):
    return list(self.people_who_pressed_start.keys())[self.current_user_index]


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