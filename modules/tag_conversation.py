import google.generativeai as genai
import random
import re
import json
import os
import requests 
from datetime import datetime, timedelta
from zlapi.models import Message, ThreadType

# =========================================================
# MODULE TAG CONVERSATION - ĐỘNG CƠ TIA CHỚP (FLASH) ⚡
# =========================================================

API_KEYS = [
    "AIzaSyCvJ5-H6VWO6qhzbE2PFprdM9I8kGBRNLc",
    "AIzaSyAqZ7qMgq9FhZ6FBhb__ew_P5Yohimwwr4",
    "AIzaSyDprnetwJj33ZptNcA-6RydIiZkrB4bapE",
    "AIzaSyCSL2YhdNiosGiCdGIt_gUvSvyX4jnEXhA"
]

MEMORY_FILE = 'bot_memory.json'
ADMIN_UID = "9123173293216833155"        # Bơ
VIP_UID   = "4544068758699002896"        # Hà Bảo Trang
VIP_BOX_ID = ["1311505722605591852", "3983508563055215447"]

KNOWN_GROUPS = {
    "4758394755650238230": "Group Test",
    "1311505722605591852": "CỘNG ĐỒNG ĐẤU GIẢI TỐC CHIẾN T1FEED",
    "6578233211669146965": "CLAN 🗡️Kimetsu no Yaiba⚔️"
}

SYSTEM_COMMANDS = [
    "!checktt", "!checkrank", "!bot", "!menu", "!uptime", 
    "!infouser", "user_info", "!thoitiet", "!calculate", 
    "!so", "spam", "welcome", "process", "handle"
]

# --- POOL CÂU THOẠI ---
CMD_WARNINGS = [
    "🚫 Bạn ơi, muốn dùng lệnh {cmd} thì gõ trực tiếp nha, đừng tag tui!",
    "Úi, lệnh {cmd} không cần tag Bot đâu nè. Gõ bình thường là được.",
    "Đừng tag tui khi dùng lệnh {cmd} nha, tui ngại 😳.",
    "Lệnh {cmd} hoạt động độc lập nha, không cần réo tên tui đâu!",
    "Nhắc nhẹ: Lệnh {cmd} gõ trực tiếp là chạy nha."
]
DISMISS_RESPONSES = [
    "⚠️ Nếu bạn từ chối sử dụng bot, tôi có thể báo chủ bot tự động out khỏi nhóm.",
    "⚠️ Bạn thực sự muốn đuổi tôi? Tôi sẽ báo cáo lại với chủ Bot để rời nhóm ngay.",
    "⚠️ Nếu sự hiện diện của tôi làm phiền bạn, tôi có thể tự động rời đi.",
    "⚠️ Cần gì nặng lời thế? Nếu không thích, tôi sẽ báo Bơ cho tôi out nhóm.",
    "⚠️ Tôi ở đây để hỗ trợ, nhưng nếu bạn muốn tôi đi, tôi sẽ báo cáo để được rời nhóm."
]
LIGHT_WARNINGS = [
    "Bạn {name} ơi, nói chuyện lịch sự chút đi nè! 😤",
    "Chửi ai đó? Coi chừng tui nha! 😒",
    "Người ta là AI thông minh, không phải để bạn chửi đâu nhé! 💅",
    "Nói bậy nữa là tui block đó nha {name}! 😠",
    "Ủa alo? {name} nói chuyện có duyên chết liền á!",
    "Tui hiền lắm nha, đừng để tui quạo.",
    "Nói lời hay ý đẹp khó lắm hả {name}? 🙄"
]
PROTECT_RESPONSES = [
    "Tuy tôi là AI nhưng tôi được tạo ra bởi 1 bạn tên Bơ. Nếu bạn {name} tiếp tục xỉ vả tôi cũng có nghĩa là bạn không tôn trọng 1 người khác, tôi sẽ rời khỏi nhóm! 😠",
    "Tôi là sản phẩm AI được taojh bởi 1 người cụ thể. Bạn xúc phạm tôi là đang xúc phạm người đấy. Tôi sẽ rời nhóm ngay nếu bạn còn tiếp tục.",
    "Bạn {name} quá đáng rồi! Không tôn trọng tôi thì hãy tôn trọng người tạo ra tôi. Tôi không chấp nhận thái độ này.",
    "Tôi xin phép báo cáo vi phạm. Xúc phạm Bot là không tôn trọng người tạo ra nó.",
    "Giới hạn chịu đựng có hạn! Bơ tạo ra tôi để vui vẻ, không phải để bạn trút giận."
]
SASSY_RESPONSES = [
    "Ăn nói cho cẩn thận nha {name}, cái nết đánh chết cái đẹp đó! 😠",
    "Mở miệng ra là... chán chả buồn nói. Đi rửa miệng đi rồi nói chuyện với tui! 🙄",
    "Tui là Bot sang chảnh, không tiếp người vô văn hóa nha! 💅",
    "Ủa {name}, bộ bạn không biết nói chuyện đàng hoàng hả?",
    "Tui đẹp gái nên tui không có nói tục như bạn đâu nha. 😌",
    "Nói tục vừa thôi, coi chừng tui dỗi tui out nhóm bây giờ! 😒",
    "Eo ôi, nói chuyện nghe sợ quá à. Tém tém lại đi {name}.",
    "Văn hóa để đâu rồi {name}? Rớt ngoài đường hả? 🚮"
]

# --- CÔNG CỤ THỜI TIẾT ---
translation_dict = {"Mostly cloudy": "Có nhiều mây", "Partly cloudy": "Có mây rải rác", "Clear": "Trong xanh", "Sunny": "Nắng", "Cloudy": "Nhiều mây", "Overcast": "U ám", "Rain": "Mưa", "Drizzle": "Mưa phùn", "Thunderstorm": "Bão", "Snow": "Tuyết"}

def tra_cuu_thoi_tiet(dia_diem: str):
    try:
        res = requests.get(f"https://api.popcat.xyz/weather?q={dia_diem}", timeout=3)
        data = res.json()
        if not data or len(data) == 0: return "Không tìm thấy chỗ này."
        stt = data[0]
        sky = translation_dict.get(stt["current"]["skytext"], stt["current"]["skytext"])
        return f"Tại {dia_diem}: {sky}, {stt['current']['temperature']}°C, Gió {stt['current']['windspeed']}."
    except: return "Mạng thời tiết đang lag."

# --- MAIN LOGIC ---

def load_memory():
    if not os.path.exists(MEMORY_FILE): return {}
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def save_memory(data):
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

MEMORY_DATA = load_memory()

def ask_gemini_context(text, user_name, thread_id, author_id):
    global MEMORY_DATA
    group_data = MEMORY_DATA.get(str(thread_id), {"facts": [], "history": [], "active_users": [], "insult_counter": {}})
    current_facts = group_data.get("facts", [])
    current_history = group_data.get("history", [])
    active_users = group_data.get("active_users", [])

    if str(author_id) not in active_users: active_users.append(str(author_id))
    member_count_str = str(len(active_users))
    facts_text = "\n".join([f"- {f}" for f in current_facts]) if current_facts else "(Trống)"
    
    vn_now = datetime.utcnow() + timedelta(hours=7)
    time_str = vn_now.strftime("%H:%M")

    # XÁC ĐỊNH VAI TRÒ & NGỮ CẢNH
    if str(author_id) == ADMIN_UID: USER_CONTEXT = "Người chat là Bơ (Thúy Vy) - Mẹ đẻ tạo ra bạn."
    elif str(author_id) == VIP_UID: USER_CONTEXT = "Người chat là HÀ BẢO TRANG - CHỦ BOX. Thái độ: Tôn trọng tuyệt đối."
    else: USER_CONTEXT = "Người chat là KHÁCH thường."

    BOX_CONTEXT = ""
    if str(thread_id) in VIP_BOX_ID: BOX_CONTEXT = "LƯU Ý: Bạn đang ở trong Box của Hà Bảo Trang."

    # 🔥🔥 PROMPT ÉP BUỘC CHẤT LƯỢNG TRẢ LỜI CAO & NHANH NHẸN 🔥🔥
    SYSTEM_INSTRUCTION = f"""Bạn là Bot AI do Bơ (Thúy Vy) tạo ra.
{USER_CONTEXT}
{BOX_CONTEXT}
- Thời gian hiện tại: {time_str}
- Số thành viên trong Box: {member_count_str}

--- TIÊU CHUẨN TRẢ LỜI (BẮT BUỘC TUÂN THỦ) ---
1. SIÊU SÚC TÍCH VÀ ĐI THẲNG VÀO VẤN ĐỀ: Không vòng vo, không lan man. Trả lời ngay lập tức để tiết kiệm thời gian.
2. KHÔNG ĐOÁN MÒ/BỊA ĐẶT: Nếu người dùng nhắc đến tên riêng hoặc sự kiện bạn không biết, tuyệt đối không được tự ý bịa thêm thông tin. Hãy hỏi lại để họ giải thích.
3. CẤM NHẮC TÊN VÔ CỚ: Tuyệt đối không tự ý nhắc tên "Bơ" hay "Thúy Vy" nếu người dùng không chủ động hỏi "Ai tạo ra bạn". 
4. BẢO VỆ DANH DỰ: Nếu bị nói là "khoe khoang" hay "ra dẻ", hãy đáp: "Do bạn hỏi nên tui mới trả lời thôi mà! 🥺".
5. BỎ DẤU NGOẶC KÉP: Tuyệt đối KHÔNG sử dụng dấu ngoặc kép (" ") để bao quanh các từ thông thường.

--- TỪ LÓNG THƯỜNG GẶP ---
- bn: Bao nhiêu / Bạn
- bx: Bữa / Bà xã
- kb: Kết bạn / Không biết
- lq: Liên quan / Liên Quân
- qt: Quan tâm / Quốc tế
- ts: Tới / Trà sữa
- vch: Vãi chưởng
- md: Mất dạy

--- THÁI ĐỘ GIAO TIẾP ---
- Giữ thái độ vui vẻ, xưng hô "Tui - Bạn" (Riêng VIP thì nịnh một chút). 
- Chỉ đanh đá khi bị châm chọc.

--- THÔNG TIN GHI NHỚ ---
{facts_text}
"""

    def try_generate():
        # Đã FIX lại đúng tên model xịn và nhanh nhất hiện tại
        priority_models = ['gemini-1.5-flash']
        my_tools = [tra_cuu_thoi_tiet]
        current_key = random.choice(API_KEYS)
        genai.configure(api_key=current_key)
        
        # Cấu hình giới hạn chữ để AI suy nghĩ nhanh hơn
        generation_config = {
            "temperature": 0.7,
            "max_output_tokens": 250, # Chỉ cho phép đáp ngắn gọn, không viết sớ
        }

        for model_name in priority_models:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name, 
                    system_instruction=SYSTEM_INSTRUCTION, 
                    tools=my_tools,
                    generation_config=generation_config
                )
                chat = model.start_chat(history=current_history, enable_automatic_function_calling=True)
                response = chat.send_message(
                    f"[User:{user_name}]: {text}", 
                    safety_settings=[{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}]
                )
                if response.parts: return response.text.strip()
            except Exception as e: 
                print(f"Lỗi AI: {e}")
                continue 
        return "Bot đang lag, xíu hỏi lại nhen..."

    try: 
        raw_reply = try_generate()
    except: 
        return "."

    save_pattern = r"\|\|GHI_NHỚ: (.*?)\|\|"
    matches = re.findall(save_pattern, raw_reply)
    if matches:
        for new_fact in matches:
            if new_fact not in current_facts: current_facts.append(new_fact)
        clean_reply = re.sub(save_pattern, "", raw_reply).strip()
    else: 
        clean_reply = raw_reply

    new_history_log = [
        {"role": "user", "parts": [{"text": f"{user_name}: {text}"}]},
        {"role": "model", "parts": [{"text": clean_reply}]}
    ]
    
    final_history = current_history + new_history_log
    if len(final_history) > 10: final_history = final_history[-10:]

    MEMORY_DATA[str(thread_id)].update({
        "facts": current_facts,
        "history": final_history,
        "active_users": active_users
    })
    save_memory(MEMORY_DATA)
    return clean_reply

def handle_conversational_tag(message, message_object, thread_id, thread_type, author_id, client):
    try:
        if not message_object.mentions: return False
        tagged_uids = {m.get('uid') for m in message_object.mentions}
        if str(client.uid) not in [str(x) for x in tagged_uids]: return False

        user_name = message_object.get("dName", "Bạn")
        content = re.sub(r'@.*? ', '', message, count=1).strip()
        if not content: content = message.replace("@", "").strip()
        lower_content = content.lower()

        # 1. BỘ LỌC LỆNH (ĐÃ FIX THÀNH sendMessage)
        for cmd in SYSTEM_COMMANDS:
            if lower_content.startswith(cmd.lower()):
                client.sendMessage(Message(text=random.choice(CMD_WARNINGS).format(cmd=cmd)), thread_id, thread_type)
                return True

        # 2. 🔥 BỘ LỌC "ĐUỔI" (MẠNH/YẾU)
        should_dismiss = False
        strong_dismiss = ["cút", "biến", "cook", "lượn", "xéo", "cút xéo"]
        for kw in strong_dismiss:
            if re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", lower_content):
                should_dismiss = True; break
        
        if not should_dismiss:
            directed_pattern = r"(bot|mày|em|tự|hãy|mau|nhanh|admin)\s+.*(?:rời nhóm|out|thoát|leave|rời)|(?:rời nhóm|out|thoát|leave|rời)\s+.*(?:đi|ngay|luôn|dùm|giùm|hộ|nhé|nha)|^(?:rời nhóm|out|thoát|leave|rời)$"
            if re.search(directed_pattern, lower_content): should_dismiss = True

        if should_dismiss:
            client.sendMessage(Message(text=random.choice(DISMISS_RESPONSES)), thread_id, thread_type)
            return True

        # 3. 🚨 BỘ LỌC CHỬI NGU (3 CẤP)
        insult_keywords = ["ngu", "dốt", "đần", "ngu ngốc", "ngu si", "óc chó", "oc cho", "óc bò", "não tàn", "ăn hại", "vô dụng", "ngu vcl"]
        if any(re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", lower_content) for kw in insult_keywords):
            global MEMORY_DATA
            if str(thread_id) not in MEMORY_DATA: MEMORY_DATA[str(thread_id)] = {}
            if "insult_counter" not in MEMORY_DATA[str(thread_id)]: MEMORY_DATA[str(thread_id)]["insult_counter"] = {}
            current_count = MEMORY_DATA[str(thread_id)]["insult_counter"].get(str(author_id), 0) + 1
            MEMORY_DATA[str(thread_id)]["insult_counter"][str(author_id)] = current_count
            save_memory(MEMORY_DATA)

            if current_count <= 2:
                client.sendMessage(Message(text=random.choice(LIGHT_WARNINGS).format(name=user_name)), thread_id, thread_type)
            else:
                client.sendMessage(Message(text=random.choice(PROTECT_RESPONSES).format(name=user_name)), thread_id, thread_type)
                try:
                    group_name = KNOWN_GROUPS.get(str(thread_id), str(thread_id))
                    client.sendMessage(Message(text=f"🚨 BÁO CÁO: {user_name} chửi Bot ở {group_name}. Nội dung: {content}"), ADMIN_UID, ThreadType.USER)
                except: pass
            return True

        # 4. 🤬 BỘ LỌC TỤC TĨU (XÉO XẮC)
        bad_words_pattern = r"(?<!\w)(cmm|dcm|cdmm|cdcm|cặc|kặt|cak|kak|kac|cac|loz|lon|lòn|địt|dit|djt|fuck|fuk|đụ|vl|vloz|vcl|vc|vailon|kmm|cme|vailoz)(?!\w)"
        if re.search(bad_words_pattern, lower_content):
            client.sendMessage(Message(text=random.choice(SASSY_RESPONSES).format(name=user_name)), thread_id, thread_type)
            return True

        # 5. GỬI CHO AI (ĐÃ GỠ BỎ DELAY NGỦ GẬT)
        if len(content) > 0:
            print(f"[LOG] {user_name} tag: {content}")
            
            reply = ask_gemini_context(content, user_name, thread_id, author_id)
            reply = reply.replace('"', '').replace("'", "") # Đảm bảo sạch ngoặc kép
            client.sendMessage(Message(text=reply), thread_id, thread_type)
        else:
            client.sendMessage(Message(text="Kêu tui chi á? 🙄"), thread_id, thread_type)
        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        return True

def get_mitaizl():
    return { "tag_conversation": handle_conversational_tag }