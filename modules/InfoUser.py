from zlapi.models import Message
from zlapi import ZaloAPIException
from datetime import datetime
from config import PREFIX

def handle_infouser_command(message, message_object, thread_id, thread_type, author_id, client):
    msg_error = f"🔴 Something went wrong\n| Không thể lấy thông tin tài khoản Zalo!"
    try:
        if message_object.mentions:
            target_id = message_object.mentions[0]['uid']
        elif message[9:].strip().isnumeric():
            target_id = message[9:].strip()
        elif message.strip() == f"{PREFIX}infouser":
            target_id = author_id
        else:
            client.send(Message(text=msg_error), thread_id, thread_type)
            return
        
        msg = ""
        try:
            info = client.fetchUserInfo(target_id)
            # Giả sử info có thuộc tính unchanged_profiles hoặc changed_profiles là dict chứa thông tin người dùng theo user id.
            profiles = info.unchanged_profiles or info.changed_profiles
            if profiles and str(target_id) in profiles:
                profile = profiles[str(target_id)]
            else:
                client.send(Message(text=msg_error), thread_id, thread_type)
                return

            userId = getattr(profile, "userId", "Undefined")
            msg += f"• UID: {userId}\n"
            userName = getattr(profile, "zaloName", "Unknown")
            msg += f"• Tên: {userName}\n"
            gender = "Nam" if getattr(profile, "gender", -1) == 0 else "Nữ" if getattr(profile, "gender", -1) == 1 else "Không khả dụng"
            msg += f"• Giới tính: {gender}\n"
            status = getattr(profile, "status", "Mặc định")
            msg += f"• Tiểu sử: {status}\n"
            dob = getattr(profile, "dob", None)
            if isinstance(dob, int):
                dob = datetime.fromtimestamp(dob).strftime("%d/%m/%Y")
            else:
                dob = "Không hiển thị"
            msg += f"• Sinh nhật: {dob}\n"
            phoneNumber = getattr(profile, "phoneNumber", "Không hiển thị")
            if target_id == client.uid:
                phoneNumber = 'Không hiển thị'
            msg += f"• Số điện thoại: {phoneNumber}\n"
            lastAction = getattr(profile, "lastActionTime", None)
            if isinstance(lastAction, int):
                lastAction = datetime.fromtimestamp(lastAction/1000).strftime("%H:%M %d/%m/%Y")
            else:
                lastAction = "Không xác định"
            msg += f"• Hoạt động gần nhất: {lastAction}\n"
            createTime = getattr(profile, "createdTs", None)
            if isinstance(createTime, int):
                createTime = datetime.fromtimestamp(createTime).strftime("%H:%M %d/%m/%Y")
            else:
                createTime = "Không xác định"
            msg += f"• Thời gian tạo: {createTime}\n"
            msg += f"• Tình trạng: {'✅ Hoạt động' if getattr(profile, 'isBlocked', 1) == 0 else '🔒 Đã bị khóa'}\n"
            msg += f"• Windows: {'🟢 Kích hoạt' if getattr(profile, 'isActivePC', 0) == 1 else '🔴 Không kích hoạt'}\n"
            msg += f"• Web: {'🟢 Kích hoạt' if getattr(profile, 'isActiveWeb', 0) == 1 else '🔴 Không kích hoạt'}\n"
            msg += f"• Avatar: {getattr(profile, 'avatar', 'N/A')}\n"
            msg += f"• Background: {getattr(profile, 'cover', 'N/A')}\n"
            msg_to_send = Message(text=msg)
            client.replyMessage(msg_to_send, message_object, thread_id, thread_type)
        except ZaloAPIException as e:
            print(f"Error fetching user info: {e}")
    except Exception as e:
        client.send(Message(text="Đã xảy ra lỗi"), thread_id, thread_type)

def get_mitaizl():
    return {
        'infouser': handle_infouser_command
    }
