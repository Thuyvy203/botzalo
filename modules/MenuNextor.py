import os
import importlib
import random
from zlapi.models import Message

des = {
    'version': "1.0.2",
    'credits': "Dang Quang Huy",
    'description': "Xem toàn bộ lệnh hiện có của bot"
}

# Danh sách các emoji
emojis = ['❤️‍🔥', '💨', '✨', '💦', '🎶', '⚡', '🌏', '🌊', '💌', '☃️', '🎡', '⛈️', '💢', '🌌', '💝', '🌋', '🌪️', '☔', '🌦️', '🏔️', '🌧️', '🚀', '🐲', '🧸', '📲', '💩', '💨', '✨', '💟', '🏵️', '🏞️', '🌠', '🛸', '💎', '⭐', '☄️', '🧊', '🍡', '🎮', '🎵', '🔮', '🇻🇳', '☠️', '🤍', '🐟', '💻', '🥳', '🐰']

def get_all_mitaizl():
    mitaizl = {}

    for module_name in os.listdir('modules'):
        if module_name.endswith('.py') and module_name != '__init__.py':
            module_path = f'modules.{module_name[:-3]}'
            module = importlib.import_module(module_path)

            if hasattr(module, 'get_mitaizl'):
                module_mitaizl = module.get_mitaizl()
                mitaizl.update(module_mitaizl)

    command_names = list(mitaizl.keys())
    
    return command_names

def handle_menu_command(message, message_object, thread_id, thread_type, author_id, client):
    command_names = get_all_mitaizl()
    total_mitaizl = len(command_names)
    
    # Thêm emoji ngẫu nhiên vào trước mỗi lệnh
    numbered_mitaizl =  [f"➜ {random.choice(emojis)} {name}" for i, name in enumerate(command_names)]
    menu_message = f"🎮 T1FEED 🎮  \nCó tổng cộng {total_mitaizl} lệnh ᰔᩚ\nSau đây là các lệnh chi tiết /-li \n" + "\n".join(numbered_mitaizl)

    message_to_send = Message(text=menu_message)

    client.replyMessage(message_to_send, message_object, thread_id, thread_type)

def get_mitaizl():
    return {
        'menu': handle_menu_command
    }