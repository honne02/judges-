from bs4 import BeautifulSoup
import requests
import time
from pathlib import Path
import json
import uuid
import random
import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
import config

def uniqueid():
    return time.time() * random.randint(2, 273) % 150


def convert_to_preferred_format(sec):
    sec = sec % (24 * 3600)
    hour = sec // 3600
    sec %= 3600
    min = sec // 60
    sec %= 60
    return "%02d:%02d:%02d" % (hour, min, sec)


def parse_client():
    URL = 'https://api.remanga.org/api/titles/last-chapters/?publisher=3173&page=1'
    responce = requests.get(URL)
    data = responce.json()
    titl = [{
        'id': str(x['id']) + x['chapter'],
        'titles': x['rus_name'],
        'date': x['upload_date'],
        'chapter': x['chapter']
    } for x in data['content']]
    return titl


def check_titles_already_added(titles) -> list:
    with open(added_titles_file, "r") as json_file:
        new_titles = []
        data = json.load(json_file)
        list_of_id = [i["id"] for i in data]
        if data:
            for k, v in enumerate(titles):
                if v.get("id") not in list_of_id:
                    new_titles.append(v)
        else:
            new_titles = titles
    if new_titles:
        print(f"INFO - Found {len(new_titles)} new titles")
    return new_titles


def start_countdown(t) -> None:
    while t:
        mins = t // 60
        secs = t % 60
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print("Next check will happen after", timer,
              end="\r")  # overwrite previous line
        time.sleep(1)
        t -= 1
    print(" " * 35, end="\r")


def is_title_already_added(title):
    """Chech is that title in json file"""
    with open(added_titles_file, "r") as json_file:
        data = json.load(json_file)
        list_of_id = [i["id"] for i in data]
        if data:
            if title.get("id") not in list_of_id:
                return False
            else:
                return True
        else:
            return False


def add_to_json(title) -> None:
    """Add title to monitor.json so as not add again and check is that title in json to not add it again"""
    is_added = is_title_already_added(title)
    if not is_added:
        with open(added_titles_file, "r") as file:
            data = json.load(file)
            json_data = {
                "id": title.get("id"),
                "titles": title.get("titles"),
                "date": title.get("date"),
                "chapter": title.get("chapter")
            }
            data.append(json_data)
            with open(added_titles_file, "w") as file:
                json.dump(data, file, indent=4)


def create_title(title):
    # TODO:
    try:
        with open('data.json', 'r',
                  encoding='utf-8') as fh:  # открываем файл на чтение
            data = json.load(fh)  # загружаем из файла данные в словарь data
        vk_session = vk_api.VkApi(config.login_vk, config.pass_vk)
        vk_session.auth()
        vk = vk_session.get_api()
        for i in data:
            if title['titles'] == i['name']:
                vk.wall.post(
                    owner_id=config.vk_group_id,
                    from_group=1,
                    message=i['post'],
                    attachments=i['pic']
            )
        add_to_json(title)
    except:
        print("НЕ ПОЛУЧИЛОСЬ с "+title['titles'])


added_titles_file = Path('monitor.json')
added_titles_file.touch(exist_ok=True)
json_file_data = []
if added_titles_file.stat().st_size == 0:
    with open(added_titles_file, "w", encoding='utf-8') as file:
        json.dump(json_file_data, file)
current_monitored_list = []
last_monitored_list = []

while True:
    monitor_title_list = parse_client()
    new_titles_list = check_titles_already_added(monitor_title_list)
    if new_titles_list:
        for k, v in enumerate(new_titles_list):
            print(f"INFO - Adding title {k + 1}")
            create_title(v)
    else:
        print("Nothing new")
    start_countdown(60)
