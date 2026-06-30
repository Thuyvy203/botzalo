import re
import json
import os
import config
from zlapi.models import Message

TRACKING_FILE = "minigame_data.json"
TARGET_BOX_ID = "1311505722605591852"

tracking_data = {}

def load_data():
    global tracking_data
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, "r", encoding="utf-8") as f:
            try: tracking_data = json.load(f)
            except: tracking_data = {}

def save_data():
    with open(TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(tracking_data, f, ensure_ascii=False, indent=2)

load_data()

def is_part_of_date_time(full_text, match_obj):
    """Kiểm tra xem số tìm được có phải ngày tháng/giờ không"""
    start, end = match_obj.start(), match_obj.end()
    # Kiểm tra ký tự ngay trước và ngay sau
    prev_char = full_text[start-1] if start > 0 else ""
    next_char = full_text[end] if end < len(full_text) else ""
    
    if prev_char in "/:" or next_char in "/:":
        return True
    return False

def process_number_message(message_object, author_id, thread_id):
    t_id = str(thread_id)
    if t_id != TARGET_BOX_ID: return
    if t_id not in tracking_data or not tracking_data[t_id].get("is_active"): return

    content = message_object.get("content", "")
    if not content: return

    # Tìm các vị trí số kèm theo đối tượng match để check vị trí
    matches = re.finditer(r'\d+', content)
    conf = tracking_data[t_id]
    has_new_update = False
    
    for m in matches:
        if is_part_of_date_time(content, m): continue
            
        try:
            num = int(m.group())
            if conf["min"] <= num <= conf["max"]:
                if num not in conf["picked_numbers"]:
                    conf["picked_numbers"].append(num)
                    has_new_update = True
        except: continue

    if has_new_update:
        conf["picked_numbers"].sort()
        save_data()

def handle_number_command(message, thread_id, thread_type, author_id, client):
    msg_lower = message.strip().lower()
    t_id = str(thread_id)
    admin_ids = getattr(config, 'ADMIN', [])
    if str(author_id) not in admin_ids: return

    if msg_lower.startswith("!so start"):
        parts = re.findall(r'\d+', message)
        try:
            v_min, v_max = int(parts[-2]), int(parts[-1])
            tracking_data[TARGET_BOX_ID] = {"is_active": True, "min": v_min, "max": v_max, "picked_numbers": []}
            save_data()
            client.sendMessage(Message(f"🎮 Đã bật quét số cho Box: {TARGET_BOX_ID}\nKhoảng: {v_min} - {v_max}"), thread_id, thread_type)
        except:
            client.sendMessage(Message("⚠️ Lỗi! Cú pháp: !so start <min> <max>"), thread_id, thread_type)

    elif msg_lower == "!so con":
        if TARGET_BOX_ID not in tracking_data:
            client.sendMessage(Message("❌ Box chưa bật quét."), thread_id, thread_type)
            return
        conf = tracking_data[TARGET_BOX_ID]
        all_range = set(range(conf["min"], conf["max"] + 1))
        picked = set(conf["picked_numbers"])
        missing = sorted(list(all_range - picked))
        count_missing = len(missing)
        text_missing = ", ".join(map(str, missing[:150]))
        res = f"📊 SỐ CHƯA NHẮN (Box: {TARGET_BOX_ID})\n🎯 Khoảng: {conf['min']}-{conf['max']}\n✅ Đã có: {len(picked)} số\n❌ Còn trống ({count_missing} số):\n{text_missing}"
        if count_missing > 150: res += "\n...(còn nhiều)..."
        client.sendMessage(Message(res), thread_id, thread_type)

    elif msg_lower.startswith("!so add"):
        if TARGET_BOX_ID not in tracking_data:
            client.sendMessage(Message("❌ Hãy dùng !so start trước!"), thread_id, thread_type)
            return

        conf = tracking_data[TARGET_BOX_ID]
        matches = re.finditer(r'\d+', message)
        
        added_count = 0
        for m in matches:
            if is_part_of_date_time(message, m): continue
                
            try:
                num = int(m.group())
                if conf["min"] <= num <= conf["max"]:
                    if num not in conf["picked_numbers"]:
                        conf["picked_numbers"].append(num)
                        added_count += 1
            except: continue
        
        if added_count > 0:
            conf["picked_numbers"].sort()
            save_data()
            client.sendMessage(Message(f"📥 Đã bổ sung xong {added_count} số từ lịch sử."), thread_id, thread_type)
        else:
            client.sendMessage(Message("⚠️ Không tìm thấy số mới hợp lệ."), thread_id, thread_type)

    elif msg_lower == "!so reset":
        if TARGET_BOX_ID in tracking_data:
            del tracking_data[TARGET_BOX_ID]
            save_data()
            client.sendMessage(Message("🗑️ Đã xóa dữ liệu minigame."), thread_id, thread_type)

def get_mitaizl():
    return {'process': process_number_message, 'handle': handle_number_command}