import re
import time
import threading
import json
import os
from datetime import datetime, timedelta
import schedule  # pip install schedule
from zlapi.models import Message, ThreadType
from modules.user_info import register_user, load_user_info

# =========================================================
# CẤU HÌNH & KHỞI TẠO
# =========================================================

# Đường dẫn file lưu trữ dữ liệu thống kê
STATS_FILE = "message_stats.json"

# Cấu trúc dữ liệu thống kê
message_stats = {}

# Định nghĩa ID của bot (để bot không tự đếm tin nhắn của mình)
BOT_ID = "770810507108566189"

# Danh sách ID của Admin (được phép dùng lệnh !checktt)
ADMIN_IDS = ["9123173293216833155", "1874166068975395869", "4544068758699002896"]

# Biến global lưu client
global_client = None

def set_client(client_obj):
    global global_client
    global_client = client_obj

# =========================================================
# QUẢN LÝ FILE DỮ LIỆU (SAVE/LOAD)
# =========================================================

def save_stats():
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(message_stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Không thể lưu file stats: {e}")

def load_stats():
    global message_stats
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                message_stats = json.load(f)
        except Exception:
            message_stats = {}
    else:
        message_stats = {}

# Tải dữ liệu khi khởi động
load_stats()

# =========================================================
# CÁC HÀM XỬ LÝ THỜI GIAN & GHI NHẬN
# =========================================================

def get_daily_storage_key(dt=None):
    """Key lưu trữ theo ngày: YYYY-MM-DD"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d")

def get_weekly_storage_key(dt=None):
    """Key lưu trữ theo tuần: YYYY-WW"""
    if dt is None:
        dt = datetime.now()
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year}-{iso_week:02d}"

def record_message(message_object, author_id, thread_id):
    """
    Ghi nhận tin nhắn vào hệ thống.
    """
    global message_stats
    
    if str(author_id) == BOT_ID:
        return

    try:
        register_user(message_object, author_id, global_client)
    except:
        pass

    user_id = str(author_id)
    dname = message_object.get("dName", "")
    
    if not dname or dname.strip().lower() == "vy":
        content = message_object.get("content", "")
        m = re.search(r"📩\s*(.+?)\s+đã gửi", content)
        if m:
            user_name = m.group(1).strip()
        else:
            user_name = f"User {user_id}"
    else:
        user_name = dname.strip()

    if thread_id not in message_stats or not isinstance(message_stats[thread_id], dict):
        message_stats[thread_id] = {"daily": {}, "weekly": {}}

    day_key = get_daily_storage_key()
    week_key = get_weekly_storage_key()

    if day_key not in message_stats[thread_id]["daily"]:
        message_stats[thread_id]["daily"][day_key] = {}
    if week_key not in message_stats[thread_id]["weekly"]:
        message_stats[thread_id]["weekly"][week_key] = {}

    if user_id in message_stats[thread_id]["daily"][day_key]:
        message_stats[thread_id]["daily"][day_key][user_id]['count'] += 1
        message_stats[thread_id]["daily"][day_key][user_id]['name'] = user_name 
    else:
        message_stats[thread_id]["daily"][day_key][user_id] = {'name': user_name, 'count': 1}

    if user_id in message_stats[thread_id]["weekly"][week_key]:
        message_stats[thread_id]["weekly"][week_key][user_id]['count'] += 1
        message_stats[thread_id]["weekly"][week_key][user_id]['name'] = user_name
    else:
        message_stats[thread_id]["weekly"][week_key][user_id] = {'name': user_name, 'count': 1}

    save_stats()

# =========================================================
# HÀM TẠO NỘI DUNG BÁO CÁO (FULL LIST - KHÔNG CẮT) 📜
# =========================================================

def generate_statistics_text(thread_id, period="daily", mode="current"):
    if period == "daily":
        if mode == "previous":
            dt = datetime.now() - timedelta(days=1)
        else:
            dt = datetime.now()
        storage_key = dt.strftime("%Y-%m-%d")
        header_date = dt.strftime("%d/%m/%Y")
        header = f"📊 Thống kê tin nhắn ngày {header_date}:\n"
        stats = message_stats.get(thread_id, {}).get("daily", {}).get(storage_key, {})
        
    elif period == "weekly":
        if mode == "previous":
            dt = datetime.now() - timedelta(weeks=1)
        else:
            dt = datetime.now()
        iso_year, iso_week, _ = dt.isocalendar()
        storage_key = f"{iso_year}-{iso_week:02d}"
        header = f"📊 Báo cáo tin nhắn Tuần {iso_week:02d} - {iso_year}:\n"
        stats = message_stats.get(thread_id, {}).get("weekly", {}).get(storage_key, {})
    else:
        return "Lỗi tham số thống kê."

    if not stats:
        return header + "📭 Không có dữ liệu tin nhắn."

    if BOT_ID in stats:
        stats = stats.copy()
        del stats[BOT_ID]

    positive = [(uid, info) for uid, info in stats.items() if info.get("count", 0) > 0]

    result = ""
    if positive:
        # Sort từ cao xuống thấp
        sorted_positive = sorted(positive, key=lambda x: x[1]["count"], reverse=True)
        
        # --- LOGIC MỚI: HIỂN THỊ TẤT CẢ (KHÔNG GIỚI HẠN) ---
        ranking_lines = [f"{i+1}. {info['name']}: {info['count']} tin nhắn" for i, (uid, info) in enumerate(sorted_positive)]
        
        result = header + "\n".join(ranking_lines)
    else:
        result = header + "📭 Không có thành viên nào nhắn tin."

    return result


# 🔥 LOGIC TÍNH TỔNG KẾT THÁNG (TOP 20) 🔥
def get_prev_month_info():
    """Lấy thông tin của tháng trước"""
    today = datetime.now()
    last_day_prev_month = today.replace(day=1) - timedelta(days=1)
    prefix = last_day_prev_month.strftime("%Y-%m")
    month_str = f"Tháng {last_day_prev_month.month}/{last_day_prev_month.year}"
    return prefix, month_str

def generate_monthly_statistics_text(thread_id):
    prefix, month_str = get_prev_month_info()
    header = f"📊 BẢNG VÀNG TƯƠNG TÁC {month_str.upper()}:\n"
    header += "🌟 TOP 20 CHÚA TỂ CÀO PHÍM:\n━━━━━━━━━━━━━━━━━━\n"

    thread_data = message_stats.get(thread_id, {}).get("daily", {})
    monthly_counts = {}

    # Quét tất cả các ngày trong tháng trước
    for date_key, users in thread_data.items():
        if date_key.startswith(prefix):
            for uid, info in users.items():
                if uid not in monthly_counts:
                    monthly_counts[uid] = {"name": info["name"], "count": 0}
                monthly_counts[uid]["count"] += info["count"]

    if BOT_ID in monthly_counts:
        del monthly_counts[BOT_ID]

    if not monthly_counts:
        return header + "📭 Tháng qua nhóm không có tương tác."

    # Lấy Top 20
    sorted_users = sorted(monthly_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:20]

    lines = []
    for i, (uid, info) in enumerate(sorted_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
        lines.append(f"{medal} Top {i}: {info['name']} - {info['count']} tin")

    footer = "\n━━━━━━━━━━━━━━━━━━\n🎉 Chúc box tháng mới tiếp tục bùng nổ!"
    return header + "\n".join(lines) + footer

# =========================================================
# XỬ LÝ LỆNH CHECK THỦ CÔNG (!checktt)
# =========================================================

def handle_checktt_command(message, message_object, thread_id, thread_type, author_id, client):
    global message_stats
    if str(author_id) not in ADMIN_IDS:
        client.sendMessage(Message(text="🚫 Bạn không có quyền sử dụng lệnh này!"), thread_id, thread_type)
        return

    msg_lower = message.strip().lower()
    tokens = msg_lower.split()

    if msg_lower == "!checktt test":
        client.sendMessage(Message(text="🚀 Đang test gửi báo cáo tháng..."), thread_id, thread_type)
        try:
            # Dùng để Bơ test thử tính năng gửi report tháng
            send_monthly_stats() 
            client.sendMessage(Message(text="✅ Đã test gửi xong."), thread_id, thread_type)
        except Exception as e:
            client.sendMessage(Message(text=f"❌ Lỗi: {e}"), thread_id, thread_type)
        return

    # 1. !checktt lday
    if msg_lower.startswith("!checktt lday"):
        if len(tokens) == 2:
            day_key = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            stats = message_stats.get(thread_id, {}).get("daily", {}).get(day_key, {})
            count = stats.get(str(author_id), {}).get("count", 0)
            client.sendMessage(Message(text=f"📩 Hôm qua bạn gửi: {count} tin."), thread_id, thread_type)
            return
            
        elif len(tokens) == 3 and tokens[2] == "all":
            response_text = generate_statistics_text(thread_id, period="daily", mode="previous")
            client.sendMessage(Message(text=response_text), thread_id, thread_type)
            return

        elif "@" in message:
            m_tag = re.search(r"!checktt lday\s+@(.+)", message)
            if m_tag:
                name = m_tag.group(1).strip()
                day_key = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                stats = message_stats.get(thread_id, {}).get("daily", {}).get(day_key, {})
                found_count = 0
                for info in stats.values():
                    if info.get("name", "").lower() == name.lower():
                        found_count = info.get("count", 0)
                        break
                client.sendMessage(Message(text=f"📩 Hôm qua {name} gửi: {found_count} tin."), thread_id, thread_type)
                return

    # 2. !checktt lweek
    if msg_lower.startswith("!checktt lweek"):
        if len(tokens) == 2:
            dt = datetime.now() - timedelta(weeks=1)
            key = get_weekly_storage_key(dt)
            stats = message_stats.get(thread_id, {}).get("weekly", {}).get(key, {})
            count = stats.get(str(author_id), {}).get("count", 0)
            client.sendMessage(Message(text=f"📩 Tuần trước bạn gửi: {count} tin."), thread_id, thread_type)
            return
            
        elif len(tokens) == 3 and tokens[2] == "all":
            response_text = generate_statistics_text(thread_id, period="weekly", mode="previous")
            client.sendMessage(Message(text=response_text), thread_id, thread_type)
            return
            
        elif "@" in message:
            m_tag = re.search(r"!checktt lweek\s+@(.+)", message)
            if m_tag:
                name = m_tag.group(1).strip()
                dt = datetime.now() - timedelta(weeks=1)
                key = get_weekly_storage_key(dt)
                stats = message_stats.get(thread_id, {}).get("weekly", {}).get(key, {})
                found_count = 0
                for info in stats.values():
                    if info.get("name", "").lower() == name.lower():
                        found_count = info.get("count", 0)
                        break
                client.sendMessage(Message(text=f"📩 Tuần trước {name} gửi: {found_count} tin."), thread_id, thread_type)
                return

    # 3. !checktt week
    if msg_lower == "!checktt week":
        response_text = generate_statistics_text(thread_id, period="weekly", mode="current")
        client.sendMessage(Message(text=response_text), thread_id, thread_type)
        return

    # 4. !checktt all
    if msg_lower == "!checktt all":
        response_text = generate_statistics_text(thread_id, period="daily", mode="current")
        client.sendMessage(Message(text=response_text), thread_id, thread_type)
        return

    # 5. !checktt @name
    m = re.search(r"!checktt\s+@(.+)", message)
    if m:
        name = m.group(1).strip()
        day_key = get_daily_storage_key()
        stats = message_stats.get(thread_id, {}).get("daily", {}).get(day_key, {})
        found_count = 0
        for info in stats.values():
            if info.get("name", "").lower() == name.lower():
                found_count = info.get("count", 0)
                break
        client.sendMessage(Message(text=f"📩 Hôm nay {name} gửi: {found_count} tin."), thread_id, thread_type)
        return

    # 6. Default
    day_key = get_daily_storage_key()
    stats = message_stats.get(thread_id, {}).get("daily", {}).get(day_key, {})
    count = stats.get(str(author_id), {}).get("count", 0)
    client.sendMessage(Message(text=f"📩 Hôm nay bạn gửi: {count} tin."), thread_id, thread_type)


def get_mitaizl():
    return {
        'checktt': record_message,
        'handle_checktt': handle_checktt_command
    }

# =========================================================
# SCHEDULER: GỬI BÁO CÁO TỰ ĐỘNG
# =========================================================

TARGET_THREAD_IDS = [
    "1311505722605591852", 
    "6578233211669146965",
    "5006041687664967782"
]

def send_daily_stats():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now_str}] 📊 BẮT ĐẦU GỬI BÁO CÁO NGÀY (Của hôm qua)...")
    
    for thread_id in TARGET_THREAD_IDS:
        try:
            report = generate_statistics_text(thread_id, period="daily", mode="previous")
            global_client.sendMessage(Message(text=report), thread_id, ThreadType.GROUP)
            print(f"✅ Đã gửi daily report cho nhóm: {thread_id}")
        except Exception as e:
            print(f"❌ Lỗi gửi daily report nhóm {thread_id}: {e}")

def send_weekly_stats():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now_str}] 📊 BẮT ĐẦU GỬI BÁO CÁO TUẦN (Của tuần trước)...")
    
    for thread_id in TARGET_THREAD_IDS:
        try:
            report = generate_statistics_text(thread_id, period="weekly", mode="previous")
            global_client.sendMessage(Message(text=report), thread_id, ThreadType.GROUP)
            print(f"✅ Đã gửi weekly report cho nhóm: {thread_id}")
        except Exception as e:
            print(f"❌ Lỗi gửi weekly report nhóm {thread_id}: {e}")

def check_and_send_monthly():
    """Hàm trung gian: Chạy mỗi ngày lúc 00:02 nhưng CHỈ kích hoạt nếu là ngày mùng 1"""
    if datetime.now().day == 1:
        send_monthly_stats()

def send_monthly_stats():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _, month_str = get_prev_month_info()
    print(f"[{now_str}] 🏆 BẮT ĐẦU GỬI BÁO CÁO THÁNG ({month_str})...")

    # Gọi hàm export rank từ module checkrank
    try:
        from modules.checkrank import export_top_10_rank
    except Exception as e:
        export_top_10_rank = None
        print(f"⚠️ Không thể gọi module checkrank: {e}")
    
    for thread_id in TARGET_THREAD_IDS:
        try:
            # 1. Bắn Top 20 Tương tác tháng
            report_tt = generate_monthly_statistics_text(thread_id)
            global_client.sendMessage(Message(text=report_tt), thread_id, ThreadType.GROUP)
            time.sleep(2) # Trễ xíu tránh bị Zalo chặn spam

            # 2. Bắn Top 10 Cày Rank
            if export_top_10_rank:
                rank_text = export_top_10_rank(thread_id)
                if rank_text:
                    rank_msg = f"🏆 TOP 10 CAO THỦ RANK CAO NHẤT BOX ({month_str.upper()})\n━━━━━━━━━━━━━━━━━━\n{rank_text}"
                    global_client.sendMessage(Message(text=rank_msg), thread_id, ThreadType.GROUP)
            
            print(f"✅ Đã vinh danh báo cáo THÁNG cho nhóm: {thread_id}")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Lỗi gửi monthly report nhóm {thread_id}: {e}")

def start_scheduler():
    schedule.every().day.at("00:00:05").do(send_daily_stats)
    schedule.every().monday.at("00:00:10").do(send_weekly_stats)
    # Cài báo cáo tháng chạy mỗi ngày nhưng hàm check_and_send_monthly sẽ chặn lại nếu ko phải mùng 1
    schedule.every().day.at("00:02:00").do(check_and_send_monthly)

    def scheduler_thread():
        print("⏳ Scheduler checktt đang chạy (Auto Report)...")
        while True:
            schedule.run_pending()
            time.sleep(1)

    scheduler = threading.Thread(target=scheduler_thread)
    scheduler.daemon = True
    scheduler.start()