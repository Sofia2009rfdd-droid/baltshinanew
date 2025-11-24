from datetime import date, time
from datetime import datetime
from requests import post
from telebot.apihelper import ApiTelegramException
import datetime
from telebot import types
from collections import defaultdict
from bs4 import BeautifulSoup
import time
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


service = Service(ChromeDriverManager().install())
options = Options()
def zapis_on_bt_end(t_ime, day, name_master, user_name, phone):
    pass
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    #
    #
    #
    #
    # # browser = webdriver.Chrome(service=service, options=options)
    # browser = webdriver.Chrome(service=service, options=chrome_options)
    # # Открытие веб-страницы
    # browser.get('https://baltshina.ru/zapis/?shag=1&mas=1')
    # # Явное ожидание для поиска элементов
    # wait = WebDriverWait(browser, 20)
    # # Телефон и имя
    # elem1 = wait.until(EC.visibility_of_element_located((By.NAME, 'name')))
    # elem2 = wait.until(EC.visibility_of_element_located((By.NAME, 'tel')))
    # elem1.clear()
    # elem1.send_keys(user_name)  # Ваше имя
    # elem2.clear()
    # elem2.send_keys(phone)  # Ваш телефон
    # # Число
    # TARGET_DAY = day
    # if TARGET_DAY < datetime.date.today().day:
    #     NEXT_MONTH_BUTTON_XPATH = "//a[@title='Next']"
    #     next_month_button = wait.until(EC.element_to_be_clickable((By.XPATH, NEXT_MONTH_BUTTON_XPATH)))
    #     next_month_button.click()
    #     time.sleep(0.7)
    # day_link = browser.find_element(By.XPATH, f"//div[@id='datepicker-inline']//a[text()='{TARGET_DAY}']")
    # day_link.click()
    # # Время и мастер
    # TARGET_MASTER = name_master
    # TARGET_TIME = t_ime
    # time_radio_xpath = (
    #     f"//div[@id='interval'][.//h2[text()='{TARGET_MASTER}']]"
    #     f"/div/label[contains(., '{TARGET_TIME}')]"
    #     f"/input[@type='radio' and @name='timei' and not(@disabled)]"
    # )
    # time_slot_radio = wait.until(EC.element_to_be_clickable((By.XPATH, time_radio_xpath)))
    # time_slot_radio.click()
    # print(f"Время {TARGET_TIME} для мастера {TARGET_MASTER} выбрано.")
    # # Кнопка записаться
    # submit_button = wait.until(
    #     EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Записаться']"))
    # )
    # submit_button.click()
    # print("Кнопка 'Записаться' нажата.")
    # # time.sleep(10)
    # browser.quit()


def zapis_data():
    today = datetime.date.today()
    keyboard = types.InlineKeyboardMarkup()
    for i in range(7):
        date = today + datetime.timedelta(days=i)
        day, month = get_russian_date_info(date)
        button = types.InlineKeyboardButton(f"{date.day} {month} ({day})", callback_data=f"button{i}")
        keyboard.add(button)
    return keyboard


def get_russian_date_info(selected_date):
    # Получаем сегодняшнюю дату
    today = datetime.date.today()

    # Получаем индекс дня недели (0 - понедельник, 6 - воскресенье)
    day_of_week_index = selected_date.weekday()

    # Массив дней недели на русском
    days_of_week_russian = [
        "понедельник",  # 0
        "вторник",     # 1
        "среда",       # 2
        "четверг",     # 3
        "пятница",      # 4
        "суббота",     # 5
        "воскресенье"  # 6
    ]


    # Получаем название дня недели на русском
    day_of_week_russian = days_of_week_russian[day_of_week_index]

    # Получаем индекс месяца
    month_index = selected_date.month

    # Массив названий месяцев на русском
    months_russian = [
                "января",   # 1
                "февраля",  # 2
                "марта",    # 3
                "апреля",   # 4
                "мая",      # 5
                "июня",     # 6
                "июля",     # 7
                "августа",  # 8
                "сентября", # 9
                "октября",  # 10
                "ноября",   # 11
                "декабря"   # 12
            ]

    # Получаем название месяца на русском
    month_name_russian = months_russian[month_index - 1]
    # Проверяем, является ли выбранная дата сегодняшней или завтрашней
    if selected_date == today:
        return "сегодня", month_name_russian
    elif selected_date == today + datetime.timedelta(days=1):
        return "завтра", month_name_russian

    return day_of_week_russian, month_name_russian




def get_available_times(date: date):
    response = post(
        "https://baltshina.ru/zapis/interval.php",
        data=f"date={date.isoformat()}^&id=1",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    inter = response.json()["inter"]
    if "Нет свободных мест" in inter:
        return []


    soup = BeautifulSoup(inter, 'html.parser')
    available_times = defaultdict(list)
    employee_divs = soup.find_all('div', style="width: 150px;float: left;")
    for employee_div in employee_divs:
        name = employee_div.find('h2').text.strip()
        labels = employee_div.find_all('label')
        for label in labels:
            if any(map(lambda x: "background-color:#C00" in x, label.get_attribute_list("style"))):
                continue
            time_text = label.get_text(strip=True)
            input_element = label.find('input')
            if input_element:
                time_value = input_element['value']
                available_times[name].append(time_text)
    print('Данные с сайта успешно спарсины функцией get_available_times')
    print(available_times)
    return available_times




def make_available_times_keyboard(employe_name: str, available_times: list[str]):
    if available_times:
        markup = types.InlineKeyboardMarkup()
        buttons = []
        for available_time in available_times:
            button = types.InlineKeyboardButton(text=available_time, callback_data=f'time_{available_time}_{employe_name}')
            buttons.append(button)
        for i in range(0, len(buttons), 2):
            markup.row(*buttons[i:i + 2])
        return markup






def safe_delete_message(bot, chat_id, msg_id):
    try:
        bot.delete_message(chat_id, msg_id)
    except ApiTelegramException as error:
        if "delete not found" not in error.description:
            raise



def bulk_safe_delete_message(bot, chat_id, msg_ids):
    for msg_id in msg_ids:
        safe_delete_message(bot, chat_id, msg_id)
