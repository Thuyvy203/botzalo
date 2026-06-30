from zlapi.models import Message
import time
import requests

start_time = time.time()

def handle_uptime_command(message, message_object, thread_id, thread_type, author_id, client):
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)

    days = uptime_seconds // (24 * 3600)
    uptime_seconds %= (24 * 3600)
    hours = uptime_seconds // 3600
    uptime_seconds %= 3600
    minutes = uptime_seconds // 60
    seconds = uptime_seconds % 60

    uptime_message = f"Bot đã hoạt động được {days} ngày, {hours} giờ, {minutes} phút, {seconds} giây."
    
    message_to_send = Message(text=uptime_message)
    client.sendMessage(message_to_send, thread_id, thread_type)
    

def get_mitaizl():
    return {
        'uptime': handle_uptime_command
    }
