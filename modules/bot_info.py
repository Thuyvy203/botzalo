import json
import re
from zlapi import ZaloAPI
from threading import Thread
from zlapi.models import *
import time

SETTING_FILE = 'setting.json'
CONFIG_FILE = 'config.json'

def load_message_log():
    """Đọc thông tin tin nhắn từ file settings.json."""
    try:
        with open(SETTING_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            return settings.get("message_log", {})
    except FileNotFoundError:
        return {}

def save_message_log(message_log):
    """Lưu thông tin tin nhắn vào file settings.json."""
    try:
        with open(SETTING_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {}

    settings["message_log"] = message_log
    with open(SETTING_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def get_content_message(message_object):
    if message_object.msgType == 'chat.sticker':
        return ""
    content = message_object.content
    if isinstance(content, dict) and 'title' in content:
        text_to_check = content['title']
    else:
        text_to_check = content if isinstance(content, str) else ""
    return text_to_check

def is_url_in_message(message_object):
    if message_object.msgType == 'chat.sticker':
        return False
    content = message_object.content
    if isinstance(content, dict) and 'title' in content:
        text_to_check = content['title']
    else:
        text_to_check = content if isinstance(content, str) else ""
    url_regex = re.compile(
        r'http[s]?://' 
        r'(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|' 
        r'(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    if re.search(url_regex, text_to_check):
        return True
    return False

def is_spamming(author_id, thread_id):
    max_messages = 15  
    time_window = 2
    min_interval = 2  
    message_log = load_message_log()
    key = f"{thread_id}_{author_id}"
    current_time = time.time()
    if key in message_log:
        user_data = message_log[key]
        last_message_time = user_data['last_message_time']
        message_times = user_data['message_times']
        if current_time - last_message_time < min_interval:
            recent_messages = [t for t in message_times if current_time - t <= min_interval]
            if len(recent_messages) >= 10:
                return True  
        message_times = [t for t in message_times if current_time - t <= time_window]
        message_times.append(current_time)
        message_log[key] = {
            'last_message_time': current_time,
            'message_times': message_times
        }
        if len(message_times) > max_messages:
            return True  
    else:
        message_log[key] = {
            'last_message_time': current_time,
            'message_times': [current_time]
        }
    save_message_log(message_log)
    return False 

def get_group_members(bot, group_id):
    """
    Lấy thông tin thành viên của nhóm từ Zalo API.
    Nếu đối tượng bot không có phương thức get_group_members, tạo đối tượng ZaloAPI riêng để lấy thông tin.
    Điều chỉnh lại phần này cho phù hợp với API thực tế của bạn.
    """
    try:
        if hasattr(bot, "get_group_members"):
            members = bot.get_group_members(group_id)
        else:
            # Nếu bot không có phương thức này, sử dụng ZaloAPI
            from zlapi import ZaloAPI
            api = ZaloAPI()  # Cấu hình nếu cần
            members = api.get_group_members(group_id)
        return members
    except Exception as e:
        print(f"[ERROR] Lỗi khi lấy thông tin thành viên của nhóm {group_id}: {e}")
        return []

def read_settings():
    """Đọc toàn bộ nội dung từ file JSON."""
    try:
        with open(SETTING_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def write_settings(settings):
    """Ghi toàn bộ nội dung vào file JSON."""
    with open(SETTING_FILE, 'w', encoding='utf-8') as file:
        json.dump(settings, file, ensure_ascii=False, indent=4)

def load_config():
    """Đọc cấu hình từ file JSON và trả về các giá trị cấu hình."""
    try:
        with open(CONFIG_FILE, 'r') as file:
            config = json.load(file)
            imei = config.get('imei')
            session_cookies = config.get('cookies')
            return imei, session_cookies
    except FileNotFoundError:
        print(f"Error: File {CONFIG_FILE} not found.")
        return None, None
    except json.JSONDecodeError:
        print(f"Error: File {CONFIG_FILE} contains invalid JSON.")
        return None, None

def is_admin(author_id):
    settings = read_settings()
    admin_bot = settings.get("admin_bot", [])
    return author_id in admin_bot

def handle_bot_admin(bot):
    settings = read_settings()
    admin_bot = settings.get("admin_bot", [])
    if bot.uid not in admin_bot:
        admin_bot.append(bot.uid)
        settings['admin_bot'] = admin_bot
        write_settings(settings)
        print(f"Đã thêm 👑{get_user_name_by_id(bot, bot.uid)} 🆔 {bot.uid} cho lần đầu tiên khởi động vào danh sách Admin")

def get_allowed_thread_ids():
    """Lấy danh sách các thread ID được phép từ setting.json."""
    settings = read_settings()
    return settings.get('allowed_thread_ids', [])

def get_allow_link_status(thread_id):
    settings = read_settings()
    if 'allow_link' in settings:
        return settings['allow_link'].get(thread_id, False)
    else:
        return False

def get_user_name_by_id(bot, author_id):
    try:
        user = bot.fetchUserInfo(author_id).changed_profiles[author_id].displayName
        return user
    except:
        return "Unknown User"

def extract_uids_from_mentions(message_object):
    uids = []
    if message_object.mentions:
        uids = [mention['uid'] for mention in message_object.mentions if 'uid' in mention]
    return uids

# Xử lý lệnh bot
def handle_bot_command(message, message_object, thread_id, thread_type, author_id, bot):
    def send_bot_response():
        try:
            parts = message_object.content.split()
            if len(parts) == 1:
                response = "🌊 BOT ZALO ┇ Chào mừng 💤 💞 🌸"
            else:
                action = parts[1].lower()
                if action == 'on':
                    if not is_admin(author_id):
                        response = "➜ Không có quyền"
                    elif thread_type != ThreadType.GROUP:
                        response = "➜ Chỉ dùng trong box ⚡"
                    else:
                        response = bot_on_group(bot, thread_id)
                elif action == 'off':
                    if not is_admin(author_id):
                        response = "➜ Không có quyền"
                    elif thread_type != ThreadType.GROUP:
                        response = "➜ Chỉ dùng trong box ⚡"
                    else:
                        response = bot_off_group(bot, thread_id)
                elif action == 'info':
                    response = f"➜ 💻 Phiên bản: 1.0.2\n➜ 👨‍💻 Tác giả: Bơ\n"
                else:
                    response = "➜ Lệnh không được hỗ trợ"
            if response:
                bot.replyMessage(Message(text=f"{response}"), message_object, thread_id=thread_id, thread_type=thread_type)
        except Exception as e:
            print(f"Error: {e}")
            bot.replyMessage(Message(text="➜ 🐞 Đã xảy ra lỗi gì đó 🐶"), message_object, thread_id=thread_id, thread_type=thread_type)
    thread = Thread(target=send_bot_response)
    thread.start()

def get_mitaizl():
    return {
        'bot': handle_bot_command
    }
