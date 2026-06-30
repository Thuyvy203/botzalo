from dotenv import load_dotenv
load_dotenv()

import os
import time
import requests
import re
import json
import random
import threading
import sys
import traceback
from datetime import datetime
from colorama import Fore, Style, init

# --- FIX GIỜ HỆ THỐNG ---
os.environ['TZ'] = 'Asia/Ho_Chi_Minh'
try:
    time.tzset()
    print("✅ Đã chuyển giờ hệ thống sang Việt Nam (UTC+7)")
except AttributeError:
    pass

from config import API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES, PREFIX
from mitaizl import CommandHandler
from zlapi import ZaloAPI
from zlapi.models import Message, ThreadType
from modules.bot_info import *
from modules.da import welcome
from modules.checktt import record_message, handle_checktt_command, set_client, start_scheduler
from modules.tag_conversation import handle_conversational_tag
from modules.math_calculator import get_mitaizl as get_math_handler
from modules.number_tracker import get_mitaizl as get_number_tracker_module
from modules.spam import get_mitaizl as get_spam_module

init(autoreset=True)
spam_handler = get_spam_module().get('spam')

# =================================================================
# ⚙️ CẤU HÌNH ADMIN & MUTE BOX
# =================================================================
ADMIN_UID = "9123173293216833155" # ID của Bơ
MUTED_FILE = "muted_groups.json"

def load_muted():
    if os.path.exists(MUTED_FILE):
        try:
            with open(MUTED_FILE, 'r') as f: return json.load(f)
        except: return []
    return []

def save_muted(data):
    try:
        with open(MUTED_FILE, 'w') as f: json.dump(data, f)
    except: pass

# =================================================================
# 🎨 HỆ THỐNG CONSOLE MÀU NEON & CACHE TÊN
# =================================================================
JOB_COLORS = [
    "00FFFF", "FF00FF", "FFFF00", "00FF00", "FF9900", "FF3399", 
    "99FF33", "33CCFF", "FF66CC", "66FF66", "FFCC00", "00FFCC", 
    "FF0099", "CCFF00", "FFB6C1", "E0FFFF", "7DF9FF", "F0E68C"
]

def rgb_text(text, hex_code):
    try:
        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        return f"\033[38;2;{r};{g};{b}m{text}\033[0m"
    except:
        return text

def get_vietnamese_time():
    now = datetime.now()
    days = {0: "Thứ Hai", 1: "Thứ Ba", 2: "Thứ Tư", 3: "Thứ Năm", 4: "Thứ Sáu", 5: "Thứ Bảy", 6: "Chủ Nhật"}
    weekday = days[now.weekday()]
    return now.strftime(f"{weekday}, ngày %d tháng %m năm %Y %H:%M")

group_name_cache = {}
user_name_cache = {}

# =================================================================
# 💬 DATA CHÀO HỎI PHONG PHÚ
# =================================================================
GREETING_DATA = {
    "morning": ["Chào buổi sáng {name}! ☀️", "Hế lô {name}, ngày mới tốt lành nhaaa ✨", "Morning {name}! 🌤️"],
    "noon": ["Trưa rồi {name} ơi, nhớ ăn cơm đầy đủ nha 🍚", "Trưa vui vẻ nha {name}!"],
    "afternoon": ["Chiều mát mẻ nhé {name} 🌬️", "Buổi chiều vui vẻ nha {name}!"],
    "evening": ["Chào buổi tối {name}! 🌙", "Tối ấm áp bên gia đình nha {name} ❤️"],
    "night": ["Khuya rồi {name} chưa ngủ hả? 🦉", "Giờ này còn online hả {name}? Đi ngủ đi nè 🛌"]
}

GOODBYE_DATA = ["Tạm biệt {name}, hẹn gặp lại nha 👋", "Pái pai {name}, mình đi đây 🏃"]
SLEEP_DATA = ["Chúc {name} ngủ ngon mơ đẹp 💤", "G9 {name}, mơ về crush nhé 🌙"]

# =================================================================

class Client(ZaloAPI):
    def __init__(self, api_key, secret_key, imei, session_cookies):
        super().__init__(api_key, secret_key, imei=imei, session_cookies=session_cookies)
        handle_bot_admin(self)
        self.version = 1.1
        self.me_name = "Bot by Bơ"
        self.command_handler = CommandHandler(self)

    def onEvent(self, event_data, event_type):
        try:
            muted_groups = load_muted()
            if str(event_data.get('groupId')) in muted_groups:
                return
            welcome(self, event_data, event_type)
        except Exception as e:
            pass

    # BỌC TRY-EXCEPT TOÀN BỘ ĐỂ CHỐNG ĐỨNG BOT
    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        try:
            self._process_message(mid, author_id, message, message_object, thread_id, thread_type)
        except Exception as e:
            print(rgb_text(f"⚠️ Đã chặn một lỗi làm sập Bot: {e}", "FF0000"))
            traceback.print_exc()

    def _process_message(self, mid, author_id, message, message_object, thread_id, thread_type):
        if str(author_id) == str(self.uid): return

        # =======================================================
        # 🔥 BỘ LỌC THÔNG MINH (TRỊ BỆNH MÙ CHỮ) 🔥
        # =======================================================
        msg_type = "1"
        if isinstance(message_object, dict):
            msg_type = str(message_object.get("msgType", "1"))
        else:
            msg_type = str(getattr(message_object, "msgType", "1"))
            
        if msg_type in ["31", "32", "14"]:
            return 
        if msg_type.isdigit() and int(msg_type) >= 1000:
            return
        # =======================================================

        # --- 1. XỬ LÝ NỘI DUNG AN TOÀN ---
        if not isinstance(message, str): 
            msg_content = getattr(message, "content", "")
        else: 
            msg_content = message
            
        if msg_content is None: msg_content = ""
        else: msg_content = str(msg_content)

        if not msg_content.strip(): 
            msg_content = "Ảnh, video hoặc kí tự đặc biệt"

        msg_lower = msg_content.lower().strip()
        clean_msg = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\ufeff]', '', msg_lower).strip()

        if clean_msg == "đã thu hồi tin nhắn" or clean_msg == "đã gỡ một tin nhắn":
            return
        if "đã bình chọn" in clean_msg or clean_msg.startswith("[bình chọn]"):
            return

        # =======================================================
        # 🔥 LOGIC LẤY TÊN NGƯỜI DÙNG (CÓ TRA CỨU API) 🔥
        # =======================================================
        user_name = ""
        if isinstance(message_object, dict):
            user_name = message_object.get("dName", "")
        else:
            user_name = getattr(message_object, "dName", "")

        if not user_name or user_name == "Người dùng":
            if author_id in user_name_cache:
                user_name = user_name_cache[author_id]
            else:
                try:
                    u_info = self.fetchUserInfo(author_id)
                    if isinstance(u_info, dict) and 'changed_profiles' in u_info:
                        profile = u_info['changed_profiles'].get(str(author_id), {})
                        user_name = profile.get('zaloName') or profile.get('displayName') or profile.get('dName', '')
                    
                    if user_name:
                        user_name_cache[author_id] = user_name
                    else:
                        user_name = f"User_{str(author_id)[-4:]}"
                except:
                    user_name = f"User_{str(author_id)[-4:]}"

        # =======================================================
        # 🔥 LOGIC LẤY TÊN NHÓM (FIX LỖI THREAD_TYPE) 🔥
        # =======================================================
        name_box = "Đang tải..."
        is_group = (thread_type == ThreadType.GROUP or "GROUP" in str(thread_type).upper() or str(thread_type) == "2")
        
        if is_group:
            if thread_id in group_name_cache:
                name_box = group_name_cache[thread_id]
            else:
                try:
                    group_info = self.fetchGroupInfo(thread_id)
                    if isinstance(group_info, dict):
                        fetched_name = group_info.get('name') or group_info.get('gName')
                        if not fetched_name:
                             grid_map = group_info.get('gridInfoMap', {})
                             current_info = grid_map.get(str(thread_id), {})
                             fetched_name = current_info.get('name')
                        
                        if fetched_name:
                            name_box = fetched_name
                            group_name_cache[thread_id] = fetched_name
                        else:
                            name_box = "Nhóm không tên"
                except:
                    name_box = "Lỗi API Nhóm"
        else:
            name_box = "Chat Riêng (DM)"

        time_str = get_vietnamese_time()
        c = [random.choice(JOB_COLORS) for _ in range(8)]

        # --- 2. IN CONSOLE ---
        print(rgb_text(f"[💓]→ Tên nhóm: {name_box}", c[0]))
        print(rgb_text(f"[🔎]→ ID nhóm: {thread_id}", c[1]))
        print(rgb_text(f"[🔱]→ Tên người dùng: {user_name}", c[2]))
        print(rgb_text(f"[📝]→ ID người dùng: {author_id}", c[3]))
        print(rgb_text(f"[📩]→ Nội dung: {msg_content}", c[4]))
        print(rgb_text(f"[ {time_str} ]", c[5]))
        print(rgb_text(f"◆━━━━━━━━━◆Bơ◆━━━━━━━━◆", c[6]))
        print("")

        # =======================================================
        # 🔥 LỆNH QUẢN LÝ HOẠT ĐỘNG BOT (CHỈ ADMIN) 🔥
        # =======================================================
        muted_groups = load_muted()

        if clean_msg.startswith(f"{PREFIX}botoff") or clean_msg.startswith("!botoff"):
            if str(author_id) == ADMIN_UID:
                if str(thread_id) not in muted_groups:
                    muted_groups.append(str(thread_id))
                    save_muted(muted_groups)
                    self.sendMessage(Message(text="Bot đã TẮT hoạt động tại nhóm này 🔇"), thread_id, thread_type)
                else:
                    self.sendMessage(Message(text="Bot đang tắt ở nhóm này rồi mà! 🤫"), thread_id, thread_type)
            else:
                self.sendMessage(Message(text="⚠️ Chỉ Admin mới có quyền tắt Bot!"), thread_id, thread_type)
            return

        if clean_msg.startswith(f"{PREFIX}boton") or clean_msg.startswith("!boton"):
            if str(author_id) == ADMIN_UID:
                if str(thread_id) in muted_groups:
                    muted_groups.remove(str(thread_id))
                    save_muted(muted_groups)
                    self.sendMessage(Message(text="Bot đã BẬT hoạt động trở lại! 🟢"), thread_id, thread_type)
                else:
                    self.sendMessage(Message(text="Bot vẫn đang hoạt động bình thường mà! 😎"), thread_id, thread_type)
            else:
                self.sendMessage(Message(text="⚠️ Chỉ Admin mới có quyền bật Bot!"), thread_id, thread_type)
            return

        if str(thread_id) in muted_groups: return

        # =======================================================
        # 🔥 LOGIC CHÀO HỎI (AI XỬ LÝ 100% NẾU BỊ TAG) 🔥
        # =======================================================
        is_command = clean_msg.startswith(PREFIX) or clean_msg.startswith("!")

        if not is_command:
            has_other_mentions = False
            has_bot_mention = False

            mentions = message_object.get('mentions', []) if isinstance(message_object, dict) else getattr(message_object, 'mentions', [])
            if mentions:
                for m in mentions:
                    uid = str(m.get('uid')) if isinstance(m, dict) else str(getattr(m, 'uid', ''))
                    if uid == str(self.uid):
                        has_bot_mention = True
                    else:
                        has_other_mentions = True

            def check_keyword(text, keywords):
                for k in keywords:
                    if re.search(rf"(?<!\w){re.escape(k)}(?!\w)", text): return True
                return False

            greetings_list = ["hi", "hello", "chào", "hí", "lô", "hé lô", "hế lô", "xin chào"]
            goodbye_list = ["bye", "tạm biệt", "pp", "bai", "pai", "goodbye"]
            sleep_list = ["ngủ ngon", "g9", "đi ngủ", "khò"]

            has_greeting = check_keyword(clean_msg, greetings_list)
            has_goodbye = check_keyword(clean_msg, goodbye_list)
            has_sleep = check_keyword(clean_msg, sleep_list)

            word_count = len(clean_msg.split())
            is_short_sentence = word_count <= 8 

            def is_general_msg(text):
                allowed_words = {
                    "xin", "chào", "hello", "hi", "hí", "lô", "hé", "hế", "helo",
                    "bot", "ad", "bơ", "admin", "mn", "mọi", "người", "ae", "anh", "em", "all", "nhóm", "box", "nhà", "cả", 
                    "nha", "nhé", "ạ", "ơi", "buổi", "sáng", "trưa", "chiều", "tối", "ngày", "mới",
                    "ngủ", "ngon", "g9", "đi", "khò", "tạm", "biệt", "bye", "bai", "pai", "pp", "pái", 
                    "chúc", "tốt", "lành", "vui", "vẻ", "nghen", "luôn", "nè", "rồi", "chưa", "thế", "này", "đó", "đây", "kia",
                    "có", "gì", "không", "hong", "ai", "đâu", "nào", "sao", "vậy"
                }
                text_clean = re.sub(r'[^\w\s]', '', text)
                words = text_clean.split()
                for w in words:
                    if w not in allowed_words:
                        return False
                return True

            # CHỈ ĐÁP LẠI TỰ ĐỘNG NẾU KHÁCH KHÔNG TAG BOT
            # (Nếu khách tag Bot, toàn bộ việc trả lời sẽ được giao cho Não AI ở dưới)
            if not has_bot_mention:
                has_general_target = is_general_msg(clean_msg)
                can_reply_fast = is_short_sentence and not has_other_mentions and has_general_target

                if has_greeting and can_reply_fast:
                    hour = datetime.now().hour
                    if 5 <= hour < 11: msg_template = random.choice(GREETING_DATA["morning"])
                    elif 11 <= hour < 14: msg_template = random.choice(GREETING_DATA["noon"])
                    elif 14 <= hour < 18: msg_template = random.choice(GREETING_DATA["afternoon"])
                    elif 18 <= hour < 22: msg_template = random.choice(GREETING_DATA["evening"])
                    else: msg_template = random.choice(GREETING_DATA["night"])
                    self.sendMessage(Message(text=msg_template.format(name=user_name)), thread_id, thread_type)
                    return

                if (has_goodbye or has_sleep) and can_reply_fast:
                    hour = datetime.now().hour
                    if has_sleep or (22 <= hour or hour < 5): msg_template = random.choice(SLEEP_DATA)
                    else: msg_template = random.choice(GOODBYE_DATA)
                    self.sendMessage(Message(text=msg_template.format(name=user_name)), thread_id, thread_type)
                    return
        
        # =================================================================
        # 🛡️ MODULES AN TOÀN
        # =================================================================
        try:
            nt_module = get_number_tracker_module()
            nt_module.get('process')(message_object, author_id, thread_id)
        except Exception as e: print(f"⚠️ Lỗi module Số đếm: {e}")

        try:
            # Não AI nằm ở đây! Cứ có Tag là nó sẽ phân tích và đáp trả!
            if handle_conversational_tag(msg_content, message_object, thread_id, thread_type, author_id, self):
                return
        except Exception as e: print(f"⚠️ Lỗi module AI Tag: {e}")

        try:
            record_message(message_object, author_id, thread_id)
        except Exception as e: print(f"⚠️ Lỗi module CheckTT (Record): {e}")

        try:
            ts = message_object.get("ts") if isinstance(message_object, dict) else getattr(message_object, "ts", None)
            warn = spam_handler(thread_id, author_id, timestamp=ts)
            if warn: self.sendMessage(Message(text=warn), thread_id, thread_type)
        except Exception as e: print(f"⚠️ Lỗi module Spam: {e}")

        # Lệnh Menu và CheckTT
        try:
            if clean_msg == PREFIX or clean_msg == f"{PREFIX}menu":
                self.sendMessage(Message(text=f"Gõ {PREFIX}menu đi"), thread_id, thread_type)
            elif clean_msg.startswith("!so") or clean_msg.startswith(f"{PREFIX}so"):
                nt_module.get('handle')(msg_content, thread_id, thread_type, author_id, self)
            elif clean_msg.startswith("!checktt") or clean_msg.startswith(f"{PREFIX}checktt"):
                handle_checktt_command(msg_content, message_object, thread_id, thread_type, author_id, self)
            else:
                self.command_handler.handle_command(msg_content, author_id, message_object, thread_id, thread_type)
        except Exception as e:
            print(rgb_text(f"⚠️ Lỗi Xử Lý Lệnh: {e}", "FFFF00"))

def schedule_smart_restart():
    def task():
        now = datetime.now()
        if (now.hour == 23 and now.minute >= 50) or (now.hour == 0 and now.minute <= 10):
            threading.Timer(900, task).start() 
        else:
            python = sys.executable
            os.execl(python, python, *sys.argv) 
    threading.Timer(3600, task).start()

if __name__ == "__main__":
    schedule_smart_restart()
    print(rgb_text(f"[{datetime.now().strftime('%H:%M')}] ✅ BOT ĐANG KHỞI ĐỘNG...", "00FF00"))
    
    try:
        client = Client(API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES)
        set_client(client)
        start_scheduler()
        print(rgb_text(f"[{datetime.now().strftime('%H:%M')}] 🔗 KẾT NỐI THÀNH CÔNG! (AI TAG FIXED)", "00FF00"))
        
        client.listen(thread=False, delay=0) 
    except Exception as e:
        print(rgb_text(f"⚠️ Đứt kết nối Zalo ({str(e)}). Đang khởi động lại Bot sau 3 giây...", "FF0000"))
        time.sleep(3)
        os.execl(sys.executable, sys.executable, *sys.argv)