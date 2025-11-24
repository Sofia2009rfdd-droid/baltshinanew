import config
import dbworker
from def_for_bot import (zapis_on_bt_end, zapis_data, get_russian_date_info, get_available_times,
                         make_available_times_keyboard, bulk_safe_delete_message)
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import time
from datetime import datetime
from threading import Lock
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import datetime
from telebot import types
import time


BSH_API_URL = 'https://baltshina.ru/zapis/?shag=1&mas=1'
bot = telebot.TeleBot(config.token)



scheduler = BackgroundScheduler()
scheduler.start()  # запустить один раз при старте приложения

def send_reminder(chat_id, time):
    try:
        if dbworker.get_current_state(chat_id) != config.States.CANCEL.value:
            keyboard_cancel = types.InlineKeyboardMarkup()
            button_back = types.InlineKeyboardButton(f"❌ Отменить запись ❌", callback_data="cancel")
            keyboard_cancel.row(button_back)

            bot.send_message(chat_id, f"❗ Напоминание ❗\n\nВы записаны на шиномонтаж через 4 часа ({time})✔️\n\n*📍 Адрес: ул. Цветочная д. 18*\n\nЕсли вы хотите отменить запись, пожалуйста, позвоните по любому номеру:\n☎️ (812)611-10-66\n (812)324-40-99\n\n\nМы вас ждем!"
                            , reply_markup=keyboard_cancel)
            print("Отправленно в чат")
        else:
            print(f'НАПОМИНАНИЕ ОТМЕНЕНО! {time}')
    except Exception as e:
        print("Ошибка отправки:", e)

def schedule_with_aps(chat_id, appointment_time, time_total, hours_before=24):
    reminder_time = appointment_time - datetime.timedelta(hours=hours_before)
    scheduler.add_job(send_reminder, 'date', run_date=reminder_time, args=[chat_id, time_total])
    print("APScheduler: напоминание запланировано на", reminder_time)




class FSMStorage:
    _data_lock = Lock()

    def __init__(self):
        self._data = {}

    def get_data(self, user_id, chat_id) -> dict:
        with self._data_lock:
            return self._data.get((user_id, chat_id), {}).copy()

    def set_data(self, user_id, chat_id, data) -> None:
        with self._data_lock:
            self._data[(user_id, chat_id)] = data

    def add_data(self, user_id, chat_id, key, value) -> None:
        with self._data_lock:
            if (user_id, chat_id) not in self._data:
                self._data[(user_id, chat_id)] = {}
            self._data[(user_id, chat_id)][key] = value


fsm_storage = FSMStorage()







@bot.message_handler(commands=['start'])
def start(message):
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', message.chat.id)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton("Запись на шиномонтаж")
    keyboard.add(button1)
    bot.send_message(message.chat.id, '🌟 Привет! 👋\n\n🚗 Я помогу вам записаться на шиномонтаж к опытным специалистам! \n\n🛠️ Нажмите кнопку "Записаться на шиномонтаж", чтобы начать.', reply_markup=keyboard)
    dbworker.set_state(message.chat.id, config.States.S_TART.value)


@bot.message_handler(commands=["reset"])
def cmd_reset(message):
    state = dbworker.get_current_state(message.chat.id)
    if state == config.States.S_SEND_PIC_OUT.value:
        bot.send_message(message.chat.id,'Вы уже записались на шиномонтаж.\nЕсли вам нужно записать еще одну машину нажмите "Записаться на шиномонтаж"')

    else:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = KeyboardButton("Запись на шиномонтаж")
        keyboard.add(button1)
        bot.send_message(message.chat.id, 'Что ж, если появится желаение записаться на шиномонтаж, нажми кнопку "Запись на шиномонтаж", чтобы начать.', reply_markup=keyboard)
        dbworker.set_state(message.chat.id, config.States.S_TART.value)



@bot.message_handler(func=lambda message: message.text == "Запись на шиномонтаж")
def handle_message(message):
    state = dbworker.get_current_state(message.chat.id)
    if state == config.States.S_SEND_PIC_OUT.value:
        bot.send_message(message.chat.id, "Я очень рад, что вы снова выбрали нас!", reply_markup=types.ReplyKeyboardRemove())

    else:
        bot.send_message(message.chat.id, "Прекрасно! Давайте начнем!", reply_markup=types.ReplyKeyboardRemove())

    msg = bot.send_message(message.chat.id, "🗓 Выберите день для записи 🗓", reply_markup=zapis_data())
    fsm_data = fsm_storage.get_data(
        message.chat.id,
        message.from_user.id,
    )
    fsm_data.setdefault("delete_messages_ids", []).append(msg.id)
    fsm_storage.set_data(
        message.chat.id,
        message.from_user.id,
        fsm_data,
    )

    dbworker.set_state(message.chat.id, config.States.S_ENTER_DATA.value)



@bot.callback_query_handler(func=lambda call: call.data.startswith('button'))
def callback_query(call):

    fsm_data = fsm_storage.get_data(
        call.message.chat.id,
        call.from_user.id,

    )
    bulk_safe_delete_message(bot, call.message.chat.id, fsm_data.pop("delete_messages_ids", []))
    bot.answer_callback_query(call.id)
    today = datetime.date.today()
    button_days = {
        "button0": 0,
        "button1": 1,
        "button2": 2,
        "button3": 3,
        "button4": 4,
        "button5": 5,
        "button6": 6
    }
    target_date = today + datetime.timedelta(days=button_days[call.data])
    print(target_date)
    print("!!!!!!!!!!!!")
    delete_messages_ids = []
    delete_messages_id = []
    all_available_time = get_available_times(target_date)
    fsm_data = {
        "selected_day": target_date.day,
        "delete_messages_ids": delete_messages_ids,
        "delete_messages_id": delete_messages_id,
        "all_time": all_available_time,
        "selected_total": target_date
    }
    selected_date = fsm_data["selected_total"]
    day, month = get_russian_date_info(selected_date)

    if not get_available_times(target_date):
        msg = bot.send_message(call.message.chat.id, f'К сожалению на {target_date.day} {month} нет свободных мест. 🙁\n----------------------------------------------------------------\n\nПожалуйста, выберите другой день:', reply_markup=zapis_data())
        delete_messages_ids.append(msg.id)
    else:
        msg = bot.send_message(call.message.chat.id, f'Свободные мастера на {target_date.day} {month}:')
        delete_messages_ids.append(msg.message_id)

        for employe_name, available_times in all_available_time.items():
            msg = bot.send_message(call.message.chat.id, employe_name + '👨🏽‍🔧', reply_markup=make_available_times_keyboard(employe_name, available_times))
            delete_messages_ids.append(msg.message_id)


        keyboard_end = types.InlineKeyboardMarkup()
        button_back = types.InlineKeyboardButton('🔙 Назад', callback_data="end_button")
        keyboard_end.add(button_back)
        msg = bot.send_message(call.message.chat.id, 'Во сколько вам было бы удобнее?', reply_markup=keyboard_end)
        delete_messages_ids.append(msg.message_id)


    fsm_storage.set_data(
        call.message.chat.id,
        call.from_user.id,
        fsm_data,
    )

    dbworker.set_state(call.message.chat.id, config.States.S_ENTER_TIME.value)




#________________________________ ПЕРВАЯ КНОПКА НАЗАД___(back)________________________________
@bot.callback_query_handler(func=lambda call: call.data == 'end_button')
def handle_end_button(call):
    fsm_data = fsm_storage.get_data(
        call.message.chat.id,
        call.from_user.id,
    )
    bulk_safe_delete_message(bot, call.message.chat.id, fsm_data.pop("delete_messages_ids", []))
    bulk_safe_delete_message(bot, call.message.chat.id, fsm_data.pop("delete_messages_id", []))
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🗓 Выберите день для записи 🗓", reply_markup=zapis_data())

    fsm_data.setdefault("delete_messages_ids", []).append(msg.id)


    fsm_storage.set_data(
        call.message.chat.id,
        call.from_user.id,
        fsm_data,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('time_'))
def handle_time_selection(call):
    bot.answer_callback_query(call.id)
    fsm_data = fsm_storage.get_data(
        call.message.chat.id,
        call.from_user.id,
    )
    bulk_safe_delete_message(bot, call.message.chat.id, fsm_data.get("delete_messages_ids", []))
    selected_time = call.data[5:10]
    fsm_data["selected_time"] = selected_time
    fsm_data["selected_name_master"] = call.data[call.data.rfind('_') + 1:]



    keyboard_end = types.InlineKeyboardMarkup()
    button_next = types.InlineKeyboardButton('✅ Подтвердить', callback_data="next_button")
    keyboard_end.add(button_next)
    button_back = types.InlineKeyboardButton('❌ Назад', callback_data="end_button1")
    keyboard_end.add(button_back)

    time.sleep(0.2)
    msg = bot.send_message(call.message.chat.id, f'⌚️ Вы выбрали время {selected_time} ⌚️', reply_markup=keyboard_end)
    fsm_data.setdefault("delete_messages_id", []).append(msg.id)


    fsm_storage.set_data(
        call.message.chat.id,
        call.from_user.id,
        fsm_data,
    )


    dbworker.set_state(call.message.chat.id, config.States.S_ENTER_TOTAL.value)


@bot.callback_query_handler(func=lambda call: call.data == 'next_button' or call.data == 'end_button1')
def handle_time_selection(call):
    try:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=None)
    except telebot.apihelper.ApiTelegramException as e:
        # Игнорируем только конкретную ошибку "message is not modified"
        if "message is not modified" in str(e):
            print("Клавиатура уже удалена — пропускаем")
        else:
            raise  # пробросить другие ошибки



    # bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    time.sleep(0.3)
    if call.data == 'next_button':
        # fsm_data = fsm_storage.get_data(
        #     call.message.chat.id,
        #     call.from_user.id,
        #
        # )
        # bulk_safe_delete_message(bot, call.message.chat.id, fsm_data.pop("delete_messages_ids", []))
        # print(fsm_data.pop("delete_messages_ids", []), '@@@')
        bot.answer_callback_query(call.id)
        time.sleep(0.15)
        bot.send_message(call.message.chat.id, f'📲 Напишите ваш телефон:')
        dbworker.set_state(call.message.chat.id, config.States.S_ENTER_TEL.value)



    elif call.data == 'end_button1':
        bot.answer_callback_query(call.id)
        fsm_data = fsm_storage.get_data(
            call.message.chat.id,
            call.from_user.id,

        )
        bulk_safe_delete_message(bot, call.message.chat.id, fsm_data.pop("delete_messages_ids", []))
        bulk_safe_delete_message(bot, call.message.chat.id, fsm_data.pop("delete_messages_id", []))

        bot.answer_callback_query(call.id)

        all_t = fsm_data["all_time"]

        for employe_name, available_times in all_t.items():
            msg1 = bot.send_message(call.message.chat.id, employe_name + '👨🏽‍🔧',
                                    reply_markup=make_available_times_keyboard(employe_name, available_times))
            fsm_data.setdefault("delete_messages_ids", []).append(msg1.id)

        keyboard_end = types.InlineKeyboardMarkup()
        button_back = types.InlineKeyboardButton('Назад к выбору даты', callback_data="end_button")
        keyboard_end.add(button_back)
        msg = bot.send_message(call.message.chat.id, 'Выберите другое время', reply_markup=keyboard_end)
        fsm_data.setdefault("delete_messages_ids", []).append(msg.id)

        fsm_storage.set_data(
            call.message.chat.id,
            call.from_user.id,
            fsm_data,
        )

        dbworker.set_state(call.message.chat.id, config.States.S_ENTER_TIME.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ENTER_TEL.value)
def user_entering_tel(message):
    if (message.text.startswith('+') and message.text[1:].isdigit()) or message.text.isdigit():
        fsm_data = fsm_storage.get_data(
            message.chat.id,
            message.from_user.id,
        )

        fsm_data['input_phone'] = message.text
        fsm_storage.set_data(
            message.chat.id,
            message.from_user.id,
            fsm_data,
        )
        keyboard_end = types.InlineKeyboardMarkup()
        button_back = types.InlineKeyboardButton('✅ Подтвердить', callback_data="YES_button")
        keyboard_end.row(button_back)
        button_next = types.InlineKeyboardButton('❌ Изменить', callback_data="next_button")
        keyboard_end.add(button_next)

        time.sleep(0.15)
        msg = bot.send_message(message.chat.id, "Подтвердите ваш номер телефона", reply_markup=keyboard_end)
        fsm_data.setdefault("delete_messages_ids", []).append(msg.id)

        fsm_storage.set_data(
            message.chat.id,
            message.from_user.id,
            fsm_data,
        )
        dbworker.set_state(message.chat.id, config.States.S_SEND_PIC.value)
    else:
        bot.send_message(message.chat.id, "🚩 что-то пошло не так, попробуйте еще раз!")
        return


@bot.callback_query_handler(func=lambda call: call.data == ('YES_button'))
def get_phone_input(call):
    bot.answer_callback_query(call.id)
    fsm_data = fsm_storage.get_data(
        call.message.chat.id,
        call.from_user.id,
    )

    bulk_safe_delete_message(bot, call.message.chat.id, fsm_data.pop("delete_messages_ids", []))
    time.sleep(0.2)
    bot.send_message(call.message.chat.id, 'Прекрасно! 📝 Напишите ваше имя:')

    dbworker.set_state(call.message.chat.id, config.States.S_ENTER_NAME.value)



@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ENTER_NAME.value)
def get_name_input(message):
    fsm_data = fsm_storage.get_data(
        message.chat.id,
        message.from_user.id,
    )
    input_name = message.text
    fsm_data['input_name'] = input_name
    fsm_storage.set_data(
        message.chat.id,
        message.from_user.id,
        fsm_data,
    )

    print(fsm_data['selected_time'], 'selected_time')

    keyboard_end = types.InlineKeyboardMarkup()
    button_back = types.InlineKeyboardButton('✅ Подтвердить', callback_data="END_button")
    keyboard_end.row(button_back)
    button_next = types.InlineKeyboardButton('❌ Изменить', callback_data="next_name_button")
    keyboard_end.add(button_next)
    time.sleep(0.15)
    msg = bot.send_message(message.chat.id, "Подтвердите ваше имя:", reply_markup=keyboard_end)
    fsm_data.setdefault("delete_messages_ids", []).append(msg.id)

    fsm_storage.set_data(
        message.chat.id,
        message.from_user.id,
        fsm_data,
    )

    dbworker.set_state(message.chat.id, config.States.S_SEND_PIC.value)



@bot.callback_query_handler(func=lambda call: call.data == 'next_name_button' or call.data == 'END_button')
def handle_time_selection(call):

    fsm_data = fsm_storage.get_data(
        call.message.chat.id,
        call.from_user.id,
    )
    bulk_safe_delete_message(bot, call.message.chat.id, fsm_data.pop("delete_messages_ids", []))

    if call.data == 'next_name_button':
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📝 Напишите ваше имя:")
        dbworker.set_state(call.message.chat.id, config.States.S_ENTER_NAME.value)

    else:
        bot.answer_callback_query(call.id)

        selected_date = fsm_data["selected_total"]
        day, month = get_russian_date_info(selected_date)

        keyboard_end = types.InlineKeyboardMarkup()
        button_back = types.InlineKeyboardButton(f"☑ Подтвердить запись", callback_data="confirmation_button")
        keyboard_end.row(button_back)

        button_back = types.InlineKeyboardButton(f"❌ Отменить запись", callback_data="not_confirmation_button")
        keyboard_end.row(button_back)

        bot.send_message(call.message.chat.id, f"🚨 Остался последний шаг! 🚨\n\n🗒 Проверьте данные:\n\n"
            f"👨🏽‍🔧 мастер {fsm_data['selected_name_master']}\n"
            f"🗓 {fsm_data['selected_day']} {month} ({day})\n"
            f"🕒 {fsm_data['selected_time']}", reply_markup=keyboard_end)

        dbworker.set_state(call.message.chat.id, config.States.S_SEND_PIC.value)




@bot.callback_query_handler(func=lambda call: call.data in ['confirmation_button', 'not_confirmation_button'])
def handle_zapis(call):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton("Запись на шиномонтаж")
    keyboard.add(button1)

    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    bot.answer_callback_query(call.id)

    if call.data == 'confirmation_button':
        fsm_data = fsm_storage.get_data(
            call.message.chat.id,
            call.from_user.id,
        )

        msg = bot.send_message(call.message.chat.id, "Ожидайте...")
        fsm_data.setdefault("delete_messages_ids", []).append(msg.id)

        date_str = fsm_data["selected_total"].strftime("%Y-%m-%d")
        appointment_str = f'{date_str} {fsm_data["selected_time"]}'
        appointment_time = datetime.datetime.strptime(appointment_str, "%Y-%m-%d %H:%M")

        fsm_storage.add_data(call.from_user.id, call.message.chat.id, "data_total", appointment_time)
        time = fsm_data["selected_time"]

        #----------------------------------------------------

        # appointment_time = datetime.datetime(2025, 11, 23, 19, 35   )  # Воскресенье, 16:00
        # schedule_with_aps(call.message.chat.id, appointment_time, time)

        # -------------------------------

        schedule_with_aps(call.message.chat.id, fsm_storage.get_data(call.from_user.id, call.from_user.id)["data_total"], time)

        zapis_on_bt_end(
            fsm_data['selected_time'],
            fsm_data['selected_day'],
            fsm_data['selected_name_master'],
            fsm_data['input_name'],
            fsm_data['input_phone'],
        )

        keyboard_cancel = types.InlineKeyboardMarkup()
        button_back = types.InlineKeyboardButton(f"❌ Отменить запись ❌", callback_data="cancel")
        keyboard_cancel.row(button_back)

        selected_date = fsm_data["selected_total"]
        day, month = get_russian_date_info(selected_date)

        bulk_safe_delete_message(bot, call.message.chat.id, fsm_data.pop("delete_messages_ids", []))

        bot.send_message(
            call.message.chat.id,

            f"       ✔️ Запись подтверждена! ✔️\n\n"
            f"{fsm_data['input_name']}, Cпасибо за ваш выбор Baltshina 🛞 \n\n"
            f"✅ Вы записались:\n"
            f"     ▫️ Шиномонтаж\n\n"
            f""
            f"к мастеру {fsm_data['selected_name_master']}\n"
            f"👉 на {fsm_data['selected_day']} {month} ({day}) в {fsm_data['selected_time']}\n\n"
            f""
            f"*Baltshina*. Выполняем работу качественно.\n"
            f"ПН-ПТ: 9.30-18.00 \nСБ-ВС: 9.30-16.00\n\n"
            f""
            f"*Адрес: ул. Цветочная д. 18*\n"
            f"☎️ (812)611-10-66\n"
            f"    (812)324-40-99\n"
            f"📍наш caйт и on-line запись 24/7⬇\n"
            f"*https://baltshina.ru/zapis/?shag=1&mas=1\n\n\n\n"
            
            f""
            f""
            f"⭐️ Поддержка @kiriltyre ⭐️\n\n\n"
            f""
            f"Мы вас ждем!\n\n", reply_markup=keyboard)

        bot.send_message(call.message.chat.id, 'Чтобы отменить запись нажмите ниже', reply_markup=keyboard_cancel)

        # fsm_storage.set_data(
        #     call.message.chat.id,
        #     call.message.from_user.id,
        #     fsm_data,
        # )

        dbworker.set_state(call.message.chat.id, config.States.S_SEND_PIC_OUT.value)

    else:

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = KeyboardButton("Запись на шиномонтаж")
        keyboard.add(button1)
        bot.send_message(call.message.chat.id,
                         '✅ Запись отменена. ✅\n\nЕсли появится желаение записаться на шиномонтаж, нажми кнопку "Запись на шиномонтаж", чтобы начать.',
                         reply_markup=keyboard)
        dbworker.set_state(call.message.chat.id, config.States.S_TART.value)



@bot.callback_query_handler(func=lambda call: call.data == 'cancel' and dbworker.get_current_state(call.message.chat.id) != config.States.CANCEL.value)
def handle_cancel(call):
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)


    bot.answer_callback_query(call.id)
    fsm_data = fsm_storage.get_data(
        call.message.chat.id,
        call.from_user.id,
    )
    selected_date = fsm_data["selected_total"]
    day, month = get_russian_date_info(selected_date)


    bot.send_message(call.message.chat.id,'❌ Запись отменена. ❌\n\nЕсли появится желаение записаться на шиномонтаж, нажми кнопку "Запись на шиномонтаж", чтобы начать.')
    # bot.send_message(303325895, f"❌ Запись отменена ❌ \n\n\n{fsm_data['selected_day']} {month} ({day}) в {fsm_data['selected_time']}\n\nДанные клиента:\nНомер телефона: {fsm_data['input_phone']}\nИмя: {fsm_data['input_name']}\n\nВозможно, запись уже отменена, проверь⬇⬇⬇\n{'https://baltshina.ru/zapis/?shag=1&mas=1'}")
    # bot.send_message(1814986681, f"❌ Запись отменена ❌ \n\n\n{fsm_data['selected_day']} {month} ({day}) в {fsm_data['selected_time']}\n\nДанные клиента:\nНомер телефона: {fsm_data['input_phone']}\nИмя: {fsm_data['input_name']}\n\nВозможно, запись уже отменена, проверь⬇⬇⬇\n{'https://baltshina.ru/zapis/?shag=1&mas=1'}")
    # bot.send_message(1501918078, f"❌ Запись отменена ❌ \n\n\n{fsm_data['selected_day']} {month} ({day}) в {fsm_data['selected_time']}\n\nДанные клиента:\nНомер телефона: {fsm_data['input_phone']}\nИмя: {fsm_data['input_name']}\n\nВозможно, запись уже отменена, проверь⬇⬇⬇\n{'https://baltshina.ru/zapis/?shag=1&mas=1'}")

    dbworker.set_state(call.message.chat.id, config.States.CANCEL.value)



@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) in [config.States.S_SEND_PIC.value, config.States.S_TART.value, config.States.S_ENTER_DATA.value, config.States.S_ENTER_TIME.value, config.States.S_ENTER_TOTAL.value, config.States.S_SEND_PIC_OUT.value])
def get_name_input(message):
    bot.delete_message(message.chat.id, message.message_id)
    # bot.reply_to(message, 'Похоже вам что-то непонятно. Нажмите /help')





# Запуск бота
bot.infinity_polling()
