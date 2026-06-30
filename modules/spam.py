import json
import os
from datetime import datetime, timedelta

# Đường dẫn file thống kê (dùng chung với checktt.py)
STATS_FILE = "message_stats.json"
# ID của bot (điền ID thực tế của bot)
BOT_ID = "770810507108566189"  # Thay đổi theo thực tế

def load_stats():
    """Tải dữ liệu thống kê từ file."""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Lỗi khi tải file stats:", e)
            return {}
    return {}

def save_stats(stats):
    """Lưu dữ liệu thống kê vào file."""
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Lỗi khi lưu file stats:", e)

def get_daily_storage_key(dt=None):
    """Trả về key ngày dạng YYYY-MM-DD."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d")

class SpamDetector:
    def __init__(self, message_limit=15, time_window=60, warning_limit=3):
        """
        message_limit: Số tin nhắn tối đa cho phép trong khoảng time_window (Tăng lên 15 cho đỡ gắt).
        time_window: Khoảng thời gian tính spam, đơn vị giây (mặc định 60 giây).
        warning_limit: Số lần cảnh cáo trước khi reset (mặc định 3).
        """
        self.message_limit = message_limit
        self.time_window = time_window
        self.warning_limit = warning_limit
        self.spam_tracker = {}   # {member_id: [ {timestamp, content}, ... ]}
        self.warnings = {}       # {member_id: warning_count}
        self.current_day = get_daily_storage_key()

    def _convert_timestamp(self, timestamp):
        if isinstance(timestamp, datetime):
            return timestamp
        try:
            ts = float(timestamp) / 1000 
            return datetime.fromtimestamp(ts)
        except Exception as e:
            return datetime.now()

    def process_message(self, thread_id, member_id, timestamp=None, content=""):
        # Reset warnings và spam_tracker nếu ngày thay đổi
        today = get_daily_storage_key()
        if today != self.current_day:
            self.current_day = today
            self.warnings = {}
            self.spam_tracker = {}

        # Bỏ qua tin nhắn của bot
        if str(member_id) == BOT_ID:
            return None

        # Chuyển đổi timestamp
        timestamp = self._convert_timestamp(timestamp) if timestamp else datetime.now()

        # Thêm tin nhắn vào spam_tracker
        self.spam_tracker.setdefault(member_id, [])
        self.spam_tracker[member_id].append({"timestamp": timestamp, "content": content})

        # Lọc danh sách tin nhắn theo khoảng thời gian gốc (time_window)
        cutoff = timestamp - timedelta(seconds=self.time_window)
        self.spam_tracker[member_id] = [m for m in self.spam_tracker[member_id] if m["timestamp"] > cutoff]
        
        spam_count = len(self.spam_tracker[member_id])
        current_warn = self.warnings.get(member_id, 0)

        # --- ĐIỀU KIỆN SPAM (ĐÃ NỚI LỎNG) ---
        # Điều kiện 1: 8 tin nhắn trong 5 giây (Tăng từ 5 -> 8)
        messages_5s = [m for m in self.spam_tracker[member_id] if m["timestamp"] > timestamp - timedelta(seconds=5)]
        condition1 = len(messages_5s) >= 8

        # Điều kiện 2: 12 tin nhắn trong 10 giây (Tăng từ 5 -> 12)
        messages_10s = [m for m in self.spam_tracker[member_id] if m["timestamp"] > timestamp - timedelta(seconds=10)]
        condition2 = len(messages_10s) >= 12

        # Điều kiện 3: 10 tin nhắn 1 từ liên tiếp trong 20 giây (Tăng từ 5 -> 10)
        messages_20s = [m for m in self.spam_tracker[member_id] if m["timestamp"] > timestamp - timedelta(seconds=20)]
        if len(messages_20s) >= 10:
            last_ten = messages_20s[-10:]
            condition3 = all(len(m["content"].strip().split()) == 1 for m in last_ten)
        else:
            condition3 = False

        # Điều kiện gốc
        original_condition = spam_count > self.message_limit

        # XỬ LÝ CẢNH BÁO
        if original_condition or condition1 or condition2 or condition3:
            # Tăng cảnh cáo
            self.warnings[member_id] = current_warn + 1
            current_warning = self.warnings[member_id]
            
            # Load stats an toàn
            stats = load_stats()
            day_key = get_daily_storage_key()
            
            # Init cấu trúc dữ liệu nếu chưa có (tránh KeyError)
            if thread_id not in stats: stats[thread_id] = {"daily": {}}
            if day_key not in stats[thread_id]["daily"]: stats[thread_id]["daily"][day_key] = {}
            
            str_member_id = str(member_id)
            if str_member_id not in stats[thread_id]["daily"][day_key]:
                 stats[thread_id]["daily"][day_key][str_member_id] = {"name": f"User {member_id}", "count": 0}

            member_name = stats[thread_id]["daily"][day_key][str_member_id].get("name", f"User {member_id}")

            if current_warning < 4:
                # Trừ spam count
                current_count = stats[thread_id]["daily"][day_key][str_member_id].get("count", 0)
                new_count = max(0, current_count - 5) # Trừ nhẹ 5 tin thôi
                stats[thread_id]["daily"][day_key][str_member_id]["count"] = new_count
                save_stats(stats)
                
                # Reset tracker để người dùng có cơ hội sửa sai
                self.spam_tracker[member_id] = []
                
                return (f"🚨 Cảnh báo spam lần {current_warning}\n"
                        f"❌ {member_name} vui lòng chat chậm lại!\n"
                        f"🚫 Đã trừ điểm tương tác.")
            else:
                # Reset về 0
                stats[thread_id]["daily"][day_key][str_member_id]["count"] = 0
                save_stats(stats)
                self.warnings[member_id] = 0
                self.spam_tracker[member_id] = []
                
                return (f"🚨 QUÁ GIỚI HẠN SPAM 🚨\n"
                        f"🚫 {member_name} đã bị reset toàn bộ tin nhắn trong ngày!")
        
        return None

def get_mitaizl():
    # Khởi tạo detector với giới hạn nới lỏng hơn
    detector = SpamDetector(message_limit=15, time_window=60, warning_limit=3)
    return {
        'spam': detector.process_message
    }