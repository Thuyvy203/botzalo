import json
import os

USER_INFO_FILE = "user_info.json"

def register_user(message_object, author_id, client):
    # Nếu file user_info.json chưa tồn tại, tạo file rỗng
    if not os.path.exists(USER_INFO_FILE):
        with open(USER_INFO_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    # Đọc dữ liệu từ file
    with open(USER_INFO_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_id = str(author_id)
    # Nếu chưa có thông tin, lưu thông tin cơ bản từ message_object
    if user_id not in data:
        data[user_id] = {"name": message_object.get("dName", "Unknown")}
        with open(USER_INFO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def load_user_info():
    if not os.path.exists(USER_INFO_FILE):
        return {}
    with open(USER_INFO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_mitaizl():
    return {
        'user_info': register_user
    }
