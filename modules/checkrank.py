import os
import re
import json
import config  # Import file config để lấy danh sách ADMIN
from datetime import datetime
from zlapi.models import Message

# -------------------------
# Cấu hình module
# -------------------------
config_mod = {
    "name": "checkrank",
    "version": "1.2.3",
    "hasPermission": 2,
    "credits": "SenProject",
    "description": ("Đánh giá rank của các thành viên dựa trên tổng số tin nhắn đã ghi nhận. "
                    "Chỉ Admin mới có quyền dùng lệnh 'all'."),
    "commandCategory": "Box",
    "usages": "!checkrank, !checkrank @tag, !checkrank all",
    "cooldowns": 5
}

STATS_FILE = "message_stats.json"
COUNT_DIR = os.path.join(os.path.dirname(__file__), "count-by-thread")

global_client = None
def set_client(client_obj):
    global global_client
    global_client = client_obj

def load_message_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"[DEBUG] Lỗi đọc {STATS_FILE}: {e}")
                return {}
    return {}

def get_total_counts(thread_id, stats_data):
    totals = {}
    thread_stats = stats_data.get(str(thread_id)) or stats_data.get(thread_id, {})
    daily_stats = thread_stats.get("daily", {})
    for key, value in daily_stats.items():
        if re.match(r"\d{4}-\d{2}-\d{2}", key):
            for uid, info in value.items():
                if uid not in totals:
                    totals[uid] = {"name": info.get("name", f"User {uid}"), "count": info.get("count", 0)}
                else:
                    totals[uid]["count"] += info.get("count", 0)
        else:
            uid = key
            info = value
            if isinstance(info, dict) and "count" in info:
                if uid not in totals:
                    totals[uid] = {"name": info.get("name", f"User {uid}"), "count": info.get("count", 0)}
                else:
                    totals[uid]["count"] += info.get("count", 0)
    return totals

# -------------------------
# HỆ THỐNG RANK
# -------------------------
def get_rank_name(count):
    if count > 50000: return 'Tối Cao'
    elif count > 20000: return 'Thách Đấu'
    elif count > 9000: return 'Đại Cao Thủ'
    elif count > 8000: return 'Cao Thủ'
    elif count > 6100: return 'Kim Cương I'
    elif count > 5900: return 'Kim Cương II'
    elif count > 5700: return 'Kim Cương III'
    elif count > 5200: return 'Kim Cương IV'
    elif count > 5000: return 'Lục Bảo I'
    elif count > 4800: return 'Lục Bảo II'
    elif count > 4500: return 'Lục Bảo III'
    elif count > 4000: return 'Lục Bảo IV'
    elif count > 3800: return 'Bạch Kim I'
    elif count > 3500: return 'Bạch Kim II'
    elif count > 3200: return 'Bạch Kim III'
    elif count > 3000: return 'Bạch Kim IV'
    elif count > 2900: return 'Vàng I'
    elif count > 2500: return 'Vàng II'
    elif count > 2300: return 'Vàng III'
    elif count > 2000: return 'Vàng IV'
    elif count > 1500: return 'Bạc I'
    elif count > 1200: return 'Bạc II'
    elif count > 1000: return 'Bạc III'
    elif count > 900: return 'Bạc IV'
    elif count > 500: return 'Đồng'
    elif count > 100: return 'Sắt'
    else: return 'Unranked'

def update_count_file_for_thread(thread_id):
    if not os.path.exists(COUNT_DIR):
        os.makedirs(COUNT_DIR, exist_ok=True)
    stats_data = load_message_stats()
    totals = get_total_counts(thread_id, stats_data)
    output_data = {uid: {"name": info["name"], "count": info["count"]} for uid, info in totals.items()}
    file_path = os.path.join(COUNT_DIR, f"{thread_id}.json")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[ERROR] Lỗi khi ghi file: {e}")

def run(api, event, args, Users, *extra):
    client = api if hasattr(api, "sendMessage") else global_client
    if not client: return

    thread_id = event.get("threadID")
    sender_id = str(event.get("senderID"))
    thread_type = event.get("threadType")
    raw_content = event.get("content", "") or event.get("message", "")
    
    update_count_file_for_thread(thread_id)
    stats_data = load_message_stats()
    totals = get_total_counts(thread_id, stats_data)
    
    if not totals:
        client.sendMessage(Message(text="⚠️ Không có dữ liệu tin nhắn để xếp hạng."), thread_id, thread_type)
        return

    ranking_list = []
    for uid, info in totals.items():
        name = info.get("name") if info.get("name") else Users.getNameUser(uid)
        ranking_list.append({"id": uid, "name": name, "count": info.get("count", 0)})
    
    ranking_list.sort(key=lambda x: (-x["count"], x["name"]))
    
    msg = ""
    query = args[0].lower() if args else ""

    if query == "all":
        # KIỂM TRA QUYỀN ADMIN TỪ FILE CONFIG
        if sender_id not in config.ADMIN:
            client.sendMessage(Message(text="🚫 Bạn không có quyền sử dụng lệnh !checkrank all!"), thread_id, thread_type)
            return

        filtered_list = [u for u in ranking_list if get_rank_name(u["count"]) != "Unranked"]
        
        if not filtered_list:
            msg = "⚠️ Nhóm này hiện chưa có ai đạt mốc Rank Sắt (>100 tin nhắn)."
        else:
            msg += "=== BẢNG XẾP HẠNG TƯƠNG TÁC ==="
            for idx, user in enumerate(filtered_list, start=1):
                msg += f"\n\n{idx}. 👤 Tên: {user['name']}\n    📝 Số tin nhắn: {user['count']}\n    🏆 Rank: {get_rank_name(user['count'])}"
                
    elif query.startswith("@"):
        match = re.search(r"checkrank\s+@\s*(.+)", raw_content, re.IGNORECASE)
        if match:
            display_name = match.group(1).strip()
            search_name = display_name.lower()
        else:
            display_name = " ".join(args).replace("@", "", 1).strip()
            search_name = display_name.lower()

        found_user = None
        current_idx = 0
        for idx, user in enumerate(ranking_list, start=1):
            if search_name in user["name"].lower() or user["name"].lower() in search_name:
                found_user = user
                current_idx = idx
                break
        
        if found_user:
            msg = (f"👤 {found_user['name']} đứng thứ {current_idx}\n"
                   f"📝 Số tin nhắn: {found_user['count']}\n"
                   f"🏆 Rank: {get_rank_name(found_user['count'])}")
        else:
            msg = f"❌ Không tìm thấy dữ liệu của thành viên có tên: {display_name}"
            
    else:
        pos = next((i for i, user in enumerate(ranking_list) if user["id"] == sender_id), None)
        if pos is not None:
            user = ranking_list[pos]
            msg += (f"{'👤 Bạn' if sender_id == user['id'] else user['name']} đứng thứ {pos+1}\n"
                    f"📝 Số tin nhắn: {user['count']}\n"
                    f"🏆 Rank: {get_rank_name(user['count'])}")
        else:
            msg = "❌ Không tìm thấy dữ liệu của bạn."
    
    client.sendMessage(Message(text=msg), thread_id, thread_type)

# 🔥 HÀM MỚI: XUẤT TOP 10 RANK CHO BÁO CÁO THÁNG 🔥
def export_top_10_rank(thread_id):
    stats_data = load_message_stats()
    totals = get_total_counts(thread_id, stats_data)
    if not totals: return None

    ranking_list = []
    for uid, info in totals.items():
        ranking_list.append({"id": uid, "name": info.get("name", f"User {uid}"), "count": info.get("count", 0)})
    
    # Sắp xếp tổng từ cao xuống thấp
    ranking_list.sort(key=lambda x: (-x["count"], x["name"]))
    
    # Lấy top 10
    top_10 = ranking_list[:10]
    if not top_10: return None
    
    msg = ""
    for idx, user in enumerate(top_10, start=1):
        msg += f"{idx}. 👤 {user['name']}\n    🏆 {get_rank_name(user['count'])} ({user['count']} tin)\n"
    return msg

def get_mitaizl():
    return {"checkrank": run}