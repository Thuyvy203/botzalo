from zlapi.models import Message
import requests
from datetime import datetime
import traceback
import urllib.parse  # Sử dụng urllib.parse để mã hóa chuỗi

# Cấu hình module
config = {
    "name": "thoitiet",
    "version": "1.0.0",
    "hasPermssion": 0,
    "credits": "D-Jukie",
    "description": "Xem thông tin thời tiết tại khu vực (toàn bộ tiếng Việt)",
    "commandCategory": "Tin tức",
    "usages": "[Location]",
    "cooldowns": 5
}

# Bảng tra các từ tiếng Anh thành tiếng Việt cho tình trạng thời tiết
translation_dict = {
    "Mostly cloudy": "Có nhiều mây",
    "Partly cloudy": "Có mây rải rác",
    "Clear": "Trong xanh",
    "Sunny": "Nắng",
    "Cloudy": "Nhiều mây",
    "Overcast": "U ám",
    "Rain": "Mưa",
    "Drizzle": "Mưa phùn",
    "Thunderstorm": "Bão",
    "Snow": "Tuyết",
    # Bạn có thể mở rộng thêm nếu cần
}

def translate_skytext(skytext):
    """Dịch trạng thái thời tiết sang tiếng Việt nếu có trong bảng tra."""
    for eng, vi in translation_dict.items():
        if eng.lower() in skytext.lower():
            return vi
    return skytext

def run(message, message_object, thread_id, thread_type, author_id, client, *extra):
    # Lấy địa điểm từ tin nhắn, bỏ phần lệnh đầu tiên.
    # Ví dụ: "!thoitiet Sài Gòn" -> "Sài Gòn"
    parts = message.split()
    if len(parts) < 2:
        client.sendMessage(Message(text="Vui lòng nhập 1 địa điểm"), thread_id, thread_type)
        return
    # Sử dụng tên địa điểm do người dùng nhập
    location = " ".join(parts[1:])
    
    try:
        res = requests.get(f"https://api.popcat.xyz/weather?q={location}")
        res.raise_for_status()
        # API trả về một mảng, lấy phần tử đầu tiên
        stt = res.json()[0]
        
        # Dịch trạng thái thời tiết (skytext) sang tiếng Việt
        skytext_en = stt["current"]["skytext"]
        skytext_vn = translate_skytext(skytext_en)
        
        # Định dạng ngày update theo "ngày-tháng-năm"
        update_date = stt["current"]["date"]  # Giả sử định dạng ban đầu là "YYYY-MM-DD"
        dt = datetime.strptime(update_date, "%Y-%m-%d")
        formatted_date = dt.strftime("%d-%m-%Y")
        
        # Sử dụng tên địa điểm do người dùng nhập (location) thay vì lấy từ API
        msg_text = (
            f"🌅 Địa điểm: {location}\n"
            f"🌡 Nhiệt độ: {stt['current']['temperature']}°C\n"
            f"☁️ Tình trạng: {skytext_vn}\n"
            f"💦 Độ ẩm: {stt['current']['humidity']}%\n"
            f"💨 Tốc độ gió: {stt['current']['windspeed']}\n"
            f"⏱️ Update: {formatted_date}"
        )
        client.sendMessage(Message(text=msg_text), thread_id, thread_type)
    except Exception:
        client.sendMessage(Message(text="Không tìm thấy địa điểm này!"), thread_id, thread_type)

def get_mitaizl():
    return {
        "thoitiet": run
    }
