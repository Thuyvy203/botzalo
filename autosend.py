from zlapi.models import Message
import requests
import random
import threading
import time

des = {
    'version': "1.0.2",
    'credits': "Nguyễn Đức Tài",
    'description': "Tự độngứi video gái"
}

autosend_threads = {}

def handle_autosend_command(message, message_object, thread_id, thread_type, author_id, client):    
    if message.text.lower() == 'autosend on':
        if thread_id not in autosend_threads:
            autosend_threads[thread_id] = threading.Thread(target=autosend, args=(thread_id, thread_type, client))
            autosend_threads[thread_id].start()
            client.sendMessage(Message(text="Autosend đã bật!"), thread_id, thread_type)
        else:
            client.sendMessage(Message(text="Autosend đã được bật trong nhóm này!"), thread_id, thread_type)

    elif message.text.lower() == 'autosend off':
        if thread_id in autosend_threads:
            autosend_threads[thread_id].do_run = False
            del autosend_threads[thread_id]
            client.sendMessage(Message(text="Autosend đã tắt!"), thread_id, thread_type)
        else:
            client.sendMessage(Message(text="Autosend chưa được bật trong nhóm này!"), thread_id, thread_type)

def autosend(thread_id, thread_type, client):
    thread = threading.currentThread()
    thread.do_run = True
    while getattr(thread, "do_run", True):
        try:
            listvd = "https://run.mocky.io/v3/c5d65f19-6369-46e9-9a73-68c2d312f1b8"
            response = requests.get(listvd)
            response.raise_for_status()
            urls = response.json()
            video_url = random.choice(urls)

            image_list_url = "https://run.mocky.io/v3/795d39c1-a370-44b8-a2dd-bfd88e41c348"
            response = requests.get(image_list_url)
            response.raise_for_status()
            json_data = response.json()
            image_url = random.choice(json_data) if isinstance(json_data, list) else json_data.get('url')

            client.sendRemoteVideo(
                video_url, 
                image_url,
                duration='1000',
                message=None,
                thread_id=thread_id,
                thread_type=thread_type,
                width=1080,
                height=1920
            )
        except Exception as e:
            error_message = Message(text=f"Đã xảy ra lỗi: {str(e)}")
            client.sendMessage(error_message, thread_id, thread_type)
        time.sleep(1800)  # Sleep for 30 minutes

def get_mitaizl():
    return {
        'autosend': handle_autosend_command
    }
