import threading
import help_methods
import cards
import events

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


def callback_more_info(self, chat_id, message_id, user_id):
    if user_id != help_methods.return_current_user_id(self):
        return

    self.bot.delete_message(chat_id, message_id)

    text1 = 'kristal'
    text2 = 'underfall'
    text3 = 'victory'
    text4 = 'havan'
    text5 = 'other'

    texts = [text1, text2, text3, text4, text5]
    help_methods.create_button_with_text(self, chat_id, 'Назад', texts[self.factions_index], 'back_to_factions')


def callback_next_faction(self, chat_id, message_id, user_id):
    if user_id != help_methods.return_current_user_id(self):
        return

    self.bot.delete_message(chat_id, message_id)
    self.factions_index += 1
    self.factions_index %= 5

    help_methods.create_buttons_with_image_for_factions(self, chat_id, self.factions_tuple[self.factions_index][0], self.factions_tuple[self.factions_index][1], self.factions_tuple[self.factions_index][2])


def callback_f(self, chat_id, message_id, user_id):
    if user_id != help_methods.return_current_user_id(self):
        return

    if not self.is_identical_factions:
        if self.factions_tuple[self.factions_index][0] in self.people_who_pressed_start.values():
            self.bot.send_message(chat_id, 'Эта фракция уже занята другим игроком')
            return

    self.bot.delete_message(chat_id, message_id)
    self.people_who_pressed_start[help_methods.return_current_user_id(self)] = self.factions_tuple[self.factions_index][0]
    help_methods.index_increase(self)
    print(self.people_who_pressed_start)
    self.start_faction_selection(chat_id)


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


def callback_deal_card(self, chat_id, user_id, message_id):
    if user_id != help_methods.return_current_user_id(self):
        return

    if self.is_first_card:
        cards.create_cards()
        self.is_first_card = False

    self.card = cards.deal()

    self.bot.delete_message(chat_id, message_id)

    events.event(self, chat_id)


def callback_event_choices(self, chat_id, user_id, message_id):
    if user_id != help_methods.return_current_user_id(self):
        return

    self.bot.send_message(chat_id, f'Это повлияло так..')
    self.bot.delete_message(chat_id, message_id)
    help_methods.index_increase(self)
    self.game_loop(chat_id)



